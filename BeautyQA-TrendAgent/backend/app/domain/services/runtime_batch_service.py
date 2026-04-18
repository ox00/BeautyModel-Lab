from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import RuntimeBatchItem, RuntimeBatchRun, RuntimeBatchRunEvent


class RuntimeBatchService:
    """Persist runtime batch runs and keyword/task-level execution events."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_run(
        self,
        *,
        run_id: str,
        run_type: str,
        trigger_source: str,
        profile_name: str,
        platforms: list[str],
        requested_options: dict[str, Any],
        effective_options: dict[str, Any],
    ) -> RuntimeBatchRun:
        batch = RuntimeBatchRun(
            run_id=run_id,
            run_type=run_type,
            trigger_source=trigger_source,
            profile_name=profile_name,
            status="running",
            platforms=platforms,
            requested_options=requested_options,
            effective_options=effective_options,
            started_at=datetime.now(),
        )
        self._session.add(batch)
        await self._session.flush()
        await self._session.refresh(batch)
        return batch

    async def get_by_run_id(self, run_id: str) -> Optional[RuntimeBatchRun]:
        stmt = select(RuntimeBatchRun).where(RuntimeBatchRun.run_id == run_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_event(
        self,
        *,
        batch_run_id: int,
        run_id: str,
        event_type: str,
        platform: str | None = None,
        keyword_id: int | None = None,
        keyword: str | None = None,
        task_id: int | None = None,
        dedup_key: str | None = None,
        payload: dict[str, Any] | None = None,
        message: str | None = None,
    ) -> RuntimeBatchRunEvent:
        event = RuntimeBatchRunEvent(
            batch_run_id=batch_run_id,
            run_id=run_id,
            event_type=event_type,
            platform=platform,
            keyword_id=keyword_id,
            keyword=keyword,
            task_id=task_id,
            dedup_key=dedup_key,
            payload=payload,
            message=message,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def finalize_run(
        self,
        *,
        batch_run_id: int,
        summary: dict[str, Any],
        report_paths: dict[str, str] | None,
        status: str,
        error_message: str = "",
    ) -> RuntimeBatchRun:
        batch = await self._session.get(RuntimeBatchRun, batch_run_id)
        if not batch:
            raise ValueError(f"Runtime batch run not found: {batch_run_id}")

        batch.summary = summary
        batch.report_paths = report_paths
        batch.status = status
        batch.error_message = error_message or None
        batch.completed_at = datetime.now()
        await self._session.flush()
        await self._session.refresh(batch)
        return batch

    async def add_batch_item(
        self,
        *,
        batch_run_id: int,
        run_id: str,
        query_unit_key: str,
        keyword_id: int | None,
        keyword: str | None,
        platform: str,
        expanded_query: str,
        query_state_id: int | None,
        payload: dict[str, Any] | None = None,
    ) -> RuntimeBatchItem:
        item = RuntimeBatchItem(
            batch_run_id=batch_run_id,
            run_id=run_id,
            query_unit_key=query_unit_key,
            keyword_id=keyword_id,
            keyword=keyword,
            platform=platform,
            expanded_query=expanded_query,
            query_state_id=query_state_id,
            item_status="planned",
            retryable=True,
            attempt_count=0,
            payload=payload,
        )
        self._session.add(item)
        await self._session.flush()
        return item
