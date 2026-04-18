from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.connection import Base


class Account(Base):
    """Platform account for crawler authentication."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="Platform: xhs/dy/bili/wb/ks/tieba/zhihu")
    cookies: Mapped[str] = mapped_column(Text, nullable=False, comment="Encrypted cookies string")
    login_type: Mapped[str] = mapped_column(String(16), nullable=False, default="cookie", comment="Login type: qrcode/phone/cookie")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active", comment="Status: active/expired/blocked")
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="Last usage time")
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Total usage count")
    rotation_strategy: Mapped[str] = mapped_column(String(32), nullable=False, default="round_robin", comment="Rotation: round_robin/least_used/random")
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Remark")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class TrendKeyword(Base):
    """Trend keyword for driving crawl tasks.

    Schema aligned with trend-keyword.csv:
    keyword_id, keyword, normalized_keyword, topic_cluster, trend_type,
    report_id, report_publish_date, signal_period_type, signal_period_label,
    time_granularity, source_scope, priority, confidence,
    suggested_platforms, query_variants, crawl_goal, risk_flag, notes
    """

    __tablename__ = "trend_keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword_id: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True, comment="Business keyword ID, e.g. KW_0001")
    keyword: Mapped[str] = mapped_column(String(255), nullable=False, comment="Keyword text")
    normalized_keyword: Mapped[str] = mapped_column(String(255), nullable=False, default="", comment="Normalized keyword form")
    topic_cluster: Mapped[str] = mapped_column(String(64), nullable=False, default="", comment="Topic cluster, e.g. ingredient_technology, anti_aging_frontier")
    trend_type: Mapped[str] = mapped_column(String(32), nullable=False, default="ingredient", comment="Trend type: ingredient/claim/scenario/category/risk_compliance")
    report_id: Mapped[str] = mapped_column(String(64), nullable=False, default="", comment="Source report ID, e.g. RPT_20260413_01")
    report_publish_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="Report publish date")
    signal_period_type: Mapped[str] = mapped_column(String(32), nullable=False, default="annual", comment="Signal period: annual/monthly/special_topic/cross_period")
    signal_period_label: Mapped[str] = mapped_column(String(64), nullable=False, default="", comment="Signal period label, e.g. 2026 annual")
    time_granularity: Mapped[str] = mapped_column(String(32), nullable=False, default="annual", comment="Time granularity: annual/monthly/special_topic")
    source_scope: Mapped[str] = mapped_column(String(64), nullable=False, default="industry_research", comment="Source scope: industry_research/douyin/xiaohongshu etc.")
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium", comment="Priority: high/medium/low")
    confidence: Mapped[str] = mapped_column(String(16), nullable=False, default="medium", comment="Confidence: high/medium/low")
    suggested_platforms: Mapped[str] = mapped_column(String(255), nullable=False, default="xiaohongshu", comment="Pipe-separated platforms: xiaohongshu|douyin|industry_news")
    query_variants: Mapped[str] = mapped_column(String(1024), nullable=False, default="", comment="Pipe-separated query variants")
    crawl_goal: Mapped[str] = mapped_column(String(32), nullable=False, default="trend_discovery", comment="Crawl goal: trend_discovery/market_validation/risk_monitoring")
    risk_flag: Mapped[str] = mapped_column(String(16), nullable=False, default="low", comment="Risk flag: low/medium/high")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Notes")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="Whether keyword is active")
    last_crawled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="Last crawl time")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class CrawlTask(Base):
    """Crawl task record."""

    __tablename__ = "crawl_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="FK to trend_keywords.id")
    keyword: Mapped[str] = mapped_column(String(255), nullable=False, comment="Snapshot of keyword at task creation")
    platform: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="Target platform")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", comment="Status: pending/running/completed/failed/cancelled")
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Celery task ID")
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="Crawl config: login_type, headless, etc.")
    account_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="FK to accounts.id")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="Task start time")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="Task completion time")
    result_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="Result summary: count, errors, etc.")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Error message if failed")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class CrawlTaskLog(Base):
    """Crawl task execution log."""

    __tablename__ = "crawl_task_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="FK to crawl_tasks.id")
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="info", comment="Log level: info/warning/error/success")
    message: Mapped[str] = mapped_column(Text, nullable=False, comment="Log message")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class ExpansionRegistry(Base):
    """First-party expansion registry for approved/candidate/deprecated queries."""

    __tablename__ = "expansion_registry"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    keyword_db_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="FK-like link to trend_keywords.id")
    keyword_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="Business keyword ID, e.g. KW_0001")
    normalized_keyword: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="Normalized keyword")
    platform: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="Platform label, e.g. xiaohongshu/douyin")
    expanded_query: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="Expanded query text")
    expansion_type: Mapped[str] = mapped_column(String(32), nullable=False, default="seed", comment="seed/seed_variant/domain_constraint/llm_supplement/etc.")
    based_on: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Base term used to derive this expansion")
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="manual", comment="manual/llm/mined_from_data")
    review_status: Mapped[str] = mapped_column(String(16), nullable=False, default="approved", comment="pending/approved/rejected")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="approved", comment="approved/candidate/deprecated")
    ttl_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30, comment="Suggested refresh TTL in days")
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="Optional expiry time")
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), comment="Last ingestion/refresh time")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="Whether this expansion remains active")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Operator notes")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class QueryScheduleState(Base):
    """Persistent schedule state for query_unit = normalized_keyword + platform + expanded_query."""

    __tablename__ = "query_schedule_states"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    query_unit_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True, index=True, comment="normalized_keyword + platform + expanded_query")
    keyword_db_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="FK-like link to trend_keywords.id")
    keyword_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="Business keyword ID, e.g. KW_0001")
    normalized_keyword: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="Normalized keyword")
    platform: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="Platform code for scheduler/crawler")
    expanded_query: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="Expanded query text")
    tier: Mapped[str] = mapped_column(String(32), nullable=False, default="watchlist-normal", comment="watchlist-hot/watchlist-normal/discovery")
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False, default="low", comment="low/medium/high")
    min_revisit_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=1440, comment="Min revisit interval in minutes")
    retry_cooldown_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=1440, comment="Retry cooldown after failure in minutes")
    next_due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True, comment="Next eligible schedule time")
    last_scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="Last scheduling time")
    last_success_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="Last successful pipeline completion")
    last_failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="Last failed pipeline completion")
    last_task_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Last related crawl task id")
    last_task_status: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="scheduled/completed/failed")
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Consecutive failure count")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="Whether this query unit is schedulable")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class RuntimeBatchRun(Base):
    """First-party runtime batch execution record for audit and replay."""

    __tablename__ = "runtime_batch_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True, comment="Stable runtime batch id")
    run_type: Mapped[str] = mapped_column(String(32), nullable=False, default="int002_runtime", comment="Batch type: int002_runtime/export/etc.")
    trigger_source: Mapped[str] = mapped_column(String(32), nullable=False, default="manual", comment="Trigger source: manual/cron/celery/api")
    profile_name: Mapped[str] = mapped_column(String(32), nullable=False, default="safe_live", comment="Applied runtime profile name")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running", comment="Status: running/completed/failed")
    completion_classification: Mapped[Optional[str]] = mapped_column(
        String(24),
        nullable=True,
        comment="completed_full/completed_partial/failed",
    )
    platforms: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="Requested platforms for the batch run")
    requested_options: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="Requested runtime options before policy merge")
    effective_options: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="Effective runtime policy/options after merge")
    summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="Run summary counts and key outcomes")
    report_paths: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="Generated report artifact paths")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Top-level batch failure message")
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), comment="Batch start time")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="Batch completion time")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class RuntimeBatchRunEvent(Base):
    """Keyword/task-level events within a runtime batch."""

    __tablename__ = "runtime_batch_run_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_run_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="FK-like link to runtime_batch_runs.id")
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="Stable runtime batch id")
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="scheduled/skipped_duplicate/no_candidates/task_completed/task_failed")
    platform: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="Target platform")
    keyword_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="FK-like link to trend_keywords.id")
    keyword: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Original keyword")
    task_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="FK-like link to crawl_tasks.id")
    dedup_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Task dedup key for replay/audit")
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="Event payload for audit and replay")
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Short event note")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class RuntimeBatchItem(Base):
    """Execution unit state for recovery and completion audit."""

    __tablename__ = "runtime_batch_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_run_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="FK-like link to runtime_batch_runs.id")
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="Stable runtime batch id")
    query_unit_key: Mapped[str] = mapped_column(String(512), nullable=False, index=True, comment="normalized_keyword + platform + expanded_query")
    keyword_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="FK-like link to trend_keywords.id")
    keyword: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Keyword snapshot")
    platform: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="Target platform code")
    expanded_query: Mapped[str] = mapped_column(String(255), nullable=False, comment="Expanded query text")
    query_state_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="FK-like link to query_schedule_states.id")
    task_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="FK-like link to crawl_tasks.id")
    item_status: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        default="planned",
        comment="planned/dispatched/running/succeeded/failed_retryable/failed_terminal/skipped_duplicate",
    )
    retryable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="Whether item can be retried")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Total dispatch attempts")
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Last failure reason")
    last_heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="Last progress heartbeat")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="Completion time if terminal")
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="Planner/runtime metadata snapshot")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class TrendSignalSeries(Base):
    """Bucketed trend signal series for dynamic trend observation."""

    __tablename__ = "trend_signal_series"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    series_key: Mapped[str] = mapped_column(String(512), nullable=False, index=True, comment="normalized_keyword + platform + bucket")
    bucket_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True, comment="12h/1d")
    bucket_start: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True, comment="Bucket start time")
    bucket_end: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="Bucket end time")
    normalized_keyword: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="Normalized keyword")
    source_platform: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="Platform label")
    support_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Number of supporting signals")
    avg_trend_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="Average trend score in bucket")
    delta_vs_prev_bucket: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="Delta metrics against previous bucket")
    top_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Representative evidence text")
    signal_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="Trace signal ids")
    task_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="Trace task ids")
    aggregation_method: Mapped[str] = mapped_column(String(64), nullable=False, default="bucket_avg_v1", comment="Aggregation method version")
    series_status: Mapped[str] = mapped_column(String(16), nullable=False, default="stable", comment="emerging/stable/cooling")
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), comment="Row generation time")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class CleanedTrendData(Base):
    """Cleaned trend data after AI processing."""

    __tablename__ = "cleaned_trend_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="Source type: note/video/article")
    source_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="Original data ID in MediaCrawler tables")
    source_platform: Mapped[str] = mapped_column(String(32), nullable=False, index=True, comment="Source platform")
    keyword: Mapped[str] = mapped_column(String(255), nullable=False, index=True, comment="Keyword that triggered this crawl")
    crawl_task_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="FK to crawl_tasks.id")
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Title of the content")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="AI-generated summary")
    topics: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True, comment="Comma-separated topic tags")
    sentiment: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, comment="Sentiment: positive/negative/neutral")
    trend_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="Trend score calculated from engagement metrics")
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="Snapshot of original data")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
