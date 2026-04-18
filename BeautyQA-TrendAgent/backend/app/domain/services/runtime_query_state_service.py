from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ExpansionRegistry, QueryScheduleState
from app.domain.services.keyword_expansion_service import PLATFORM_LABEL_TO_CODE


TIER_POLICY = {
    # docs/20 + docs/19 runtime policy defaults
    "watchlist-hot": {
        "default_revisit_minutes": 12 * 60,
        "xhs_revisit_minutes": 24 * 60,
        "default_retry_cooldown_minutes": 24 * 60,
        "xhs_retry_cooldown_minutes": 72 * 60,
    },
    "watchlist-normal": {
        "default_revisit_minutes": 24 * 60,
        "xhs_revisit_minutes": 48 * 60,
        "default_retry_cooldown_minutes": 24 * 60,
        "xhs_retry_cooldown_minutes": 72 * 60,
    },
    "discovery": {
        "default_revisit_minutes": 3 * 24 * 60,
        "xhs_revisit_minutes": 7 * 24 * 60,
        "default_retry_cooldown_minutes": 12 * 60,
        "xhs_retry_cooldown_minutes": 72 * 60,
    },
}


def infer_watchlist_tier(priority: str, crawl_goal: str) -> str:
    if crawl_goal == "risk_monitoring" or priority == "high":
        return "watchlist-hot"
    if priority == "low":
        return "discovery"
    return "watchlist-normal"


def build_query_unit_key(normalized_keyword: str, platform: str, expanded_query: str) -> str:
    return f"{normalized_keyword.strip().lower()}__{platform.strip().lower()}__{expanded_query.strip().lower()}"


def tier_intervals(tier: str, platform_code: str) -> tuple[int, int]:
    policy = TIER_POLICY.get(tier, TIER_POLICY["watchlist-normal"])
    is_xhs = platform_code == "xhs"
    revisit = policy["xhs_revisit_minutes"] if is_xhs else policy["default_revisit_minutes"]
    cooldown = policy["xhs_retry_cooldown_minutes"] if is_xhs else policy["default_retry_cooldown_minutes"]
    return revisit, cooldown


class RuntimeQueryStateService:
    """Owns expansion registry and durable query schedule state."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_expansion_registry(
        self,
        *,
        keyword_meta: dict,
        expansion_rows: list[dict],
    ) -> list[ExpansionRegistry]:
        now = datetime.now()
        saved: list[ExpansionRegistry] = []

        for row in expansion_rows:
            normalized_keyword = keyword_meta.get("normalized_keyword") or keyword_meta.get("keyword") or ""
            stmt = select(ExpansionRegistry).where(
                ExpansionRegistry.keyword_db_id == int(keyword_meta["id"]),
                ExpansionRegistry.platform == row["platform"],
                ExpansionRegistry.expanded_query == row["expanded_query"],
            )
            existing = (await self._session.execute(stmt)).scalar_one_or_none()

            status = row.get("status", "approved")
            review_status = row.get("review_status", "approved")
            source_type = row.get("source_type", "manual")
            ttl_days = int(row.get("ttl_days", 30) or 30)

            if existing:
                existing.expansion_type = row.get("expansion_type", existing.expansion_type)
                existing.based_on = row.get("based_on", existing.based_on)
                existing.ttl_days = ttl_days
                existing.expires_at = now + timedelta(days=ttl_days)
                existing.last_seen_at = now
                existing.notes = row.get("notes", existing.notes)
                # Preserve operator decisions once a registry row has been reviewed or manually deprecated.
                operator_locked = existing.review_status in {"approved", "rejected"} or existing.status in {
                    "approved",
                    "deprecated",
                }
                if not operator_locked:
                    existing.source_type = source_type
                    existing.review_status = review_status
                    existing.status = status
                    existing.is_active = status != "deprecated"
                saved.append(existing)
                continue

            item = ExpansionRegistry(
                keyword_db_id=int(keyword_meta["id"]),
                keyword_id=str(keyword_meta.get("keyword_id", "")),
                normalized_keyword=normalized_keyword,
                platform=row["platform"],
                expanded_query=row["expanded_query"],
                expansion_type=row.get("expansion_type", "seed"),
                based_on=row.get("based_on"),
                source_type=source_type,
                review_status=review_status,
                status=status,
                ttl_days=ttl_days,
                expires_at=now + timedelta(days=ttl_days),
                is_active=status != "deprecated",
                notes=row.get("notes"),
            )
            self._session.add(item)
            saved.append(item)

        await self._session.flush()
        return saved

    async def list_active_registry_rows(
        self,
        *,
        keyword_db_id: int,
        platform_codes: list[str] | None = None,
    ) -> list[ExpansionRegistry]:
        stmt = (
            select(ExpansionRegistry)
            .where(ExpansionRegistry.keyword_db_id == keyword_db_id)
            .where(ExpansionRegistry.is_active == True)  # noqa: E712
            .where(ExpansionRegistry.status == "approved")
        )
        if platform_codes:
            platform_labels = sorted(
                {
                    label
                    for label, code in PLATFORM_LABEL_TO_CODE.items()
                    if code in set(platform_codes) and label not in PLATFORM_LABEL_TO_CODE.values()
                }
            )
            if platform_labels:
                stmt = stmt.where(ExpansionRegistry.platform.in_(platform_labels))
        stmt = stmt.order_by(ExpansionRegistry.platform.asc(), ExpansionRegistry.expanded_query.asc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def ensure_query_state_for_expansions(
        self,
        *,
        keyword_meta: dict,
        approved_rows: list[ExpansionRegistry],
        platform_label_to_code: dict[str, str],
    ) -> list[QueryScheduleState]:
        now = datetime.now()
        tier = infer_watchlist_tier(
            str(keyword_meta.get("priority", "medium")),
            str(keyword_meta.get("crawl_goal", "trend_discovery")),
        )
        risk_level = str(keyword_meta.get("risk_flag", "low"))

        states: list[QueryScheduleState] = []
        for row in approved_rows:
            platform_code = platform_label_to_code.get(row.platform, row.platform)
            query_key = build_query_unit_key(row.normalized_keyword, platform_code, row.expanded_query)
            stmt = select(QueryScheduleState).where(QueryScheduleState.query_unit_key == query_key)
            existing = (await self._session.execute(stmt)).scalar_one_or_none()
            revisit, cooldown = tier_intervals(tier, platform_code)

            if existing:
                existing.tier = tier
                existing.risk_level = risk_level
                existing.min_revisit_interval_minutes = revisit
                existing.retry_cooldown_minutes = cooldown
                existing.is_active = row.is_active and row.status == "approved"
                states.append(existing)
                continue

            state = QueryScheduleState(
                query_unit_key=query_key,
                keyword_db_id=int(keyword_meta["id"]),
                keyword_id=str(keyword_meta.get("keyword_id", "")),
                normalized_keyword=row.normalized_keyword,
                platform=platform_code,
                expanded_query=row.expanded_query,
                tier=tier,
                risk_level=risk_level,
                min_revisit_interval_minutes=revisit,
                retry_cooldown_minutes=cooldown,
                next_due_at=now,
                is_active=row.is_active and row.status == "approved",
            )
            self._session.add(state)
            states.append(state)

        await self._session.flush()
        return states

    async def list_due_query_units(
        self,
        *,
        keyword_db_id: int,
        platform_code: str,
        limit: int,
    ) -> list[QueryScheduleState]:
        now = datetime.now()
        stmt = (
            select(QueryScheduleState)
            .where(QueryScheduleState.keyword_db_id == keyword_db_id)
            .where(QueryScheduleState.platform == platform_code)
            .where(QueryScheduleState.is_active == True)  # noqa: E712
            .where(QueryScheduleState.next_due_at <= now)
            .order_by(QueryScheduleState.next_due_at.asc())
            .limit(limit)
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def mark_scheduled(self, query_state_id: int, *, task_id: int) -> None:
        state = await self._session.get(QueryScheduleState, query_state_id)
        if not state:
            return
        now = datetime.now()
        state.last_scheduled_at = now
        state.last_task_id = task_id
        state.last_task_status = "scheduled"

    async def mark_task_success(self, task_config: dict) -> None:
        query_state_id = task_config.get("query_state_id")
        if not query_state_id:
            return
        state = await self._session.get(QueryScheduleState, int(query_state_id))
        if not state:
            return

        now = datetime.now()
        state.last_success_at = now
        state.last_task_status = "completed"
        state.failure_count = 0
        state.next_due_at = now + timedelta(minutes=state.min_revisit_interval_minutes)

    async def mark_task_failure(self, task_config: dict) -> None:
        query_state_id = task_config.get("query_state_id")
        if not query_state_id:
            return
        state = await self._session.get(QueryScheduleState, int(query_state_id))
        if not state:
            return

        now = datetime.now()
        state.last_failed_at = now
        state.last_task_status = "failed"
        state.failure_count = int(state.failure_count or 0) + 1
        state.next_due_at = now + timedelta(minutes=state.retry_cooldown_minutes)
