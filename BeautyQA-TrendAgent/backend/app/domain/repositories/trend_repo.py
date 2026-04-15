from __future__ import annotations

from typing import Protocol, Optional, Sequence

from app.infrastructure.database.models import CleanedTrendData


class TrendRepository(Protocol):
    """Repository interface for CleanedTrendData persistence."""

    async def get_by_id(self, data_id: int) -> Optional[CleanedTrendData]: ...
    async def query(
        self,
        keyword: Optional[str] = None,
        platform: Optional[str] = None,
        sentiment: Optional[str] = None,
        min_score: Optional[float] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[CleanedTrendData]: ...
    async def create(self, data: CleanedTrendData) -> CleanedTrendData: ...
    async def bulk_create(self, data_list: list[CleanedTrendData]) -> list[CleanedTrendData]: ...
    async def count_by_keyword(self, keyword: str, platform: Optional[str] = None) -> int: ...
