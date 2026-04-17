from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TRENDAGENT_BACKEND = REPO_ROOT / "BeautyQA-TrendAgent" / "backend"
if str(TRENDAGENT_BACKEND) not in sys.path:
    sys.path.insert(0, str(TRENDAGENT_BACKEND))

from app.config.settings import settings  # noqa: E402
from app.infrastructure.crawler.config_mapper import CrawlerConfigMapper  # noqa: E402


VENDOR_ROOT = REPO_ROOT / "BeautyQA-vendor" / "MediaCrawler"
VENDOR_FILES = {
    "main_entry": VENDOR_ROOT / "main.py",
    "cli_args": VENDOR_ROOT / "cmd_arg" / "arg.py",
    "db_config": VENDOR_ROOT / "config" / "db_config.py",
    "db_models": VENDOR_ROOT / "database" / "models.py",
}
REQUIRED_CLI_ARGS = [
    "--platform",
    "--lt",
    "--type",
    "--keywords",
    "--save_data_option",
    "--headless",
    "--get_comment",
    "--get_sub_comment",
    "--max_comments_count_singlenotes",
    "--max_concurrency_num",
    "--init_db",
]
REQUIRED_ENV_VARS = [
    "POSTGRES_DB_HOST",
    "POSTGRES_DB_PORT",
    "POSTGRES_DB_USER",
    "POSTGRES_DB_PWD",
    "POSTGRES_DB_NAME",
]
REQUIRED_RAW_TABLES = [
    "xhs_note",
    "douyin_aweme",
    "bilibili_video",
    "weibo_note",
]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _contains_all(text: str, tokens: list[str]) -> dict[str, bool]:
    return {token: token in text for token in tokens}


def main() -> None:
    cli_text = _read_text(VENDOR_FILES["cli_args"])
    db_config_text = _read_text(VENDOR_FILES["db_config"])
    db_models_text = _read_text(VENDOR_FILES["db_models"])
    cleaning_text = _read_text(
        TRENDAGENT_BACKEND / "app" / "agents" / "cleaning_agent.py"
    )

    command = CrawlerConfigMapper().build_command(
        platform="xhs",
        keyword="外泌体",
        login_type="cookie",
        headless=True,
        enable_comments=True,
        enable_sub_comments=False,
        start_page=1,
        save_data_option="postgres",
        keywords_for_crawler="外泌体 护肤",
    )

    cli_checks = _contains_all(cli_text, REQUIRED_CLI_ARGS)
    env_checks = _contains_all(db_config_text, REQUIRED_ENV_VARS)
    raw_table_checks = _contains_all(db_models_text, REQUIRED_RAW_TABLES)
    cleaning_checks = _contains_all(cleaning_text, REQUIRED_RAW_TABLES)

    report = {
        "task_id": "TrendAgent-vendor-contract-check",
        "check_date": "2026-04-16",
        "vendor_root": str(VENDOR_ROOT.relative_to(REPO_ROOT)),
        "path_contract": {
            "settings_mediacrawler_dir": settings.MEDIACRAWLER_DIR,
            "settings_path_exists": Path(settings.MEDIACRAWLER_DIR).exists(),
            "vendor_key_files_exist": {name: path.exists() for name, path in VENDOR_FILES.items()},
        },
        "cli_contract": {
            "required_args_present": cli_checks,
            "sample_command": command.command,
            "sample_cwd": command.cwd,
            "sample_cwd_matches_settings": command.cwd == settings.MEDIACRAWLER_DIR,
        },
        "env_contract": {
            "required_env_vars_present": env_checks,
        },
        "raw_schema_contract": {
            "vendor_models_have_required_tables": raw_table_checks,
            "cleaning_agent_references_same_tables": cleaning_checks,
        },
        "summary": {
            "path_contract_ok": Path(settings.MEDIACRAWLER_DIR).exists() and all(path.exists() for path in VENDOR_FILES.values()),
            "cli_contract_ok": all(cli_checks.values()) and command.cwd == settings.MEDIACRAWLER_DIR,
            "env_contract_ok": all(env_checks.values()),
            "raw_schema_contract_ok": all(raw_table_checks.values()) and all(cleaning_checks.values()),
        },
    }
    report["summary"]["all_contracts_ok"] = all(report["summary"].values())

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
