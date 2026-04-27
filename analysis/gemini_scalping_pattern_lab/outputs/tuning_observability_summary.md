# Tuning Observability Summary

- target_date: `2026-04-17`
- analysis_period: `2026-04-01 ~ 2026-04-17`

## Entry Funnel

- gatekeeper_decisions: `14`
- gatekeeper_eval_ms_p95: `29336ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `0ms`
- budget_pass_events: `6634`
- submitted_events: `67`
- budget_pass_to_submitted_rate: `1.0%`
- latency_block_events: `6567`
- quote_fresh_latency_blocks: `5354`

## Buy Recovery Canary

- total_candidates: `0`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `0.0%`

## Priority Findings

- `Gatekeeper latency high`: 경고 — `gatekeeper_eval_ms_p95=29336ms`로 지연 경고 구간에 들어가 있다.
