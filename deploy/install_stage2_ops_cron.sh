#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '!/REMOTE_LATENCY_BASELINE_PREOPEN/ && !/REMOTE_LATENCY_BASELINE_MIDMORNING/ && !/REMOTE_LATENCY_BASELINE_AFTERNOON/ && !/RUN_MONITOR_SNAPSHOT_1000/ && !/RUN_MONITOR_SNAPSHOT_1200/ && !/REMOTE_SCALPING_FETCH_1600/ && !/SYSTEM_METRIC_SAMPLER_1MIN/' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

cat >> "$TMP_CRON" <<EOF
# stage2 ops cron
* * * * 1-5 $PROJECT_DIR/deploy/run_system_metric_sampler_cron.sh >> $PROJECT_DIR/logs/system_metric_sampler_cron.log 2>&1 # SYSTEM_METRIC_SAMPLER_1MIN
0 10 * * 1-5 $PROJECT_DIR/deploy/run_monitor_snapshot_cron.sh >> $PROJECT_DIR/logs/run_monitor_snapshot_cron.log 2>&1 # RUN_MONITOR_SNAPSHOT_1000
0 12 * * 1-5 $PROJECT_DIR/deploy/run_monitor_snapshot_cron.sh >> $PROJECT_DIR/logs/run_monitor_snapshot_cron.log 2>&1 # RUN_MONITOR_SNAPSHOT_1200
EOF

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
