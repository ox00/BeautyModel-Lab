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

from app.domain.services.trend_signal_series_service import TrendSignalSeriesService  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run INT-004 trend_signal_series aggregation.")
    parser.add_argument("--bucket-type", choices=["12h", "1d"], default="1d")
    return parser.parse_args()


async def _main(args: argparse.Namespace) -> dict:
    service = TrendSignalSeriesService()
    return await service.aggregate_and_persist(bucket_type=args.bucket_type)


if __name__ == "__main__":
    print(json.dumps(asyncio.run(_main(parse_args())), ensure_ascii=False, indent=2))
