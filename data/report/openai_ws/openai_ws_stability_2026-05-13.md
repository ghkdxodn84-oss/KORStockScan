# OpenAI WS Stability Report - 2026-05-13

- generated_at: `2026-05-13T16:13:05+09:00`
- decision: `keep_ws`
- unique WS calls: `752`
- endpoint counts: `{'analyze_target': 752}`
- WS fallback: `0` / `752` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{}`
- AI response ms: `{'n': 752, 'avg': 1493.5, 'median': 1388.0, 'p75': 1644.2, 'p90': 1933.8, 'p95': 2409.1, 'max': 5819.0}`
- WS roundtrip ms: `{'n': 752, 'avg': 1459.8, 'median': 1352.5, 'p75': 1607.2, 'p90': 1902.4, 'p95': 2378.4, 'max': 5794.0}`
- WS queue wait ms: `{'n': 752, 'avg': 0.6, 'median': 0.0, 'p75': 0.0, 'p90': 1.0, 'p95': 2.0, 'max': 154.0}`
- <=3s rate: `0.9774`
- HTTP late baseline AI response ms: `{'n': 11, 'avg': 3834.1, 'median': 1832.0, 'p75': 2515.5, 'p90': 7088.0, 'p95': 12727.5, 'max': 18367.0}`
- baseline median improvement: `0.2424`
- baseline p75 improvement: `0.3464`
- entry_price WS sample count: `0`
- entry_price canary summary: `{'canary_event_count': 0, 'applied_count': 0, 'transport_observable_count': 0, 'applied_transport_observable_count': 0, 'ws_observable_unique_count': 0, 'applied_ai_eval_ms': {'n': 0, 'avg': None, 'median': None, 'p75': None, 'p90': None, 'p95': None, 'max': None}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price`는 해당 날짜에 WS transport 표본이 없어 hook 미발생 또는 표본 부족으로 분리한다.
- 이는 OpenAI WS 실패 근거가 아니며, 다음 장중 표본에서 `entry_price` provenance를 재확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
