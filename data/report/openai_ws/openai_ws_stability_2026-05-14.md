# OpenAI WS Stability Report - 2026-05-14

- generated_at: `2026-05-14T17:12:23+09:00`
- decision: `rollback_http`
- unique WS calls: `962`
- endpoint counts: `{'analyze_target': 962}`
- WS fallback: `0` / `962` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{'TimeoutError': 2}`
- AI response ms: `{'n': 962, 'avg': 1723.9, 'median': 1561.5, 'p75': 1934.2, 'p90': 2426.5, 'p95': 2863.0, 'max': 15100.0}`
- WS roundtrip ms: `{'n': 962, 'avg': 1637.3, 'median': 1509.0, 'p75': 1874.0, 'p90': 2353.9, 'p95': 2805.3, 'max': 9860.0}`
- WS queue wait ms: `{'n': 962, 'avg': 0.9, 'median': 0.0, 'p75': 0.0, 'p90': 2.0, 'p95': 5.0, 'max': 87.0}`
- <=3s rate: `0.9584`
- HTTP late baseline AI response ms: `{'n': 14, 'avg': 2744.5, 'median': 2754.0, 'p75': 3294.5, 'p90': 3509.7, 'p95': 3666.8, 'max': 3930.0}`
- baseline median improvement: `0.433`
- baseline p75 improvement: `0.4129`
- entry_price WS sample count: `0`
- entry_price canary summary: `{'canary_event_count': 0, 'applied_count': 0, 'transport_observable_count': 0, 'applied_transport_observable_count': 0, 'ws_observable_unique_count': 0, 'applied_ai_eval_ms': {'n': 0, 'avg': None, 'median': None, 'p75': None, 'p90': None, 'p95': None, 'max': None}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price`는 해당 날짜에 WS transport 표본이 없어 hook 미발생 또는 표본 부족으로 분리한다.
- 이는 OpenAI WS 실패 근거가 아니며, 다음 장중 표본에서 `entry_price` provenance를 재확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
