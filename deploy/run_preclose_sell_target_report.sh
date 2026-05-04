#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/KORStockScan}"
VENV_PY="${PROJECT_DIR}/.venv/bin/python"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"

if [[ $# -gt 0 ]]; then
  shift
fi

cd "$PROJECT_DIR"
PYTHONPATH=. "$VENV_PY" -m src.scanners.preclose_sell_target_report --date "$TARGET_DATE" "$@"
