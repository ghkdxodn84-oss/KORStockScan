# Server Comparison (2026-04-16)

- remote: `https://songstockscan.ddns.net`
- since: `09:00:00`
- policy: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`

## Trade Review
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/trade-review?date=2026-04-16`
- excluded_from_criteria: `win_trades, loss_trades, avg_profit_rate, realized_pnl_krw, row-level profit_rate`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_trades` | `14` | `26` | `12.0` |
| `completed_trades` | `9` | `25` | `16.0` |
| `open_trades` | `5` | `1` | `-4.0` |
| `holding_events` | `1739` | `689` | `-1050.0` |
| `all_rows` | `170` | `182` | `12.0` |
| `entered_rows` | `14` | `26` | `12.0` |
| `expired_rows` | `125` | `130` | `5.0` |

## Performance Tuning
- status: `remote_error`
- remote_url: `https://songstockscan.ddns.net/api/performance-tuning?date=2026-04-16&since=09:00:00`
- remote_error: `TimeoutError: The read operation timed out`

## Post Sell Feedback
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/post-sell-feedback?date=2026-04-16`
- excluded_from_criteria: `missed_upside_rate, good_exit_rate, avg_realized_profit_rate, avg_extra_upside_10m_pct, median_extra_upside_10m_pct, avg_close_after_sell_10m_pct, capture_efficiency_avg_pct, estimated_extra_upside_10m_krw_sum, estimated_extra_upside_10m_krw_avg, timing_tuning_pressure_score, case-level profit_rate`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_candidates` | `9` | `24` | `15.0` |
| `evaluated_candidates` | `9` | `24` | `15.0` |

## Entry Pipeline Flow
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/entry-pipeline-flow?date=2026-04-16&since=09:00:00&top=10`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_events` | `261136` | `271146` | `10010.0` |
| `tracked_stocks` | `151` | `151` | `0.0` |
| `submitted_stocks` | `0` | `0` | `0.0` |
| `blocked_stocks` | `23` | `18` | `-5.0` |
| `waiting_stocks` | `0` | `0` | `0.0` |

- local_latest_stage_breakdown:
  - `name=strength_momentum_observed, count=104`
  - `name=blocked_overbought, count=13`
  - `name=watching_shared_prompt_shadow, count=12`
  - `name=strength_momentum_pass, count=6`
  - `name=partial_fill_reconciled, count=6`

- remote_latest_stage_breakdown:
  - `name=strength_momentum_observed, count=106`
  - `name=watching_shared_prompt_shadow, count=16`
  - `name=blocked_overbought, count=14`
  - `name=strength_momentum_pass, count=8`
  - `name=blocked_gatekeeper_reject, count=4`
