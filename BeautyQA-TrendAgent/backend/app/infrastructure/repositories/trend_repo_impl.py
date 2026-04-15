from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import CleanedTrendData


class TrendRepositoryImpl:
    """SQLAlchemy implementation of TrendRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, data_id: int) -> Optional[CleanedTrendData]:
        result = await self._session.get(CleanedTrendData, data_id)
        return result

    async def query(
        self,
        keyword: Optional[str] = None,
        platform: Optional[str] = None,
        sentiment: Optional[str] = None,
        min_score: Optional[float] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[CleanedTrendData]:
        stmt = select(CleanedTrendData)
        if keyword:
            stmt = stmt.where(CleanedTrendData.keyword == keyword)
        if platform:
            stmt = stmt.where(CleanedTrendData.source_platform == platform)
        if sentiment:
            stmt = stmt.where(CleanedTrendData.sentiment == sentiment)
        if min_score is not None:
            stmt = stmt.where(CleanedTrendData.trend_score >= min_score)
        stmt = stmt.order_by(CleanedTrendData.trend_score.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: CleanedTrendData) -> CleanedTrendData:
        self._session.add(data)
        await self._session.flush()
        await self._session.refresh(data)
        return data

    async def bulk_create(self, data_list: list[CleanedTrendData]) -> list[CleanedTrendData]:
        self._session.add_all(data_list)
        await self._session.flush()
        for item in data_list:
            await self._session.refresh(item)
        return data_list

    async def count_by_keyword(self, keyword: str, platform: Optional[str] = None) -> int:
        stmt = select(func.count()).select_from(CleanedTrendData).where(CleanedTrendData.keyword == keyword)
        if platform:
            stmt = stmt.where(CleanedTrendData.source_platform == platform)
        result = await self._session.execute(stmt)
        return result.scalar() or 0
