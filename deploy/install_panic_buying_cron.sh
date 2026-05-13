#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/panic buying intraday report-only/ && !/PANIC_BUYING_0905_0955/ && !/PANIC_BUYING_1000_1455/ && !/PANIC_BUYING_1500_1530/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# panic buying intraday report-only (2m cadence, offset from 5m sentinels)
6,8,12,14,16,18,22,24,26,28,32,34,36,38,42,44,46,48,52,54,56,58 9 * * 1-5 PANIC_BUYING_COOLDOWN_SEC=90 $PROJECT_DIR/deploy/run_panic_buying_intraday.sh \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/run_panic_buying_cron.log 2>&1 # PANIC_BUYING_0905_0955
2,4,6,8,12,14,16,18,22,24,26,28,32,34,36,38,42,44,46,48,52,54,56,58 10-14 * * 1-5 PANIC_BUYING_COOLDOWN_SEC=90 $PROJECT_DIR/deploy/run_panic_buying_intraday.sh \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/run_panic_buying_cron.log 2>&1 # PANIC_BUYING_1000_1455
2,4,6,8,12,14,16,18,22,24,26,28 15 * * 1-5 PANIC_BUYING_COOLDOWN_SEC=90 $PROJECT_DIR/deploy/run_panic_buying_intraday.sh \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/run_panic_buying_cron.log 2>&1 # PANIC_BUYING_1500_1530
EOF

crontab "$TMP_CRON"
crontab -l | sed -n '1,280p'
