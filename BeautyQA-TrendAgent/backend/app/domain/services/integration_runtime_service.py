from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.agents.base import AgentContext
from app.agents.cleaning_agent import CleaningAgent
from app.agents.crawler_agent import CrawlerAgent
from app.agents.scheduler_agent import SchedulerAgent
from app.agents.signal_agent import SignalAgent
from app.agents.trend_agent import TrendAgent
from app.config.settings import settings
from app.domain.services.account_service import AccountService
from app.domain.services.keyword_service import KeywordService
from app.domain.services.task_service import TaskService
from app.infrastructure.crawler.adapter import CrawlerAdapter
from app.infrastructure.database.connection import async_session_factory, init_db
from app.infrastructure.repositories.account_repo_impl import AccountRepositoryImpl
from app.infrastructure.repositories.keyword_repo_impl import KeywordRepositoryImpl
from app.infrastructure.repositories.task_repo_impl import TaskRepositoryImpl

logger = logging.getLogger(__name__)


class IntegrationRuntimeService:
    """Run the first-party INT-002 chain without depending on Celery workers."""

    def __init__(self) -> None:
        self._report_dir = Path(settings.DATA_DIR) / "runtime_runs" / "int002"

    async def run(
        self,
        *,
        platforms: list[str],
        per_platform_limit: int = 1,
        bootstrap_keywords_from_csv: bool = True,
        login_type: str = "cookie",
        headless: bool = False,
        enable_comments: bool = False,
        enable_sub_comments: bool = False,
        max_comments_per_note: int = 2,
        max_concurrency: int = 1,
        allow_local_state_fallback: bool = True,
        max_raw_items: int = 2,
        max_tasks_per_keyword: int = 1,
        dedup_window_hours: int = 168,
        retry_cooldown_hours: int = 24,
        task_delay_seconds: int = 12,
    ) -> dict[str, Any]:
        await init_db()
        keyword_bootstrap = await self._maybe_bootstrap_keywords(bootstrap_keywords_from_csv)

        run_id = datetime.now(timezone.utc).strftime("int002_%Y%m%d_%H%M%S")
        started_at = datetime.now(timezone.utc)
        scheduled_tasks: list[dict[str, Any]] = []
        task_results: list[dict[str, Any]] = []
        platform_summaries: list[dict[str, Any]] = []

        task_config_overrides = {
            "login_type": login_type,
            "headless": headless,
            "enable_comments": enable_comments,
            "enable_sub_comments": enable_sub_comments,
            "max_comments_per_note": max_comments_per_note,
            "max_concurrency": max_concurrency,
            "allow_local_state_fallback": allow_local_state_fallback,
            "max_raw_items": max_raw_items,
        }

        for platform in platforms:
            schedule_result = await self._schedule_platform(
                platform=platform,
                per_platform_limit=per_platform_limit,
                task_config_overrides=task_config_overrides,
                max_tasks_per_keyword=max_tasks_per_keyword,
                dedup_window_hours=dedup_window_hours,
                retry_cooldown_hours=retry_cooldown_hours,
                task_delay_seconds=task_delay_seconds,
            )
            platform_summaries.append(schedule_result["summary"])
            scheduled_tasks.extend(schedule_result["scheduled_tasks"])

        for index, task in enumerate(scheduled_tasks):
            task_result = await self._run_task_pipeline(task["id"], max_raw_items=max_raw_items)
            task_results.append(task_result)
            if index < len(scheduled_tasks) - 1 and task_delay_seconds > 0:
                await asyncio.sleep(task_delay_seconds)

        completed_count = sum(1 for item in task_results if item["success"])
        failed_count = len(task_results) - completed_count
        total_signal_count = sum(item.get("signal_count", 0) for item in task_results)
        total_cleaned_count = sum(item.get("cleaned_count", 0) for item in task_results)

        report = {
            "task_id": "INT-002",
            "run_id": run_id,
            "started_at": started_at.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "platforms": platforms,
            "run_options": {
                "per_platform_limit": per_platform_limit,
                "bootstrap_keywords_from_csv": bootstrap_keywords_from_csv,
                "login_type": login_type,
                "headless": headless,
                "enable_comments": enable_comments,
                "enable_sub_comments": enable_sub_comments,
                "max_comments_per_note": max_comments_per_note,
                "max_concurrency": max_concurrency,
                "allow_local_state_fallback": allow_local_state_fallback,
                "max_raw_items": max_raw_items,
                "max_tasks_per_keyword": max_tasks_per_keyword,
                "dedup_window_hours": dedup_window_hours,
                "retry_cooldown_hours": retry_cooldown_hours,
                "task_delay_seconds": task_delay_seconds,
            },
            "keyword_bootstrap": keyword_bootstrap,
            "summary": {
                "platform_count": len(platforms),
                "scheduled_task_count": len(scheduled_tasks),
                "completed_task_count": completed_count,
                "failed_task_count": failed_count,
                "generated_signal_count": total_signal_count,
                "cleaned_row_count": total_cleaned_count,
                "success": failed_count == 0,
            },
            "platform_summaries": platform_summaries,
            "task_results": task_results,
        }

        json_path, md_path = self._write_report(report)
        report["report_paths"] = {
            "json": str(json_path),
            "md": str(md_path),
        }
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(self._render_markdown(report), encoding="utf-8")
        return report

    async def _maybe_bootstrap_keywords(self, enabled: bool) -> dict[str, Any]:
        async with async_session_factory() as session:
            keyword_service = KeywordService(KeywordRepositoryImpl(session))
            existing = await keyword_service.list_keywords(limit=1)
            if existing or not enabled:
                return {
                    "performed": False,
                    "existing_keyword_count_hint": len(existing),
                }

            csv_path = Path(settings.TREND_KEYWORD_CSV)
            imported = await keyword_service.import_csv(csv_path.read_text(encoding="utf-8"))
            await session.commit()
            return {
                "performed": True,
                "source_csv": str(csv_path),
                "imported_count": len(imported),
            }

    async def _schedule_platform(
        self,
        *,
        platform: str,
        per_platform_limit: int,
        task_config_overrides: dict[str, Any],
        max_tasks_per_keyword: int,
        dedup_window_hours: int,
        retry_cooldown_hours: int,
        task_delay_seconds: int,
    ) -> dict[str, Any]:
        async with async_session_factory() as session:
            keyword_service = KeywordService(KeywordRepositoryImpl(session))
            task_service = TaskService(TaskRepositoryImpl(session))

            trend_agent = TrendAgent(keyword_service)
            trend_result = await trend_agent.execute(AgentContext(platform=platform))
            due_keywords = trend_result.data.get("due_keywords", []) if trend_result.success else []
            selected_due_keywords = due_keywords[:per_platform_limit] if per_platform_limit > 0 else due_keywords

            scheduler = SchedulerAgent(task_service, keyword_service)
            scheduler_result = await scheduler.execute(
                AgentContext(
                    platform=platform,
                    extra={
                        "due_keywords": selected_due_keywords,
                        "task_config_overrides": task_config_overrides,
                        "max_tasks_per_keyword": max_tasks_per_keyword,
                        "dedup_window_hours": dedup_window_hours,
                        "retry_cooldown_hours": retry_cooldown_hours,
                    },
                )
            )
            await session.commit()

            scheduled_tasks = scheduler_result.data.get("scheduled_tasks", []) if scheduler_result.success else []
            skipped_duplicates = scheduler_result.data.get("skipped_duplicates", []) if scheduler_result.success else []
            return {
                "summary": {
                    "platform": platform,
                    "due_keyword_count": len(due_keywords),
                    "selected_due_keyword_count": len(selected_due_keywords),
                    "scheduled_task_count": len(scheduled_tasks),
                    "skipped_duplicate_count": len(skipped_duplicates),
                    "scheduler_success": scheduler_result.success,
                    "scheduler_error": scheduler_result.error if not scheduler_result.success else "",
                    "task_delay_seconds": task_delay_seconds,
                },
                "scheduled_tasks": scheduled_tasks,
                "skipped_duplicates": skipped_duplicates,
            }

    async def _run_task_pipeline(self, task_id: int, *, max_raw_items: int) -> dict[str, Any]:
        crawl_result = await self._run_crawl(task_id)
        if not crawl_result["success"]:
            return crawl_result

        task_context = AgentContext(
            task_id=task_id,
            keyword=crawl_result["keyword"],
            platform=crawl_result["platform"],
            extra={"max_raw_items": max_raw_items},
        )
        cleaning_agent = CleaningAgent()
        cleaning_result = await cleaning_agent.execute(task_context)

        signal_result_data = {
            "success": False,
            "signal_count": 0,
            "output_file": "",
            "error": "skipped_due_to_cleaning_failure",
        }
        if cleaning_result.success:
            signal_agent = SignalAgent()
            signal_result = await signal_agent.execute(task_context)
            signal_result_data = {
                "success": signal_result.success,
                "signal_count": signal_result.data.get("signal_count", 0) if signal_result.success else 0,
                "output_file": signal_result.data.get("output_file", "") if signal_result.success else "",
                "error": signal_result.error if not signal_result.success else "",
            }

        overall_success = cleaning_result.success and signal_result_data["success"]
        error_parts: list[str] = []
        if not cleaning_result.success and cleaning_result.error:
            error_parts.append(f"cleaning_failed: {cleaning_result.error}")
        if cleaning_result.success and not signal_result_data["success"] and signal_result_data["error"]:
            error_parts.append(f"signal_failed: {signal_result_data['error']}")

        await self._finalize_task_pipeline(
            task_id=task_id,
            keyword_id=crawl_result["keyword_id"],
            cleaned_count=cleaning_result.data.get("cleaned_count", 0) if cleaning_result.success else 0,
            signal_result=signal_result_data,
            success=overall_success,
            error_message="; ".join(error_parts),
        )

        return {
            "task_id": task_id,
            "keyword_id": crawl_result["keyword_id"],
            "keyword": crawl_result["keyword"],
            "platform": crawl_result["platform"],
            "success": overall_success,
            "cleaned_count": cleaning_result.data.get("cleaned_count", 0) if cleaning_result.success else 0,
            "signal_count": signal_result_data["signal_count"],
            "signal_output_file": signal_result_data["output_file"],
            "error": "; ".join(error_parts),
        }

    async def _run_crawl(self, task_id: int) -> dict[str, Any]:
        async with async_session_factory() as session:
            task_service = TaskService(TaskRepositoryImpl(session))
            account_service = AccountService(AccountRepositoryImpl(session))
            crawler_agent = CrawlerAgent(CrawlerAdapter(), account_service, task_service)

            task = await task_service.get_task(task_id)
            if not task:
                return {
                    "task_id": task_id,
                    "success": False,
                    "keyword_id": 0,
                    "keyword": "",
                    "platform": "",
                    "error": "task_not_found",
                }

            result = await crawler_agent.execute(
                AgentContext(
                    task_id=task.id,
                    keyword_id=task.keyword_id,
                    keyword=task.keyword,
                    platform=task.platform,
                )
            )
            await session.commit()

            return {
                "task_id": task.id,
                "success": result.success,
                "keyword_id": task.keyword_id,
                "keyword": task.keyword,
                "platform": task.platform,
                "error": result.error if not result.success else "",
            }

    async def _finalize_task_pipeline(
        self,
        *,
        task_id: int,
        keyword_id: int,
        cleaned_count: int,
        signal_result: dict[str, Any],
        success: bool,
        error_message: str,
    ) -> None:
        async with async_session_factory() as session:
            task_service = TaskService(TaskRepositoryImpl(session))
            keyword_service = KeywordService(KeywordRepositoryImpl(session))

            await task_service.merge_result_summary(
                task_id,
                {
                    "cleaned_count": cleaned_count,
                    "signal_generation": signal_result,
                    "pipeline_status": "completed" if success else "failed",
                },
            )

            if success:
                await keyword_service.mark_crawled(keyword_id)
                await task_service.add_log(
                    task_id,
                    "success",
                    f"INT-002 pipeline completed. cleaned_count={cleaned_count}, signal_count={signal_result['signal_count']}",
                )
            else:
                await task_service.mark_failed(task_id, error_message or "postprocess_failed")
            await session.commit()

    def _write_report(self, report: dict[str, Any]) -> tuple[Path, Path]:
        self._report_dir.mkdir(parents=True, exist_ok=True)
        run_id = report["run_id"]
        json_path = self._report_dir / f"{run_id}.json"
        md_path = self._report_dir / f"{run_id}.md"
        return json_path, md_path

    def _render_markdown(self, report: dict[str, Any]) -> str:
        lines = [
            "# INT-002 Runtime Report",
            "",
            "## Summary",
            f"- run_id: `{report['run_id']}`",
            f"- started_at: `{report['started_at']}`",
            f"- completed_at: `{report['completed_at']}`",
            f"- platforms: `{', '.join(report['platforms'])}`",
            f"- scheduled_task_count: `{report['summary']['scheduled_task_count']}`",
            f"- completed_task_count: `{report['summary']['completed_task_count']}`",
            f"- failed_task_count: `{report['summary']['failed_task_count']}`",
            f"- cleaned_row_count: `{report['summary']['cleaned_row_count']}`",
            f"- generated_signal_count: `{report['summary']['generated_signal_count']}`",
            f"- success: `{str(report['summary']['success']).lower()}`",
            "",
            "## Platform Summaries",
        ]
        for item in report["platform_summaries"]:
            lines.append(
                f"- `{item['platform']}` due={item['due_keyword_count']} selected={item['selected_due_keyword_count']} scheduled={item['scheduled_task_count']}"
            )
        lines.extend(["", "## Task Results"])
        for item in report["task_results"]:
            lines.append(
                f"- task `{item['task_id']}` `{item['platform']}` `{item['keyword']}` success=`{str(item['success']).lower()}` cleaned=`{item['cleaned_count']}` signals=`{item['signal_count']}` error=`{item['error']}`"
            )
        return "\n".join(lines) + "\n"
