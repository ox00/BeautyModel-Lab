from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from openai import AsyncOpenAI

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.config.settings import settings
from app.domain.services.keyword_expansion_service import (
    PLATFORM_LABEL_TO_CODE,
    build_keyword_execution_plan,
    parse_query_variants,
)
from app.domain.services.runtime_query_state_service import infer_watchlist_tier

logger = logging.getLogger(__name__)

KEYWORD_EXPANSION_USER_TEMPLATE = """原始关键词: {original_keyword}
归一化主题: {normalized_keyword}
主题簇: {topic_cluster}
趋势类型: {trend_type}
抓取目标: {crawl_goal}
平台: {platform}
风险等级: {risk_flag}
优先级: {priority}
置信度: {confidence}
已有变体: {existing_variants}

请只补充 1-2 个适合该平台抓取的新增搜索词，严格按以下JSON格式返回：
{{"expanded_keywords": ["搜索词1", "搜索词2"]}}"""


def _load_skill_system_prompt(skill_path: str) -> str:
    """Load the System Prompt section from the skill markdown file."""
    path = Path(skill_path)
    if not path.exists():
        logger.warning("[KeywordExpanderAgent] Skill file not found: %s, using fallback prompt", skill_path)
        return _fallback_system_prompt()

    content = path.read_text(encoding="utf-8")
    marker = "### System Prompt"
    idx = content.find(marker)
    if idx == -1:
        logger.warning("[KeywordExpanderAgent] '### System Prompt' not found in %s, using fallback", skill_path)
        return _fallback_system_prompt()

    after_marker = content[idx + len(marker):]
    code_start = after_marker.find("```")
    if code_start == -1:
        next_section = after_marker.find("\n## ")
        prompt_text = after_marker.strip() if next_section == -1 else after_marker[:next_section].strip()
    else:
        after_code_start = after_marker[code_start + 3:]
        newline_after_code = after_code_start.find("\n")
        if newline_after_code != -1:
            after_code_start = after_code_start[newline_after_code + 1:]
        code_end = after_code_start.find("```")
        prompt_text = after_code_start.strip() if code_end == -1 else after_code_start[:code_end].strip()

    if not prompt_text:
        logger.warning("[KeywordExpanderAgent] Empty system prompt extracted from %s, using fallback", skill_path)
        return _fallback_system_prompt()

    logger.info("[KeywordExpanderAgent] Loaded system prompt from %s (%s chars)", skill_path, len(prompt_text))
    return prompt_text


def _fallback_system_prompt() -> str:
    return (
        "你是一个专门为美妆护肤领域社交媒体爬虫服务的关键词扩充专家。"
        "根据用户提供的原始趋势关键词及其元数据，只补充少量更适合平台抓取的搜索词变体。"
        "所有搜索词必须明确指向护肤品、化妆品、个人护理相关内容。"
        "返回JSON格式：{\"expanded_keywords\": [\"词1\", \"词2\"]}"
    )


class KeywordExpanderAgent(BaseAgent):
    """Build a platform-aware execution plan for trend keyword crawling."""

    def __init__(self) -> None:
        self._client = (
            AsyncOpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
            )
            if settings.LLM_API_KEY
            else None
        )
        self._system_prompt = _load_skill_system_prompt(settings.KEYWORD_SKILL_PATH)

    @property
    def name(self) -> str:
        return "KeywordExpanderAgent"

    async def execute(self, context: AgentContext) -> AgentResult:
        keyword = context.keyword
        if not keyword:
            return AgentResult(success=False, error="Missing keyword in context")

        keyword_meta: dict[str, Any] = {
            "keyword_id": context.extra.get("keyword_id", ""),
            "keyword": keyword,
            "normalized_keyword": context.extra.get("normalized_keyword", keyword),
            "topic_cluster": context.extra.get("topic_cluster", ""),
            "trend_type": context.extra.get("trend_type", "ingredient"),
            "query_variants": context.extra.get("query_variants", ""),
            "suggested_platforms": context.extra.get("suggested_platforms", "xiaohongshu"),
            "crawl_goal": context.extra.get("crawl_goal", "trend_discovery"),
            "risk_flag": context.extra.get("risk_flag", "low"),
            "priority": context.extra.get("priority", "medium"),
            "confidence": context.extra.get("confidence", "medium"),
            "signal_period_type": context.extra.get("signal_period_type", ""),
            "signal_period_label": context.extra.get("signal_period_label", ""),
            "report_id": context.extra.get("report_id", ""),
            "notes": context.extra.get("notes", ""),
        }
        platform_scope_override = context.extra.get("platform_scope_override")

        try:
            baseline_plan = build_keyword_execution_plan(
                keyword_meta,
                platform_scope_override=platform_scope_override,
            )
            llm_supplements: dict[str, list[str]] = {}

            if context.extra.get("enable_llm", True):
                for platform in baseline_plan["crawl_targets"]:
                    llm_supplements[platform] = await self._expand_keyword(keyword_meta, platform)

            plan = build_keyword_execution_plan(
                keyword_meta,
                llm_supplements=llm_supplements,
                platform_scope_override=platform_scope_override,
            )
            plan["registry_rows"] = self._build_registry_rows(keyword_meta, plan)

            logger.info(
                "[%s] Built execution plan for '%s': %s crawl targets, %s reference sources, %s task candidates",
                self.name,
                keyword,
                len(plan.get("crawl_targets", [])),
                len(plan.get("reference_sources", [])),
                len(plan.get("task_candidates", [])),
            )
            return AgentResult(success=True, data=plan)
        except Exception as e:
            logger.error("[%s] Keyword planning failed for '%s': %s", self.name, keyword, e)
            fallback = build_keyword_execution_plan(
                keyword_meta,
                platform_scope_override=platform_scope_override,
            )
            fallback["registry_rows"] = self._build_registry_rows(keyword_meta, fallback)
            return AgentResult(success=True, data=fallback)

    @staticmethod
    def _build_registry_rows(keyword_meta: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
        """Build first-party expansion registry rows from planned candidates.

        Policy:
        - seed/seed_variant/rule-based rows => approved
        - llm_supplement => candidate (needs approval first)
        """
        rows: list[dict[str, Any]] = []
        tier = infer_watchlist_tier(
            str(keyword_meta.get("priority", "medium")),
            str(keyword_meta.get("crawl_goal", "trend_discovery")),
        )
        ttl_days = 14 if tier == "watchlist-hot" else 30 if tier == "watchlist-normal" else 60
        for candidate in plan.get("task_candidates", []):
            expansion_type = candidate.get("expansion_type", "seed")
            is_candidate = expansion_type == "llm_supplement"
            status = "candidate" if is_candidate else "approved"
            review_status = "pending" if is_candidate else "approved"
            source_type = "llm" if is_candidate else "manual"
            platform_label = candidate.get("platform", "")
            rows.append(
                {
                    "platform": platform_label,
                    "platform_code": PLATFORM_LABEL_TO_CODE.get(platform_label, platform_label),
                    "expanded_query": candidate.get("expanded_query", ""),
                    "expansion_type": expansion_type,
                    "based_on": candidate.get("based_on", ""),
                    "source_type": source_type,
                    "review_status": review_status,
                    "status": status,
                    "ttl_days": ttl_days,
                    "notes": "auto-ingested from keyword planner",
                }
            )
        return rows

    async def _expand_keyword(
        self,
        keyword_meta: dict[str, Any],
        platform: str,
    ) -> list[str]:
        if self._client is None:
            return []

        existing_variants = parse_query_variants(keyword_meta.get("query_variants"))
        user_prompt = KEYWORD_EXPANSION_USER_TEMPLATE.format(
            original_keyword=keyword_meta.get("keyword", ""),
            normalized_keyword=keyword_meta.get("normalized_keyword", keyword_meta.get("keyword", "")),
            topic_cluster=keyword_meta.get("topic_cluster", "") or "unknown",
            trend_type=keyword_meta.get("trend_type", "ingredient"),
            crawl_goal=keyword_meta.get("crawl_goal", "trend_discovery"),
            platform=platform,
            risk_flag=keyword_meta.get("risk_flag", "low"),
            priority=keyword_meta.get("priority", "medium"),
            confidence=keyword_meta.get("confidence", "medium"),
            existing_variants=str(existing_variants) if existing_variants else "[]",
        )

        response = await self._client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=400,
            extra_body={"thinking": {"type": "disabled"}},
        )

        content = response.choices[0].message.content or "{}"
        content = content.strip()
        if content.startswith("```"):
            first_newline = content.index("\n") + 1
            content = content[first_newline:]
            if content.rstrip().endswith("```"):
                content = content.rstrip()[:-3].rstrip()

        result = json.loads(content)
        expanded = result.get("expanded_keywords", [])
        if not isinstance(expanded, list):
            logger.warning("[%s] LLM returned non-list expanded_keywords: %s", self.name, type(expanded))
            return []
        return [str(kw).strip() for kw in expanded if str(kw).strip()]
