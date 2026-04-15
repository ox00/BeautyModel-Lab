from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import CrawlTask, CrawlTaskLog


class TaskRepositoryImpl:
    """SQLAlchemy implementation of TaskRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, task_id: int) -> Optional[CrawlTask]:
        result = await self._session.get(CrawlTask, task_id)
        return result

    async def list_by_status(
        self, status: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> Sequence[CrawlTask]:
        stmt = select(CrawlTask)
        if status:
            stmt = stmt.where(CrawlTask.status == status)
        stmt = stmt.order_by(CrawlTask.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_by_keyword(self, keyword_id: int) -> Sequence[CrawlTask]:
        stmt = select(CrawlTask).where(CrawlTask.keyword_id == keyword_id)
        stmt = stmt.order_by(CrawlTask.created_at.desc())
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create(self, task: CrawlTask) -> CrawlTask:
        self._session.add(task)
        await self._session.flush()
        await self._session.refresh(task)
        return task

    async def update(self, task: CrawlTask) -> CrawlTask:
        await self._session.flush()
        await self._session.refresh(task)
        return task

    async def add_log(self, task_id: int, level: str, message: str) -> CrawlTaskLog:
        log = CrawlTaskLog(task_id=task_id, level=level, message=message)
        self._session.add(log)
        await self._session.flush()
        return log

    async def get_logs(self, task_id: int, limit: int = 100) -> Sequence[CrawlTaskLog]:
        stmt = (
            select(CrawlTaskLog)
            .where(CrawlTaskLog.task_id == task_id)
            .order_by(CrawlTaskLog.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
