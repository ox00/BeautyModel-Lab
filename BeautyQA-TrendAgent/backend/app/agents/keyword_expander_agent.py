from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.config.settings import settings

logger = logging.getLogger(__name__)

# User prompt template kept inline (short, stable interface between code and skill)
KEYWORD_EXPANSION_USER_TEMPLATE = """原始关键词: {original_keyword}
主题簇: {topic_cluster}
趋势类型: {trend_type}
已有变体: {existing_variants}

请生成扩充后的美妆护肤领域搜索词，严格按以下JSON格式返回：
{{"expanded_keywords": ["搜索词1", "搜索词2", "搜索词3"]}}"""


def _load_skill_system_prompt(skill_path: str) -> str:
    """Load the System Prompt section from the skill markdown file.

    The skill file (enhance_trend_keyword.md) contains a '### System Prompt'
    section with the full LLM instruction. This function extracts that section
    so the prompt stays in sync with the skill file — just edit the .md file
    and the agent picks up changes automatically.
    """
    path = Path(skill_path)
    if not path.exists():
        logger.warning(f"[KeywordExpanderAgent] Skill file not found: {skill_path}, using fallback prompt")
        return _fallback_system_prompt()

    content = path.read_text(encoding="utf-8")

    # Extract the System Prompt section between "### System Prompt" and next "###" or "##"
    # The skill file has: ### System Prompt\n```\n...content...\n```\n
    marker = "### System Prompt"
    idx = content.find(marker)
    if idx == -1:
        logger.warning(f"[KeywordExpanderAgent] '### System Prompt' not found in {skill_path}, using fallback")
        return _fallback_system_prompt()

    # Find the opening code block after the marker
    after_marker = content[idx + len(marker):]
    code_start = after_marker.find("```")
    if code_start == -1:
        # No code block, take everything until next ## heading
        next_section = after_marker.find("\n## ")
        if next_section == -1:
            prompt_text = after_marker.strip()
        else:
            prompt_text = after_marker[:next_section].strip()
    else:
        # Extract content inside the code block
        after_code_start = after_marker[code_start + 3:]
        # Skip the language identifier line (e.g. blank line after ```)
        newline_after_code = after_code_start.find("\n")
        if newline_after_code != -1:
            after_code_start = after_code_start[newline_after_code + 1:]
        code_end = after_code_start.find("```")
        if code_end == -1:
            prompt_text = after_code_start.strip()
        else:
            prompt_text = after_code_start[:code_end].strip()

    if not prompt_text:
        logger.warning(f"[KeywordExpanderAgent] Empty system prompt extracted from {skill_path}, using fallback")
        return _fallback_system_prompt()

    logger.info(f"[KeywordExpanderAgent] Loaded system prompt from {skill_path} ({len(prompt_text)} chars)")
    return prompt_text


def _fallback_system_prompt() -> str:
    """Minimal fallback prompt if the skill file is unavailable."""
    return (
        "你是一个专门为美妆护肤领域社交媒体爬虫服务的关键词扩充专家。"
        "根据用户提供的原始趋势关键词及其元数据，生成3~6个聚焦于美妆护肤领域的搜索词变体。"
        "所有搜索词必须明确指向护肤品、化妆品、个人护理相关内容。"
        "返回JSON格式：{\"expanded_keywords\": [\"词1\", \"词2\"]}"
    )


class KeywordExpanderAgent(BaseAgent):
    """Agent responsible for expanding trend keywords into beauty/skincare-focused
    search terms using LLM.

    This agent:
    1. Loads the System Prompt from the skill markdown file at runtime
    2. Takes a keyword with its metadata (topic_cluster, trend_type, query_variants)
    3. Calls LLM to generate beauty-domain-specific search variants
    4. Merges expanded keywords with existing variants (deduped)
    5. Returns the final search keyword list for MediaCrawler
    """

    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        # Load system prompt from skill file at init time
        self._system_prompt = _load_skill_system_prompt(settings.KEYWORD_SKILL_PATH)

    @property
    def name(self) -> str:
        return "KeywordExpanderAgent"

    async def execute(self, context: AgentContext) -> AgentResult:
        """Expand a keyword into beauty-focused search terms.

        Expects context to have:
        - keyword: The original trend keyword
        - extra['topic_cluster']: Topic cluster (e.g. 'ingredient_technology')
        - extra['trend_type']: Trend type (e.g. 'ingredient', 'claim')
        - extra['query_variants']: Pipe-separated existing variants (optional)
        """
        keyword = context.keyword
        if not keyword:
            return AgentResult(success=False, error="Missing keyword in context")

        topic_cluster = context.extra.get("topic_cluster", "")
        trend_type = context.extra.get("trend_type", "ingredient")
        query_variants_str = context.extra.get("query_variants", "")

        # Parse existing variants from pipe-separated string
        existing_variants = [v.strip() for v in query_variants_str.split("|") if v.strip()]

        try:
            expanded_keywords = await self._expand_keyword(
                keyword, topic_cluster, trend_type, existing_variants
            )

            # Merge: original keyword + top expanded keywords (deduped, max 3 total)
            # Limit to avoid triggering platform anti-crawl when searching too many keywords
            MAX_CRAWL_KEYWORDS = 3
            merged = [keyword]  # Always include original
            for v in expanded_keywords:
                if v not in merged:
                    merged.append(v)
                if len(merged) >= MAX_CRAWL_KEYWORDS:
                    break
            # existing variants are lower priority, add if room
            for v in existing_variants:
                if v not in merged and len(merged) < MAX_CRAWL_KEYWORDS:
                    merged.append(v)

            logger.info(
                f"[{self.name}] Expanded keyword '{keyword}': "
                f"{len(existing_variants)} existing + {len(expanded_keywords)} new → {len(merged)} for crawl"
            )

            return AgentResult(
                success=True,
                data={
                    "original_keyword": keyword,
                    "expanded_keywords": expanded_keywords,
                    "merged_keywords": merged,
                    # Comma-separated for MediaCrawler --keywords arg
                    "keywords_for_crawler": ",".join(merged),
                },
            )

        except Exception as e:
            logger.error(f"[{self.name}] Keyword expansion failed for '{keyword}': {e}")
            # Fallback: use original keyword + existing variants only
            fallback = [keyword] + existing_variants
            return AgentResult(
                success=True,
                data={
                    "original_keyword": keyword,
                    "expanded_keywords": [],
                    "merged_keywords": fallback,
                    "keywords_for_crawler": ",".join(fallback),
                },
            )

    async def _expand_keyword(
        self,
        keyword: str,
        topic_cluster: str,
        trend_type: str,
        existing_variants: list[str],
    ) -> list[str]:
        """Call LLM to expand a keyword into beauty-focused search terms."""
        user_prompt = KEYWORD_EXPANSION_USER_TEMPLATE.format(
            original_keyword=keyword,
            topic_cluster=topic_cluster or "unknown",
            trend_type=trend_type,
            existing_variants=str(existing_variants) if existing_variants else "[]",
        )

        response = await self._client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=500,
            extra_body={"thinking": {"type": "disabled"}},
        )

        content = response.choices[0].message.content or "{}"
        # Strip markdown code block wrappers (e.g. ```json ... ```)
        content = content.strip()
        if content.startswith("```"):
            first_newline = content.index("\n") + 1
            content = content[first_newline:]
            if content.rstrip().endswith("```"):
                content = content.rstrip()[:-3].rstrip()

        result = json.loads(content)
        expanded = result.get("expanded_keywords", [])

        if not isinstance(expanded, list):
            logger.warning(f"[{self.name}] LLM returned non-list expanded_keywords: {type(expanded)}")
            return []

        return [str(kw).strip() for kw in expanded if str(kw).strip()]
