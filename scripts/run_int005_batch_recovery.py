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

from app.infrastructure.database.connection import async_session_factory, init_db  # noqa: E402
from app.domain.services.runtime_recovery_service import RuntimeRecoveryService  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run INT-005 recovery reconciliation for one runtime batch.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--stale-minutes", type=int, default=45)
    parser.add_argument("--requeue-limit", type=int, default=20)
    return parser.parse_args()


async def _main(args: argparse.Namespace) -> dict:
    await init_db()
    async with async_session_factory() as session:
        service = RuntimeRecoveryService(session)
        actions = await service.reconcile_stale_running_items(run_id=args.run_id, stale_minutes=args.stale_minutes)
        candidates = await service.list_requeue_candidates(run_id=args.run_id, limit=args.requeue_limit)
        summary = await service.build_completion_audit(run_id=args.run_id)
        await session.commit()

    return {
        "run_id": args.run_id,
        "reconcile_actions": actions,
        "requeue_candidates": [
            {
                "id": item.id,
                "query_unit_key": item.query_unit_key,
                "item_status": item.item_status,
                "attempt_count": item.attempt_count,
                "task_id": item.task_id,
                "last_error": item.last_error,
            }
            for item in candidates
        ],
        "completion_audit": {
            "completion_classification": summary.completion_classification,
            "total_items": summary.total_items,
            "succeeded_items": summary.succeeded_items,
            "failed_retryable_items": summary.failed_retryable_items,
            "failed_terminal_items": summary.failed_terminal_items,
            "running_items": summary.running_items,
        },
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(_main(parse_args())), ensure_ascii=False, indent=2))
