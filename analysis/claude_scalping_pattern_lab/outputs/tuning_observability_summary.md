# Tuning Observability Summary

- target_date: `2026-04-20`
- analysis_period: `2026-04-20 ~ 2026-04-20`

## Entry Funnel

- gatekeeper_decisions: `61`
- gatekeeper_eval_ms_p95: `19917ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `0ms`
- budget_pass_events: `1433`
- submitted_events: `38`
- budget_pass_to_submitted_rate: `2.7%`
- latency_block_events: `1395`
- quote_fresh_latency_blocks: `984`

## Buy Recovery Canary

- total_candidates: `0`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `0.0%`

## Priority Findings

- `Gatekeeper latency high`: 경고 — `gatekeeper_eval_ms_p95=19917ms`로 지연 경고 구간에 들어가 있다.
