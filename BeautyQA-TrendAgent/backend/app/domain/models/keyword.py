from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KeywordCreate(BaseModel):
    """Request schema for creating a trend keyword.

    Fields align with trend-keyword.csv columns.
    """

    keyword_id: str = Field(..., min_length=1, max_length=32, description="Business keyword ID, e.g. KW_0001")
    keyword: str = Field(..., min_length=1, max_length=255)
    normalized_keyword: str = Field(default="", max_length=255)
    topic_cluster: str = Field(default="", max_length=64, description="e.g. ingredient_technology, anti_aging_frontier")
    trend_type: str = Field(default="ingredient", pattern=r"^(ingredient|claim|scenario|category|risk_compliance)$")
    report_id: str = Field(default="", max_length=64)
    report_publish_date: Optional[str] = Field(default=None, max_length=32)
    signal_period_type: str = Field(default="annual", pattern=r"^(annual|monthly|special_topic|cross_period)$")
    signal_period_label: str = Field(default="", max_length=64)
    time_granularity: str = Field(default="annual", pattern=r"^(annual|monthly|special_topic|cross_period)$")
    source_scope: str = Field(default="industry_research", max_length=64)
    priority: str = Field(default="medium", pattern=r"^(high|medium|low)$")
    confidence: str = Field(default="medium", pattern=r"^(high|medium|low)$")
    suggested_platforms: str = Field(default="xiaohongshu", description="Pipe-separated: xiaohongshu|douyin|industry_news")
    query_variants: str = Field(default="", max_length=1024, description="Pipe-separated query variants")
    crawl_goal: str = Field(default="trend_discovery", pattern=r"^(trend_discovery|market_validation|risk_monitoring)$")
    risk_flag: str = Field(default="low", pattern=r"^(high|medium|low)$")
    notes: Optional[str] = None


class KeywordUpdate(BaseModel):
    """Request schema for updating a trend keyword."""

    keyword: Optional[str] = Field(default=None, min_length=1, max_length=255)
    normalized_keyword: Optional[str] = Field(default=None, max_length=255)
    topic_cluster: Optional[str] = Field(default=None, max_length=64)
    trend_type: Optional[str] = Field(default=None, pattern=r"^(ingredient|claim|scenario|category|risk_compliance)$")
    signal_period_type: Optional[str] = Field(default=None, pattern=r"^(annual|monthly|special_topic|cross_period)$")
    priority: Optional[str] = Field(default=None, pattern=r"^(high|medium|low)$")
    confidence: Optional[str] = Field(default=None, pattern=r"^(high|medium|low)$")
    suggested_platforms: Optional[str] = None
    query_variants: Optional[str] = None
    crawl_goal: Optional[str] = Field(default=None, pattern=r"^(trend_discovery|market_validation|risk_monitoring)$")
    risk_flag: Optional[str] = Field(default=None, pattern=r"^(high|medium|low)$")
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class KeywordRead(BaseModel):
    """Response schema for reading a trend keyword."""

    id: int
    keyword_id: str
    keyword: str
    normalized_keyword: str
    topic_cluster: str
    trend_type: str
    report_id: str
    report_publish_date: Optional[str] = None
    signal_period_type: str
    signal_period_label: str
    time_granularity: str
    source_scope: str
    priority: str
    confidence: str
    suggested_platforms: str
    query_variants: str
    crawl_goal: str
    risk_flag: str
    notes: Optional[str] = None
    is_active: bool
    last_crawled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KeywordBatchImport(BaseModel):
    """Request schema for batch importing keywords from CSV data."""

    keywords: list[KeywordCreate]


class KeywordCsvRow(BaseModel):
    """Schema matching a single row in trend-keyword.csv.

    Used for CSV file upload and parsing.
    """

    keyword_id: str = Field(alias="keyword_id")
    keyword: str
    normalized_keyword: str = ""
    topic_cluster: str = ""
    trend_type: str = "ingredient"
    report_id: str = ""
    report_publish_date: Optional[str] = None
    signal_period_type: str = "annual"
    signal_period_label: str = ""
    time_granularity: str = "annual"
    source_scope: str = "industry_research"
    priority: str = "medium"
    confidence: str = "medium"
    suggested_platforms: str = "xiaohongshu"
    query_variants: str = ""
    crawl_goal: str = "trend_discovery"
    risk_flag: str = "low"
    notes: Optional[str] = None

    model_config = {"populate_by_name": True}
