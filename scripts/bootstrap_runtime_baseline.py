#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "BeautyQA-TrendAgent" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.agents.base import AgentContext  # noqa: E402
from app.agents.keyword_expander_agent import KeywordExpanderAgent  # noqa: E402
from app.domain.services.keyword_expansion_service import (  # noqa: E402
    DEFAULT_RUNTIME_CRAWL_TARGETS,
    PLATFORM_LABEL_TO_CODE,
    PLATFORM_CODE_TO_LABEL,
    parse_platform_tokens,
)
from app.domain.services.keyword_service import KeywordService  # noqa: E402
from app.domain.services.runtime_query_state_service import RuntimeQueryStateService  # noqa: E402
from app.infrastructure.database.connection import async_session_factory, init_db  # noqa: E402
from app.infrastructure.repositories.keyword_repo_impl import KeywordRepositoryImpl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap first-party expansion registry and query schedule state for a cross-platform runtime baseline."
    )
    parser.add_argument(
        "--keyword-id",
        nargs="+",
        type=int,
        required=True,
        help="Keyword DB ids to seed into the runtime baseline.",
    )
    parser.add_argument(
        "--platform",
        nargs="+",
        default=["xhs", "dy", "bili"],
        help="Crawler platforms to seed, default: xhs dy bili",
    )
    parser.add_argument(
        "--enable-llm",
        action="store_true",
        help="Allow LLM supplements when building the execution plan.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview registry/query-state changes without committing.",
    )
    return parser.parse_args()


def resolve_platform_labels(platform_args: list[str]) -> list[str]:
    requested = parse_platform_tokens(platform_args)
    if not requested:
        requested = DEFAULT_RUNTIME_CRAWL_TARGETS
    return [PLATFORM_CODE_TO_LABEL.get(platform, platform) for platform in requested]


async def _main(args: argparse.Namespace) -> dict:
    await init_db()
    platform_labels = resolve_platform_labels(args.platform)
    platform_codes = [PLATFORM_LABEL_TO_CODE[label] for label in platform_labels]
    report: dict = {
        "task": "bootstrap_runtime_baseline",
        "keyword_ids": args.keyword_id,
        "platform_labels": platform_labels,
        "dry_run": args.dry_run,
        "results": [],
    }

    async with async_session_factory() as session:
        keyword_service = KeywordService(KeywordRepositoryImpl(session))
        query_state_service = RuntimeQueryStateService(session)
        agent = KeywordExpanderAgent()

        for keyword_id in args.keyword_id:
            keyword = await keyword_service.get_keyword(keyword_id)
            if not keyword:
                report["results"].append(
                    {
                        "keyword_id": keyword_id,
                        "status": "missing_keyword",
                    }
                )
                continue

            keyword_meta = keyword.model_dump()
            expander_context = {
                **keyword_meta,
                "platform_scope_override": platform_labels,
                "enable_llm": args.enable_llm,
            }
            plan_result = await agent.execute(AgentContext(keyword=keyword_meta["keyword"], extra=expander_context))
            if not plan_result.success:
                report["results"].append(
                    {
                        "keyword_id": keyword_id,
                        "keyword": keyword_meta["keyword"],
                        "status": "plan_failed",
                        "error": plan_result.error,
                    }
                )
                continue

            plan = plan_result.data
            registry_rows = plan.get("registry_rows", [])
            saved_rows = await query_state_service.upsert_expansion_registry(
                keyword_meta=keyword_meta,
                expansion_rows=registry_rows,
            )
            approved_rows = await query_state_service.list_active_registry_rows(
                keyword_db_id=keyword_id,
                platform_codes=platform_codes,
            )
            filtered_approved_rows = [
                row
                for row in approved_rows
                if row.platform in platform_labels and row.status == "approved" and row.is_active
            ]
            states = await query_state_service.ensure_query_state_for_expansions(
                keyword_meta=keyword_meta,
                approved_rows=filtered_approved_rows,
                platform_label_to_code=PLATFORM_LABEL_TO_CODE,
            )

            report["results"].append(
                {
                    "keyword_id": keyword_id,
                    "keyword": keyword_meta["keyword"],
                    "status": "ok",
                    "crawl_targets": plan.get("crawl_targets", []),
                    "reference_sources": plan.get("reference_sources", []),
                    "approved_registry_count": len(filtered_approved_rows),
                    "query_state_count": len(states),
                    "sample_queries": [row.expanded_query for row in filtered_approved_rows[:6]],
                }
            )

        if args.dry_run:
            await session.rollback()
        else:
            await session.commit()

    return report


if __name__ == "__main__":
    print(json.dumps(asyncio.run(_main(parse_args())), ensure_ascii=False, indent=2))
