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
| `total_trades` | `19` | `28` | `9.0` |
| `completed_trades` | `12` | `26` | `14.0` |
| `open_trades` | `7` | `2` | `-5.0` |
| `holding_events` | `3360` | `96` | `-3264.0` |
| `all_rows` | `195` | `208` | `13.0` |
| `entered_rows` | `19` | `28` | `9.0` |
| `expired_rows` | `145` | `159` | `14.0` |

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
| `total_candidates` | `11` | `25` | `14.0` |
| `evaluated_candidates` | `11` | `25` | `14.0` |

## Entry Pipeline Flow
- status: `remote_error`
- remote_url: `https://songstockscan.ddns.net/api/entry-pipeline-flow?date=2026-04-16&since=09:00:00&top=10`
- remote_error: `TimeoutError: The read operation timed out`
