#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/panic sell defense intraday report-only/ && !/PANIC_SELL_DEFENSE_0905_0955/ && !/PANIC_SELL_DEFENSE_1000_1455/ && !/PANIC_SELL_DEFENSE_1500_1530/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# panic sell defense intraday report-only
5-55/5 9 * * 1-5 $PROJECT_DIR/deploy/run_panic_sell_defense_intraday.sh \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/run_panic_sell_defense_cron.log 2>&1 # PANIC_SELL_DEFENSE_0905_0955
*/5 10-14 * * 1-5 $PROJECT_DIR/deploy/run_panic_sell_defense_intraday.sh \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/run_panic_sell_defense_cron.log 2>&1 # PANIC_SELL_DEFENSE_1000_1455
0-30/5 15 * * 1-5 $PROJECT_DIR/deploy/run_panic_sell_defense_intraday.sh \$(TZ=Asia/Seoul date +\\%F) >> $PROJECT_DIR/logs/run_panic_sell_defense_cron.log 2>&1 # PANIC_SELL_DEFENSE_1500_1530
EOF

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
