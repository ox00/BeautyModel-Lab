"""add expansion registry and query schedule state

Revision ID: 98d4a7b21f33
Revises: 4c2b2af7a1d2
Create Date: 2026-04-17 23:55:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "98d4a7b21f33"
down_revision: Union[str, None] = "4c2b2af7a1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expansion_registry",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("keyword_db_id", sa.Integer(), nullable=False, comment="FK-like link to trend_keywords.id"),
        sa.Column("keyword_id", sa.String(length=32), nullable=False, comment="Business keyword ID, e.g. KW_0001"),
        sa.Column("normalized_keyword", sa.String(length=255), nullable=False, comment="Normalized keyword"),
        sa.Column("platform", sa.String(length=32), nullable=False, comment="Platform label, e.g. xiaohongshu/douyin"),
        sa.Column("expanded_query", sa.String(length=255), nullable=False, comment="Expanded query text"),
        sa.Column("expansion_type", sa.String(length=32), nullable=False, comment="seed/seed_variant/domain_constraint/llm_supplement/etc."),
        sa.Column("based_on", sa.String(length=255), nullable=True, comment="Base term used to derive this expansion"),
        sa.Column("source_type", sa.String(length=32), nullable=False, comment="manual/llm/mined_from_data"),
        sa.Column("review_status", sa.String(length=16), nullable=False, comment="pending/approved/rejected"),
        sa.Column("status", sa.String(length=16), nullable=False, comment="approved/candidate/deprecated"),
        sa.Column("ttl_days", sa.Integer(), nullable=False, comment="Suggested refresh TTL in days"),
        sa.Column("expires_at", sa.DateTime(), nullable=True, comment="Optional expiry time"),
        sa.Column("last_seen_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False, comment="Last ingestion/refresh time"),
        sa.Column("is_active", sa.Boolean(), nullable=False, comment="Whether this expansion remains active"),
        sa.Column("notes", sa.Text(), nullable=True, comment="Operator notes"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_expansion_registry_keyword_db_id"), "expansion_registry", ["keyword_db_id"], unique=False)
    op.create_index(op.f("ix_expansion_registry_keyword_id"), "expansion_registry", ["keyword_id"], unique=False)
    op.create_index(op.f("ix_expansion_registry_normalized_keyword"), "expansion_registry", ["normalized_keyword"], unique=False)
    op.create_index(op.f("ix_expansion_registry_platform"), "expansion_registry", ["platform"], unique=False)
    op.create_index(op.f("ix_expansion_registry_expanded_query"), "expansion_registry", ["expanded_query"], unique=False)

    op.create_table(
        "query_schedule_states",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("query_unit_key", sa.String(length=512), nullable=False, comment="normalized_keyword + platform + expanded_query"),
        sa.Column("keyword_db_id", sa.Integer(), nullable=False, comment="FK-like link to trend_keywords.id"),
        sa.Column("keyword_id", sa.String(length=32), nullable=False, comment="Business keyword ID, e.g. KW_0001"),
        sa.Column("normalized_keyword", sa.String(length=255), nullable=False, comment="Normalized keyword"),
        sa.Column("platform", sa.String(length=32), nullable=False, comment="Platform code for scheduler/crawler"),
        sa.Column("expanded_query", sa.String(length=255), nullable=False, comment="Expanded query text"),
        sa.Column("tier", sa.String(length=32), nullable=False, comment="watchlist-hot/watchlist-normal/discovery"),
        sa.Column("risk_level", sa.String(length=16), nullable=False, comment="low/medium/high"),
        sa.Column("min_revisit_interval_minutes", sa.Integer(), nullable=False, comment="Min revisit interval in minutes"),
        sa.Column("retry_cooldown_minutes", sa.Integer(), nullable=False, comment="Retry cooldown after failure in minutes"),
        sa.Column("next_due_at", sa.DateTime(), nullable=False, comment="Next eligible schedule time"),
        sa.Column("last_scheduled_at", sa.DateTime(), nullable=True, comment="Last scheduling time"),
        sa.Column("last_success_at", sa.DateTime(), nullable=True, comment="Last successful pipeline completion"),
        sa.Column("last_failed_at", sa.DateTime(), nullable=True, comment="Last failed pipeline completion"),
        sa.Column("last_task_id", sa.Integer(), nullable=True, comment="Last related crawl task id"),
        sa.Column("last_task_status", sa.String(length=16), nullable=True, comment="scheduled/completed/failed"),
        sa.Column("failure_count", sa.Integer(), nullable=False, comment="Consecutive failure count"),
        sa.Column("is_active", sa.Boolean(), nullable=False, comment="Whether this query unit is schedulable"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_query_schedule_states_query_unit_key"), "query_schedule_states", ["query_unit_key"], unique=True)
    op.create_index(op.f("ix_query_schedule_states_keyword_db_id"), "query_schedule_states", ["keyword_db_id"], unique=False)
    op.create_index(op.f("ix_query_schedule_states_keyword_id"), "query_schedule_states", ["keyword_id"], unique=False)
    op.create_index(op.f("ix_query_schedule_states_normalized_keyword"), "query_schedule_states", ["normalized_keyword"], unique=False)
    op.create_index(op.f("ix_query_schedule_states_platform"), "query_schedule_states", ["platform"], unique=False)
    op.create_index(op.f("ix_query_schedule_states_expanded_query"), "query_schedule_states", ["expanded_query"], unique=False)
    op.create_index(op.f("ix_query_schedule_states_next_due_at"), "query_schedule_states", ["next_due_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_query_schedule_states_next_due_at"), table_name="query_schedule_states")
    op.drop_index(op.f("ix_query_schedule_states_expanded_query"), table_name="query_schedule_states")
    op.drop_index(op.f("ix_query_schedule_states_platform"), table_name="query_schedule_states")
    op.drop_index(op.f("ix_query_schedule_states_normalized_keyword"), table_name="query_schedule_states")
    op.drop_index(op.f("ix_query_schedule_states_keyword_id"), table_name="query_schedule_states")
    op.drop_index(op.f("ix_query_schedule_states_keyword_db_id"), table_name="query_schedule_states")
    op.drop_index(op.f("ix_query_schedule_states_query_unit_key"), table_name="query_schedule_states")
    op.drop_table("query_schedule_states")

    op.drop_index(op.f("ix_expansion_registry_expanded_query"), table_name="expansion_registry")
    op.drop_index(op.f("ix_expansion_registry_platform"), table_name="expansion_registry")
    op.drop_index(op.f("ix_expansion_registry_normalized_keyword"), table_name="expansion_registry")
    op.drop_index(op.f("ix_expansion_registry_keyword_id"), table_name="expansion_registry")
    op.drop_index(op.f("ix_expansion_registry_keyword_db_id"), table_name="expansion_registry")
    op.drop_table("expansion_registry")
