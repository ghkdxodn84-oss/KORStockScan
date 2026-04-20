#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"

"$PROJECT_DIR/deploy/run_monitor_snapshot_safe.sh" "$TARGET_DATE"
