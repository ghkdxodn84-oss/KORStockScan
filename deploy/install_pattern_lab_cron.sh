#!/usr/bin/env bash
set -euo pipefail

# Deprecated: pattern labs are now run by TUNING_MONITORING_POSTCLOSE after
# parquet/DuckDB refresh and shadow diff. Keep this script as a cleanup shim so
# older docs/operators do not reintroduce the former Friday-only duplicate jobs.
TMP_CRON="$(mktemp)"
trap 'rm -f "$TMP_CRON"' EXIT

crontab -l 2>/dev/null > "$TMP_CRON" || true
awk '
  /PATTERN_LAB_CLAUDE_FRI_POSTCLOSE/ {next}
  /PATTERN_LAB_GEMINI_FRI_POSTCLOSE/ {next}
  /^# pattern lab weekly cron$/ {next}
  {print}
' "$TMP_CRON" > "$TMP_CRON.filtered"
mv "$TMP_CRON.filtered" "$TMP_CRON"

crontab "$TMP_CRON"
crontab -l | sed -n '1,260p'
