# OpenAI WS Stability Report - 2026-05-11

- generated_at: `2026-05-11T16:21:06+09:00`
- decision: `keep_ws`
- unique WS calls: `569`
- endpoint counts: `{'analyze_target': 569}`
- WS fallback: `0` / `569` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{}`
- AI response ms: `{'n': 569, 'avg': 1603.2, 'median': 1460.0, 'p75': 1811.0, 'p90': 2242.2, 'p95': 2741.8, 'max': 6952.0}`
- WS roundtrip ms: `{'n': 569, 'avg': 1552.0, 'median': 1412.0, 'p75': 1757.0, 'p90': 2199.6, 'p95': 2689.6, 'max': 6924.0}`
- WS queue wait ms: `{'n': 569, 'avg': 0.9, 'median': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 1.0, 'max': 68.0}`
- <=3s rate: `0.9666`
- HTTP late baseline AI response ms: `{'n': 455, 'avg': 3169.7, 'median': 2072.0, 'p75': 2555.5, 'p90': 3821.0, 'p95': 11963.4, 'max': 29247.0}`
- baseline median improvement: `0.2954`
- baseline p75 improvement: `0.2913`
- entry_price WS sample count: `0`
- entry_price canary summary: `{'canary_event_count': 3, 'applied_count': 3, 'transport_observable_count': 0, 'applied_transport_observable_count': 0, 'ws_observable_unique_count': 0, 'applied_ai_eval_ms': {'n': 3, 'avg': 19043.0, 'median': 15416.0, 'p75': 24264.5, 'p90': 29573.6, 'p95': 31343.3, 'max': 33113.0}, 'instrumentation_gap': True}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price`는 canary 적용 이벤트가 있으나 OpenAI transport metadata가 누락되어 WS 적용 여부를 이 리포트만으로 확정할 수 없다.
- 이 결함은 rollback 근거가 아니라 instrumentation gap이다. 이후 `entry_ai_price_canary_*` 이벤트에 `openai_*` provenance를 같이 남겨 재판정한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
