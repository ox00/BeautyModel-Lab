from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from app.domain.models.crawl_task import CrawlTaskCreate, CrawlTaskRead
from app.infrastructure.database.models import CrawlTask
from app.infrastructure.repositories.task_repo_impl import TaskRepositoryImpl

logger = logging.getLogger(__name__)


class TaskService:
    """Domain service for managing crawl tasks."""

    def __init__(self, repo: TaskRepositoryImpl) -> None:
        self._repo = repo

    async def create_task(self, data: CrawlTaskCreate, keyword_text: str) -> CrawlTaskRead:
        task = CrawlTask(
            keyword_id=data.keyword_id,
            keyword=keyword_text,
            platform=data.platform,
            status="pending",
            config={
                "login_type": data.login_type,
                "headless": data.headless,
                "enable_comments": data.enable_comments,
                "enable_sub_comments": data.enable_sub_comments,
                "start_page": data.start_page,
                "max_notes_count": data.max_notes_count,
            },
        )
        task = await self._repo.create(task)
        return CrawlTaskRead.model_validate(task)

    async def get_task(self, task_id: int) -> Optional[CrawlTaskRead]:
        task = await self._repo.get_by_id(task_id)
        return CrawlTaskRead.model_validate(task) if task else None

    async def list_tasks(
        self, status: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> list[CrawlTaskRead]:
        tasks = await self._repo.list_by_status(status, limit, offset)
        return [CrawlTaskRead.model_validate(t) for t in tasks]

    async def mark_running(self, task_id: int, celery_task_id: str, account_id: int) -> Optional[CrawlTaskRead]:
        task = await self._repo.get_by_id(task_id)
        if not task:
            return None
        task.status = "running"
        task.celery_task_id = celery_task_id
        task.account_id = account_id
        task.started_at = datetime.now()
        task = await self._repo.update(task)
        await self._repo.add_log(task_id, "info", f"Task started with celery_task_id={celery_task_id}")
        return CrawlTaskRead.model_validate(task)

    async def mark_completed(self, task_id: int, result_summary: dict) -> Optional[CrawlTaskRead]:
        task = await self._repo.get_by_id(task_id)
        if not task:
            return None
        task.status = "completed"
        task.completed_at = datetime.now()
        task.result_summary = result_summary
        task = await self._repo.update(task)
        await self._repo.add_log(task_id, "success", f"Task completed. Summary: {result_summary}")
        return CrawlTaskRead.model_validate(task)

    async def mark_failed(self, task_id: int, error_message: str) -> Optional[CrawlTaskRead]:
        task = await self._repo.get_by_id(task_id)
        if not task:
            return None
        task.status = "failed"
        task.completed_at = datetime.now()
        task.error_message = error_message
        task = await self._repo.update(task)
        await self._repo.add_log(task_id, "error", f"Task failed: {error_message}")
        return CrawlTaskRead.model_validate(task)

    async def mark_cancelled(self, task_id: int) -> Optional[CrawlTaskRead]:
        task = await self._repo.get_by_id(task_id)
        if not task:
            return None
        task.status = "cancelled"
        task.completed_at = datetime.now()
        task = await self._repo.update(task)
        await self._repo.add_log(task_id, "warning", "Task cancelled by user")
        return CrawlTaskRead.model_validate(task)

    async def add_log(self, task_id: int, level: str, message: str) -> None:
        await self._repo.add_log(task_id, level, message)

    async def update_config(self, task_id: int, config: dict) -> Optional[CrawlTaskRead]:
        """Update the config JSON of an existing task."""
        task = await self._repo.get_by_id(task_id)
        if not task:
            return None
        task.config = config
        task = await self._repo.update(task)
        return CrawlTaskRead.model_validate(task)
