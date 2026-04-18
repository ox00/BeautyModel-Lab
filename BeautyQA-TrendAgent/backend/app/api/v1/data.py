from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.api.deps import TrendRepoDep
from app.config.settings import settings
from app.domain.models.trend_data import TrendDataRead, TrendDataExport

router = APIRouter(prefix="/data", tags=["data"])


def _normalize_platform_filter(platform: str) -> str:
    mapping = {
        "xhs": "xiaohongshu",
        "dy": "douyin",
        "bili": "bilibili",
        "wb": "weibo",
        "ks": "kuaishou",
    }
    return mapping.get(platform, platform)


def _load_handoff_signals() -> list[dict]:
    handoff_file = Path(settings.TREND_SIGNAL_HANDOFF_DIR) / "current" / "trend_signal_latest.json"
    if not handoff_file.exists():
        return []
    try:
        payload = json.loads(handoff_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    results = payload.get("results", [])
    return results if isinstance(results, list) else []


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


@router.get("/trend-signals/export", response_class=JSONResponse)
async def export_trend_signals(
    platform: Optional[str] = None,
    normalized_keyword: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    """Export first-party trend_signal records for downstream retrieval."""
    handoff_signals = _load_handoff_signals()
    normalized_platform = _normalize_platform_filter(platform) if platform else None
    if handoff_signals:
        selected = []
        for signal in handoff_signals:
            if not isinstance(signal, dict):
                continue
            if normalized_keyword and signal.get("normalized_keyword") != normalized_keyword:
                continue
            if normalized_platform and signal.get("source_platform") != normalized_platform:
                continue
            selected.append(signal)
            if len(selected) >= limit:
                break
        return {"count": len(selected), "results": selected, "source": "handoff_current"}

    base_dir = Path(settings.DATA_DIR) / "trend_signal"
    if not base_dir.exists():
        return {"count": 0, "results": []}

    pattern = "*.json"

    if platform:
        search_dir = base_dir / platform
        files = sorted(search_dir.glob(pattern), reverse=True) if search_dir.exists() else []
    else:
        files = sorted(base_dir.glob("*/*.json"), reverse=True)

    selected: list[dict] = []
    for fpath in files:
        try:
            payload = json.loads(fpath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        signals = payload.get("trend_signals", [])
        if not isinstance(signals, list):
            continue

        for signal in signals:
            if not isinstance(signal, dict):
                continue
            if normalized_keyword and signal.get("normalized_keyword") != normalized_keyword:
                continue
            if normalized_platform and signal.get("source_platform") != normalized_platform:
                continue
            selected.append(signal)
            if len(selected) >= limit:
                break
        if len(selected) >= limit:
            break

    return {"count": len(selected), "results": selected, "source": "task_json_legacy"}
