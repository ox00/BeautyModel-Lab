from __future__ import annotations

from fastapi import APIRouter

from app.config.settings import settings

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "debug": settings.DEBUG,
    }


@router.get("/config")
async def get_system_config():
    """Get non-sensitive system configuration."""
    return {
        "mediacrawler_dir": settings.MEDIACRAWLER_DIR,
        "llm_model": settings.LLM_MODEL,
        "supported_platforms": [
            {"value": "xiaohongshu", "label": "小红书", "cli_name": "xhs"},
            {"value": "douyin", "label": "抖音", "cli_name": "dy"},
            {"value": "bilibili", "label": "B站", "cli_name": "bili"},
            {"value": "weibo", "label": "微博", "cli_name": "wb"},
            {"value": "kuaishou", "label": "快手", "cli_name": "ks"},
            {"value": "tieba", "label": "百度贴吧", "cli_name": "tieba"},
            {"value": "zhihu", "label": "知乎", "cli_name": "zhihu"},
        ],
        "signal_period_type_options": [
            {"value": "annual", "label": "年度趋势"},
            {"value": "monthly", "label": "月度趋势"},
            {"value": "special_topic", "label": "专题趋势"},
            {"value": "cross_period", "label": "跨期趋势"},
        ],
        "crawl_goal_options": [
            {"value": "trend_discovery", "label": "趋势发现"},
            {"value": "market_validation", "label": "市场验证"},
            {"value": "risk_monitoring", "label": "风险监控"},
        ],
    }
