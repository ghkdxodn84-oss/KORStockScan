#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="${VENV_PY:-$PROJECT_DIR/.venv/bin/python}"
TARGET_DATE="${1:-$(TZ=Asia/Seoul date +%F)}"
MAX_ITERATIONS="${THRESHOLD_CYCLE_MAX_ITERATIONS:-80}"
MAX_INPUT_LINES="${THRESHOLD_CYCLE_MAX_INPUT_LINES_PER_CHUNK:-20000}"
MAX_OUTPUT_LINES="${THRESHOLD_CYCLE_MAX_OUTPUT_LINES_PER_PARTITION:-25000}"
SKIP_DB="${THRESHOLD_CYCLE_SKIP_DB:-false}"
USE_SNAPSHOT="${THRESHOLD_CYCLE_USE_SNAPSHOT:-true}"
AI_CORRECTION_PROVIDER="${THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER:-openai}"
AI_CORRECTION_RESPONSE_JSON="${THRESHOLD_CYCLE_AI_CORRECTION_RESPONSE_JSON:-}"
RUN_PATTERN_LABS="${THRESHOLD_CYCLE_RUN_PATTERN_LABS:-true}"
PATTERN_LAB_START_DATE="${PATTERN_LAB_ANALYSIS_START_DATE:-2026-04-21}"
RUN_SWING_LIFECYCLE_AUDIT="${THRESHOLD_CYCLE_RUN_SWING_LIFECYCLE_AUDIT:-true}"
SWING_THRESHOLD_AI_REVIEW_PROVIDER="${SWING_THRESHOLD_AI_REVIEW_PROVIDER:-openai}"
BUILD_CODE_IMPROVEMENT_WORKORDER="${THRESHOLD_CYCLE_BUILD_CODE_IMPROVEMENT_WORKORDER:-true}"
CODE_IMPROVEMENT_WORKORDER_MAX_ORDERS="${CODE_IMPROVEMENT_WORKORDER_MAX_ORDERS:-12}"
RUN_DEEPSEEK_SWING_LAB="${THRESHOLD_CYCLE_RUN_DEEPSEEK_SWING_LAB:-true}"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"

trap 'failed_at="$(TZ=Asia/Seoul date +%FT%T%z)"; echo "[FAIL] threshold-cycle postclose target_date=$TARGET_DATE failed_at=$failed_at"' ERR

started_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[START] threshold-cycle postclose target_date=$TARGET_DATE max_iterations=$MAX_ITERATIONS started_at=$started_at"

SOURCE_ARGS=()
if [ "$USE_SNAPSHOT" = "true" ]; then
  SNAPSHOT_DIR="$PROJECT_DIR/data/threshold_cycle/snapshots"
  mkdir -p "$SNAPSHOT_DIR"
  SNAPSHOT_TS="$(TZ=Asia/Seoul date +%Y%m%d_%H%M%S)"
  RAW_SOURCE="$PROJECT_DIR/data/pipeline_events/pipeline_events_${TARGET_DATE}.jsonl"
  SNAPSHOT_PATH="$SNAPSHOT_DIR/pipeline_events_${TARGET_DATE}_${SNAPSHOT_TS}.jsonl"
  if [ -f "$RAW_SOURCE" ]; then
    cp --reflink=auto "$RAW_SOURCE" "$SNAPSHOT_PATH"
    SOURCE_ARGS=(--source-path "$SNAPSHOT_PATH")
    echo "[threshold-cycle] using immutable snapshot source=$SNAPSHOT_PATH"
  else
    echo "[threshold-cycle] raw source missing, falling back to default source target_date=$TARGET_DATE"
  fi
fi

for i in $(seq 1 "$MAX_ITERATIONS"); do
  resume_args=(--resume)
  if [ "$i" = "1" ] && [ "$USE_SNAPSHOT" = "true" ]; then
    resume_args=(--overwrite)
  fi
  out="$(
    PYTHONPATH=. "$VENV_PY" -m src.engine.backfill_threshold_cycle_events \
      --date "$TARGET_DATE" \
      --mode incremental \
      "${resume_args[@]}" \
      "${SOURCE_ARGS[@]}" \
      --max-input-lines-per-chunk "$MAX_INPUT_LINES" \
      --max-output-lines-per-partition "$MAX_OUTPUT_LINES"
  )"
  echo "$out"
  completed="$(printf '%s' "$out" | "$VENV_PY" -c 'import json,sys; print(str(json.load(sys.stdin).get("completed", False)).lower())')"
  status="$(printf '%s' "$out" | "$VENV_PY" -c 'import json,sys; print(json.load(sys.stdin).get("status", ""))')"
  paused_reason="$(printf '%s' "$out" | "$VENV_PY" -c 'import json,sys; print(json.load(sys.stdin).get("paused_reason") or "")')"
  if [ "$completed" = "true" ]; then
    break
  fi
  if [ "$status" = "paused_by_availability_guard" ] && [ -n "$paused_reason" ]; then
    echo "[threshold-cycle] availability guard paused target_date=$TARGET_DATE reason=$paused_reason"
    break
  fi
  sleep 1
done

if [ "${completed:-false}" != "true" ]; then
  echo "[threshold-cycle] compact collection incomplete target_date=$TARGET_DATE status=${status:-unknown} paused_reason=${paused_reason:-}" >&2
  exit 2
fi

report_args=(--date "$TARGET_DATE")
if [ "$SKIP_DB" = "true" ]; then
  report_args+=(--skip-db)
fi
if [ -n "$AI_CORRECTION_RESPONSE_JSON" ]; then
  report_args+=(--ai-correction-response-json "$AI_CORRECTION_RESPONSE_JSON")
else
  report_args+=(--ai-correction-provider "$AI_CORRECTION_PROVIDER")
fi

PYTHONPATH=. "$VENV_PY" -m src.engine.daily_threshold_cycle_report \
  --calibration-run-phase postclose \
  "${report_args[@]}"
if [ "$RUN_SWING_LIFECYCLE_AUDIT" = "true" ] || [ "$RUN_SWING_LIFECYCLE_AUDIT" = "1" ]; then
  PYTHONPATH=. "$VENV_PY" -m src.engine.swing_lifecycle_audit \
    --date "$TARGET_DATE" \
    --ai-review-provider "$SWING_THRESHOLD_AI_REVIEW_PROVIDER"
fi
if [ "$RUN_DEEPSEEK_SWING_LAB" = "true" ] || [ "$RUN_DEEPSEEK_SWING_LAB" = "1" ]; then
  echo "[threshold-cycle] running deepseek swing pattern lab target_date=$TARGET_DATE"
  ANALYSIS_START_DATE="$TARGET_DATE" ANALYSIS_END_DATE="$TARGET_DATE" \
    bash "$PROJECT_DIR/analysis/deepseek_swing_pattern_lab/run_all.sh" "$TARGET_DATE" || \
    echo "[threshold-cycle] deepseek swing pattern lab failed (non-fatal)" >&2
fi
if [ "$RUN_PATTERN_LABS" = "true" ] || [ "$RUN_PATTERN_LABS" = "1" ]; then
  ANALYSIS_START_DATE="$PATTERN_LAB_START_DATE" ANALYSIS_END_DATE="$TARGET_DATE" \
    "$PROJECT_DIR/analysis/gemini_scalping_pattern_lab/run.sh"
  ANALYSIS_START_DATE="$PATTERN_LAB_START_DATE" ANALYSIS_END_DATE="$TARGET_DATE" \
    "$PROJECT_DIR/analysis/claude_scalping_pattern_lab/run_all.sh"
fi
PYTHONPATH=. "$VENV_PY" -m src.engine.scalping_pattern_lab_automation --date "$TARGET_DATE"
PYTHONPATH=. "$VENV_PY" -m src.engine.swing_pattern_lab_automation --date "$TARGET_DATE" || \
  echo "[threshold-cycle] swing pattern lab automation failed (non-fatal)" >&2
if [ "$BUILD_CODE_IMPROVEMENT_WORKORDER" = "true" ] || [ "$BUILD_CODE_IMPROVEMENT_WORKORDER" = "1" ]; then
  PYTHONPATH=. "$VENV_PY" -m src.engine.build_code_improvement_workorder \
    --date "$TARGET_DATE" \
    --max-orders "$CODE_IMPROVEMENT_WORKORDER_MAX_ORDERS"
fi
PYTHONPATH=. "$VENV_PY" -m src.engine.threshold_cycle_ev_report --date "$TARGET_DATE"
PYTHONPATH=. "$VENV_PY" -m src.engine.runtime_approval_summary --date "$TARGET_DATE"
PYTHONPATH=. "$VENV_PY" -m src.engine.build_next_stage2_checklist --source-date "$TARGET_DATE"
PYTHONPATH=. "$VENV_PY" -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500 >/dev/null
finished_at="$(TZ=Asia/Seoul date +%FT%T%z)"
echo "[DONE] threshold-cycle postclose target_date=$TARGET_DATE ai_correction_provider=$AI_CORRECTION_PROVIDER swing_lifecycle=$RUN_SWING_LIFECYCLE_AUDIT swing_ai_review_provider=$SWING_THRESHOLD_AI_REVIEW_PROVIDER pattern_labs=$RUN_PATTERN_LABS deepseek_swing_lab=$RUN_DEEPSEEK_SWING_LAB code_improvement_workorder=$BUILD_CODE_IMPROVEMENT_WORKORDER daily_ev=true runtime_approval_summary=true next_stage2_checklist=true finished_at=$finished_at"
