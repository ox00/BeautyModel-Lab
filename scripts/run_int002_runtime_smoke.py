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
    parser.add_argument(
        "--platform",
        nargs="+",
        default=["xhs"],
        help="One or more platform codes, e.g. xhs dy bili",
    )
    parser.add_argument("--per-platform-limit", type=int, default=1)
    parser.add_argument("--login-type", choices=["cookie", "qrcode", "phone"], default="cookie")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--enable-comments", action="store_true")
    parser.add_argument("--enable-sub-comments", action="store_true")
    parser.add_argument("--max-comments-per-note", type=int, default=2)
    parser.add_argument("--max-concurrency", type=int, default=1)
    parser.add_argument("--max-raw-items", type=int, default=2)
    parser.add_argument("--max-tasks-per-keyword", type=int, default=1)
    parser.add_argument("--dedup-window-hours", type=int, default=168)
    parser.add_argument("--retry-cooldown-hours", type=int, default=24)
    parser.add_argument("--task-delay-seconds", type=int, default=12)
    parser.add_argument("--no-bootstrap-keywords", action="store_true")
    parser.add_argument("--no-local-state-fallback", action="store_true")
    return parser.parse_args()


async def _main(args: argparse.Namespace) -> dict:
    service = IntegrationRuntimeService()
    return await service.run(
        platforms=args.platform,
        per_platform_limit=args.per_platform_limit,
        bootstrap_keywords_from_csv=not args.no_bootstrap_keywords,
        login_type=args.login_type,
        headless=args.headless,
        enable_comments=args.enable_comments,
        enable_sub_comments=args.enable_sub_comments,
        max_comments_per_note=args.max_comments_per_note,
        max_concurrency=args.max_concurrency,
        allow_local_state_fallback=not args.no_local_state_fallback,
        max_raw_items=args.max_raw_items,
        max_tasks_per_keyword=args.max_tasks_per_keyword,
        dedup_window_hours=args.dedup_window_hours,
        retry_cooldown_hours=args.retry_cooldown_hours,
        task_delay_seconds=args.task_delay_seconds,
    )


if __name__ == "__main__":
    result = asyncio.run(_main(parse_args()))
    print(json.dumps(result, ensure_ascii=False, indent=2))
