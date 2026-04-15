from __future__ import annotations

import logging
from typing import Optional

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.domain.services.keyword_service import KeywordService

logger = logging.getLogger(__name__)


class TrendAgent(BaseAgent):
    """Agent responsible for managing the trend keyword library.

    This agent handles keyword CRUD operations, priority-based sorting,
    batch import from CSV, and detection of keywords that are due for crawling.
    """

    def __init__(self, keyword_service: KeywordService) -> None:
        self._keyword_service = keyword_service

    @property
    def name(self) -> str:
        return "TrendAgent"

    async def execute(self, context: AgentContext) -> AgentResult:
        """Find due keywords for the specified platform.

        If context.platform is set, filters by that platform.
        Returns the list of due keywords in result data.
        """
        try:
            platform = context.platform or None
            due_keywords = await self._keyword_service.get_due_keywords(platform)

            if not due_keywords:
                logger.info(f"[{self.name}] No keywords due for crawling")
                return AgentResult(success=True, data={"due_keywords": [], "count": 0})

            logger.info(f"[{self.name}] Found {len(due_keywords)} keywords due for crawling")
            return AgentResult(
                success=True,
                data={
                    "due_keywords": [k.model_dump() for k in due_keywords],
                    "count": len(due_keywords),
                },
            )
        except Exception as e:
            logger.error(f"[{self.name}] Error finding due keywords: {e}")
            return AgentResult(success=False, error=str(e))
