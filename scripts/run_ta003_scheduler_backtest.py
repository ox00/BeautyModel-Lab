from __future__ import annotations

import asyncio
import csv
import json
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TRENDAGENT_BACKEND = REPO_ROOT / "BeautyQA-TrendAgent" / "backend"
if str(TRENDAGENT_BACKEND) not in sys.path:
    sys.path.insert(0, str(TRENDAGENT_BACKEND))

# SchedulerAgent only needs these services for constructor typing.
# Stub them here so the backtest can run without pulling in DB drivers.
for module_name, class_name in [
    ("app.domain.services.task_service", "TaskService"),
    ("app.domain.services.keyword_service", "KeywordService"),
]:
    if module_name not in sys.modules:
        module = types.ModuleType(module_name)
        setattr(module, class_name, object)
        sys.modules[module_name] = module

from app.agents.base import AgentContext  # noqa: E402
from app.agents.scheduler_agent import SchedulerAgent  # noqa: E402


SEED_CSV = REPO_ROOT / "data" / "eval" / "trend_monitor" / "2026-04-13-trend-keyword-seed.csv"
REQUIRED_CONFIG_FIELDS = {
    "keywords_for_crawler",
    "original_keyword",
    "normalized_keyword",
    "query_origin",
    "based_on",
    "review_needed",
    "crawl_goal",
    "risk_flag",
    "priority",
    "confidence",
    "reference_sources",
    "reference_packages",
    "task_dedup_key",
}


@dataclass
class FakeTaskRead:
    id: int
    keyword_id: int
    keyword: str
    platform: str
    config: dict[str, Any]
    status: str = "pending"

    def model_dump(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "keyword_id": self.keyword_id,
            "keyword": self.keyword,
            "platform": self.platform,
            "status": self.status,
            "config": self.config,
        }


class FakeTaskService:
    def __init__(self) -> None:
        self.created_tasks: list[FakeTaskRead] = []
        self._next_id = 1

    async def create_task(
        self,
        data,
        keyword_text: str,
        *,
        task_keyword: str | None = None,
        config_overrides: dict[str, Any] | None = None,
    ) -> FakeTaskRead:
        config = {
            "login_type": data.login_type,
            "headless": data.headless,
            "enable_comments": data.enable_comments,
            "enable_sub_comments": data.enable_sub_comments,
            "start_page": data.start_page,
            "max_notes_count": data.max_notes_count,
        }
        if config_overrides:
            config.update(config_overrides)

        task = FakeTaskRead(
            id=self._next_id,
            keyword_id=data.keyword_id,
            keyword=task_keyword or keyword_text,
            platform=data.platform,
            config=config,
        )
        self._next_id += 1
        self.created_tasks.append(task)
        return task


class FakeKeywordService:
    async def get_due_keywords(self, platform: str | None = None) -> list[dict[str, Any]]:
        return []



def _load_cases() -> list[dict[str, Any]]:
    selected = {"KW_0002", "KW_0031", "KW_0040"}
    rows: list[dict[str, Any]] = []
    with SEED_CSV.open("r", encoding="utf-8") as f:
        for idx, row in enumerate(csv.DictReader(f), start=1):
            if row["keyword_id"] not in selected:
                continue
            row["id"] = idx
            rows.append(row)
    return rows



def _task_check(task: FakeTaskRead) -> dict[str, Any]:
    config_keys = set(task.config.keys())
    missing = sorted(REQUIRED_CONFIG_FIELDS - config_keys)
    return {
        "task_id": task.id,
        "platform": task.platform,
        "keyword": task.keyword,
        "query_origin": task.config.get("query_origin"),
        "reference_sources": task.config.get("reference_sources", []),
        "missing_config_fields": missing,
        "keyword_matches_keywords_for_crawler": task.keyword == task.config.get("keywords_for_crawler"),
        "reference_not_as_platform": task.platform not in {"taobao", "industry_news"},
    }


async def _run_scheduler_backtest() -> dict[str, Any]:
    due_keywords = _load_cases()

    all_task_service = FakeTaskService()
    scheduler = SchedulerAgent(all_task_service, FakeKeywordService())
    all_result = await scheduler.execute(AgentContext(extra={"due_keywords": due_keywords}))
    all_checks = [_task_check(task) for task in all_task_service.created_tasks]

    xhs_task_service = FakeTaskService()
    xhs_scheduler = SchedulerAgent(xhs_task_service, FakeKeywordService())
    xhs_result = await xhs_scheduler.execute(
        AgentContext(platform="xhs", extra={"due_keywords": due_keywords})
    )
    xhs_checks = [_task_check(task) for task in xhs_task_service.created_tasks]

    per_keyword_counts: dict[str, int] = {}
    for task in all_task_service.created_tasks:
        original_keyword = task.config.get("original_keyword", task.keyword)
        per_keyword_counts[original_keyword] = per_keyword_counts.get(original_keyword, 0) + 1

    return {
        "task_id": "TA-003-scheduler-backtest",
        "backtest_date": "2026-04-16",
        "seed_file": str(SEED_CSV.relative_to(REPO_ROOT)),
        "all_platform_run": {
            "scheduled_count": all_result.data.get("count", 0) if all_result.success else 0,
            "success": all_result.success,
            "per_keyword_task_count": per_keyword_counts,
            "checks": all_checks,
        },
        "target_platform_run": {
            "input_platform": "xhs",
            "scheduled_count": xhs_result.data.get("count", 0) if xhs_result.success else 0,
            "success": xhs_result.success,
            "all_platforms_are_xhs": all(task.platform == "xhs" for task in xhs_task_service.created_tasks),
            "checks": xhs_checks,
        },
        "summary": {
            "all_task_configs_complete": all(not check["missing_config_fields"] for check in all_checks),
            "all_tasks_use_single_query_payload": all(
                check["keyword_matches_keywords_for_crawler"] for check in all_checks
            ),
            "reference_sources_never_scheduled": all(
                check["reference_not_as_platform"] for check in all_checks
            ),
            "target_platform_filter_valid": all(task.platform == "xhs" for task in xhs_task_service.created_tasks),
        },
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(_run_scheduler_backtest()), ensure_ascii=False, indent=2))
