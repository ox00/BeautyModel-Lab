from __future__ import annotations

import logging

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.agents.keyword_expander_agent import KeywordExpanderAgent
from app.domain.models.crawl_task import CrawlTaskCreate
from app.domain.services.keyword_expansion_service import (
    PLATFORM_LABEL_TO_CODE,
    normalize_due_platform,
)
from app.domain.services.runtime_query_state_service import build_query_unit_key
from app.domain.services.keyword_service import KeywordService
from app.domain.services.runtime_query_state_service import RuntimeQueryStateService
from app.domain.services.task_service import TaskService
from app.infrastructure.database.connection import async_session_factory

logger = logging.getLogger(__name__)


def _int_with_default(value: int | None, default: int) -> int:
    if value is None:
        return default
    return int(value)


class SchedulerAgent(BaseAgent):
    """Create platform-aware crawl tasks from structured keyword plans."""

    def __init__(self, task_service: TaskService, keyword_service: KeywordService) -> None:
        self._task_service = task_service
        self._keyword_service = keyword_service
        self._expander = KeywordExpanderAgent()

    @property
    def name(self) -> str:
        return "SchedulerAgent"

    async def execute(self, context: AgentContext) -> AgentResult:
        try:
            due_keywords = context.extra.get("due_keywords", [])
            if not due_keywords:
                platform = context.platform or None
                keyword_reads = await self._keyword_service.get_due_keywords(platform)
                due_keywords = [k.model_dump() for k in keyword_reads]

            if not due_keywords:
                logger.info("[%s] No due keywords to schedule", self.name)
                return AgentResult(success=True, data={"scheduled_tasks": [], "count": 0})

            scheduled: list[dict] = []
            skipped_duplicates: list[dict] = []
            keyword_events: list[dict] = []
            target_platform = normalize_due_platform(context.platform or None)
            task_config_overrides = context.extra.get("task_config_overrides", {})
            max_tasks_per_keyword = context.extra.get("max_tasks_per_keyword")
            dedup_window_hours = _int_with_default(context.extra.get("dedup_window_hours"), 168)
            retry_cooldown_hours = _int_with_default(context.extra.get("retry_cooldown_hours"), 24)

            for kw_data in due_keywords:
                keyword_id = kw_data["id"]
                keyword_text = kw_data["keyword"]

                expander_context = AgentContext(keyword=keyword_text, extra=kw_data)
                expander_result = await self._expander.execute(expander_context)
                if not expander_result.success:
                    logger.warning("[%s] Keyword plan build failed for '%s', skipping", self.name, keyword_text)
                    keyword_events.append(
                        {
                            "event_type": "planning_failed",
                            "keyword_id": keyword_id,
                            "keyword": keyword_text,
                            "platform": target_platform or "",
                            "message": expander_result.error or "planning_failed",
                        }
                    )
                    continue

                execution_plan = expander_result.data
                task_candidates = await self._load_due_candidates_from_registry(
                    keyword_meta=kw_data,
                    execution_plan=execution_plan,
                    target_platform=target_platform,
                    max_tasks_per_keyword=max_tasks_per_keyword,
                )

                if not task_candidates:
                    logger.info(
                        "[%s] No crawlable task candidates for '%s' (targets: %s)",
                        self.name,
                        keyword_text,
                        execution_plan.get("crawl_targets", []),
                    )
                    keyword_events.append(
                        {
                            "event_type": "no_task_candidates",
                            "keyword_id": keyword_id,
                            "keyword": keyword_text,
                            "platform": target_platform or "",
                            "payload": {
                                "crawl_targets": execution_plan.get("crawl_targets", []),
                                "reference_sources": execution_plan.get("reference_sources", []),
                            },
                            "message": "No crawlable task candidates after policy filtering",
                        }
                    )
                    continue

                for candidate in task_candidates:
                    platform = candidate["platform_code"]
                    task_keyword = candidate["expanded_query"]
                    task_config = {
                        "keywords_for_crawler": task_keyword,
                        "original_keyword": keyword_text,
                        "normalized_keyword": kw_data.get("normalized_keyword", keyword_text),
                        "query_origin": candidate["expansion_type"],
                        "based_on": candidate["based_on"],
                        "review_needed": candidate["review_needed"],
                        "crawl_goal": kw_data.get("crawl_goal", "trend_discovery"),
                        "risk_flag": kw_data.get("risk_flag", "low"),
                        "priority": kw_data.get("priority", "medium"),
                        "confidence": kw_data.get("confidence", "medium"),
                        "reference_sources": execution_plan.get("reference_sources", []),
                        "reference_packages": execution_plan.get("reference_packages", []),
                        "task_dedup_key": candidate["dedup_key"],
                        "query_unit_key": candidate["query_unit_key"],
                        "query_state_id": candidate["query_state_id"],
                    }

                    duplicate = await self._task_service.find_recent_duplicate(
                        keyword_id=keyword_id,
                        dedup_key=candidate["dedup_key"],
                        within_hours=dedup_window_hours,
                        retry_cooldown_hours=retry_cooldown_hours,
                    )
                    if duplicate:
                        duplicate_item = {
                            "keyword_id": keyword_id,
                            "keyword": keyword_text,
                            "platform": platform,
                            "task_keyword": task_keyword,
                            "dedup_key": candidate["dedup_key"],
                            "existing_task_id": duplicate.id,
                            "existing_status": duplicate.status,
                        }
                        skipped_duplicates.append(duplicate_item)
                        keyword_events.append(
                            {
                                "event_type": "skipped_duplicate",
                                **duplicate_item,
                                "message": f"Skipped duplicate task because existing task {duplicate.id} is {duplicate.status}",
                            }
                        )
                        logger.info(
                            "[%s] Skip duplicate task for '%s' on %s (query: %s, existing_task=%s, status=%s)",
                            self.name,
                            keyword_text,
                            platform,
                            task_keyword,
                            duplicate.id,
                            duplicate.status,
                        )
                        continue

                    task_create = CrawlTaskCreate(keyword_id=keyword_id, platform=platform)
                    task_read = await self._task_service.create_task(
                        task_create,
                        keyword_text,
                        task_keyword=task_keyword,
                        config_overrides={**task_config, **task_config_overrides},
                    )
                    scheduled_item = task_read.model_dump()
                    scheduled.append(scheduled_item)
                    await self._mark_query_state_scheduled(candidate["query_state_id"], task_read.id)
                    keyword_events.append(
                        {
                            "event_type": "scheduled",
                            "keyword_id": keyword_id,
                            "keyword": keyword_text,
                            "platform": platform,
                            "task_keyword": task_keyword,
                            "task_id": task_read.id,
                            "dedup_key": candidate["dedup_key"],
                            "payload": {
                                "query_origin": candidate["expansion_type"],
                                "based_on": candidate["based_on"],
                                "review_needed": candidate["review_needed"],
                                "query_unit_key": candidate["query_unit_key"],
                            },
                            "message": f"Scheduled task {task_read.id} for query {task_keyword}",
                        }
                    )

                    logger.info(
                        "[%s] Created crawl task %s for '%s' on %s (query: %s, origin: %s)",
                        self.name,
                        task_read.id,
                        keyword_text,
                        platform,
                        task_keyword,
                        candidate["expansion_type"],
                    )

            logger.info("[%s] Scheduled %s crawl tasks", self.name, len(scheduled))
            return AgentResult(
                success=True,
                data={
                    "scheduled_tasks": scheduled,
                    "skipped_duplicates": skipped_duplicates,
                    "keyword_events": keyword_events,
                    "count": len(scheduled),
                },
            )
        except Exception as e:
            logger.error("[%s] Error scheduling tasks: %s", self.name, e)
            return AgentResult(success=False, error=str(e))

    async def _load_due_candidates_from_registry(
        self,
        *,
        keyword_meta: dict,
        execution_plan: dict,
        target_platform: str | None,
        max_tasks_per_keyword: int | None,
    ) -> list[dict]:
        # Persist planner output into first-party registry + query schedule state.
        # Runtime scheduling reads only approved + due query units.
        async with async_session_factory() as session:
            query_state_service = RuntimeQueryStateService(session)
            registry_rows = execution_plan.get("registry_rows", [])
            await query_state_service.upsert_expansion_registry(
                keyword_meta=keyword_meta,
                expansion_rows=registry_rows,
            )
            platform_codes_filter = []
            platform_label = target_platform or ""
            platform_code = PLATFORM_LABEL_TO_CODE.get(platform_label, platform_label)
            if platform_code:
                platform_codes_filter = [platform_code]

            active_registry_rows = await query_state_service.list_active_registry_rows(
                keyword_db_id=int(keyword_meta["id"]),
                platform_codes=platform_codes_filter or None,
            )
            approved_rows = [row for row in active_registry_rows if row.status == "approved" and row.is_active]
            states = await query_state_service.ensure_query_state_for_expansions(
                keyword_meta=keyword_meta,
                approved_rows=approved_rows,
                platform_label_to_code=PLATFORM_LABEL_TO_CODE,
            )
            state_map = {state.query_unit_key: state for state in states}

            if platform_code:
                due_states = await query_state_service.list_due_query_units(
                    keyword_db_id=int(keyword_meta["id"]),
                    platform_code=platform_code,
                    limit=int(max_tasks_per_keyword) if isinstance(max_tasks_per_keyword, int) and max_tasks_per_keyword > 0 else 3,
                )
            else:
                due_states = []
                platform_codes = sorted(
                    {PLATFORM_LABEL_TO_CODE.get(row.platform, row.platform) for row in active_registry_rows}
                )
                for code in platform_codes:
                    due_states.extend(
                        await query_state_service.list_due_query_units(
                            keyword_db_id=int(keyword_meta["id"]),
                            platform_code=code,
                            limit=int(max_tasks_per_keyword) if isinstance(max_tasks_per_keyword, int) and max_tasks_per_keyword > 0 else 3,
                        )
                    )

            planner_candidate_map = {}
            normalized_keyword = keyword_meta.get("normalized_keyword") or keyword_meta.get("keyword") or ""
            for candidate in execution_plan.get("task_candidates", []):
                query_unit_key = build_query_unit_key(
                    normalized_keyword,
                    candidate.get("platform_code", ""),
                    candidate.get("expanded_query", ""),
                )
                planner_candidate_map[query_unit_key] = candidate

            registry_map = {}
            for row in approved_rows:
                row_platform_code = PLATFORM_LABEL_TO_CODE.get(row.platform, row.platform)
                query_unit_key = build_query_unit_key(normalized_keyword, row_platform_code, row.expanded_query)
                registry_map[query_unit_key] = row

            candidates: list[dict] = []
            review_needed = execution_plan.get("review_needed", False)
            keyword_business_id = keyword_meta.get("keyword_id", "KW_UNKNOWN")
            for due_state in due_states:
                state = state_map.get(due_state.query_unit_key, due_state)
                registry_row = registry_map.get(due_state.query_unit_key)
                if not registry_row:
                    continue
                planner_candidate = planner_candidate_map.get(due_state.query_unit_key, {})
                platform_label_value = registry_row.platform
                platform_code_value = PLATFORM_LABEL_TO_CODE.get(platform_label_value, platform_label_value)
                candidates.append(
                    {
                        "expanded_query": registry_row.expanded_query,
                        "platform": platform_label_value,
                        "platform_code": platform_code_value,
                        "expansion_type": planner_candidate.get("expansion_type", registry_row.expansion_type),
                        "based_on": planner_candidate.get("based_on", registry_row.based_on),
                        "crawl_goal": planner_candidate.get(
                            "crawl_goal",
                            keyword_meta.get("crawl_goal", "trend_discovery"),
                        ),
                        "confidence": planner_candidate.get(
                            "confidence",
                            keyword_meta.get("confidence", "medium"),
                        ),
                        "review_needed": planner_candidate.get("review_needed", review_needed),
                        "dedup_key": planner_candidate.get(
                            "dedup_key",
                            f"{keyword_business_id}__{platform_label_value}__{registry_row.expanded_query}",
                        ),
                        "query_unit_key": due_state.query_unit_key,
                        "query_state_id": state.id,
                    }
                )

            await session.commit()
            return candidates

    async def _mark_query_state_scheduled(self, query_state_id: int, task_id: int) -> None:
        async with async_session_factory() as session:
            query_state_service = RuntimeQueryStateService(session)
            await query_state_service.mark_scheduled(query_state_id, task_id=task_id)
            await session.commit()
