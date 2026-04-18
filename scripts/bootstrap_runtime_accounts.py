#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "BeautyQA-TrendAgent" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.config.settings import settings  # noqa: E402
from app.domain.services.account_runtime import (  # noqa: E402
    LOCAL_BROWSER_STATE_COOKIE,
    build_local_browser_state_remark,
    normalize_account_platform,
)
from app.infrastructure.database.connection import async_session_factory, init_db  # noqa: E402
from app.infrastructure.database.models import Account  # noqa: E402


@dataclass(frozen=True)
class BrowserStateCandidate:
    platform: str
    browser_state_dir: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap first-party runtime accounts from vendor browser_data login-state directories."
    )
    parser.add_argument(
        "--platform",
        nargs="+",
        help="Optional platform filters, e.g. xhs dy bili",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview account import/update results without writing to the database.",
    )
    return parser.parse_args()


def discover_browser_state_candidates(platform_filters: set[str] | None) -> list[BrowserStateCandidate]:
    browser_data_root = Path(settings.MEDIACRAWLER_DIR) / "browser_data"
    candidates: list[BrowserStateCandidate] = []

    if not browser_data_root.exists():
        return candidates

    for child in sorted(browser_data_root.iterdir()):
        if not child.is_dir() or not child.name.endswith("_user_data_dir"):
            continue
        platform = normalize_account_platform(child.name.removesuffix("_user_data_dir"))
        if platform_filters and platform not in platform_filters:
            continue
        if not (child / "Default").exists():
            continue
        candidates.append(BrowserStateCandidate(platform=platform, browser_state_dir=child.resolve()))
    return candidates


async def bootstrap_accounts(candidates: list[BrowserStateCandidate], *, dry_run: bool) -> dict:
    await init_db()

    summary = {
        "task": "bootstrap_runtime_accounts",
        "dry_run": dry_run,
        "vendor_browser_state_root": str(Path(settings.MEDIACRAWLER_DIR) / "browser_data"),
        "detected_candidates": [
            {"platform": item.platform, "browser_state_dir": str(item.browser_state_dir)}
            for item in candidates
        ],
        "results": [],
    }

    async with async_session_factory() as session:
        for candidate in candidates:
            stmt = (
                select(Account)
                .where(Account.platform == candidate.platform)
                .where(Account.cookies == LOCAL_BROWSER_STATE_COOKIE)
                .order_by(Account.id.asc())
            )
            existing = (await session.execute(stmt)).scalars().first()
            desired_remark = build_local_browser_state_remark(candidate.browser_state_dir)

            if existing:
                existing.login_type = "cookie"
                existing.status = "active"
                existing.rotation_strategy = "round_robin"
                existing.remark = desired_remark
                existing.cookies = LOCAL_BROWSER_STATE_COOKIE
                action = "update"
                account_id = existing.id
            else:
                account = Account(
                    platform=candidate.platform,
                    cookies=LOCAL_BROWSER_STATE_COOKIE,
                    login_type="cookie",
                    status="active",
                    rotation_strategy="round_robin",
                    remark=desired_remark,
                )
                session.add(account)
                await session.flush()
                action = "create"
                account_id = account.id

            summary["results"].append(
                {
                    "platform": candidate.platform,
                    "action": action,
                    "account_id": account_id,
                    "browser_state_dir": str(candidate.browser_state_dir),
                    "remark": desired_remark,
                }
            )

        if dry_run:
            await session.rollback()
        else:
            await session.commit()

    summary["imported_platforms"] = [item["platform"] for item in summary["results"]]
    summary["imported_count"] = len(summary["results"])
    return summary


async def _main(args: argparse.Namespace) -> dict:
    platform_filters = None
    if args.platform:
        platform_filters = {normalize_account_platform(item) for item in args.platform}
    candidates = discover_browser_state_candidates(platform_filters)
    return await bootstrap_accounts(candidates, dry_run=args.dry_run)


if __name__ == "__main__":
    result = asyncio.run(_main(parse_args()))
    print(json.dumps(result, ensure_ascii=False, indent=2))
