#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import create_engine, text


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "BeautyQA-TrendAgent" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.config.settings import settings  # noqa: E402
from app.infrastructure.database.connection import Base  # noqa: E402
import app.infrastructure.database.models  # noqa: F401,E402


def ensure_runtime_schema() -> dict:
    engine = create_engine(settings.DATABASE_URL_SYNC)
    report: dict = {
        "task": "sync_runtime_schema",
        "database_url_sync": settings.DATABASE_URL_SYNC,
        "actions": [],
        "runtime_batch_runs_columns": [],
    }

    with engine.begin() as conn:
        # create_all only creates missing tables; it does not alter existing columns
        Base.metadata.create_all(bind=conn)

        conn.execute(
            text(
                """
                ALTER TABLE runtime_batch_runs
                ADD COLUMN IF NOT EXISTS completion_classification VARCHAR(24)
                """
            )
        )
        report["actions"].append("ensure runtime_batch_runs.completion_classification")

        conn.execute(
            text(
                """
                COMMENT ON COLUMN runtime_batch_runs.completion_classification
                IS 'completed_full/completed_partial/failed'
                """
            )
        )
        report["actions"].append("comment runtime_batch_runs.completion_classification")

        rows = conn.execute(
            text(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'runtime_batch_runs'
                ORDER BY ordinal_position
                """
            )
        ).fetchall()
        report["runtime_batch_runs_columns"] = [
            {"column_name": row[0], "data_type": row[1]}
            for row in rows
        ]

    engine.dispose()
    return report


if __name__ == "__main__":
    print(json.dumps(ensure_runtime_schema(), ensure_ascii=False, indent=2))
