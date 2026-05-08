# Tuning Observability Summary

- target_date: `2026-05-08`
- analysis_period: `2026-04-21 ~ 2026-05-08`

## Entry Funnel

- gatekeeper_decisions: `44`
- gatekeeper_eval_ms_p95: `11428ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `11428ms`
- budget_pass_events: `703`
- submitted_events: `10`
- budget_pass_to_submitted_rate: `1.4%`
- latency_block_events: `692`
- quote_fresh_latency_blocks: `588`

## Buy Recovery Canary

- total_candidates: `511`
- recovery_check: `0`
- promoted: `0`
- submitted: `1`
- blocked_ai_score_share: `90.2%`

## Priority Findings

- `AI threshold dominance`: 경고 — `blocked_ai_score_share=90.2%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.
