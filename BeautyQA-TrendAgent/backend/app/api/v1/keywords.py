from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.api.deps import KeywordServiceDep
from app.domain.models.keyword import KeywordCreate, KeywordUpdate, KeywordRead, KeywordBatchImport

router = APIRouter(prefix="/keywords", tags=["keywords"])


@router.post("", response_model=KeywordRead, status_code=201)
async def create_keyword(data: KeywordCreate, service: KeywordServiceDep):
    """Add a new trend keyword."""
    return await service.create_keyword(data)


@router.get("", response_model=list[KeywordRead])
async def list_keywords(
    is_active: Optional[bool] = None,
    trend_type: Optional[str] = None,
    crawl_goal: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    service: KeywordServiceDep = None,
):
    """List trend keywords with optional filtering."""
    return await service.list_keywords(is_active, limit, offset)


@router.get("/{keyword_id}", response_model=KeywordRead)
async def get_keyword(keyword_id: int, service: KeywordServiceDep):
    """Get keyword by ID."""
    keyword = await service.get_keyword(keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return keyword


@router.patch("/{keyword_id}", response_model=KeywordRead)
async def update_keyword(keyword_id: int, data: KeywordUpdate, service: KeywordServiceDep):
    """Update a keyword."""
    keyword = await service.update_keyword(keyword_id, data)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return keyword


@router.delete("/{keyword_id}", status_code=204)
async def delete_keyword(keyword_id: int, service: KeywordServiceDep):
    """Delete a keyword."""
    if not await service.delete_keyword(keyword_id):
        raise HTTPException(status_code=404, detail="Keyword not found")


@router.post("/batch", response_model=list[KeywordRead], status_code=201)
async def batch_import_keywords(data: KeywordBatchImport, service: KeywordServiceDep):
    """Batch import keywords from JSON list."""
    return await service.batch_import(data)


@router.post("/import/csv", response_model=list[KeywordRead], status_code=201)
async def import_csv(
    file: UploadFile = File(..., description="CSV file matching trend-keyword.csv format"),
    service: KeywordServiceDep = None,
):
    """Import keywords from a CSV file upload.

    CSV columns must match trend-keyword.csv format:
    keyword_id, keyword, normalized_keyword, topic_cluster, trend_type,
    report_id, report_publish_date, signal_period_type, signal_period_label,
    time_granularity, source_scope, priority, confidence,
    suggested_platforms, query_variants, crawl_goal, risk_flag, notes
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    try:
        content = await file.read()
        csv_text = content.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV file: {e}")

    try:
        result = await service.import_csv(csv_text)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"CSV parsing error: {e}")

    return result


@router.get("/due/list", response_model=list[KeywordRead])
async def list_due_keywords(
    platform: Optional[str] = None,
    service: KeywordServiceDep = None,
):
    """List keywords that are due for crawling."""
    return await service.get_due_keywords(platform)
