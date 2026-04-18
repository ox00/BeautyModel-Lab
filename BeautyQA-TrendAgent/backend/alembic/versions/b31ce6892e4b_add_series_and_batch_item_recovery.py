"""add trend signal series and batch item recovery tables

Revision ID: b31ce6892e4b
Revises: 98d4a7b21f33
Create Date: 2026-04-18 12:45:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b31ce6892e4b"
down_revision: Union[str, None] = "98d4a7b21f33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "runtime_batch_runs",
        sa.Column(
            "completion_classification",
            sa.String(length=24),
            nullable=True,
            comment="completed_full/completed_partial/failed",
        ),
    )

    op.create_table(
        "runtime_batch_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("batch_run_id", sa.Integer(), nullable=False, comment="FK-like link to runtime_batch_runs.id"),
        sa.Column("run_id", sa.String(length=64), nullable=False, comment="Stable runtime batch id"),
        sa.Column("query_unit_key", sa.String(length=512), nullable=False, comment="normalized_keyword + platform + expanded_query"),
        sa.Column("keyword_id", sa.Integer(), nullable=True, comment="FK-like link to trend_keywords.id"),
        sa.Column("keyword", sa.String(length=255), nullable=True, comment="Keyword snapshot"),
        sa.Column("platform", sa.String(length=32), nullable=False, comment="Target platform code"),
        sa.Column("expanded_query", sa.String(length=255), nullable=False, comment="Expanded query text"),
        sa.Column("query_state_id", sa.BigInteger(), nullable=True, comment="FK-like link to query_schedule_states.id"),
        sa.Column("task_id", sa.Integer(), nullable=True, comment="FK-like link to crawl_tasks.id"),
        sa.Column("item_status", sa.String(length=24), nullable=False, comment="planned/dispatched/running/succeeded/failed_retryable/failed_terminal/skipped_duplicate"),
        sa.Column("retryable", sa.Boolean(), nullable=False, comment="Whether item can be retried"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, comment="Total dispatch attempts"),
        sa.Column("last_error", sa.Text(), nullable=True, comment="Last failure reason"),
        sa.Column("last_heartbeat_at", sa.DateTime(), nullable=True, comment="Last progress heartbeat"),
        sa.Column("completed_at", sa.DateTime(), nullable=True, comment="Completion time if terminal"),
        sa.Column("payload", sa.JSON(), nullable=True, comment="Planner/runtime metadata snapshot"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_runtime_batch_items_batch_run_id"), "runtime_batch_items", ["batch_run_id"], unique=False)
    op.create_index(op.f("ix_runtime_batch_items_run_id"), "runtime_batch_items", ["run_id"], unique=False)
    op.create_index(op.f("ix_runtime_batch_items_query_unit_key"), "runtime_batch_items", ["query_unit_key"], unique=False)
    op.create_index(op.f("ix_runtime_batch_items_platform"), "runtime_batch_items", ["platform"], unique=False)

    op.create_table(
        "trend_signal_series",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("series_key", sa.String(length=512), nullable=False, comment="normalized_keyword + platform + bucket"),
        sa.Column("bucket_type", sa.String(length=16), nullable=False, comment="12h/1d"),
        sa.Column("bucket_start", sa.DateTime(), nullable=False, comment="Bucket start time"),
        sa.Column("bucket_end", sa.DateTime(), nullable=False, comment="Bucket end time"),
        sa.Column("normalized_keyword", sa.String(length=255), nullable=False, comment="Normalized keyword"),
        sa.Column("source_platform", sa.String(length=32), nullable=False, comment="Platform label"),
        sa.Column("support_count", sa.Integer(), nullable=False, comment="Number of supporting signals"),
        sa.Column("avg_trend_score", sa.Float(), nullable=False, comment="Average trend score in bucket"),
        sa.Column("delta_vs_prev_bucket", sa.JSON(), nullable=True, comment="Delta metrics against previous bucket"),
        sa.Column("top_evidence", sa.Text(), nullable=True, comment="Representative evidence text"),
        sa.Column("signal_ids", sa.JSON(), nullable=True, comment="Trace signal ids"),
        sa.Column("task_ids", sa.JSON(), nullable=True, comment="Trace task ids"),
        sa.Column("aggregation_method", sa.String(length=64), nullable=False, comment="Aggregation method version"),
        sa.Column("series_status", sa.String(length=16), nullable=False, comment="emerging/stable/cooling"),
        sa.Column("generated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False, comment="Row generation time"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trend_signal_series_series_key"), "trend_signal_series", ["series_key"], unique=False)
    op.create_index(op.f("ix_trend_signal_series_bucket_type"), "trend_signal_series", ["bucket_type"], unique=False)
    op.create_index(op.f("ix_trend_signal_series_bucket_start"), "trend_signal_series", ["bucket_start"], unique=False)
    op.create_index(op.f("ix_trend_signal_series_normalized_keyword"), "trend_signal_series", ["normalized_keyword"], unique=False)
    op.create_index(op.f("ix_trend_signal_series_source_platform"), "trend_signal_series", ["source_platform"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_trend_signal_series_source_platform"), table_name="trend_signal_series")
    op.drop_index(op.f("ix_trend_signal_series_normalized_keyword"), table_name="trend_signal_series")
    op.drop_index(op.f("ix_trend_signal_series_bucket_start"), table_name="trend_signal_series")
    op.drop_index(op.f("ix_trend_signal_series_bucket_type"), table_name="trend_signal_series")
    op.drop_index(op.f("ix_trend_signal_series_series_key"), table_name="trend_signal_series")
    op.drop_table("trend_signal_series")

    op.drop_index(op.f("ix_runtime_batch_items_platform"), table_name="runtime_batch_items")
    op.drop_index(op.f("ix_runtime_batch_items_query_unit_key"), table_name="runtime_batch_items")
    op.drop_index(op.f("ix_runtime_batch_items_run_id"), table_name="runtime_batch_items")
    op.drop_index(op.f("ix_runtime_batch_items_batch_run_id"), table_name="runtime_batch_items")
    op.drop_table("runtime_batch_items")

    op.drop_column("runtime_batch_runs", "completion_classification")
