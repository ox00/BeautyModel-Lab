from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Optional

from app.domain.models.keyword import KeywordCreate, KeywordUpdate, KeywordRead, KeywordBatchImport, KeywordCsvRow
from app.domain.services.keyword_expansion_service import normalize_due_platform
from app.infrastructure.database.models import TrendKeyword
from app.infrastructure.repositories.keyword_repo_impl import KeywordRepositoryImpl

logger = logging.getLogger(__name__)


def _create_to_orm(data: KeywordCreate) -> TrendKeyword:
    """Convert KeywordCreate Pydantic model to TrendKeyword ORM model."""
    return TrendKeyword(
        keyword_id=data.keyword_id,
        keyword=data.keyword,
        normalized_keyword=data.normalized_keyword or data.keyword,
        topic_cluster=data.topic_cluster,
        trend_type=data.trend_type,
        report_id=data.report_id,
        report_publish_date=data.report_publish_date,
        signal_period_type=data.signal_period_type,
        signal_period_label=data.signal_period_label,
        time_granularity=data.time_granularity,
        source_scope=data.source_scope,
        priority=data.priority,
        confidence=data.confidence,
        suggested_platforms=data.suggested_platforms,
        query_variants=data.query_variants,
        crawl_goal=data.crawl_goal,
        risk_flag=data.risk_flag,
        notes=data.notes,
    )


class KeywordService:
    """Domain service for managing trend keywords."""

    def __init__(self, repo: KeywordRepositoryImpl) -> None:
        self._repo = repo

    async def create_keyword(self, data: KeywordCreate) -> KeywordRead:
        keyword = _create_to_orm(data)
        keyword = await self._repo.create(keyword)
        return KeywordRead.model_validate(keyword)

    async def update_keyword(self, keyword_id: int, data: KeywordUpdate) -> Optional[KeywordRead]:
        keyword = await self._repo.get_by_id(keyword_id)
        if not keyword:
            return None

        update_fields = [
            "keyword", "normalized_keyword", "topic_cluster", "trend_type",
            "signal_period_type", "priority", "confidence",
            "suggested_platforms", "query_variants", "crawl_goal",
            "risk_flag", "is_active", "notes",
        ]
        for field in update_fields:
            value = getattr(data, field, None)
            if value is not None:
                setattr(keyword, field, value)

        keyword = await self._repo.update(keyword)
        return KeywordRead.model_validate(keyword)

    async def delete_keyword(self, keyword_id: int) -> bool:
        return await self._repo.delete(keyword_id)

    async def get_keyword(self, keyword_id: int) -> Optional[KeywordRead]:
        keyword = await self._repo.get_by_id(keyword_id)
        return KeywordRead.model_validate(keyword) if keyword else None

    async def list_keywords(
        self, is_active: Optional[bool] = None, limit: int = 100, offset: int = 0
    ) -> list[KeywordRead]:
        keywords = await self._repo.list_all(is_active, limit, offset)
        return [KeywordRead.model_validate(k) for k in keywords]

    async def batch_import(self, data: KeywordBatchImport) -> list[KeywordRead]:
        """Batch import keywords from a list of KeywordCreate objects."""
        keywords = [_create_to_orm(item) for item in data.keywords]
        created = await self._repo.bulk_create(keywords)
        return [KeywordRead.model_validate(k) for k in created]

    async def import_csv(self, csv_content: str) -> list[KeywordRead]:
        """Import keywords from CSV content string.

        CSV format must match trend-keyword.csv columns:
        keyword_id, keyword, normalized_keyword, topic_cluster, trend_type,
        report_id, report_publish_date, signal_period_type, signal_period_label,
        time_granularity, source_scope, priority, confidence,
        suggested_platforms, query_variants, crawl_goal, risk_flag, notes

        Uses upsert logic: if keyword_id already exists, updates the row instead.
        """
        reader = csv.DictReader(io.StringIO(csv_content))
        results = []

        for row in reader:
            csv_row = KeywordCsvRow(**row)
            create_data = KeywordCreate(**csv_row.model_dump())

            # Check if keyword_id already exists (upsert)
            existing = await self._repo.get_by_keyword_id(create_data.keyword_id)
            if existing:
                # Update existing keyword
                update_fields = [
                    "keyword", "normalized_keyword", "topic_cluster", "trend_type",
                    "report_id", "report_publish_date", "signal_period_type",
                    "signal_period_label", "time_granularity", "source_scope",
                    "priority", "confidence", "suggested_platforms",
                    "query_variants", "crawl_goal", "risk_flag", "notes",
                ]
                for field in update_fields:
                    value = getattr(create_data, field, None)
                    if value is not None:
                        setattr(existing, field, value)
                existing = await self._repo.update(existing)
                results.append(KeywordRead.model_validate(existing))
            else:
                # Create new keyword
                keyword = _create_to_orm(create_data)
                keyword = await self._repo.create(keyword)
                results.append(KeywordRead.model_validate(keyword))

        if not results:
            return []

        logger.info(f"[KeywordService] Imported/updated {len(results)} keywords from CSV")
        return results

    async def get_due_keywords(self, platform: Optional[str] = None) -> list[KeywordRead]:
        keywords = await self._repo.list_due_for_crawl(normalize_due_platform(platform))
        return [KeywordRead.model_validate(k) for k in keywords]

    async def mark_crawled(self, keyword_id: int, when: Optional[datetime] = None) -> Optional[KeywordRead]:
        keyword = await self._repo.get_by_id(keyword_id)
        if not keyword:
            return None
        keyword.last_crawled_at = when or datetime.now()
        keyword = await self._repo.update(keyword)
        return KeywordRead.model_validate(keyword)
