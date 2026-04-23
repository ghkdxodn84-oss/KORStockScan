# Tuning Observability Summary

- target_date: `2026-04-22`
- analysis_period: `2026-04-22 ~ 2026-04-22`

## Entry Funnel

- gatekeeper_decisions: `37`
- gatekeeper_eval_ms_p95: `16637ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `0ms`
- budget_pass_events: `1188`
- submitted_events: `1`
- budget_pass_to_submitted_rate: `0.1%`
- latency_block_events: `1187`
- quote_fresh_latency_blocks: `947`

## Buy Recovery Canary

- total_candidates: `246`
- recovery_check: `40`
- promoted: `6`
- submitted: `0`
- blocked_ai_score_share: `84.6%`

## Priority Findings

- `AI threshold dominance`: 경고 — `blocked_ai_score_share=84.6%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.
- `Prompt improved but submit disconnected`: 경고 — `promoted=6`인데 `submitted=0`라 프롬프트 개선과 주문 회복을 동일시할 수 없다.
- `Gatekeeper latency high`: 경고 — `gatekeeper_eval_ms_p95=16637ms`로 지연 경고 구간에 들어가 있다.
