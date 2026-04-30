#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
SOURCE_DATE="${THRESHOLD_CYCLE_SOURCE_DATE:-}"
APPLY_MODE="${THRESHOLD_CYCLE_APPLY_MODE:-manifest_only}"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

echo "[threshold-cycle] preopen start target_date=$TARGET_DATE apply_mode=$APPLY_MODE"

args=(--date "$TARGET_DATE" --apply-mode "$APPLY_MODE")
if [ -n "$SOURCE_DATE" ]; then
  args+=(--source-date "$SOURCE_DATE")
fi

PYTHONPATH=. "$VENV_PY" -m src.engine.threshold_cycle_preopen_apply "${args[@]}"
echo "[threshold-cycle] preopen manifest complete target_date=$TARGET_DATE"
