from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.config.settings import settings
from app.infrastructure.database.connection import async_session_factory
from app.infrastructure.database.models import CleanedTrendData
from app.infrastructure.repositories.trend_repo_impl import TrendRepositoryImpl

logger = logging.getLogger(__name__)

# SQL to fetch raw data from MediaCrawler tables after a crawl
# Only fetch posts from the last 12 months (time is millisecond timestamp)
RAW_DATA_QUERIES = {
    "xhs": "SELECT note_id as source_id, title, \"desc\", 'note' as source_type, liked_count, collected_count, comment_count, share_count, source_keyword FROM xhs_note WHERE source_keyword = :keyword AND time >= :time_threshold",
    "dy": "SELECT aweme_id as source_id, title, \"desc\", 'video' as source_type, liked_count, '' as collected_count, comment_count, share_count, source_keyword FROM douyin_aweme WHERE source_keyword = :keyword AND create_time >= :time_threshold_sec",
    "bili": "SELECT video_id as source_id, title, \"desc\" as description, 'video' as source_type, liked_count, video_favorite_count as collected_count, video_comment as comment_count, video_share_count as share_count, source_keyword FROM bilibili_video WHERE source_keyword = :keyword AND create_time >= :time_threshold_sec",
    "wb": "SELECT note_id as source_id, '' as title, content as \"desc\", 'note' as source_type, liked_count, '' as collected_count, comments_count as comment_count, shared_count as share_count, source_keyword FROM weibo_note WHERE source_keyword = :keyword",
}

CLEANING_PROMPT = """你是一个专业的内容分析助手。请对以下社交媒体内容进行分析，返回JSON格式的结果。

要求：
1. summary: 生成50-150字的内容摘要
2. topics: 提取主题标签，从以下类别中选择：概念类、成分类、产品形态、美学风格，也可添加具体标签
3. sentiment: 情感分析，选择 positive/negative/neutral 之一
4. noise: 是否为广告/无关内容 (true/false)

待分析内容：
标题: {title}
描述: {desc}

请严格按以下JSON格式返回，不要添加其他内容：
{{"summary": "...", "topics": ["标签1", "标签2"], "sentiment": "positive/negative/neutral", "noise": false}}"""

NEGATIVE_HINTS = ("曝光", "避雷", "风险", "副作用", "骗局", "三无", "虚假", "神药")
POSITIVE_HINTS = ("推荐", "教程", "干货", "分享", "测评", "好用", "入门")


class CleaningAgent(BaseAgent):
    """Agent responsible for AI-powered data cleaning of crawled content.

    This agent:
    1. Reads raw data from MediaCrawler tables in PostgreSQL
    2. Calls LLM for summarization, topic classification, and sentiment analysis
    3. Calculates trend score based on engagement metrics
    4. Writes cleaned results to cleaned_trend_data table
    """

    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )

    @property
    def name(self) -> str:
        return "CleaningAgent"

    async def execute(self, context: AgentContext) -> AgentResult:
        """Clean raw data for a completed crawl task.

        Expects context to have:
        - task_id: The completed crawl task ID
        - platform: The platform that was crawled
        - keyword: The keyword that was used
        """
        task_id = context.task_id
        platform = context.platform
        keyword = context.keyword

        if not task_id or not platform or not keyword:
            return AgentResult(success=False, error="Missing task_id, platform, or keyword")

        try:
            # Step 1: Read raw data from MediaCrawler tables
            raw_items = await self._fetch_raw_data(
                platform,
                keyword,
                max_raw_items=context.extra.get("max_raw_items"),
            )

            if not raw_items:
                logger.info(f"[{self.name}] No raw data found for {platform}/{keyword}")
                return AgentResult(success=True, data={"cleaned_count": 0})

            # Step 2: Process each item through LLM
            cleaned_items = []
            for item in raw_items:
                if item.get("noise", False):
                    continue

                cleaned = await self._process_item(item, platform, keyword, task_id)
                if cleaned:
                    cleaned_items.append(cleaned)

            # Step 3: Bulk save cleaned data to database
            async with async_session_factory() as session:
                repo = TrendRepositoryImpl(session)
                if cleaned_items:
                    await repo.bulk_create(cleaned_items)
                    await session.commit()

            # Step 4: Save cleaned data to local JSON file
            if cleaned_items:
                self._save_to_local_json(cleaned_items, platform, keyword, task_id)

            logger.info(f"[{self.name}] Cleaned {len(cleaned_items)} items for task {task_id}")
            return AgentResult(
                success=True,
                data={"cleaned_count": len(cleaned_items), "task_id": task_id},
            )

        except Exception as e:
            logger.error(f"[{self.name}] Cleaning failed for task {task_id}: {e}")
            return AgentResult(success=False, error=str(e))

    async def _fetch_raw_data(
        self,
        platform: str,
        keyword: str,
        max_raw_items: Optional[int] = None,
    ) -> list[dict]:
        """Fetch raw data from MediaCrawler tables.
        
        Only fetches posts from the last 12 months to control data volume.
        """
        query = RAW_DATA_QUERIES.get(platform)
        if not query:
            logger.warning(f"[{self.name}] No raw data query for platform: {platform}")
            return []

        # Calculate time threshold: 12 months ago in millisecond timestamp
        import time as _time
        from datetime import datetime, timedelta
        twelve_months_ago = datetime.now() - timedelta(days=365)
        time_threshold_ms = int(twelve_months_ago.timestamp() * 1000)
        time_threshold_sec = int(twelve_months_ago.timestamp())
        time_threshold_str = twelve_months_ago.strftime("%Y-%m-%d")

        from sqlalchemy import text
        async with async_session_factory() as session:
            result = await session.execute(
                text(query),
                {
                    "keyword": keyword,
                    "time_threshold": time_threshold_ms,
                    "time_threshold_sec": time_threshold_sec,
                    "time_threshold_str": time_threshold_str,
                },
            )
            rows = result.mappings().all()
            if isinstance(max_raw_items, int) and max_raw_items > 0:
                rows = rows[:max_raw_items]
            logger.info(
                f"[{self.name}] Fetched {len(rows)} raw items for {platform}/{keyword} "
                f"(time_threshold: {time_threshold_str})"
            )
            return [dict(row) for row in rows]

    async def _process_item(
        self, item: dict, platform: str, keyword: str, task_id: int
    ) -> Optional[CleanedTrendData]:
        """Process a single raw data item through LLM and return cleaned data."""
        title = item.get("title", "") or ""
        desc = item.get("desc", "") or item.get("description", "") or ""

        if not title and not desc:
            return None

        # Call LLM for analysis
        prompt = CLEANING_PROMPT.format(title=title[:500], desc=desc[:1000])

        try:
            response = await self._client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=1.0,
                max_tokens=4096,
                # Enable thinking mode for better analysis quality
                extra_body={"thinking": {"type": "enabled"}},
            )

            content = response.choices[0].message.content or "{}"
            analysis = self._parse_analysis(content)
            if analysis is None:
                logger.warning(f"[{self.name}] LLM returned invalid JSON, falling back to heuristic summary")
                analysis = self._build_fallback_analysis(title, desc, keyword)

            # Skip noise
            if analysis.get("noise", False):
                return None

            # Calculate trend score
            liked = self._safe_int(item.get("liked_count", "0"))
            collected = self._safe_int(item.get("collected_count", "0"))
            comment = self._safe_int(item.get("comment_count", "0"))
            share = self._safe_int(item.get("share_count", "0"))

            trend_score = liked * 1.0 + collected * 2.0 + comment * 1.5 + share * 3.0

            return CleanedTrendData(
                source_type=item.get("source_type", "note"),
                source_id=str(item.get("source_id", "")),
                source_platform=platform,
                keyword=keyword,
                crawl_task_id=task_id,
                title=title[:500],
                summary=analysis.get("summary", ""),
                topics=",".join(analysis.get("topics", [])),
                sentiment=analysis.get("sentiment", "neutral"),
                trend_score=min(trend_score, 10000.0),
                raw_data=item,
            )

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"[{self.name}] LLM analysis failed for item: {e}")
            analysis = self._build_fallback_analysis(title, desc, keyword)

            liked = self._safe_int(item.get("liked_count", "0"))
            collected = self._safe_int(item.get("collected_count", "0"))
            comment = self._safe_int(item.get("comment_count", "0"))
            share = self._safe_int(item.get("share_count", "0"))
            trend_score = liked * 1.0 + collected * 2.0 + comment * 1.5 + share * 3.0

            return CleanedTrendData(
                source_type=item.get("source_type", "note"),
                source_id=str(item.get("source_id", "")),
                source_platform=platform,
                keyword=keyword,
                crawl_task_id=task_id,
                title=title[:500],
                summary=analysis.get("summary", ""),
                topics=",".join(analysis.get("topics", [])),
                sentiment=analysis.get("sentiment", "neutral"),
                trend_score=min(trend_score, 10000.0),
                raw_data=item,
            )

    @staticmethod
    def _strip_code_fences(content: str) -> str:
        content = content.strip()
        if content.startswith("```"):
            first_newline = content.find("\n")
            if first_newline != -1:
                content = content[first_newline + 1 :]
            if content.rstrip().endswith("```"):
                content = content.rstrip()[:-3].rstrip()
        return content.strip()

    @classmethod
    def _parse_analysis(cls, content: str) -> Optional[dict]:
        normalized = cls._strip_code_fences(content)
        candidates = [normalized]

        first_brace = normalized.find("{")
        last_brace = normalized.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            candidates.append(normalized[first_brace : last_brace + 1])

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
        return None

    @staticmethod
    def _build_fallback_analysis(title: str, desc: str, keyword: str) -> dict:
        merged = " ".join(part.strip() for part in (title, desc) if part and part.strip())
        summary = merged[:150] if merged else keyword
        sentiment = "neutral"
        if any(token in merged for token in NEGATIVE_HINTS):
            sentiment = "negative"
        elif any(token in merged for token in POSITIVE_HINTS):
            sentiment = "positive"

        topics = [keyword]
        return {
            "summary": summary,
            "topics": topics,
            "sentiment": sentiment,
            "noise": False,
        }

    @staticmethod
    def _safe_int(value) -> int:
        """Safely convert a value to int."""
        try:
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _save_to_local_json(
        cleaned_items: list[CleanedTrendData],
        platform: str,
        keyword: str,
        task_id: int,
    ) -> Path:
        """Save cleaned results to a local JSON file.

        Files are saved under backend/data/cleaned/{platform}/{keyword}_{timestamp}.json
        This provides a local backup alongside the PostgreSQL database storage.

        Returns:
            Path to the saved JSON file.
        """
        # Build output path: backend/data/cleaned/{platform}/
        base_dir = Path(settings.DATA_DIR) / "cleaned" / platform
        base_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_keyword = keyword.replace(" ", "_").replace("/", "_")
        filename = f"{safe_keyword}_task{task_id}_{timestamp}.json"
        filepath = base_dir / filename

        # Serialize cleaned items to JSON-compatible list
        records = []
        for item in cleaned_items:
            record = {
                "source_type": item.source_type,
                "source_id": item.source_id,
                "source_platform": item.source_platform,
                "keyword": item.keyword,
                "crawl_task_id": item.crawl_task_id,
                "title": item.title,
                "summary": item.summary,
                "topics": item.topics,
                "sentiment": item.sentiment,
                "trend_score": item.trend_score,
                "raw_data": item.raw_data,
            }
            records.append(record)

        output = {
            "metadata": {
                "platform": platform,
                "keyword": keyword,
                "task_id": task_id,
                "cleaned_count": len(records),
                "generated_at": datetime.now().isoformat(),
            },
            "data": records,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        logger.info(f"[{CleaningAgent.__name__}] Saved {len(records)} cleaned items to {filepath}")
        return filepath
