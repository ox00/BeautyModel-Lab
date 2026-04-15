from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from app.infrastructure.crawler.config_mapper import CrawlerConfigMapper, CrawlCommand
from app.infrastructure.crawler.process_manager import CrawlerProcessManager, CrawlResult, ProcessStatus

logger = logging.getLogger(__name__)


@dataclass
class CrawlRequest:
    """Business-level request to crawl a keyword on a platform."""

    task_id: int
    platform: str
    keyword: str
    login_type: str = "cookie"
    cookies: str = ""
    headless: bool = True
    enable_comments: bool = True
    enable_sub_comments: bool = False
    start_page: int = 1
    max_comments_per_note: int = CrawlerConfigMapper.DEFAULT_MAX_COMMENTS_PER_NOTE
    max_concurrency: int = CrawlerConfigMapper.DEFAULT_MAX_CONCURRENCY
    keywords_for_crawler: str = ""


@dataclass
class CrawlResponse:
    """Response after a crawl operation completes."""

    task_id: int
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    status: ProcessStatus
    error_message: str = ""


class CrawlerAdapter:
    """Unified interface for the Agent layer to invoke MediaCrawler.

    This is the single entry point that the CrawlerAgent uses to
    execute crawl operations. It encapsulates:
    1. Building CLI commands via CrawlerConfigMapper
    2. Managing subprocess lifecycle via CrawlerProcessManager
    3. Returning structured results
    """

    def __init__(self) -> None:
        self._config_mapper = CrawlerConfigMapper()
        self._process_manager = CrawlerProcessManager()

    async def crawl_keyword(self, request: CrawlRequest) -> CrawlResponse:
        """Execute a keyword crawl on a specific platform.

        Starts the MediaCrawler subprocess, waits for completion,
        and returns a structured response.

        Args:
            request: The crawl request containing platform, keyword, etc.

        Returns:
            CrawlResponse with the execution result.
        """
        task_id_str = str(request.task_id)

        # Step 1: Build command
        try:
            command = self._config_mapper.build_command(
                platform=request.platform,
                keyword=request.keyword,
                login_type=request.login_type,
                cookies=request.cookies,
                headless=request.headless,
                enable_comments=request.enable_comments,
                enable_sub_comments=request.enable_sub_comments,
                start_page=request.start_page,
                max_comments_per_note=request.max_comments_per_note,
                max_concurrency=request.max_concurrency,
                keywords_for_crawler=request.keywords_for_crawler,
            )
            logger.info(f"[CrawlerAdapter] Built command for task {request.task_id}: {' '.join(command.command)}")
        except Exception as e:
            logger.error(f"[CrawlerAdapter] Failed to build command: {e}")
            return CrawlResponse(
                task_id=request.task_id,
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                status=ProcessStatus.FAILED,
                error_message=f"Command build failed: {e}",
            )

        # Step 2: Start subprocess
        try:
            mp = await self._process_manager.start_crawl(command, task_id_str)
        except Exception as e:
            logger.error(f"[CrawlerAdapter] Failed to start process: {e}")
            return CrawlResponse(
                task_id=request.task_id,
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                status=ProcessStatus.FAILED,
                error_message=f"Process start failed: {e}",
            )

        # Step 3: Wait for completion
        # Timeout strategy:
        # - qrcode login: 15 min (first keyword needs user to scan)
        # - cookie/login already done: 10 min (subsequent keywords reuse login)
        # Each subprocess now handles only ONE keyword, so these timeouts are per-keyword.
        timeout = 900.0 if request.login_type == "qrcode" else 600.0
        result: Optional[CrawlResult] = await self._process_manager.wait_for_completion(task_id_str, timeout=timeout)

        if result is None:
            return CrawlResponse(
                task_id=request.task_id,
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Process not found",
                status=ProcessStatus.FAILED,
                error_message="Process not found after start",
            )

        return CrawlResponse(
            task_id=request.task_id,
            success=result.is_success,
            exit_code=result.exit_code,
            stdout=result.stdout[-5000:] if result.stdout else "",  # Truncate large output
            stderr=result.stderr[-5000:] if result.stderr else "",
            status=result.status,
            error_message="" if result.is_success else (
                f"Crawl failed with exit code {result.exit_code}: "
                f"{(result.stderr or '')[-500:]}"
            ),
        )

    async def stop_crawl(self, task_id: int) -> bool:
        """Stop a running crawl by task ID."""
        return await self._process_manager.stop_crawl(str(task_id))

    def get_status(self, task_id: int) -> Optional[ProcessStatus]:
        """Get the current status of a crawl task."""
        return self._process_manager.get_status(str(task_id))
