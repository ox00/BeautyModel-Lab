from __future__ import annotations

import asyncio
import logging

from celery import chain

from app.tasks.celery_app import celery_app
from app.tasks.crawl_tasks import crawl_platform
from app.tasks.clean_tasks import process_trend_data
from app.agents.base import AgentContext
from app.agents.trend_agent import TrendAgent
from app.agents.scheduler_agent import SchedulerAgent
from app.domain.services.keyword_service import KeywordService
from app.domain.services.task_service import TaskService
from app.infrastructure.database.connection import async_session_factory
from app.infrastructure.repositories.keyword_repo_impl import KeywordRepositoryImpl
from app.infrastructure.repositories.task_repo_impl import TaskRepositoryImpl

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.schedule_tasks.scheduled_crawl", queue="schedule")
def scheduled_crawl(platform: str) -> dict:
    """Celery Beat task: Find due keywords for a platform and schedule crawl tasks.

    This task runs on the 'schedule' queue and orchestrates:
    1. TrendAgent finds due keywords
    2. SchedulerAgent creates crawl tasks
    3. Each task is dispatched as a Celery chain: crawl -> clean

    Args:
        platform: The platform to schedule crawls for (xhs/dy/bili/wb).

    Returns:
        Dict with scheduling results.
    """
    return asyncio.run(_scheduled_crawl_async(platform))


async def _scheduled_crawl_async(platform: str) -> dict:
    """Async implementation of scheduled_crawl."""
    try:
        async with async_session_factory() as session:
            keyword_repo = KeywordRepositoryImpl(session)
            task_repo = TaskRepositoryImpl(session)

            keyword_service = KeywordService(keyword_repo)
            task_service = TaskService(task_repo)

            # Step 1: TrendAgent finds due keywords
            trend_agent = TrendAgent(keyword_service)
            trend_context = AgentContext(platform=platform)
            trend_result = await trend_agent.execute(trend_context)

            if not trend_result.success or trend_result.data.get("count", 0) == 0:
                logger.info(f"[scheduled_crawl] No due keywords for platform: {platform}")
                return {"platform": platform, "scheduled_count": 0}

            # Step 2: SchedulerAgent creates crawl tasks
            scheduler_agent = SchedulerAgent(task_service, keyword_service)
            scheduler_context = AgentContext(
                platform=platform,
                extra={"due_keywords": trend_result.data.get("due_keywords", [])},
            )
            scheduler_result = await scheduler_agent.execute(scheduler_context)

            if not scheduler_result.success:
                logger.error(f"[scheduled_crawl] Scheduler failed: {scheduler_result.error}")
                return {"platform": platform, "scheduled_count": 0, "error": scheduler_result.error}

            # Step 3: Dispatch Celery chains for each task
            scheduled_tasks = scheduler_result.data.get("scheduled_tasks", [])
            dispatched_count = 0

            for task_data in scheduled_tasks:
                task_id = task_data.get("id")
                if not task_id:
                    continue

                # Chain: crawl -> clean
                task_chain = chain(
                    crawl_platform.s(task_id),
                    process_trend_data.s(),
                )
                task_chain.apply_async()
                dispatched_count += 1

                logger.info(f"[scheduled_crawl] Dispatched chain for task {task_id} on {platform}")

            logger.info(f"[scheduled_crawl] Dispatched {dispatched_count} crawl chains for {platform}")
            return {"platform": platform, "scheduled_count": dispatched_count}

    except Exception as e:
        logger.error(f"[scheduled_crawl] Error for platform {platform}: {e}")
        return {"platform": platform, "scheduled_count": 0, "error": str(e)}
