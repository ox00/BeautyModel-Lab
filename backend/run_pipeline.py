#!/usr/bin/env python
"""
趋势采集自动化流程脚本
============================
支持模式：
  - 测试模式：仅从 trend-keyword.csv 提取前5个关键词
  - 正式模式：处理全部关键词，支持周期调度

用法：
  python run_pipeline.py --mode test --platform xhs
  python run_pipeline.py --mode prod --platform xhs,douyin,bili --schedule weekly
  python run_pipeline.py --mode prod --platform xhs --schedule daily --login-type qrcode
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Ensure backend is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config.settings import settings
from app.agents.base import AgentContext, AgentResult
from app.agents.keyword_expander_agent import KeywordExpanderAgent
from app.agents.cleaning_agent import CleaningAgent
from app.infrastructure.crawler.config_mapper import CrawlerConfigMapper
from app.infrastructure.crawler.adapter import CrawlerAdapter, CrawlRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
# Enable debug-level logging for subprocess output forwarding
logging.getLogger("app.infrastructure.crawler.process_manager").setLevel(logging.DEBUG)
logger = logging.getLogger("pipeline")

# ── Constants ──────────────────────────────────────────────────────────
TEST_KEYWORD_LIMIT = 5
SCHEDULE_INTERVALS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
    "monthly": timedelta(days=30),
}
PLATFORM_NAMES = {
    "xhs": "小红书",
    "dy": "抖音",
    "bili": "B站",
    "wb": "微博",
}


# ── CSV Loader ──────────────────────────────────────────────────────────
def load_keywords_from_csv(csv_path: str, limit: Optional[int] = None) -> list[dict]:
    """Load keywords from trend-keyword.csv.

    Returns list of dicts with keys:
      keyword, topic_cluster, trend_type, query_variants, suggested_platforms
    """
    keywords = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            keywords.append({
                "keyword": row.get("keyword", ""),
                "topic_cluster": row.get("topic_cluster", ""),
                "trend_type": row.get("trend_type", "ingredient"),
                "query_variants": row.get("query_variants", ""),
                "suggested_platforms": row.get("suggested_platforms", "xiaohongshu"),
            })

    if limit and limit < len(keywords):
        keywords = keywords[:limit]
        logger.info(f"[CSV] Loaded {limit}/{len(keywords)} keywords (test mode limit)")

    logger.info(f"[CSV] Loaded {len(keywords)} keywords from {csv_path}")
    return keywords


# ── Pipeline Steps ──────────────────────────────────────────────────────
async def expand_keyword(
    keyword: str,
    topic_cluster: str,
    trend_type: str,
    query_variants: str,
) -> dict:
    """Step 1: Expand keyword via LLM (thinking:disabled)."""
    expander = KeywordExpanderAgent()
    ctx = AgentContext(
        keyword=keyword,
        extra={
            "topic_cluster": topic_cluster,
            "trend_type": trend_type,
            "query_variants": query_variants,
        },
    )
    result = await expander.execute(ctx)
    if result.success:
        return {
            "original_keyword": keyword,
            "expanded_keywords": result.data.get("expanded_keywords", []),
            "keywords_for_crawler": result.data.get("keywords_for_crawler", keyword),
        }
    else:
        logger.warning(f"[Expand] Failed for '{keyword}': {result.error}")
        return {
            "original_keyword": keyword,
            "expanded_keywords": [],
            "keywords_for_crawler": keyword,
        }


async def run_crawl(
    task_id: int,
    platform: str,
    keyword: str,
    keywords_for_crawler: str,
    login_type: str = "qrcode",
    headless: bool = False,
) -> dict:
    """Step 2: Execute MediaCrawler crawl for a keyword on a platform.

    Each expanded keyword is crawled in a SEPARATE subprocess so that:
    1. A hang on one keyword doesn't block others
    2. Progress is visible after each keyword completes
    3. The subprocess timeout (15 min) applies per-keyword, not per-batch
    """
    # Split expanded keywords into individual crawl tasks.
    # Each keyword runs in its own subprocess for isolation.
    individual_keywords = [k.strip() for k in keywords_for_crawler.split(",") if k.strip()]
    if not individual_keywords:
        individual_keywords = [keyword]

    all_results = []
    adapter = CrawlerAdapter()

    for i, single_kw in enumerate(individual_keywords):
        sub_task_id = task_id * 100 + i
        # First keyword uses the requested login_type (e.g. qrcode);
        # subsequent keywords switch to cookie mode to reuse saved login state.
        effective_login_type = login_type if i == 0 else "cookie"
        request = CrawlRequest(
            task_id=sub_task_id,
            platform=platform,
            keyword=single_kw,  # Use the individual keyword as the primary
            login_type=effective_login_type,
            headless=headless,
            enable_comments=True,
            enable_sub_comments=False,
            keywords_for_crawler=single_kw,  # ONE keyword per subprocess
        )

        logger.info(f"[Crawl] Starting subprocess: platform={platform}, keyword={single_kw}")
        try:
            response = await adapter.crawl_keyword(request)
            all_results.append({
                "keyword": single_kw,
                "success": response.success,
                "exit_code": response.exit_code,
                "error_message": response.error_message if not response.success else "",
            })
        except Exception as e:
            logger.error(f"[Crawl] Subprocess error for '{single_kw}': {e}")
            all_results.append({
                "keyword": single_kw,
                "success": False,
                "exit_code": -1,
                "error_message": str(e),
            })

        # Log per-keyword result
        r = all_results[-1]
        status = "OK" if r["success"] else f"FAILED ({r['error_message'][:80]})"
        logger.info(f"[Crawl] Keyword '{single_kw}': {status}")

    # Aggregate results
    success_count = sum(1 for r in all_results if r["success"])
    overall_success = success_count > 0  # At least one keyword succeeded

    return {
        "task_id": task_id,
        "platform": platform,
        "keyword": keyword,
        "success": overall_success,
        "exit_code": 0 if overall_success else -1,
        "error_message": "" if overall_success else "; ".join(
            f"{r['keyword']}: {r['error_message']}" for r in all_results if not r["success"]
        ),
        "detail": all_results,
    }


async def run_cleaning(
    task_id: int,
    platform: str,
    keyword: str,
) -> dict:
    """Step 3: AI-powered data cleaning (thinking:enabled)."""
    cleaner = CleaningAgent()
    ctx = AgentContext(
        task_id=task_id,
        platform=platform,
        keyword=keyword,
    )
    result = await cleaner.execute(ctx)

    return {
        "task_id": task_id,
        "platform": platform,
        "keyword": keyword,
        "success": result.success,
        "cleaned_count": result.data.get("cleaned_count", 0) if result.success else 0,
        "error": result.error if not result.success else "",
    }


# ── Main Pipeline ───────────────────────────────────────────────────────
async def run_pipeline_once(
    mode: str,
    platforms: list[str],
    login_type: str = "qrcode",
    headless: bool = False,
) -> dict:
    """Execute the full pipeline once: expand → crawl → clean.

    Args:
        mode: "test" (first 5 keywords) or "prod" (all keywords)
        platforms: List of platform codes (e.g. ["xhs"], ["xhs", "dy", "bili"])
        login_type: MediaCrawler login type (qrcode/phone/cookie)
        headless: Whether to run browser headless

    Returns:
        Summary dict with results.
    """
    csv_path = settings.TREND_KEYWORD_CSV
    limit = TEST_KEYWORD_LIMIT if mode == "test" else None
    keywords = load_keywords_from_csv(csv_path, limit=limit)

    if not keywords:
        logger.error("[Pipeline] No keywords loaded from CSV!")
        return {"status": "error", "message": "No keywords loaded"}

    mode_label = "测试" if mode == "test" else "正式"
    platform_labels = [PLATFORM_NAMES.get(p, p) for p in platforms]
    logger.info(f"\n{'='*60}")
    logger.info(f"  趋势采集流水线 [{mode_label}模式]")
    logger.info(f"  平台: {', '.join(platform_labels)}")
    logger.info(f"  关键词数: {len(keywords)}")
    logger.info(f"{'='*60}\n")

    summary = {
        "mode": mode,
        "platforms": platforms,
        "total_keywords": len(keywords),
        "results": [],
        "start_time": datetime.now().isoformat(),
    }

    task_id_counter = 9000  # Virtual task IDs for standalone pipeline

    for idx, kw_data in enumerate(keywords, 1):
        keyword = kw_data["keyword"]
        topic_cluster = kw_data["topic_cluster"]
        trend_type = kw_data["trend_type"]
        query_variants = kw_data["query_variants"]
        suggested_platforms = kw_data["suggested_platforms"]

        logger.info(f"\n[{idx}/{len(keywords)}] 处理关键词: {keyword}")
        kw_result = {"keyword": keyword, "platforms": {}}

        # Step 1: Expand keyword
        logger.info(f"  [1/3] 扩充关键词 (thinking:off)...")
        expansion = await expand_keyword(keyword, topic_cluster, trend_type, query_variants)
        keywords_for_crawler = expansion["keywords_for_crawler"]
        logger.info(f"  扩充结果: {expansion['expanded_keywords']}")

        # Determine which platforms to crawl for this keyword
        crawlable = CrawlerConfigMapper.parse_suggested_platforms(suggested_platforms)
        target_platforms = [p for p in crawlable if p in platforms]

        if not target_platforms:
            logger.info(f"  跳过: 关键词 '{keyword}' 的建议平台 {suggested_platforms} 中无目标平台")
            continue

        for platform in target_platforms:
            task_id = task_id_counter
            task_id_counter += 1

            # Step 2: Crawl
            # First CSV keyword uses original login_type; subsequent ones use cookie
            # to reuse saved login state from the first keyword's browser session.
            effective_login = login_type if idx == 1 else "cookie"
            platform_name = PLATFORM_NAMES.get(platform, platform)
            logger.info(f"  [2/3] 爬取 {platform_name} (login={effective_login})...")
            try:
                crawl_result = await run_crawl(
                    task_id=task_id,
                    platform=platform,
                    keyword=keyword,
                    keywords_for_crawler=keywords_for_crawler,
                    login_type=effective_login,
                    headless=headless,
                )
            except Exception as e:
                logger.error(f"  爬取失败: {e}")
                crawl_result = {
                    "task_id": task_id,
                    "platform": platform,
                    "keyword": keyword,
                    "success": False,
                    "exit_code": -1,
                    "error_message": str(e),
                }

            if not crawl_result["success"]:
                logger.error(f"  爬取失败: {crawl_result['error_message']}")
                kw_result["platforms"][platform] = {"crawl": "failed", "clean": "skipped"}
                continue

            # Step 3: Clean
            logger.info(f"  [3/3] AI数据清洗 (thinking:on)...")
            try:
                clean_result = await run_cleaning(
                    task_id=task_id,
                    platform=platform,
                    keyword=keyword,
                )
            except Exception as e:
                logger.error(f"  清洗失败: {e}")
                clean_result = {
                    "task_id": task_id,
                    "success": False,
                    "cleaned_count": 0,
                    "error": str(e),
                }

            status = "ok" if clean_result["success"] else "failed"
            logger.info(f"  清洗完成: {clean_result['cleaned_count']} 条数据 [{status}]")
            kw_result["platforms"][platform] = {
                "crawl": "ok",
                "clean": status,
                "cleaned_count": clean_result["cleaned_count"],
            }

        summary["results"].append(kw_result)

    summary["end_time"] = datetime.now().isoformat()
    summary["total_results"] = len(summary["results"])

    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info(f"  流水线执行完成")
    logger.info(f"  处理关键词: {summary['total_results']}/{summary['total_keywords']}")
    for r in summary["results"]:
        platforms_str = ", ".join(
            f"{p}: {info.get('clean', 'unknown')}"
            for p, info in r["platforms"].items()
        )
        logger.info(f"    {r['keyword']} → {platforms_str}")
    logger.info(f"{'='*60}")

    return summary


async def run_scheduled_pipeline(
    mode: str,
    platforms: list[str],
    schedule: str,
    login_type: str = "qrcode",
    headless: bool = False,
) -> None:
    """Run the pipeline on a schedule (prod mode only).

    Args:
        schedule: "daily", "weekly", or "monthly"
    """
    interval = SCHEDULE_INTERVALS.get(schedule, timedelta(weeks=1))
    schedule_label = {"daily": "每天", "weekly": "每周", "monthly": "每月"}.get(schedule, schedule)

    logger.info(f"\n{'#'*60}")
    logger.info(f"  定时调度模式: {schedule_label} 自动执行")
    logger.info(f"  间隔: {interval}")
    logger.info(f"  按 Ctrl+C 停止")
    logger.info(f"{'#'*60}\n")

    iteration = 0
    while True:
        iteration += 1
        next_run = datetime.now() + interval

        logger.info(f"\n--- 第 {iteration} 次执行 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ---")
        await run_pipeline_once(mode=mode, platforms=platforms, login_type=login_type, headless=headless)

        logger.info(f"\n下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"等待中... (Ctrl+C 停止)")

        try:
            await asyncio.sleep(interval.total_seconds())
        except asyncio.CancelledError:
            logger.info("收到停止信号，退出调度")
            break


# ── CLI ─────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="趋势采集自动化流程脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_pipeline.py --mode test --platform xhs
  python run_pipeline.py --mode prod --platform xhs,douyin,bili --schedule weekly
  python run_pipeline.py --mode prod --platform xhs --schedule daily --login-type cookie --headless
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["test", "prod"],
        default="test",
        help="运行模式: test=前5个关键词, prod=全部关键词 (默认: test)",
    )
    parser.add_argument(
        "--platform",
        type=str,
        default="xhs",
        help="目标平台，逗号分隔: xhs,douyin,bili,weibo (默认: xhs)",
    )
    parser.add_argument(
        "--schedule",
        choices=["daily", "weekly", "monthly"],
        default=None,
        help="正式模式下的爬取周期 (仅prod模式生效, 默认: 单次执行)",
    )
    parser.add_argument(
        "--login-type",
        choices=["qrcode", "phone", "cookie"],
        default="qrcode",
        help="MediaCrawler登录方式 (默认: qrcode)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="是否无头模式运行浏览器 (默认: 否, 显示浏览器窗口)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Parse platforms
    platforms = [p.strip() for p in args.platform.split(",")]

    # Validate schedule only in prod mode
    if args.schedule and args.mode == "test":
        logger.warning("测试模式不支持定时调度，将仅执行一次")
        args.schedule = None

    # Run pipeline
    if args.schedule:
        asyncio.run(run_scheduled_pipeline(
            mode=args.mode,
            platforms=platforms,
            schedule=args.schedule,
            login_type=args.login_type,
            headless=args.headless,
        ))
    else:
        asyncio.run(run_pipeline_once(
            mode=args.mode,
            platforms=platforms,
            login_type=args.login_type,
            headless=args.headless,
        ))


if __name__ == "__main__":
    main()
