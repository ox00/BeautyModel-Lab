from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    """Request schema for creating an account."""

    platform: str = Field(..., pattern=r"^(xiaohongshu|douyin|bilibili|weibo|kuaishou|tieba|zhihu|xhs|dy|bili|wb|ks)$")
    cookies: str = Field(..., min_length=1)
    login_type: str = Field(default="cookie", pattern=r"^(qrcode|phone|cookie)$")
    rotation_strategy: str = Field(default="round_robin", pattern=r"^(round_robin|least_used|random)$")
    remark: Optional[str] = None


class AccountUpdate(BaseModel):
    """Request schema for updating an account."""

    cookies: Optional[str] = None
    login_type: Optional[str] = Field(default=None, pattern=r"^(qrcode|phone|cookie)$")
    status: Optional[str] = Field(default=None, pattern=r"^(active|expired|blocked)$")
    rotation_strategy: Optional[str] = Field(default=None, pattern=r"^(round_robin|least_used|random)$")
    remark: Optional[str] = None


class AccountRead(BaseModel):
    """Response schema for reading an account."""

    id: int
    platform: str
    login_type: str
    status: str
    last_used_at: Optional[datetime] = None
    usage_count: int
    rotation_strategy: str
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AccountBrief(BaseModel):
    """Brief account info (no sensitive data)."""

    id: int
    platform: str
    status: str
    last_used_at: Optional[datetime] = None
    usage_count: int

    model_config = {"from_attributes": True}
