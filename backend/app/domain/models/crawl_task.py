from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CrawlTaskCreate(BaseModel):
    """Request schema for creating a crawl task."""

    keyword_id: int
    platform: str = Field(..., pattern=r"^(xiaohongshu|douyin|bilibili|weibo|kuaishou|tieba|zhihu|xhs|dy|bili|wb|ks)$")
    login_type: str = Field(default="cookie", pattern=r"^(qrcode|phone|cookie)$")
    headless: bool = Field(default=True)
    enable_comments: bool = Field(default=True)
    enable_sub_comments: bool = Field(default=False)
    start_page: int = Field(default=1, ge=1)
    max_notes_count: int = Field(default=50, ge=1)


class CrawlTaskRead(BaseModel):
    """Response schema for reading a crawl task."""

    id: int
    keyword_id: int
    keyword: str
    platform: str
    status: str
    celery_task_id: Optional[str] = None
    config: Optional[dict] = None
    account_id: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_summary: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CrawlTaskLogRead(BaseModel):
    """Response schema for reading a crawl task log entry."""

    id: int
    task_id: int
    level: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}
