# Tuning Observability Summary

- target_date: `2026-05-14`
- analysis_period: `2026-04-21 ~ 2026-05-14`

## Entry Funnel

- gatekeeper_decisions: `73`
- gatekeeper_eval_ms_p95: `5508ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `5508ms`
- budget_pass_events: `0`
- submitted_events: `0`
- budget_pass_to_submitted_rate: `0.0%`
- latency_block_events: `0`
- quote_fresh_latency_blocks: `0`

## Buy Recovery Canary

- total_candidates: `19`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `94.7%`

## Priority Findings

- `AI threshold dominance`: 경고 — `blocked_ai_score_share=94.7%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.
