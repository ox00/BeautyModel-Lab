from __future__ import annotations

from collections.abc import Iterable
from typing import Any


PLATFORM_LABEL_TO_CODE = {
    "xiaohongshu": "xhs",
    "xhs": "xhs",
    "douyin": "dy",
    "dy": "dy",
    "bilibili": "bili",
    "bili": "bili",
    "weibo": "wb",
    "wb": "wb",
    "kuaishou": "ks",
    "ks": "ks",
    "tieba": "tieba",
    "zhihu": "zhihu",
}

PLATFORM_CODE_TO_LABEL = {
    "xhs": "xiaohongshu",
    "dy": "douyin",
    "bili": "bilibili",
    "wb": "weibo",
    "ks": "kuaishou",
    "tieba": "tieba",
    "zhihu": "zhihu",
}

REFERENCE_SOURCES = {"taobao", "industry_news"}

GOAL_SUFFIXES: dict[str, dict[str, list[tuple[str, str]]]] = {
    "trend_discovery": {
        "xiaohongshu": [("domain_constraint", "护肤"), ("scenario_binding", "趋势")],
        "douyin": [("platform_style", "趋势"), ("domain_constraint", "成分")],
    },
    "market_validation": {
        "xiaohongshu": [("platform_style", "测评"), ("category_binding", "推荐")],
        "douyin": [("platform_style", "推荐"), ("category_binding", "热度")],
    },
    "risk_monitoring": {
        "xiaohongshu": [("risk_probe", "风险"), ("risk_probe", "避雷"), ("risk_probe", "副作用")],
        "douyin": [("risk_probe", "风险"), ("risk_probe", "翻车"), ("risk_probe", "避雷")],
    },
}

TREND_TYPE_SUFFIXES: dict[str, dict[str, list[tuple[str, str]]]] = {
    "ingredient": {
        "xiaohongshu": [("domain_constraint", "护肤"), ("category_binding", "成分")],
        "douyin": [("domain_constraint", "成分"), ("category_binding", "原料")],
    },
    "claim": {
        "xiaohongshu": [("domain_constraint", "功效"), ("platform_style", "护肤")],
        "douyin": [("platform_style", "功效"), ("platform_style", "推荐")],
    },
    "category": {
        "xiaohongshu": [("platform_style", "测评"), ("category_binding", "推荐")],
        "douyin": [("platform_style", "推荐"), ("platform_style", "热度")],
    },
    "scenario": {
        "xiaohongshu": [("scenario_binding", "护肤"), ("scenario_binding", "场景")],
        "douyin": [("platform_style", "热门"), ("scenario_binding", "分享")],
    },
    "risk_compliance": {
        "xiaohongshu": [("risk_probe", "风险"), ("risk_probe", "避雷")],
        "douyin": [("risk_probe", "风险"), ("risk_probe", "翻车")],
    },
}

REFERENCE_SUFFIXES: dict[str, dict[str, list[str]]] = {
    "industry_news": {
        "trend_discovery": ["行业趋势", "原料创新"],
        "market_validation": ["市场洞察", "行业分析"],
        "risk_monitoring": ["法规", "争议"],
    },
    "taobao": {
        "trend_discovery": ["精华", "护肤品"],
        "market_validation": ["产品", "类目"],
        "risk_monitoring": ["护肤品", "功效"],
    },
}


def normalize_platform_label(platform: str) -> str:
    token = (platform or "").strip().lower()
    if token in PLATFORM_CODE_TO_LABEL:
        return PLATFORM_CODE_TO_LABEL[token]
    if token in PLATFORM_LABEL_TO_CODE:
        return token
    return token


def platform_to_code(platform: str) -> str:
    token = normalize_platform_label(platform)
    return PLATFORM_LABEL_TO_CODE.get(token, token)


def parse_platform_tokens(platforms: str | Iterable[str] | None) -> list[str]:
    if platforms is None:
        return []
    if isinstance(platforms, str):
        raw_tokens = platforms.split("|")
    else:
        raw_tokens = list(platforms)

    seen: set[str] = set()
    normalized: list[str] = []
    for token in raw_tokens:
        value = normalize_platform_label(str(token).strip())
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def parse_query_variants(variants: str | Iterable[str] | None) -> list[str]:
    if variants is None:
        return []
    if isinstance(variants, str):
        raw_values = variants.split("|")
    else:
        raw_values = list(variants)

    seen: set[str] = set()
    parsed: list[str] = []
    for value in raw_values:
        token = str(value).strip()
        lowered = token.lower()
        if not token or lowered in seen:
            continue
        seen.add(lowered)
        parsed.append(token)
    return parsed


def split_execution_sources(platforms: str | Iterable[str] | None) -> dict[str, list[str]]:
    crawl_targets: list[str] = []
    reference_sources: list[str] = []
    unsupported_sources: list[str] = []

    for token in parse_platform_tokens(platforms):
        if token in REFERENCE_SOURCES:
            reference_sources.append(token)
        elif token in PLATFORM_LABEL_TO_CODE:
            crawl_targets.append(token)
        else:
            unsupported_sources.append(token)

    return {
        "crawl_targets": crawl_targets,
        "reference_sources": reference_sources,
        "unsupported_sources": unsupported_sources,
    }


def normalize_due_platform(platform: str | None) -> str | None:
    if not platform:
        return None
    normalized = normalize_platform_label(platform)
    if normalized in PLATFORM_LABEL_TO_CODE:
        return normalized
    return platform


def _unique_strings(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        token = str(value).strip()
        lowered = token.lower()
        if not token or lowered in seen:
            continue
        seen.add(lowered)
        result.append(token)
    return result


def _review_needed(keyword_meta: dict[str, Any]) -> bool:
    risk_flag = str(keyword_meta.get("risk_flag", "low"))
    confidence = str(keyword_meta.get("confidence", "medium"))
    return risk_flag == "high" or confidence != "high"


def _per_platform_limit(keyword_meta: dict[str, Any]) -> int:
    priority = str(keyword_meta.get("priority", "medium"))
    confidence = str(keyword_meta.get("confidence", "medium"))
    if priority == "low" or confidence == "low":
        return 1
    if priority == "medium" or confidence == "medium":
        return 2
    return 3


def _seed_queries(keyword_meta: dict[str, Any]) -> list[tuple[str, str, str]]:
    keyword = str(keyword_meta.get("keyword", "")).strip()
    normalized_keyword = str(keyword_meta.get("normalized_keyword", "")).strip()

    items: list[tuple[str, str, str]] = []
    if keyword:
        items.append((keyword, "seed", keyword))
    if normalized_keyword and normalized_keyword.lower() != keyword.lower():
        items.append((normalized_keyword, "seed_variant", normalized_keyword))
    return items


def _variant_queries(keyword_meta: dict[str, Any]) -> list[tuple[str, str, str]]:
    keyword = str(keyword_meta.get("keyword", "")).strip()
    normalized_keyword = str(keyword_meta.get("normalized_keyword", "")).strip()
    variants = parse_query_variants(keyword_meta.get("query_variants"))

    items: list[tuple[str, str, str]] = []
    for variant in variants:
        if variant.lower() in {keyword.lower(), normalized_keyword.lower()}:
            continue
        items.append((variant, "seed_variant", variant))
    return items


def _rule_suffix_candidates(keyword_meta: dict[str, Any], platform: str) -> list[tuple[str, str]]:
    goal = str(keyword_meta.get("crawl_goal", "trend_discovery"))
    trend_type = str(keyword_meta.get("trend_type", "ingredient"))
    risk_flag = str(keyword_meta.get("risk_flag", "low"))

    candidates: list[tuple[str, str]] = []
    candidates.extend(GOAL_SUFFIXES.get(goal, {}).get(platform, []))
    candidates.extend(TREND_TYPE_SUFFIXES.get(trend_type, {}).get(platform, []))
    if risk_flag == "high" and goal != "risk_monitoring":
        candidates.append(("risk_probe", "风险"))

    dedup: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in candidates:
        if item in seen:
            continue
        seen.add(item)
        dedup.append(item)
    return dedup


def _reference_queries(keyword_meta: dict[str, Any], source: str) -> list[str]:
    keyword = str(keyword_meta.get("keyword", "")).strip()
    goal = str(keyword_meta.get("crawl_goal", "trend_discovery"))
    variants = parse_query_variants(keyword_meta.get("query_variants"))
    suffixes = REFERENCE_SUFFIXES.get(source, {}).get(goal, [])

    candidates = [keyword]
    if variants:
        candidates.append(variants[0])
    for suffix in suffixes:
        if keyword:
            candidates.append(f"{keyword} {suffix}")
    return _unique_strings(candidates)[:3]


def build_keyword_execution_plan(
    keyword_meta: dict[str, Any],
    *,
    llm_supplements: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    source_split = split_execution_sources(keyword_meta.get("suggested_platforms"))
    crawl_targets = source_split["crawl_targets"]
    reference_sources = source_split["reference_sources"]
    unsupported_sources = source_split["unsupported_sources"]
    seed_queries = _seed_queries(keyword_meta)
    variant_queries = _variant_queries(keyword_meta)
    review_needed = _review_needed(keyword_meta)
    per_platform_limit = _per_platform_limit(keyword_meta)

    platform_packages: list[dict[str, Any]] = []
    task_candidates: list[dict[str, Any]] = []

    for platform in crawl_targets:
        platform_code = platform_to_code(platform)
        query_rows: list[dict[str, Any]] = []
        query_values: set[str] = set()

        for query, expansion_type, based_on in seed_queries:
            lowered = query.lower()
            if lowered in query_values:
                continue
            query_values.add(lowered)
            query_rows.append(
                {
                    "expanded_query": query,
                    "platform": platform,
                    "platform_code": platform_code,
                    "expansion_type": expansion_type,
                    "based_on": based_on,
                    "crawl_goal": keyword_meta.get("crawl_goal", "trend_discovery"),
                    "confidence": keyword_meta.get("confidence", "medium"),
                    "review_needed": review_needed,
                    "dedup_key": f"{keyword_meta.get('keyword_id', 'KW_UNKNOWN')}__{platform}__{query}",
                }
            )
            if len(query_rows) >= per_platform_limit:
                break

        if len(query_rows) < per_platform_limit:
            base_keyword = str(keyword_meta.get("keyword", "")).strip()
            for expansion_type, suffix in _rule_suffix_candidates(keyword_meta, platform):
                if not base_keyword:
                    continue
                candidate = f"{base_keyword} {suffix}".strip()
                lowered = candidate.lower()
                if lowered in query_values:
                    continue
                query_values.add(lowered)
                query_rows.append(
                    {
                        "expanded_query": candidate,
                        "platform": platform,
                        "platform_code": platform_code,
                        "expansion_type": expansion_type,
                        "based_on": base_keyword,
                        "crawl_goal": keyword_meta.get("crawl_goal", "trend_discovery"),
                        "confidence": keyword_meta.get("confidence", "medium"),
                        "review_needed": review_needed,
                        "dedup_key": f"{keyword_meta.get('keyword_id', 'KW_UNKNOWN')}__{platform}__{candidate}",
                    }
                )
                if len(query_rows) >= per_platform_limit:
                    break

        for query, expansion_type, based_on in variant_queries:
            lowered = query.lower()
            if lowered in query_values or len(query_rows) >= per_platform_limit:
                continue
            query_values.add(lowered)
            query_rows.append(
                {
                    "expanded_query": query,
                    "platform": platform,
                    "platform_code": platform_code,
                    "expansion_type": expansion_type,
                    "based_on": based_on,
                    "crawl_goal": keyword_meta.get("crawl_goal", "trend_discovery"),
                    "confidence": keyword_meta.get("confidence", "medium"),
                    "review_needed": review_needed,
                    "dedup_key": f"{keyword_meta.get('keyword_id', 'KW_UNKNOWN')}__{platform}__{query}",
                }
            )

        for llm_query in (llm_supplements or {}).get(platform, []):
            candidate = str(llm_query).strip()
            lowered = candidate.lower()
            if not candidate or lowered in query_values or len(query_rows) >= per_platform_limit:
                continue
            query_values.add(lowered)
            query_rows.append(
                {
                    "expanded_query": candidate,
                    "platform": platform,
                    "platform_code": platform_code,
                    "expansion_type": "llm_supplement",
                    "based_on": keyword_meta.get("keyword", ""),
                    "crawl_goal": keyword_meta.get("crawl_goal", "trend_discovery"),
                    "confidence": keyword_meta.get("confidence", "medium"),
                    "review_needed": review_needed,
                    "dedup_key": f"{keyword_meta.get('keyword_id', 'KW_UNKNOWN')}__{platform}__{candidate}",
                }
            )

        platform_packages.append(
            {
                "platform": platform,
                "platform_code": platform_code,
                "review_needed": review_needed,
                "query_count": len(query_rows),
                "queries": query_rows,
            }
        )
        task_candidates.extend(query_rows)

    reference_packages = [
        {
            "source": source,
            "execution_mode": "reference_only",
            "queries": _reference_queries(keyword_meta, source),
        }
        for source in reference_sources
    ]

    flattened_queries = [row["expanded_query"] for row in task_candidates]

    return {
        "keyword_id": keyword_meta.get("keyword_id", ""),
        "keyword": keyword_meta.get("keyword", ""),
        "normalized_keyword": keyword_meta.get("normalized_keyword", ""),
        "crawl_goal": keyword_meta.get("crawl_goal", "trend_discovery"),
        "risk_flag": keyword_meta.get("risk_flag", "low"),
        "priority": keyword_meta.get("priority", "medium"),
        "confidence": keyword_meta.get("confidence", "medium"),
        "review_needed": review_needed,
        "crawl_targets": crawl_targets,
        "reference_sources": reference_sources,
        "unsupported_sources": unsupported_sources,
        "platform_packages": platform_packages,
        "reference_packages": reference_packages,
        "task_candidates": task_candidates,
        "expanded_keywords": _unique_strings(flattened_queries),
        "merged_keywords": _unique_strings(flattened_queries),
        "keywords_for_crawler": ",".join(flattened_queries[:per_platform_limit]),
    }
