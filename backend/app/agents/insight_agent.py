from __future__ import annotations

import logging
from typing import Optional

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.infrastructure.database.connection import async_session_factory
from app.infrastructure.repositories.trend_repo_impl import TrendRepositoryImpl

logger = logging.getLogger(__name__)


class InsightAgent(BaseAgent):
    """Agent responsible for trend analysis and insight generation.

    This agent performs cross-platform trend aggregation, trend change
    detection, and report generation. Marked as optional in the requirements.
    """

    def __init__(self) -> None:
        pass

    @property
    def name(self) -> str:
        return "InsightAgent"

    async def execute(self, context: AgentContext) -> AgentResult:
        """Generate trend insights from cleaned data.

        Expects context to have:
        - keyword: The keyword to analyze
        - platform: Optional platform filter
        """
        keyword = context.keyword

        if not keyword:
            return AgentResult(success=False, error="Missing keyword in context")

        try:
            async with async_session_factory() as session:
                repo = TrendRepositoryImpl(session)

                # Get cleaned data for this keyword
                platform = context.platform or None
                items = await repo.query(keyword=keyword, platform=platform, limit=100)
                total_count = await repo.count_by_keyword(keyword, platform)

                if not items:
                    return AgentResult(
                        success=True,
                        data={"keyword": keyword, "insight": "No data available for analysis", "total_count": 0},
                    )

                # Simple aggregation analysis
                sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
                topic_counts: dict[str, int] = {}
                total_score = 0.0

                for item in items:
                    if item.sentiment:
                        sentiment_counts[item.sentiment] = sentiment_counts.get(item.sentiment, 0) + 1
                    if item.topics:
                        for topic in item.topics.split(","):
                            topic = topic.strip()
                            if topic:
                                topic_counts[topic] = topic_counts.get(topic, 0) + 1
                    total_score += item.trend_score

                avg_score = total_score / len(items) if items else 0
                top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]

                insight = {
                    "keyword": keyword,
                    "total_count": total_count,
                    "analyzed_count": len(items),
                    "avg_trend_score": round(avg_score, 2),
                    "sentiment_distribution": sentiment_counts,
                    "top_topics": top_topics,
                    "platform": platform or "all",
                }

                logger.info(f"[{self.name}] Generated insight for keyword '{keyword}': {insight}")
                return AgentResult(success=True, data=insight)

        except Exception as e:
            logger.error(f"[{self.name}] Insight generation failed: {e}")
            return AgentResult(success=False, error=str(e))
