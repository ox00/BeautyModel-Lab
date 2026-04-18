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

from app.domain.services.trend_signal_export_service import TrendSignalExportService  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run INT-003 stable trend_signal handoff export from runtime batch history."
    )
    parser.add_argument("--trigger-source", default="manual")
    parser.add_argument(
        "--source-run-id",
        action="append",
        default=[],
        help="Optional INT-002 runtime run_id to limit export sources. Can be passed multiple times.",
    )
    return parser.parse_args()


async def _main(args: argparse.Namespace) -> dict:
    service = TrendSignalExportService()
    return await service.export_latest(
        trigger_source=args.trigger_source,
        source_run_ids=args.source_run_id or None,
    )


if __name__ == "__main__":
    result = asyncio.run(_main(parse_args()))
    print(json.dumps(result, ensure_ascii=False, indent=2))
