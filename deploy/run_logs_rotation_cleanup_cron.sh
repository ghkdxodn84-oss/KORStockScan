#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
LOG_DIR="$PROJECT_DIR/logs"
RETENTION_DAYS="${1:-7}"
TARGET_DATE="${TARGET_DATE:-$(TZ=Asia/Seoul date +%F)}"

if [[ ! "$RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
  echo "[LOG_CLEANUP_ERROR] retention days must be integer: $RETENTION_DAYS"
  exit 2
fi

mkdir -p "$LOG_DIR"
started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] log_rotation_cleanup target_date=${TARGET_DATE} retention_days=${RETENTION_DAYS} started_at=${started_at}"
trap 'failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"; echo "[FAIL] log_rotation_cleanup target_date=${TARGET_DATE} failed_at=${failed_at}"' ERR

before_count="$(find "$LOG_DIR" -maxdepth 1 -type f -regex '.*\.log\.[0-9]+' | wc -l | tr -d ' ')"
before_size="$(du -sh "$LOG_DIR" | awk '{print $1}')"

deleted_count="$(find "$LOG_DIR" -maxdepth 1 -type f -regex '.*\.log\.[0-9]+' -mtime "+$RETENTION_DAYS" -print -delete | wc -l | tr -d ' ')"
after_count="$(find "$LOG_DIR" -maxdepth 1 -type f -regex '.*\.log\.[0-9]+' | wc -l | tr -d ' ')"
after_size="$(du -sh "$LOG_DIR" | awk '{print $1}')"

echo "[LOG_CLEANUP] retention_days=$RETENTION_DAYS deleted=$deleted_count rotated_before=$before_count rotated_after=$after_count size_before=$before_size size_after=$after_size"
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] log_rotation_cleanup target_date=${TARGET_DATE} retention_days=${RETENTION_DAYS} deleted=${deleted_count} finished_at=${finished_at}"
