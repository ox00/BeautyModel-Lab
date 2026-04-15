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
