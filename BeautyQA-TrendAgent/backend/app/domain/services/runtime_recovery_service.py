from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import CrawlTask, RuntimeBatchItem, RuntimeBatchRun


RETRYABLE_ERROR_TOKENS = (
    "timeout",
    "network",
    "connection",
    "temporary",
    "rate",
    "retry",
)


@dataclass
class BatchAuditSummary:
    run_id: str
    total_items: int
    succeeded_items: int
    failed_retryable_items: int
    failed_terminal_items: int
    running_items: int
    completion_classification: str


class RuntimeRecoveryService:
    """INT-005 recovery and completion-audit service."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_batch_item(self, *, batch_run_id: int, run_id: str, payload: dict[str, Any]) -> RuntimeBatchItem:
        query_unit_key = str(payload.get("query_unit_key", ""))
        stmt = select(RuntimeBatchItem).where(
            RuntimeBatchItem.batch_run_id == batch_run_id,
            RuntimeBatchItem.query_unit_key == query_unit_key,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()

        if existing:
            existing.keyword_id = payload.get("keyword_id", existing.keyword_id)
            existing.keyword = payload.get("keyword", existing.keyword)
            existing.platform = payload.get("platform", existing.platform)
            existing.expanded_query = payload.get("expanded_query", existing.expanded_query)
            existing.query_state_id = payload.get("query_state_id", existing.query_state_id)
            existing.payload = payload
            return existing

        item = RuntimeBatchItem(
            batch_run_id=batch_run_id,
            run_id=run_id,
            query_unit_key=query_unit_key,
            keyword_id=payload.get("keyword_id"),
            keyword=payload.get("keyword"),
            platform=str(payload.get("platform", "")),
            expanded_query=str(payload.get("expanded_query", "")),
            query_state_id=payload.get("query_state_id"),
            item_status="planned",
            retryable=True,
            attempt_count=0,
            payload=payload,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def mark_dispatched(self, *, run_id: str, query_unit_key: str, task_id: int) -> None:
        item = await self._get_item(run_id, query_unit_key)
        if not item:
            return
        item.task_id = task_id
        item.attempt_count = int(item.attempt_count or 0) + 1
        item.item_status = "dispatched"
        item.last_heartbeat_at = datetime.now()

    async def reconcile_stale_running_items(self, *, run_id: str, stale_minutes: int = 45) -> list[dict[str, Any]]:
        threshold = datetime.now() - timedelta(minutes=stale_minutes)
        stmt = select(RuntimeBatchItem).where(RuntimeBatchItem.run_id == run_id)
        items = list((await self._session.execute(stmt)).scalars().all())
        actions: list[dict[str, Any]] = []

        for item in items:
            if item.item_status not in {"running", "dispatched", "planned"}:
                continue
            if item.last_heartbeat_at and item.last_heartbeat_at > threshold:
                continue

            task = await self._session.get(CrawlTask, item.task_id) if item.task_id else None
            if task and task.status in {"completed"}:
                item.item_status = "succeeded"
                item.completed_at = datetime.now()
                actions.append({"query_unit_key": item.query_unit_key, "action": "close_as_succeeded"})
                continue
            if task and task.status in {"failed", "cancelled"}:
                retryable = self._is_retryable(task.error_message or "")
                item.item_status = "failed_retryable" if retryable else "failed_terminal"
                item.retryable = retryable
                item.last_error = task.error_message
                item.completed_at = datetime.now() if not retryable else None
                actions.append({
                    "query_unit_key": item.query_unit_key,
                    "action": "mark_failed_retryable" if retryable else "mark_failed_terminal",
                })
                continue

            # No terminal task state found -> keep retryable and push back to planned.
            item.item_status = "planned"
            item.retryable = True
            item.task_id = None
            actions.append({"query_unit_key": item.query_unit_key, "action": "requeue_planned"})

        await self._session.flush()
        return actions

    async def update_item_from_task_result(
        self,
        *,
        run_id: str,
        task_id: int,
        success: bool,
        cleaned_count: int,
        signal_count: int,
        error_message: str,
    ) -> None:
        stmt = select(RuntimeBatchItem).where(
            RuntimeBatchItem.run_id == run_id,
            RuntimeBatchItem.task_id == task_id,
        )
        items = list((await self._session.execute(stmt)).scalars().all())
        if not items:
            return

        for item in items:
            item.last_heartbeat_at = datetime.now()
            if success:
                if cleaned_count <= 0 or signal_count <= 0:
                    item.item_status = "failed_terminal"
                    item.retryable = False
                    item.last_error = (
                        f"empty_pipeline_output cleaned_count={cleaned_count} signal_count={signal_count}"
                    )
                    item.completed_at = datetime.now()
                    continue
                item.item_status = "succeeded"
                item.retryable = False
                item.completed_at = datetime.now()
                item.last_error = None
                continue

            retryable = self._is_retryable(error_message)
            item.item_status = "failed_retryable" if retryable else "failed_terminal"
            item.retryable = retryable
            item.last_error = error_message
            if not retryable:
                item.completed_at = datetime.now()

    async def build_completion_audit(self, *, run_id: str) -> BatchAuditSummary:
        stmt = select(RuntimeBatchItem).where(RuntimeBatchItem.run_id == run_id)
        items = list((await self._session.execute(stmt)).scalars().all())
        for item in items:
            await self._normalize_pipeline_outcome(item)

        total = len(items)
        succeeded = sum(1 for x in items if x.item_status == "succeeded")
        retryable_failed = sum(1 for x in items if x.item_status == "failed_retryable")
        terminal_failed = sum(1 for x in items if x.item_status == "failed_terminal")
        running = sum(1 for x in items if x.item_status in {"planned", "dispatched", "running"})

        classification = "failed"
        if total == 0:
            # No planned execution units means a no-op batch; keep batch/result aligned as completed.
            classification = "completed_full"
        elif succeeded == total:
            classification = "completed_full"
        elif succeeded > 0 and terminal_failed > 0 and retryable_failed == 0 and running == 0:
            classification = "completed_partial"

        batch_stmt = select(RuntimeBatchRun).where(RuntimeBatchRun.run_id == run_id)
        batch = (await self._session.execute(batch_stmt)).scalar_one_or_none()
        if batch:
            batch.completion_classification = classification
            if classification == "completed_full":
                batch.status = "completed"
            elif classification == "completed_partial":
                batch.status = "completed"
            else:
                batch.status = "failed"

        await self._session.flush()
        return BatchAuditSummary(
            run_id=run_id,
            total_items=total,
            succeeded_items=succeeded,
            failed_retryable_items=retryable_failed,
            failed_terminal_items=terminal_failed,
            running_items=running,
            completion_classification=classification,
        )

    async def list_requeue_candidates(self, *, run_id: str, limit: int = 50) -> list[RuntimeBatchItem]:
        stmt = (
            select(RuntimeBatchItem)
            .where(RuntimeBatchItem.run_id == run_id)
            .where(RuntimeBatchItem.item_status.in_(["planned", "failed_retryable"]))
            .order_by(RuntimeBatchItem.updated_at.asc())
            .limit(limit)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def _get_item(self, run_id: str, query_unit_key: str) -> RuntimeBatchItem | None:
        stmt = select(RuntimeBatchItem).where(
            RuntimeBatchItem.run_id == run_id,
            RuntimeBatchItem.query_unit_key == query_unit_key,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def _normalize_pipeline_outcome(self, item: RuntimeBatchItem) -> None:
        if item.item_status != "succeeded" or not item.task_id:
            return
        task = await self._session.get(CrawlTask, item.task_id)
        if not task:
            return

        result_summary = task.result_summary or {}
        signal_generation = result_summary.get("signal_generation", {}) or {}
        cleaned_count = int(result_summary.get("cleaned_count", 0) or 0)
        signal_count = int(signal_generation.get("signal_count", 0) or 0)

        if cleaned_count > 0 and signal_count > 0:
            return

        item.item_status = "failed_terminal"
        item.retryable = False
        item.last_error = f"empty_pipeline_output cleaned_count={cleaned_count} signal_count={signal_count}"
        item.completed_at = item.completed_at or datetime.now()

    @staticmethod
    def _is_retryable(error_message: str) -> bool:
        lowered = (error_message or "").lower()
        return any(token in lowered for token in RETRYABLE_ERROR_TOKENS)
