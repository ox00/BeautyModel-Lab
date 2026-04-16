from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app
from app.agents.base import AgentContext
from app.agents.cleaning_agent import CleaningAgent
from app.agents.signal_agent import SignalAgent

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.clean_tasks.process_trend_data", queue="process")
def process_trend_data(self, crawl_result: dict) -> dict:
    """Celery task: Run AI data cleaning on crawled data.

    This task runs in the 'process' queue and:
    1. Reads raw data from MediaCrawler tables
    2. Calls LLM for summarization, classification, and sentiment analysis
    3. Writes cleaned results to cleaned_trend_data table

    Typically chained after crawl_platform:
        chain(crawl_platform.s(task_id), process_trend_data.s())

    Args:
        crawl_result: Output from the previous crawl task.
            Expected keys: task_id, success, platform, keyword

    Returns:
        Dict with cleaning results.
    """
    if not crawl_result.get("success", False):
        logger.warning(f"[process_trend_data] Skipping - crawl failed: {crawl_result.get('error', '')}")
        return {"task_id": crawl_result.get("task_id", 0), "success": False, "skipped": True}

    return asyncio.run(_process_trend_data_async(crawl_result))


async def _process_trend_data_async(crawl_result: dict) -> dict:
    """Async implementation of process_trend_data."""
    task_id = crawl_result.get("task_id", 0)
    platform = crawl_result.get("platform", "")
    keyword = crawl_result.get("keyword", "")

    if not task_id or not platform or not keyword:
        logger.error(f"[process_trend_data] Missing required fields in crawl_result: {crawl_result}")
        return {"task_id": task_id, "success": False, "error": "Missing task_id, platform, or keyword"}

    try:
        cleaning_agent = CleaningAgent()
        context = AgentContext(
            task_id=task_id,
            keyword=keyword,
            platform=platform,
        )

        result = await cleaning_agent.execute(context)
        signal_result = {"success": False, "signal_count": 0, "error": "cleaning_not_run"}

        if result.success:
            signal_agent = SignalAgent()
            signal_agent_result = await signal_agent.execute(context)
            signal_result = {
                "success": signal_agent_result.success,
                "signal_count": signal_agent_result.data.get("signal_count", 0) if signal_agent_result.success else 0,
                "output_file": signal_agent_result.data.get("output_file", ""),
                "error": signal_agent_result.error if not signal_agent_result.success else "",
            }
        else:
            signal_result = {"success": False, "signal_count": 0, "error": "skipped_due_to_cleaning_failure"}

        # TA-001 requires first-party trend_signal output path.
        # Mark the task as success only when both cleaning and signal generation succeed.
        overall_success = result.success and signal_result["success"]
        error_parts = []
        if not result.success and result.error:
            error_parts.append(f"cleaning_failed: {result.error}")
        if result.success and not signal_result["success"] and signal_result["error"]:
            error_parts.append(f"signal_generation_failed: {signal_result['error']}")

        return {
            "task_id": task_id,
            "success": overall_success,
            "cleaned_count": result.data.get("cleaned_count", 0) if result.success else 0,
            "error": "; ".join(error_parts),
            "signal_generation": signal_result,
        }

    except Exception as e:
        logger.error(f"[process_trend_data] Cleaning failed for task {task_id}: {e}")
        return {"task_id": task_id, "success": False, "error": str(e)}
