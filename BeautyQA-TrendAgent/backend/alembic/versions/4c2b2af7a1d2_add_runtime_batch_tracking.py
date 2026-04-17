"""add runtime batch tracking tables

Revision ID: 4c2b2af7a1d2
Revises: 0928faa6e124
Create Date: 2026-04-17 23:05:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4c2b2af7a1d2"
down_revision: Union[str, None] = "0928faa6e124"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "runtime_batch_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False, comment="Stable runtime batch id"),
        sa.Column("run_type", sa.String(length=32), nullable=False, comment="Batch type: int002_runtime/export/etc."),
        sa.Column("trigger_source", sa.String(length=32), nullable=False, comment="Trigger source: manual/cron/celery/api"),
        sa.Column("profile_name", sa.String(length=32), nullable=False, comment="Applied runtime profile name"),
        sa.Column("status", sa.String(length=16), nullable=False, comment="Status: running/completed/failed"),
        sa.Column("platforms", sa.JSON(), nullable=True, comment="Requested platforms for the batch run"),
        sa.Column("requested_options", sa.JSON(), nullable=True, comment="Requested runtime options before policy merge"),
        sa.Column("effective_options", sa.JSON(), nullable=True, comment="Effective runtime policy/options after merge"),
        sa.Column("summary", sa.JSON(), nullable=True, comment="Run summary counts and key outcomes"),
        sa.Column("report_paths", sa.JSON(), nullable=True, comment="Generated report artifact paths"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="Top-level batch failure message"),
        sa.Column("started_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False, comment="Batch start time"),
        sa.Column("completed_at", sa.DateTime(), nullable=True, comment="Batch completion time"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_runtime_batch_runs_run_id"), "runtime_batch_runs", ["run_id"], unique=True)

    op.create_table(
        "runtime_batch_run_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("batch_run_id", sa.Integer(), nullable=False, comment="FK-like link to runtime_batch_runs.id"),
        sa.Column("run_id", sa.String(length=64), nullable=False, comment="Stable runtime batch id"),
        sa.Column("event_type", sa.String(length=32), nullable=False, comment="scheduled/skipped_duplicate/no_candidates/task_completed/task_failed"),
        sa.Column("platform", sa.String(length=32), nullable=True, comment="Target platform"),
        sa.Column("keyword_id", sa.Integer(), nullable=True, comment="FK-like link to trend_keywords.id"),
        sa.Column("keyword", sa.String(length=255), nullable=True, comment="Original keyword"),
        sa.Column("task_id", sa.Integer(), nullable=True, comment="FK-like link to crawl_tasks.id"),
        sa.Column("dedup_key", sa.String(length=255), nullable=True, comment="Task dedup key for replay/audit"),
        sa.Column("payload", sa.JSON(), nullable=True, comment="Event payload for audit and replay"),
        sa.Column("message", sa.Text(), nullable=True, comment="Short event note"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_runtime_batch_run_events_batch_run_id"), "runtime_batch_run_events", ["batch_run_id"], unique=False)
    op.create_index(op.f("ix_runtime_batch_run_events_run_id"), "runtime_batch_run_events", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_runtime_batch_run_events_run_id"), table_name="runtime_batch_run_events")
    op.drop_index(op.f("ix_runtime_batch_run_events_batch_run_id"), table_name="runtime_batch_run_events")
    op.drop_table("runtime_batch_run_events")
    op.drop_index(op.f("ix_runtime_batch_runs_run_id"), table_name="runtime_batch_runs")
    op.drop_table("runtime_batch_runs")
