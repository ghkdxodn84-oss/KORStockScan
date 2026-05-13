# OpenAI WS Stability Report - 2026-05-12

- generated_at: `2026-05-13T08:49:43+09:00`
- decision: `keep_ws`
- unique WS calls: `582`
- endpoint counts: `{'analyze_target': 582}`
- WS fallback: `0` / `582` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{}`
- AI response ms: `{'n': 582, 'avg': 1725.2, 'median': 1624.0, 'p75': 1995.2, 'p90': 2363.7, 'p95': 2648.2, 'max': 4526.0}`
- WS roundtrip ms: `{'n': 582, 'avg': 1654.0, 'median': 1557.0, 'p75': 1900.0, 'p90': 2269.1, 'p95': 2575.7, 'max': 4480.0}`
- WS queue wait ms: `{'n': 582, 'avg': 0.7, 'median': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 5.0, 'max': 65.0}`
- <=3s rate: `0.9656`
- HTTP late baseline AI response ms: `{'n': 6, 'avg': 2589.2, 'median': 2598.0, 'p75': 2973.2, 'p90': 3040.0, 'p95': 3051.5, 'max': 3063.0}`
- baseline median improvement: `0.3749`
- baseline p75 improvement: `0.3289`
- entry_price WS sample count: `0`
- entry_price canary summary: `{'canary_event_count': 0, 'applied_count': 0, 'transport_observable_count': 0, 'applied_transport_observable_count': 0, 'ws_observable_unique_count': 0, 'applied_ai_eval_ms': {'n': 0, 'avg': None, 'median': None, 'p75': None, 'p90': None, 'p95': None, 'max': None}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price`는 해당 날짜에 WS transport 표본이 없어 hook 미발생 또는 표본 부족으로 분리한다.
- 이는 OpenAI WS 실패 근거가 아니며, 다음 장중 표본에서 `entry_price` provenance를 재확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
