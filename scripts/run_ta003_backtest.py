from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TRENDAGENT_BACKEND = REPO_ROOT / "BeautyQA-TrendAgent" / "backend"
if str(TRENDAGENT_BACKEND) not in sys.path:
    sys.path.insert(0, str(TRENDAGENT_BACKEND))

from app.domain.services.keyword_expansion_service import build_keyword_execution_plan, parse_query_variants  # noqa: E402


SEED_CSV = REPO_ROOT / "data" / "eval" / "trend_monitor" / "2026-04-13-trend-keyword-seed.csv"


def _load_rows() -> dict[str, dict[str, str]]:
    with SEED_CSV.open("r", encoding="utf-8") as f:
        return {row["keyword_id"]: row for row in csv.DictReader(f)}


def _legacy_flat_plan(row: dict[str, str]) -> dict[str, object]:
    keyword = row["keyword"]
    variants = parse_query_variants(row.get("query_variants"))
    merged = [keyword]
    for variant in variants:
        if variant not in merged:
            merged.append(variant)
        if len(merged) >= 3:
            break
    return {
        "keywords_for_crawler": ",".join(merged),
        "same_query_for_all_targets": True,
        "suggested_platforms_raw": row.get("suggested_platforms", ""),
    }


def _render_case(row: dict[str, str]) -> dict[str, object]:
    plan = build_keyword_execution_plan(row)
    scheduled_platforms = sorted({item["platform"] for item in plan["task_candidates"]})
    scheduled_queries = [item["expanded_query"] for item in plan["task_candidates"]]

    return {
        "keyword_id": row["keyword_id"],
        "keyword": row["keyword"],
        "crawl_goal": row["crawl_goal"],
        "risk_flag": row["risk_flag"],
        "legacy_before": _legacy_flat_plan(row),
        "ta003_after": {
            "crawl_targets": plan["crawl_targets"],
            "reference_sources": plan["reference_sources"],
            "reference_packages": plan["reference_packages"],
            "platform_packages": plan["platform_packages"],
            "scheduled_platforms": scheduled_platforms,
            "scheduled_query_count": len(plan["task_candidates"]),
            "scheduled_queries": scheduled_queries,
        },
        "checks": {
            "reference_not_scheduled": not any(
                source in scheduled_platforms for source in plan["reference_sources"]
            ),
            "all_scheduled_platforms_are_crawl_targets": all(
                platform in plan["crawl_targets"] for platform in scheduled_platforms
            ),
            "has_platform_specific_packages": bool(plan["platform_packages"]),
        },
    }


def main() -> None:
    rows = _load_rows()
    selected_ids = ["KW_0002", "KW_0031", "KW_0040"]
    cases = [_render_case(rows[keyword_id]) for keyword_id in selected_ids]

    print(
        json.dumps(
            {
                "task_id": "TA-003",
                "backtest_date": "2026-04-16",
                "seed_file": str(SEED_CSV.relative_to(REPO_ROOT)),
                "summary": {
                    "selected_case_count": len(cases),
                    "reference_not_scheduled": all(
                        case["checks"]["reference_not_scheduled"] for case in cases
                    ),
                    "platform_filtering_valid": all(
                        case["checks"]["all_scheduled_platforms_are_crawl_targets"] for case in cases
                    ),
                    "platform_specific_packages_present": all(
                        case["checks"]["has_platform_specific_packages"] for case in cases
                    ),
                },
                "cases": cases,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
