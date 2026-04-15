# Server Comparison (2026-04-14)

- remote: `https://songstockscan.ddns.net`
- since: `09:00:00`
- policy: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`

## Trade Review
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/trade-review?date=2026-04-14`
- excluded_from_criteria: `win_trades, loss_trades, avg_profit_rate, realized_pnl_krw, row-level profit_rate`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_trades` | `8` | `12` | `4.0` |
| `completed_trades` | `7` | `12` | `5.0` |
| `open_trades` | `1` | `0` | `-1.0` |
| `holding_events` | `0` | `0` | `0.0` |
| `all_rows` | `169` | `171` | `2.0` |
| `entered_rows` | `8` | `12` | `4.0` |
| `expired_rows` | `138` | `146` | `8.0` |

## Performance Tuning
- status: `remote_error`
- remote_url: `https://songstockscan.ddns.net/api/performance-tuning?date=2026-04-14&since=09:00:00`
- remote_error: `TimeoutError: The read operation timed out`

## Post Sell Feedback
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/post-sell-feedback?date=2026-04-14`
- excluded_from_criteria: `missed_upside_rate, good_exit_rate, avg_realized_profit_rate, avg_extra_upside_10m_pct, median_extra_upside_10m_pct, avg_close_after_sell_10m_pct, capture_efficiency_avg_pct, estimated_extra_upside_10m_krw_sum, estimated_extra_upside_10m_krw_avg, timing_tuning_pressure_score, case-level profit_rate`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_candidates` | `7` | `8` | `1.0` |
| `evaluated_candidates` | `7` | `8` | `1.0` |

## Entry Pipeline Flow
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/entry-pipeline-flow?date=2026-04-14&since=09:00:00&top=10`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_events` | `455903` | `440556` | `-15347.0` |
| `tracked_stocks` | `154` | `152` | `-2.0` |
| `submitted_stocks` | `4` | `6` | `2.0` |
| `blocked_stocks` | `39` | `39` | `0.0` |
| `waiting_stocks` | `1` | `0` | `-1.0` |

- local_latest_stage_breakdown:
  - `name=strength_momentum_observed, count=103`
  - `name=blocked_overbought, count=17`
  - `name=blocked_ai_score, count=16`
  - `name=strength_momentum_pass, count=7`
  - `name=blocked_gatekeeper_reject, count=5`

- remote_latest_stage_breakdown:
  - `name=strength_momentum_observed, count=99`
  - `name=blocked_overbought, count=16`
  - `name=blocked_ai_score, count=14`
  - `name=strength_momentum_pass, count=8`
  - `name=order_leg_sent, count=6`
