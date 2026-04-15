from __future__ import annotations

import logging

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.agents.keyword_expander_agent import KeywordExpanderAgent
from app.domain.services.task_service import TaskService
from app.domain.services.keyword_service import KeywordService
from app.domain.models.crawl_task import CrawlTaskCreate
from app.infrastructure.crawler.config_mapper import CrawlerConfigMapper

logger = logging.getLogger(__name__)


class SchedulerAgent(BaseAgent):
    """Agent responsible for scheduling crawl tasks based on keyword configurations.

    This agent:
    1. Gets due keywords from TrendAgent
    2. Expands keywords via KeywordExpanderAgent (LLM-powered beauty domain expansion)
    3. Creates CrawlTask records with expanded keywords for each keyword/platform pair
    4. Dispatches Celery tasks for execution
    """

    def __init__(self, task_service: TaskService, keyword_service: KeywordService) -> None:
        self._task_service = task_service
        self._keyword_service = keyword_service
        self._expander = KeywordExpanderAgent()

    @property
    def name(self) -> str:
        return "SchedulerAgent"

    async def execute(self, context: AgentContext) -> AgentResult:
        """Create crawl tasks for due keywords and dispatch them.

        Expects context.data['due_keywords'] to contain the list of due keywords
        (typically provided by TrendAgent's output).
        """
        try:
            due_keywords = context.extra.get("due_keywords", [])

            if not due_keywords:
                # Try to fetch due keywords ourselves
                platform = context.platform or None
                keyword_reads = await self._keyword_service.get_due_keywords(platform)
                due_keywords = [k.model_dump() for k in keyword_reads]

            if not due_keywords:
                logger.info(f"[{self.name}] No due keywords to schedule")
                return AgentResult(success=True, data={"scheduled_tasks": [], "count": 0})

            scheduled = []
            for kw_data in due_keywords:
                keyword_id = kw_data["id"]
                keyword_text = kw_data["keyword"]
                topic_cluster = kw_data.get("topic_cluster", "")
                trend_type = kw_data.get("trend_type", "ingredient")
                query_variants = kw_data.get("query_variants", "")

                # Step 1: Expand keyword via LLM
                expander_context = AgentContext(
                    keyword=keyword_text,
                    extra={
                        "topic_cluster": topic_cluster,
                        "trend_type": trend_type,
                        "query_variants": query_variants,
                    },
                )
                expander_result = await self._expander.execute(expander_context)

                if expander_result.success:
                    keywords_for_crawler = expander_result.data.get(
                        "keywords_for_crawler", keyword_text
                    )
                    expanded_keywords = expander_result.data.get("expanded_keywords", [])
                    logger.info(
                        f"[{self.name}] Keyword '{keyword_text}' expanded: "
                        f"{expanded_keywords} → crawler keywords: {keywords_for_crawler}"
                    )
                else:
                    # Fallback: use original keyword only
                    keywords_for_crawler = keyword_text
                    logger.warning(
                        f"[{self.name}] Keyword expansion failed for '{keyword_text}', "
                        f"using original keyword only"
                    )

                # Step 2: Parse crawlable platforms
                suggested = kw_data.get("suggested_platforms", "xiaohongshu")
                crawlable_platforms = CrawlerConfigMapper.parse_suggested_platforms(suggested)

                if not crawlable_platforms:
                    logger.info(
                        f"[{self.name}] No crawlable platforms for keyword '{keyword_text}' "
                        f"(suggested: {suggested}), skipping"
                    )
                    continue

                # Step 3: Create crawl tasks with expanded keywords
                for platform in crawlable_platforms:
                    task_create = CrawlTaskCreate(
                        keyword_id=keyword_id,
                        platform=platform,
                    )
                    task_read = await self._task_service.create_task(task_create, keyword_text)

                    # Store expanded keywords in task config for CrawlerAgent to use
                    if keywords_for_crawler != keyword_text:
                        task = await self._task_service.get_task(task_read.id)
                        if task:
                            existing_config = task.config or {}
                            existing_config["keywords_for_crawler"] = keywords_for_crawler
                            existing_config["original_keyword"] = keyword_text
                            existing_config["expanded_keywords"] = expanded_keywords if expander_result.success else []
                            await self._task_service.update_config(task_read.id, existing_config)

                    scheduled.append(task_read.model_dump())

                    logger.info(
                        f"[{self.name}] Created crawl task {task_read.id} "
                        f"for keyword '{keyword_text}' on {platform} "
                        f"(expanded: {keywords_for_crawler})"
                    )

            logger.info(f"[{self.name}] Scheduled {len(scheduled)} crawl tasks")
            return AgentResult(
                success=True,
                data={"scheduled_tasks": scheduled, "count": len(scheduled)},
            )
        except Exception as e:
            logger.error(f"[{self.name}] Error scheduling tasks: {e}")
            return AgentResult(success=False, error=str(e))
