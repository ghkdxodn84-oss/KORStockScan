# Tuning Observability Summary

- target_date: `2026-05-11`
- analysis_period: `2026-04-21 ~ 2026-05-11`

## Entry Funnel

- gatekeeper_decisions: `73`
- gatekeeper_eval_ms_p95: `10495ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `10495ms`
- budget_pass_events: `712`
- submitted_events: `3`
- budget_pass_to_submitted_rate: `0.4%`
- latency_block_events: `709`
- quote_fresh_latency_blocks: `679`

## Buy Recovery Canary

- total_candidates: `128`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `60.9%`

## Priority Findings

- `No acute observability alert`: 중립 — 주요 관찰축에서 즉시 경고할 단일 병목이 두드러지지 않는다.
