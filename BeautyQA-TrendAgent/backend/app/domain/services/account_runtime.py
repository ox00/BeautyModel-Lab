from __future__ import annotations

from pathlib import Path


LOCAL_BROWSER_STATE_COOKIE = "__LOCAL_BROWSER_STATE__"

ACCOUNT_PLATFORM_MAP = {
    "xiaohongshu": "xhs",
    "xhs": "xhs",
    "douyin": "dy",
    "dy": "dy",
    "bilibili": "bili",
    "bili": "bili",
    "weibo": "wb",
    "wb": "wb",
    "kuaishou": "ks",
    "ks": "ks",
    "tieba": "tieba",
    "zhihu": "zhihu",
}


def normalize_account_platform(platform: str) -> str:
    return ACCOUNT_PLATFORM_MAP.get(platform.strip(), platform.strip())


def is_local_browser_state_account(cookie_value: str | None) -> bool:
    return (cookie_value or "").strip() == LOCAL_BROWSER_STATE_COOKIE


def build_local_browser_state_remark(browser_state_dir: Path) -> str:
    return f"managed_local_browser_state:{browser_state_dir}"
