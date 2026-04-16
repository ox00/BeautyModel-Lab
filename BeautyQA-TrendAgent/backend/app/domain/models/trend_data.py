from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TrendDataRead(BaseModel):
    """Response schema for reading cleaned trend data."""

    id: int
    source_type: str
    source_id: str
    source_platform: str
    keyword: str
    crawl_task_id: int
    title: Optional[str] = None
    summary: Optional[str] = None
    topics: Optional[str] = None
    sentiment: Optional[str] = None
    trend_score: float
    raw_data: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TrendDataExport(BaseModel):
    """Export schema for JSON output API."""

    keyword: str
    platform: str
    results: list[TrendDataRead]


class TrendDataQuery(BaseModel):
    """Query parameters for searching trend data."""

    keyword: Optional[str] = None
    platform: Optional[str] = None
    sentiment: Optional[str] = Field(default=None, pattern=r"^(positive|negative|neutral)$")
    min_score: Optional[float] = Field(default=None, ge=0.0)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class TrendSignalListExport(BaseModel):
    """JSON export schema for first-party trend_signal output files."""

    task_id: int
    keyword: str
    normalized_keyword: str
    platform: str
    generated_at: str
    count: int
    run_summary: dict
    trend_signals: list[dict]
