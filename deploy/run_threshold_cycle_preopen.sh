#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
SOURCE_DATE="${THRESHOLD_CYCLE_SOURCE_DATE:-}"
APPLY_MODE="${THRESHOLD_CYCLE_APPLY_MODE:-auto_bounded_live}"
AUTO_APPLY="${THRESHOLD_CYCLE_AUTO_APPLY:-true}"
REQUIRE_AI="${THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI:-true}"

mkdir -p "$PROJECT_DIR/logs"
LOCK_FILE="$PROJECT_DIR/logs/threshold_cycle_preopen.lock"
exec 9>"$LOCK_FILE"
if command -v flock >/dev/null 2>&1; then
  if ! flock -n 9; then
    echo "[SKIP] threshold-cycle preopen already running target_date=$TARGET_DATE lock_file=$LOCK_FILE"
    exit 0
  fi
fi
cd "$PROJECT_DIR"

echo "[START] threshold-cycle preopen target_date=$TARGET_DATE apply_mode=$APPLY_MODE auto_apply=$AUTO_APPLY require_ai=$REQUIRE_AI"

args=(--date "$TARGET_DATE" --apply-mode "$APPLY_MODE")
if [ -n "$SOURCE_DATE" ]; then
  args+=(--source-date "$SOURCE_DATE")
fi
if [ "$AUTO_APPLY" = "true" ] || [ "$AUTO_APPLY" = "1" ]; then
  args+=(--auto-apply)
fi
if [ "$REQUIRE_AI" = "false" ] || [ "$REQUIRE_AI" = "0" ]; then
  args+=(--allow-deterministic-without-ai)
fi

PYTHONPATH=. "$VENV_PY" -m src.engine.threshold_cycle_preopen_apply "${args[@]}"
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] threshold-cycle preopen target_date=$TARGET_DATE finished_at=$finished_at"
