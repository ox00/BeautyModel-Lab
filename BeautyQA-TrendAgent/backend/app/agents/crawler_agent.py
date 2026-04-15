from __future__ import annotations

import logging

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.infrastructure.crawler.adapter import CrawlerAdapter, CrawlRequest
from app.domain.services.account_service import AccountService
from app.domain.services.task_service import TaskService

logger = logging.getLogger(__name__)


class CrawlerAgent(BaseAgent):
    """Agent responsible for executing crawl operations via MediaCrawler.

    This agent:
    1. Picks an available account for the target platform
    2. Builds and executes the MediaCrawler subprocess command
    3. Updates the task status based on results
    """

    def __init__(
        self,
        crawler_adapter: CrawlerAdapter,
        account_service: AccountService,
        task_service: TaskService,
    ) -> None:
        self._adapter = crawler_adapter
        self._account_service = account_service
        self._task_service = task_service

    @property
    def name(self) -> str:
        return "CrawlerAgent"

    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute a crawl operation for the given task.

        Expects context to have:
        - task_id: The crawl task ID
        - platform: The target platform
        - keyword: The search keyword
        - extra.get('config'): Optional crawl config overrides
        """
        task_id = context.task_id
        platform = context.platform
        keyword = context.keyword

        if not task_id or not platform or not keyword:
            return AgentResult(success=False, error="Missing task_id, platform, or keyword in context")

        try:
            # Step 1: Pick an account
            account = await self._account_service.pick_account_for_crawl(platform)
            if not account:
                error_msg = f"No active account available for platform: {platform}"
                await self._task_service.mark_failed(task_id, error_msg)
                return AgentResult(success=False, error=error_msg)

            # Step 2: Get task config
            task_read = await self._task_service.get_task(task_id)
            config = task_read.config if task_read else {}
            task_config = {**(config or {}), **context.extra.get("config", {})}

            # Step 3: Build crawl request
            keywords_for_crawler = task_config.get("keywords_for_crawler", "")
            request = CrawlRequest(
                task_id=task_id,
                platform=platform,
                keyword=keyword,
                login_type=task_config.get("login_type", account.login_type),
                cookies=account.cookies,
                headless=task_config.get("headless", True),
                enable_comments=task_config.get("enable_comments", True),
                enable_sub_comments=task_config.get("enable_sub_comments", False),
                start_page=task_config.get("start_page", 1),
                keywords_for_crawler=keywords_for_crawler,
            )

            # Step 4: Mark task as running
            await self._task_service.mark_running(task_id, "", account.id)

            # Step 5: Execute crawl
            logger.info(f"[{self.name}] Starting crawl for task {task_id}: {platform}/{keyword}")
            response = await self._adapter.crawl_keyword(request)

            # Step 6: Update task based on result
            if response.success:
                await self._task_service.mark_completed(task_id, {
                    "exit_code": response.exit_code,
                    "platform": platform,
                    "keyword": keyword,
                })
                logger.info(f"[{self.name}] Crawl completed for task {task_id}")
                return AgentResult(
                    success=True,
                    data={"task_id": task_id, "platform": platform, "keyword": keyword},
                )
            else:
                await self._task_service.mark_failed(task_id, response.error_message)
                return AgentResult(success=False, error=response.error_message)

        except Exception as e:
            logger.error(f"[{self.name}] Crawl failed for task {task_id}: {e}")
            await self._task_service.mark_failed(task_id, str(e))
            return AgentResult(success=False, error=str(e))
