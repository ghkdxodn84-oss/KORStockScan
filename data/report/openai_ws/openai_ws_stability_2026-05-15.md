# OpenAI WS Stability Report - 2026-05-15

- generated_at: `2026-05-15T19:41:51+09:00`
- decision: `keep_ws`
- unique WS calls: `763`
- endpoint counts: `{'analyze_target': 762, 'entry_price': 1}`
- WS fallback: `0` / `763` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{}`
- WS transport warning: `{'ws_error_count': 0, 'ws_error_rate': 0.0, 'warning_only': False, 'rollback_threshold_error_count': 3, 'rollback_threshold_error_rate': 0.01}`
- AI response ms: `{'n': 762, 'avg': 1573.1, 'median': 1481.0, 'p75': 1754.8, 'p90': 2183.9, 'p95': 2576.7, 'max': 5469.0}`
- WS roundtrip ms: `{'n': 763, 'avg': 1520.0, 'median': 1430.0, 'p75': 1695.5, 'p90': 2108.8, 'p95': 2538.0, 'max': 5409.0}`
- WS queue wait ms: `{'n': 763, 'avg': 2.2, 'median': 0.0, 'p75': 0.0, 'p90': 2.0, 'p95': 7.0, 'max': 127.0}`
- <=3s rate: `0.9738`
- HTTP late baseline AI response ms: `{'n': 6, 'avg': 1942.0, 'median': 1887.0, 'p75': 2167.2, 'p90': 2417.5, 'p95': 2514.8, 'max': 2612.0}`
- baseline median improvement: `0.2152`
- baseline p75 improvement: `0.1903`
- entry_price WS sample count: `1`
- entry_price canary summary: `{'canary_event_count': 1, 'applied_count': 1, 'transport_observable_count': 1, 'applied_transport_observable_count': 1, 'ws_observable_unique_count': 1, 'applied_ai_eval_ms': {'n': 1, 'avg': 1691.0, 'median': 1691.0, 'p75': 1691.0, 'p90': 1691.0, 'p95': 1691.0, 'max': 1691.0}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price` WS transport 표본이 관찰됐다.
- 장중/장후 표본에서 fallback/fail-closed/latency guard를 계속 분리 확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
