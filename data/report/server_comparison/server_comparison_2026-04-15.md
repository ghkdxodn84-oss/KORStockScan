# Server Comparison (2026-04-15)

- remote: `https://songstockscan.ddns.net`
- since: `09:00:00`
- policy: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`

## Trade Review
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/trade-review?date=2026-04-15`
- excluded_from_criteria: `win_trades, loss_trades, avg_profit_rate, realized_pnl_krw, row-level profit_rate`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_trades` | `25` | `31` | `6.0` |
| `completed_trades` | `23` | `25` | `2.0` |
| `open_trades` | `2` | `6` | `4.0` |
| `holding_events` | `0` | `0` | `0.0` |
| `all_rows` | `184` | `193` | `9.0` |
| `entered_rows` | `25` | `31` | `6.0` |
| `expired_rows` | `118` | `119` | `1.0` |

## Performance Tuning
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/performance-tuning?date=2026-04-15&since=09:00:00`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `holding_reviews` | `492` | `656` | `164.0` |
| `holding_skips` | `34` | `16` | `-18.0` |
| `holding_skip_ratio` | `6.5` | `2.4` | `-4.1` |
| `holding_ai_cache_hit_ratio` | `0.0` | `0.3` | `0.3` |
| `holding_review_ms_avg` | `6312.72` | `5721.19` | `-591.53` |
| `holding_review_ms_p95` | `10709.0` | `10618.0` | `-91.0` |
| `holding_skip_ws_age_p95` | `0.55` | `0.48` | `-0.07` |
| `gatekeeper_decisions` | `63` | `74` | `11.0` |
| `gatekeeper_fast_reuse_ratio` | `0.0` | `0.0` | `0.0` |
| `gatekeeper_ai_cache_hit_ratio` | `0.0` | `0.0` | `0.0` |
| `gatekeeper_eval_ms_avg` | `10508.37` | `10658.88` | `150.51` |
| `gatekeeper_eval_ms_p95` | `13249.0` | `12876.0` | `-373.0` |
| `gatekeeper_fast_reuse_ws_age_p95` | `0.0` | `0.0` | `0.0` |
| `gatekeeper_action_age_p95` | `1484.18` | `1310.83` | `-173.35` |
| `gatekeeper_allow_entry_age_p95` | `1484.18` | `1310.83` | `-173.35` |
| `gatekeeper_bypass_evaluation_samples` | `63` | `75` | `12.0` |
| `exit_signals` | `34` | `35` | `1.0` |
| `dual_persona_shadow_samples` | `0` | `0` | `0.0` |
| `dual_persona_gatekeeper_samples` | `0` | `0` | `0.0` |
| `dual_persona_overnight_samples` | `0` | `0` | `0.0` |
| `dual_persona_conflict_ratio` | `0.0` | `0.0` | `0.0` |
| `dual_persona_conservative_veto_ratio` | `0.0` | `0.0` | `0.0` |
| `dual_persona_extra_ms_p95` | `0.0` | `0.0` | `0.0` |
| `dual_persona_fused_override_ratio` | `0.0` | `0.0` | `0.0` |

- local_watch_items:
  - `label=보유 AI skip 비율, value=6.5%, target=20% ~ 60%`
  - `label=보유 AI skip WS age p95, value=0.55s, target=<= 1.50s`
  - `label=Gatekeeper 평가 p95, value=13249ms, target=re-enable <= 5000ms / preferred < 1200ms`
  - `label=Gatekeeper fast reuse 비율, value=0.0%, target=15% ~ 55%`
  - `label=Gatekeeper fast reuse WS age p95, value=0.00s, target=<= 2.00s`

- remote_watch_items:
  - `label=보유 AI skip 비율, value=2.4%, target=20% ~ 60%`
  - `label=보유 AI skip WS age p95, value=0.48s, target=<= 1.50s`
  - `label=Gatekeeper 평가 p95, value=12876ms, target=re-enable <= 5000ms / preferred < 1200ms`
  - `label=Gatekeeper fast reuse 비율, value=0.0%, target=15% ~ 55%`
  - `label=Gatekeeper fast reuse WS age p95, value=0.00s, target=<= 2.00s`

## Post Sell Feedback
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/post-sell-feedback?date=2026-04-15`
- excluded_from_criteria: `missed_upside_rate, good_exit_rate, avg_realized_profit_rate, avg_extra_upside_10m_pct, median_extra_upside_10m_pct, avg_close_after_sell_10m_pct, capture_efficiency_avg_pct, estimated_extra_upside_10m_krw_sum, estimated_extra_upside_10m_krw_avg, timing_tuning_pressure_score, case-level profit_rate`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_candidates` | `22` | `26` | `4.0` |
| `evaluated_candidates` | `22` | `26` | `4.0` |

## Entry Pipeline Flow
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/entry-pipeline-flow?date=2026-04-15&since=09:00:00&top=10`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_events` | `104550` | `97741` | `-6809.0` |
| `tracked_stocks` | `142` | `152` | `10.0` |
| `submitted_stocks` | `3` | `5` | `2.0` |
| `blocked_stocks` | `32` | `33` | `1.0` |
| `waiting_stocks` | `1` | `0` | `-1.0` |

- local_latest_stage_breakdown:
  - `name=strength_momentum_observed, count=82`
  - `name=blocked_overbought, count=16`
  - `name=blocked_gatekeeper_reject, count=11`
  - `name=watching_shared_prompt_shadow, count=11`
  - `name=partial_fill_reconciled, count=8`

- remote_latest_stage_breakdown:
  - `name=strength_momentum_observed, count=97`
  - `name=blocked_overbought, count=18`
  - `name=blocked_gatekeeper_reject, count=11`
  - `name=watching_shared_prompt_shadow, count=8`
  - `name=order_leg_sent, count=5`
