#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_ENV="$REPO_ROOT/BeautyQA-TrendAgent/backend/.env"
MEDIACRAWLER_DIR="$REPO_ROOT/BeautyQA-vendor/MediaCrawler"
PYTHON_BIN="$REPO_ROOT/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "error: shared python not found at $PYTHON_BIN" >&2
  echo "hint: create the shared environment first, then run:" >&2
  echo "  ./.venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

if [[ ! -d "$MEDIACRAWLER_DIR" ]]; then
  echo "error: MediaCrawler directory not found at $MEDIACRAWLER_DIR" >&2
  exit 1
fi

if [[ -f "$BACKEND_ENV" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$BACKEND_ENV"
  set +a
fi

export POSTGRES_DB_HOST="${POSTGRES_DB_HOST:-localhost}"
export POSTGRES_DB_PORT="${POSTGRES_DB_PORT:-5433}"
export POSTGRES_DB_USER="${POSTGRES_DB_USER:-postgres}"
export POSTGRES_DB_PWD="${POSTGRES_DB_PWD:-123456}"
export POSTGRES_DB_NAME="${POSTGRES_DB_NAME:-media_crawler}"

export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/beautyqa-mpl-cache}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/beautyqa-xdg-cache}"
mkdir -p "$MPLCONFIGDIR" "$XDG_CACHE_HOME"

cd "$MEDIACRAWLER_DIR"
exec "$PYTHON_BIN" main.py "$@"
