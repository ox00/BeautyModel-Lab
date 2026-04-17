from __future__ import annotations

import importlib
import json
import os
import socket
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = REPO_ROOT / "BeautyQA-vendor" / "MediaCrawler"
BACKEND_ENV = REPO_ROOT / "BeautyQA-TrendAgent" / "backend" / ".env"


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _env_value(name: str, env_file_values: dict[str, str]) -> str:
    return os.getenv(name) or env_file_values.get(name, "")


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def _module_status(name: str) -> str:
    try:
        importlib.import_module(name)
        return "ok"
    except Exception as exc:
        return f"missing: {exc}"


def main() -> None:
    env_file_values = _load_env_file(BACKEND_ENV)
    llm_api_key = _env_value("LLM_API_KEY", env_file_values) or _env_value("OPENAI_API_KEY", env_file_values)
    llm_base_url = _env_value("LLM_BASE_URL", env_file_values)
    llm_model = _env_value("LLM_MODEL", env_file_values)
    browser_dirs = sorted(
        str(path.relative_to(REPO_ROOT))
        for path in VENDOR_ROOT.glob("**/*")
        if path.is_dir() and path.name in {"browser_data", "user_data"}
    )

    report = {
        "task_id": "runtime-smoke-readiness",
        "check_date": date.today().isoformat(),
        "python_dependencies": {
            name: _module_status(name)
            for name in ["asyncpg", "redis", "aiosqlite", "sqlalchemy", "openai", "multipart"]
        },
        "local_infra": {
            "postgres_5433_open": _port_open("127.0.0.1", 5433),
            "redis_6379_open": _port_open("127.0.0.1", 6379),
        },
        "config": {
            "backend_env_exists": BACKEND_ENV.exists(),
            "llm_api_key_present": bool(llm_api_key),
            "llm_base_url_present": bool(llm_base_url),
            "llm_model_present": bool(llm_model),
        },
        "vendor_runtime": {
            "vendor_root_exists": VENDOR_ROOT.exists(),
            "vendor_main_exists": (VENDOR_ROOT / "main.py").exists(),
            "browser_state_dirs": browser_dirs,
        },
    }
    report["summary"] = {
        "dependencies_ready": all(value == "ok" for value in report["python_dependencies"].values()),
        "infra_ready": all(report["local_infra"].values()),
        "llm_ready": report["config"]["llm_api_key_present"],
        "vendor_runtime_ready": report["vendor_runtime"]["vendor_root_exists"] and report["vendor_runtime"]["vendor_main_exists"],
        "browser_state_ready": bool(report["vendor_runtime"]["browser_state_dirs"]),
    }
    report["summary"]["runtime_smoke_ready"] = all(report["summary"].values())

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
