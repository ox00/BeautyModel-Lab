from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.config.settings import settings


@dataclass
class CrawlCommand:
    """Represents a fully built MediaCrawler CLI command."""

    command: list[str]
    cwd: str


class CrawlerConfigMapper:
    """Maps business-level crawl configuration to MediaCrawler CLI arguments.

    MediaCrawler is invoked as a subprocess with CLI args like:
        python main.py --platform xhs --keywords "露营" --save_data_option postgres ...

    The subprocess uses the project's shared .venv Python interpreter so that
    MediaCrawler runs with the same unified dependency set as the backend.
    No separate .venv is needed under MediaCrawler-main/.

    Platform mapping handles the naming convention from trend-keyword.csv:
    - CSV uses: xiaohongshu, douyin, bilibili, weibo, kuaishou, tieba, zhihu
    - MediaCrawler CLI uses: xhs, dy, bili, wb, ks, tieba, zhihu
    - Non-crawlable platforms (industry_news, taobao) are filtered out upstream
    """

    # Mapping from CSV/trend-keyword.csv naming → MediaCrawler CLI naming
    PLATFORM_MAP = {
        "xiaohongshu": "xhs",
        "xhs": "xhs",
        "douyin": "dy",
        "dy": "dy",
        "bilibili": "bili",
        "bili": "bili",
        "weibo": "wb",
        "wb": "wb",
        "kuaishou": "ks",
        "ks": "ks",
        "tieba": "tieba",
        "zhihu": "zhihu",
    }

    # Platforms that are NOT crawlable by MediaCrawler (data source, not target)
    NON_CRAWLABLE_PLATFORMS = {"industry_news", "taobao"}

    @classmethod
    def is_crawlable(cls, platform: str) -> bool:
        """Check if a platform can be crawled by MediaCrawler."""
        return platform in cls.PLATFORM_MAP

    @classmethod
    def parse_suggested_platforms(cls, suggested_platforms: str) -> list[str]:
        """Parse pipe-separated platforms from CSV and return normalized CLI codes.

        CSV format: "xiaohongshu|douyin|industry_news"
        Returns: ["xhs", "dy"] (filtered, non-crawlable removed, normalized to CLI codes)
        """
        raw = [p.strip() for p in suggested_platforms.split("|") if p.strip()]
        return [cls.PLATFORM_MAP[p] for p in raw if p in cls.PLATFORM_MAP]

    @classmethod
    def _resolve_python_path(cls) -> str:
        """Resolve the absolute path to the project's shared Python executable.

        Uses the root .venv's Python so that MediaCrawler runs with the same
        unified dependency set as the backend – no separate .venv needed.
        """
        # 1. Check project root .venv (the single consolidated environment)
        project_venv_python = str(
            Path(settings.PROJECT_ROOT).parent / ".venv" / "Scripts" / "python.exe"
        )
        if Path(project_venv_python).exists():
            return project_venv_python
        # 2. Fallback to current interpreter (may work if same venv)
        return sys.executable

    # Default limits to prevent excessively long subprocess runs.
    # XHS returns 20 notes per page; we only need 1 page per keyword.
    # Note: CRAWLER_MAX_NOTES_COUNT cannot be set via CLI (no --max_notes_count
    # arg exists in MediaCrawler). XHS forces it to min(config, 20) = 20.
    DEFAULT_MAX_COMMENTS_PER_NOTE = 10
    DEFAULT_MAX_CONCURRENCY = 2

    def build_command(
        self,
        platform: str,
        keyword: str,
        login_type: str = "cookie",
        cookies: str = "",
        headless: bool = True,
        enable_comments: bool = True,
        enable_sub_comments: bool = False,
        start_page: int = 1,
        max_comments_per_note: int = DEFAULT_MAX_COMMENTS_PER_NOTE,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        save_data_option: str = "postgres",
        keywords_for_crawler: str = "",
    ) -> CrawlCommand:
        """Build the CLI command for running MediaCrawler.

        Key parameters that affect subprocess duration:
        - max_comments_per_note: Limits comments per note (default 10).
        - max_concurrency: Parallel comment fetch tasks (default 2).
        - keywords_for_crawler: Should contain max 1 keyword per subprocess
          to isolate failures and enable progress tracking.

        Note: max_notes_count is NOT controllable via CLI. XHS forces it to 20
        (1 page). See core.py xhs_limit_count = 20.
        """
        mc_platform = self.PLATFORM_MAP.get(platform, platform)

        # Use expanded keywords if provided, otherwise fall back to single keyword
        keywords_arg = keywords_for_crawler if keywords_for_crawler else keyword

        python_path = self._resolve_python_path()
        cmd = [
            python_path, "main.py",
            "--platform", mc_platform,
            "--lt", login_type,
            "--type", "search",
            "--keywords", keywords_arg,
            "--save_data_option", save_data_option,
            "--headless", str(headless).lower(),
            "--get_comment", str(enable_comments).lower(),
            "--get_sub_comment", str(enable_sub_comments).lower(),
            "--max_comments_count_singlenotes", str(max_comments_per_note),
            "--max_concurrency_num", str(max_concurrency),
        ]

        if start_page > 1:
            cmd.extend(["--start", str(start_page)])

        if cookies:
            cmd.extend(["--cookies", cookies])

        return CrawlCommand(command=cmd, cwd=settings.MEDIACRAWLER_DIR)
