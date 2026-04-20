# Server Comparison (2026-04-20)

- remote: `https://songstockscan.ddns.net`
- since: `09:00:00`
- policy: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`

## Trade Review
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/trade-review?date=2026-04-20`
- excluded_from_criteria: `win_trades, loss_trades, avg_profit_rate, realized_pnl_krw, row-level profit_rate`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_trades` | `14` | `1` | `-13.0` |
| `completed_trades` | `11` | `1` | `-10.0` |
| `open_trades` | `3` | `0` | `-3.0` |
| `holding_events` | `1308` | `0` | `-1308.0` |
| `all_rows` | `84` | `72` | `-12.0` |
| `entered_rows` | `14` | `1` | `-13.0` |
| `expired_rows` | `18` | `22` | `4.0` |

## Performance Tuning
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/performance-tuning?date=2026-04-20&since=09:00:00`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `holding_reviews` | `367` | `19` | `-348.0` |
| `holding_skips` | `31` | `1` | `-30.0` |
| `holding_skip_ratio` | `7.8` | `5.0` | `-2.8` |
| `holding_ai_cache_hit_ratio` | `0.0` | `10.5` | `10.5` |
| `holding_review_ms_avg` | `1946.67` | `6368.79` | `4422.12` |
| `holding_review_ms_p95` | `2866.0` | `74603.0` | `71737.0` |
| `holding_skip_ws_age_p95` | `1.04` | `0.07` | `-0.97` |
| `gatekeeper_decisions` | `13` | `18` | `5.0` |
| `gatekeeper_fast_reuse_ratio` | `0.0` | `0.0` | `0.0` |
| `gatekeeper_ai_cache_hit_ratio` | `0.0` | `0.0` | `0.0` |
| `gatekeeper_eval_ms_avg` | `17085.54` | `10369.44` | `-6716.1` |
| `gatekeeper_eval_ms_p95` | `30794.0` | `13269.0` | `-17525.0` |
| `gatekeeper_fast_reuse_ws_age_p95` | `0.0` | `0.0` | `0.0` |
| `gatekeeper_action_age_p95` | `3057.52` | `1646.53` | `-1410.99` |
| `gatekeeper_allow_entry_age_p95` | `3057.52` | `1646.53` | `-1410.99` |
| `gatekeeper_bypass_evaluation_samples` | `13` | `19` | `6.0` |
| `exit_signals` | `14` | `5` | `-9.0` |
| `dual_persona_shadow_samples` | `0` | `0` | `0.0` |
| `dual_persona_gatekeeper_samples` | `0` | `0` | `0.0` |
| `dual_persona_overnight_samples` | `0` | `0` | `0.0` |
| `dual_persona_conflict_ratio` | `0.0` | `0.0` | `0.0` |
| `dual_persona_conservative_veto_ratio` | `0.0` | `0.0` | `0.0` |
| `dual_persona_extra_ms_p95` | `0.0` | `0.0` | `0.0` |
| `dual_persona_fused_override_ratio` | `0.0` | `0.0` | `0.0` |

- local_watch_items:
  - `label=보유 AI skip 비율, value=7.8%, target=20% ~ 60%`
  - `label=보유 AI skip WS age p95, value=1.04s, target=<= 1.50s`
  - `label=Gatekeeper 평가 p95, value=30794ms, target=re-enable <= 5000ms / preferred < 1200ms`
  - `label=Gatekeeper fast reuse 비율, value=0.0%, target=15% ~ 55%`
  - `label=Gatekeeper fast reuse WS age p95, value=0.00s, target=<= 2.00s`

- remote_watch_items:
  - `label=보유 AI skip 비율, value=5.0%, target=20% ~ 60%`
  - `label=보유 AI skip WS age p95, value=0.07s, target=<= 1.50s`
  - `label=Gatekeeper 평가 p95, value=13269ms, target=re-enable <= 5000ms / preferred < 1200ms`
  - `label=Gatekeeper fast reuse 비율, value=0.0%, target=15% ~ 55%`
  - `label=Gatekeeper fast reuse WS age p95, value=0.00s, target=<= 2.00s`

## Post Sell Feedback
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/post-sell-feedback?date=2026-04-20`
- excluded_from_criteria: `missed_upside_rate, good_exit_rate, avg_realized_profit_rate, avg_extra_upside_10m_pct, median_extra_upside_10m_pct, avg_close_after_sell_10m_pct, capture_efficiency_avg_pct, estimated_extra_upside_10m_krw_sum, estimated_extra_upside_10m_krw_avg, timing_tuning_pressure_score, case-level profit_rate`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_candidates` | `13` | `5` | `-8.0` |
| `evaluated_candidates` | `13` | `5` | `-8.0` |

## Entry Pipeline Flow
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/entry-pipeline-flow?date=2026-04-20&since=09:00:00&top=10`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_events` | `22081` | `28445` | `6364.0` |
| `tracked_stocks` | `59` | `59` | `0.0` |
| `submitted_stocks` | `1` | `0` | `-1.0` |
| `blocked_stocks` | `19` | `22` | `3.0` |
| `waiting_stocks` | `0` | `0` | `0.0` |

- local_latest_stage_breakdown:
  - `name=strength_momentum_observed, count=24`
  - `name=blocked_overbought, count=10`
  - `name=blocked_gatekeeper_reject, count=7`
  - `name=watching_shared_prompt_shadow, count=7`
  - `name=partial_fill_reconciled, count=5`

- remote_latest_stage_breakdown:
  - `name=strength_momentum_observed, count=24`
  - `name=watching_shared_prompt_shadow, count=12`
  - `name=blocked_overbought, count=9`
  - `name=blocked_gatekeeper_reject, count=7`
  - `name=blocked_strength_momentum, count=4`
