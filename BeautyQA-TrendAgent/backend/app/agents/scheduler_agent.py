from __future__ import annotations

import logging

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.agents.keyword_expander_agent import KeywordExpanderAgent
from app.domain.models.crawl_task import CrawlTaskCreate
from app.domain.services.keyword_expansion_service import normalize_due_platform
from app.domain.services.keyword_service import KeywordService
from app.domain.services.task_service import TaskService

logger = logging.getLogger(__name__)


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
            target_platform = normalize_due_platform(context.platform or None)

            for kw_data in due_keywords:
                keyword_id = kw_data["id"]
                keyword_text = kw_data["keyword"]

                expander_context = AgentContext(keyword=keyword_text, extra=kw_data)
                expander_result = await self._expander.execute(expander_context)
                if not expander_result.success:
                    logger.warning("[%s] Keyword plan build failed for '%s', skipping", self.name, keyword_text)
                    continue

                execution_plan = expander_result.data
                task_candidates = execution_plan.get("task_candidates", [])
                if target_platform:
                    task_candidates = [
                        item
                        for item in task_candidates
                        if item.get("platform") == target_platform
                    ]

                if not task_candidates:
                    logger.info(
                        "[%s] No crawlable task candidates for '%s' (targets: %s)",
                        self.name,
                        keyword_text,
                        execution_plan.get("crawl_targets", []),
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
                    }

                    task_create = CrawlTaskCreate(keyword_id=keyword_id, platform=platform)
                    task_read = await self._task_service.create_task(
                        task_create,
                        keyword_text,
                        task_keyword=task_keyword,
                        config_overrides=task_config,
                    )
                    scheduled.append(task_read.model_dump())

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
            return AgentResult(success=True, data={"scheduled_tasks": scheduled, "count": len(scheduled)})
        except Exception as e:
            logger.error("[%s] Error scheduling tasks: %s", self.name, e)
            return AgentResult(success=False, error=str(e))
