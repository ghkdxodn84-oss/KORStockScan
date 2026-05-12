# Swing Daily Simulation - 2026-05-11

- runtime_change: `False`
- recommendation_rows: `23` / live `23` / diagnostic `0`
- recommendation_sources: `{'recommendation_history': 20, 'daily_recommendations_v2_csv': 3}`
- db_recommendation_rows: `20`
- source_signal_dates: `['2026-05-11']`
- simulated_count: `23`
- closed_count: `0`
- planned_or_open_count: `23`
- closed win_rate: `0.00%`
- closed avg_net_ret: `0.00%`

## Model Backtest Snapshot

- range: `2026-01-02` ~ `2026-03-16`
- trades: `123`
- win_rate: `47.15%`
- avg_net_ret: `1.51%`
- sum_net_ret: `185.32%`

## Runtime Dry-Run Policy

- mode: `runtime_order_dry_run_daily_proxy`
- entry: `runtime guard dry-run, no broker order submit`
- order_type: `최유리지정가` (`6`)
- simulation_cash_krw: `10000000`

## Observation Arms

| arm | simulated | closed | win_rate | avg_net_ret | status_counts |
| --- | ---: | ---: | ---: | ---: | --- |
| `gap_pass` | 23 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 23}` |
| `gatekeeper_pass` | 23 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 23}` |
| `selection_only` | 23 | 0 | 0.00% | 0.00% | `{'PLANNED_ENTRY': 23}` |

## Runtime Entry Funnel

- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-11.jsonl`

| stage | raw | unique_records | examples |
| --- | ---: | ---: | --- |
| `blocked_swing_gap` | 17801 | 4 | 삼성물산(028260), 삼성생명(032830), 삼성물산(028260), 삼성생명(032830), 삼성물산(028260) |
| `blocked_gatekeeper_reject` | 73 | 9 | 코리안리(003690), 하나금융지주(086790), LG(003550), 이노션(214320), 삼양식품(003230) |

## Simulated Trades

| code | name | source | status | guard | qty | entry | exit | net_ret | reason |
| --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| `000880` | 한화 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `003230` | 삼양식품 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `003530` | 한화투자증권 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `003550` | LG | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `003690` | 코리안리 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `005380` | 현대차 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-12 |  |  |  |
| `005720` | 넥센 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `005830` | DB손해보험 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `006040` | 동원산업 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `008770` | 호텔신라 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `010690` | 화신 | `daily_recommendations_v2_csv` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-12 |  |  |  |
| `011780` | 금호석유화학 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `028260` | 삼성물산 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-12 |  |  |  |
| `032830` | 삼성생명 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-12 |  |  |  |
| `036460` | 한국가스공사 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `037270` | YG PLUS | `daily_recommendations_v2_csv` | `PLANNED_ENTRY` | `PASS_DRY_RUN` | 283 | 2026-05-12 |  |  |  |
| `066570` | LG전자 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_SWING_GAP` | 0 | 2026-05-12 |  |  |  |
| `078930` | GS | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `086790` | 하나금융지주 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `214320` | 이노션 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `267260` | HD현대일렉트릭 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `373220` | LG에너지솔루션 | `recommendation_history` | `PLANNED_ENTRY` | `BLOCKED_MARKET_REGIME` | 0 | 2026-05-12 |  |  |  |
| `950210` | 프레스티지바이오파마 | `daily_recommendations_v2_csv` | `PLANNED_ENTRY` | `PASS_DRY_RUN` | 164 | 2026-05-12 |  |  |  |
