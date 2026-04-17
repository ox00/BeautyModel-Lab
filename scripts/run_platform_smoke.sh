#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER="$REPO_ROOT/scripts/run_mediacrawler.sh"

DEFAULT_LOGIN_TYPE="${SMOKE_LOGIN_TYPE:-cookie}"
DEFAULT_HEADLESS="${SMOKE_HEADLESS:-false}"
GET_COMMENT="${SMOKE_GET_COMMENT:-false}"
GET_SUB_COMMENT="${SMOKE_GET_SUB_COMMENT:-false}"
MAX_COMMENTS="${SMOKE_MAX_COMMENTS:-2}"
MAX_CONCURRENCY="${SMOKE_MAX_CONCURRENCY:-1}"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/run_platform_smoke.sh xhs
  ./scripts/run_platform_smoke.sh xhs dy bili
  ./scripts/run_platform_smoke.sh --fresh-login xhs

Purpose:
  Run the standard MediaCrawler smoke flow with project defaults.
  You only need to pass platform codes such as: xhs dy bili

Supported platform codes:
  xhs   小红书
  dy    抖音
  bili  B站

Optional flags:
  --fresh-login   use qrcode login instead of cookie reuse
  --headless      run browser in headless mode
  --help          show this message

Optional env overrides:
  XHS_KEYWORD
  DY_KEYWORD
  BILI_KEYWORD
  SMOKE_LOGIN_TYPE
  SMOKE_HEADLESS
  SMOKE_GET_COMMENT
  SMOKE_GET_SUB_COMMENT
  SMOKE_MAX_COMMENTS
  SMOKE_MAX_CONCURRENCY
EOF
}

if [[ ! -x "$RUNNER" ]]; then
  echo "error: runner not found at $RUNNER" >&2
  exit 1
fi

if [[ $# -eq 0 ]]; then
  usage
  exit 1
fi

LOGIN_TYPE="$DEFAULT_LOGIN_TYPE"
HEADLESS="$DEFAULT_HEADLESS"
platforms=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --fresh-login)
      LOGIN_TYPE="qrcode"
      shift
      ;;
    --headless)
      HEADLESS="true"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    xhs|dy|bili)
      platforms+=("$1")
      shift
      ;;
    *)
      echo "error: unsupported argument '$1'" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ${#platforms[@]} -eq 0 ]]; then
  echo "error: at least one platform code is required" >&2
  usage
  exit 1
fi

platform_keyword() {
  case "$1" in
    xhs) echo "${XHS_KEYWORD:-以油养肤}" ;;
    dy) echo "${DY_KEYWORD:-油敷法}" ;;
    bili) echo "${BILI_KEYWORD:-以油养肤}" ;;
    *) return 1 ;;
  esac
}

platform_label() {
  case "$1" in
    xhs) echo "小红书" ;;
    dy) echo "抖音" ;;
    bili) echo "B站" ;;
    *) echo "$1" ;;
  esac
}

failures=0

for platform in "${platforms[@]}"; do
  keyword="$(platform_keyword "$platform")"
  label="$(platform_label "$platform")"

  echo
  echo "=== Smoke: $label ($platform) ==="
  echo "keyword: $keyword"
  echo "login_type: $LOGIN_TYPE"
  echo "headless: $HEADLESS"

  if ! bash "$RUNNER" \
    --platform "$platform" \
    --lt "$LOGIN_TYPE" \
    --type search \
    --keywords "$keyword" \
    --save_data_option postgres \
    --headless "$HEADLESS" \
    --get_comment "$GET_COMMENT" \
    --get_sub_comment "$GET_SUB_COMMENT" \
    --max_comments_count_singlenotes "$MAX_COMMENTS" \
    --max_concurrency_num "$MAX_CONCURRENCY"; then
    failures=$((failures + 1))
    echo "failed: $platform" >&2
  fi

  if [[ "$LOGIN_TYPE" == "qrcode" ]]; then
    LOGIN_TYPE="cookie"
  fi
done

if [[ $failures -gt 0 ]]; then
  echo
  echo "smoke finished with $failures failed platform(s)" >&2
  exit 1
fi

echo
echo "smoke finished successfully for ${#platforms[@]} platform(s)"
