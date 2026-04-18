#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "BeautyQA-TrendAgent" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.domain.services.integration_runtime_service import IntegrationRuntimeService  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the first-party INT-002 integration smoke from scheduling to trend_signal output."
    )
    parser.add_argument("--runtime-profile", choices=["safe_live", "debug_fast"], default="safe_live")
    parser.add_argument("--trigger-source", default="manual")
    parser.add_argument("--due-keyword-id", nargs="+", type=int, help="Optional keyword DB ids to run explicitly")
    parser.add_argument(
        "--platform",
        nargs="+",
        default=["xhs"],
        help="One or more platform codes, e.g. xhs dy bili",
    )
    parser.add_argument("--per-platform-limit", type=int)
    parser.add_argument("--login-type", choices=["cookie", "qrcode", "phone"])
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--enable-comments", action="store_true")
    parser.add_argument("--enable-sub-comments", action="store_true")
    parser.add_argument("--max-comments-per-note", type=int)
    parser.add_argument("--max-concurrency", type=int)
    parser.add_argument("--max-raw-items", type=int)
    parser.add_argument("--max-tasks-per-keyword", type=int)
    parser.add_argument("--dedup-window-hours", type=int)
    parser.add_argument("--retry-cooldown-hours", type=int)
    parser.add_argument("--task-delay-seconds", type=int)
    parser.add_argument("--no-bootstrap-keywords", action="store_true")
    parser.add_argument("--no-local-state-fallback", action="store_true")
    return parser.parse_args()


async def _main(args: argparse.Namespace) -> dict:
    service = IntegrationRuntimeService()
    return await service.run(
        platforms=args.platform,
        runtime_profile=args.runtime_profile,
        trigger_source=args.trigger_source,
        due_keyword_ids=args.due_keyword_id,
        per_platform_limit=args.per_platform_limit,
        bootstrap_keywords_from_csv=not args.no_bootstrap_keywords,
        login_type=args.login_type,
        headless=True if args.headless else None,
        enable_comments=True if args.enable_comments else None,
        enable_sub_comments=True if args.enable_sub_comments else None,
        max_comments_per_note=args.max_comments_per_note,
        max_concurrency=args.max_concurrency,
        allow_local_state_fallback=False if args.no_local_state_fallback else None,
        max_raw_items=args.max_raw_items,
        max_tasks_per_keyword=args.max_tasks_per_keyword,
        dedup_window_hours=args.dedup_window_hours,
        retry_cooldown_hours=args.retry_cooldown_hours,
        task_delay_seconds=args.task_delay_seconds,
    )


if __name__ == "__main__":
    result = asyncio.run(_main(parse_args()))
    print(json.dumps(result, ensure_ascii=False, indent=2))
