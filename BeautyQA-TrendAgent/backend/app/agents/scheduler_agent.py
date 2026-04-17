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
            skipped_duplicates: list[dict] = []
            keyword_events: list[dict] = []
            target_platform = normalize_due_platform(context.platform or None)
            task_config_overrides = context.extra.get("task_config_overrides", {})
            max_tasks_per_keyword = context.extra.get("max_tasks_per_keyword")
            dedup_window_hours = int(context.extra.get("dedup_window_hours", 168) or 168)
            retry_cooldown_hours = int(context.extra.get("retry_cooldown_hours", 24) or 24)

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
                task_candidates = execution_plan.get("task_candidates", [])
                if target_platform:
                    task_candidates = [
                        item
                        for item in task_candidates
                        if item.get("platform") == target_platform
                    ]
                if isinstance(max_tasks_per_keyword, int) and max_tasks_per_keyword > 0:
                    task_candidates = task_candidates[:max_tasks_per_keyword]

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
