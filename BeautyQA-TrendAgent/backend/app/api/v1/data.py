from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.api.deps import TrendRepoDep
from app.domain.models.trend_data import TrendDataRead, TrendDataExport, TrendDataQuery

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/cleaned", response_model=list[TrendDataRead])
async def query_cleaned_data(
    keyword: Optional[str] = None,
    platform: Optional[str] = None,
    sentiment: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repo: TrendRepoDep = None,
):
    """Query cleaned trend data with optional filters."""
    return await repo.query(
        keyword=keyword,
        platform=platform,
        sentiment=sentiment,
        min_score=min_score,
        limit=limit,
        offset=offset,
    )


@router.get("/export", response_class=JSONResponse)
async def export_trend_data(
    keyword: str,
    platform: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    repo: TrendRepoDep = None,
):
    """Export trend data as JSON for a specific keyword.

    Returns the JSON output format specified in the requirements:
    {
        "keyword": "露营",
        "platform": "douyin",
        "results": [...]
    }
    """
    items = await repo.query(keyword=keyword, platform=platform, limit=limit)
    export = TrendDataExport(
        keyword=keyword,
        platform=platform or "all",
        results=[TrendDataRead.model_validate(item) for item in items],
    )
    return export.model_dump()


@router.get("/count")
async def count_trend_data(
    keyword: str,
    platform: Optional[str] = None,
    repo: TrendRepoDep = None,
):
    """Count cleaned trend data entries for a keyword."""
    count = await repo.count_by_keyword(keyword, platform)
    return {"keyword": keyword, "platform": platform or "all", "count": count}
