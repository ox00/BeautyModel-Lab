from __future__ import annotations

import logging

from sqlalchemy import select

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.domain.services.signal_service import generate_trend_signals, save_trend_signals_json
from app.infrastructure.database.connection import async_session_factory
from app.infrastructure.database.models import CleanedTrendData, CrawlTask, TrendKeyword

logger = logging.getLogger(__name__)


class SignalAgent(BaseAgent):
    """Generate first-party trend_signal outputs from cleaned_trend_data."""

    @property
    def name(self) -> str:
        return "SignalAgent"

    async def execute(self, context: AgentContext) -> AgentResult:
        task_id = context.task_id
        platform = context.platform
        keyword = context.keyword

        if not task_id or not platform or not keyword:
            return AgentResult(success=False, error="Missing task_id, platform, or keyword")

        try:
            async with async_session_factory() as session:
                cleaned_rows = (
                    (
                        await session.execute(
                            select(CleanedTrendData)
                            .where(CleanedTrendData.crawl_task_id == task_id)
                            .order_by(CleanedTrendData.trend_score.desc())
                        )
                    )
                    .scalars()
                    .all()
                )

                if not cleaned_rows:
                    logger.info(f"[{self.name}] No cleaned records for task_id={task_id}")
                    return AgentResult(success=True, data={"signal_count": 0, "trend_signals": []})

                crawl_task = await session.get(CrawlTask, task_id)
                keyword_meta = {}

                if crawl_task:
                    kw = await session.get(TrendKeyword, crawl_task.keyword_id)
                    if kw:
                        keyword_meta = {
                            "keyword_id": kw.keyword_id,
                            "normalized_keyword": kw.normalized_keyword,
                            "topic_cluster": kw.topic_cluster,
                            "trend_type": kw.trend_type,
                            "report_id": kw.report_id,
                            "signal_period_type": kw.signal_period_type,
                            "signal_period_label": kw.signal_period_label,
                            "source_scope": kw.source_scope,
                            "confidence": kw.confidence,
                            "risk_flag": kw.risk_flag,
                        }

                trend_signals, run_summary = generate_trend_signals(
                    cleaned_rows=cleaned_rows,
                    keyword_meta=keyword_meta,
                )

                output_file = save_trend_signals_json(
                    task_id=task_id,
                    platform=platform,
                    keyword=keyword,
                    trend_signals=trend_signals,
                    run_summary=run_summary,
                )

            logger.info(
                f"[{self.name}] Generated {len(trend_signals)} trend_signal records for task {task_id}: {output_file}"
            )
            return AgentResult(
                success=True,
                data={
                    "task_id": task_id,
                    "signal_count": len(trend_signals),
                    "trend_signals": trend_signals,
                    "run_summary": run_summary,
                    "output_file": str(output_file),
                },
            )

        except Exception as e:
            logger.error(f"[{self.name}] Signal generation failed for task {task_id}: {e}")
            return AgentResult(success=False, error=str(e))
