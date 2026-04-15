from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app
from app.agents.base import AgentContext
from app.agents.crawler_agent import CrawlerAgent
from app.domain.services.account_service import AccountService
from app.domain.services.task_service import TaskService
from app.infrastructure.crawler.adapter import CrawlerAdapter
from app.infrastructure.database.connection import async_session_factory
from app.infrastructure.repositories.account_repo_impl import AccountRepositoryImpl
from app.infrastructure.repositories.task_repo_impl import TaskRepositoryImpl

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.crawl_tasks.crawl_platform", queue="crawl")
def crawl_platform(self, task_id: int) -> dict:
    """Celery task: Execute a platform crawl via CrawlerAgent.

    This task runs in the 'crawl' queue and:
    1. Loads the CrawlTask from DB
    2. Executes the crawl via CrawlerAgent
    3. Returns the result for downstream chaining

    Args:
        task_id: The crawl_tasks table ID.

    Returns:
        Dict with task_id, success status, and platform/keyword info.
    """
    return asyncio.run(_crawl_platform_async(self, task_id))


async def _crawl_platform_async(celery_task, task_id: int) -> dict:
    """Async implementation of crawl_platform."""
    async with async_session_factory() as session:
        task_repo = TaskRepositoryImpl(session)
        account_repo = AccountRepositoryImpl(session)

        task_service = TaskService(task_repo)
        account_service = AccountService(account_repo)
        crawler_adapter = CrawlerAdapter()

        # Load task
        task = await task_service.get_task(task_id)
        if not task:
            logger.error(f"[crawl_platform] Task {task_id} not found")
            return {"task_id": task_id, "success": False, "error": "Task not found"}

        if task.status not in ("pending",):
            logger.warning(f"[crawl_platform] Task {task_id} is not pending (status={task.status})")
            return {"task_id": task_id, "success": False, "error": f"Task status is {task.status}"}

        # Execute via CrawlerAgent
        crawler_agent = CrawlerAgent(crawler_adapter, account_service, task_service)
        context = AgentContext(
            task_id=task_id,
            keyword_id=task.keyword_id,
            keyword=task.keyword,
            platform=task.platform,
        )

        result = await crawler_agent.execute(context)

        # Update celery task ID in DB
        if task_id:
            task_orm = await task_repo.get_by_id(task_id)
            if task_orm:
                task_orm.celery_task_id = celery_task.request.id
                await session.commit()

        return {
            "task_id": task_id,
            "success": result.success,
            "platform": task.platform,
            "keyword": task.keyword,
            "error": result.error if not result.success else "",
        }
