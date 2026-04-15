from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Sequence

from sqlalchemy import select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import TrendKeyword


class KeywordRepositoryImpl:
    """SQLAlchemy implementation of KeywordRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, keyword_id: int) -> Optional[TrendKeyword]:
        result = await self._session.get(TrendKeyword, keyword_id)
        return result

    async def get_by_keyword_id(self, keyword_id: str) -> Optional[TrendKeyword]:
        """Get a keyword by its business keyword_id (e.g. KW_0001)."""
        stmt = select(TrendKeyword).where(TrendKeyword.keyword_id == keyword_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self, is_active: Optional[bool] = None, limit: int = 100, offset: int = 0
    ) -> Sequence[TrendKeyword]:
        stmt = select(TrendKeyword)
        if is_active is not None:
            stmt = stmt.where(TrendKeyword.is_active == is_active)
        # Sort: high > medium > low priority using CASE expression
        priority_order = case(
            (TrendKeyword.priority == "high", 0),
            (TrendKeyword.priority == "medium", 1),
            (TrendKeyword.priority == "low", 2),
            else_=3,
        )
        stmt = stmt.order_by(priority_order.asc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_due_for_crawl(self, platform: Optional[str] = None) -> Sequence[TrendKeyword]:
        """List keywords that are due for crawling based on their signal_period_type and last_crawled_at.

        signal_period_type determines the crawl interval:
        - monthly: every 30 days
        - annual: every 365 days
        - special_topic: every 90 days
        - cross_period: every 180 days
        """
        stmt = select(TrendKeyword).where(TrendKeyword.is_active == True)  # noqa: E712

        if platform:
            stmt = stmt.where(TrendKeyword.suggested_platforms.contains(platform))

        # Filter by signal_period_type-based due time
        now = datetime.now()
        monthly_cutoff = now - timedelta(days=30)
        annual_cutoff = now - timedelta(days=365)
        special_cutoff = now - timedelta(days=90)
        cross_period_cutoff = now - timedelta(days=180)

        stmt = stmt.where(
            # Never crawled
            (TrendKeyword.last_crawled_at.is_(None))
            # Or past the signal period interval
            | (
                (TrendKeyword.signal_period_type == "monthly")
                & (TrendKeyword.last_crawled_at < monthly_cutoff)
            )
            | (
                (TrendKeyword.signal_period_type == "annual")
                & (TrendKeyword.last_crawled_at < annual_cutoff)
            )
            | (
                (TrendKeyword.signal_period_type == "special_topic")
                & (TrendKeyword.last_crawled_at < special_cutoff)
            )
            | (
                (TrendKeyword.signal_period_type == "cross_period")
                & (TrendKeyword.last_crawled_at < cross_period_cutoff)
            )
        )
        # Sort by priority: high first using CASE expression
        priority_order = case(
            (TrendKeyword.priority == "high", 0),
            (TrendKeyword.priority == "medium", 1),
            (TrendKeyword.priority == "low", 2),
            else_=3,
        )
        stmt = stmt.order_by(priority_order.asc())

        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create(self, keyword: TrendKeyword) -> TrendKeyword:
        self._session.add(keyword)
        await self._session.flush()
        await self._session.refresh(keyword)
        return keyword

    async def update(self, keyword: TrendKeyword) -> TrendKeyword:
        await self._session.flush()
        await self._session.refresh(keyword)
        return keyword

    async def delete(self, keyword_id: int) -> bool:
        keyword = await self.get_by_id(keyword_id)
        if not keyword:
            return False
        await self._session.delete(keyword)
        await self._session.flush()
        return True

    async def bulk_create(self, keywords: list[TrendKeyword]) -> list[TrendKeyword]:
        self._session.add_all(keywords)
        await self._session.flush()
        for kw in keywords:
            await self._session.refresh(kw)
        return keywords
