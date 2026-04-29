# OpenAI Parity + Responses WS 코드 리뷰 결과보고서

작성일: 2026-04-30

## 1. 판정

- OpenAI 엔진에 Gemini parity 범위의 schema registry 개선과 Responses API transport 추상화가 반영되었다.
- phase 1 범위의 Responses WebSocket 후보 경로는 `analyze_target`, `analyze_target_shadow_prompt`, `evaluate_condition_entry`, `evaluate_condition_exit`로 제한되며, `realtime_report`, `gatekeeper`, `overnight`, `scanner_report`, `EOD` 텍스트 경로는 HTTP 유지로 분리되었다.
- 운영 기본값은 여전히 `OPENAI_TRANSPORT_MODE=http`, `OPENAI_RESPONSES_WS_ENABLED=False`로 닫혀 있어 same-day live behavior 변경은 없다.

## 2. 변경 범위

### 2.1 Schema registry 공용화

- `src/engine/ai_response_contracts.py` 신설
- Gemini/OpenAI 공용 response schema registry 추가
- registry key 고정:
  - `entry_v1`
  - `holding_exit_v1`
  - `overnight_v1`
  - `condition_entry_v1`
  - `condition_exit_v1`
  - `eod_top5_v1`

### 2.2 Gemini parity 정렬

- `src/engine/ai_engine.py`
- 기존 Gemini in-file registry를 제거하고 공용 registry alias로 교체
- `_resolve_gemini_response_schema()`가 공용 resolver를 사용하도록 정리

### 2.3 OpenAI Responses transport 재편

- `src/engine/ai_engine_openai.py`
- `_call_openai_safe()`가 기존 Chat Completions 중심 경로에서 `OpenAIResponseRequest -> transport -> parsed payload` 구조로 재편됨
- HTTP path는 `client.responses.create(...)` 기반으로 변경
- WebSocket path는 `OpenAIResponsesWSWorker`, `OpenAIResponsesWSPool`로 분리
- transport meta를 thread-local에 기록하고, 분석 결과 payload에 병합 가능하도록 정리

### 2.4 Endpoint별 schema_name wiring

- `analyze_target` / `analyze_target_shadow_prompt`
  - 기본 `entry_v1`
  - `scalping_holding`, `scalping_exit`는 `holding_exit_v1`
- `evaluate_scalping_overnight_decision` -> `overnight_v1`
- `evaluate_condition_entry` -> `condition_entry_v1`
- `evaluate_condition_exit` -> `condition_exit_v1`
- `generate_eod_tomorrow_bundle` -> `eod_top5_v1`

### 2.5 운영 flag / env override 추가

- `src/utils/constants.py`
- 기본값 추가:
  - `OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED`
  - `OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED`
  - `OPENAI_TRANSPORT_MODE`
  - `OPENAI_RESPONSES_WS_ENABLED`
  - `OPENAI_RESPONSES_WS_POOL_SIZE`
  - `OPENAI_RESPONSES_WS_TIMEOUT_MS`
  - `OPENAI_RESPONSES_WS_LATE_DISCARD_ENABLED`
  - `OPENAI_ENTRY_TIMEOUT_REJECT_ENABLED`
  - `OPENAI_PREVIOUS_RESPONSE_ID_ENABLED`
- env override 추가:
  - `KORSTOCKSCAN_OPENAI_*`

### 2.6 Shadow 운영 문서 반영

- `docs/2026-05-04-stage2-todo-checklist.md`
- `docs/workorder-shadow-canary-runtime-classification.md`
- `openai_responses_ws_shadow_flag_off` observe-only cohort 추가

## 3. 리뷰 포인트

### 3.1 계약/호출 경계

- OpenAI JSON path가 endpoint별 schema registry를 실제로 타는지
- text/report path에는 deterministic JSON config와 structured schema가 섞이지 않는지
- `previous_response_id`가 phase 1 기본값에서 요청 payload에 실리지 않는지

### 3.2 Hot path fallback

- WS timeout / parse failure / late response 시 buy-side가 보수적으로 닫히는지
- `analyze_target`는 `DROP`
- `condition_entry`는 `SKIP`
- late response가 live decision으로 반영되지 않고 discard metric으로만 집계되는지

### 3.3 Transport safety

- request/response correlation이 `request_id` 기준으로만 유지되는지
- WS fallback이 동일 request contract를 들고 HTTP Responses로 내려가는지
- phase 1 scope 밖 endpoint가 WS로 우발 전환되지 않는지

## 4. 검증 결과

- `py_compile` 통과
- OpenAI schema registry wiring 스모크 통과
- WS -> HTTP fallback 스모크 통과
- buy-side timeout reject 스모크 통과
- checklist parser 검증 통과
- env override 스모크 통과

검증에 사용한 대표 확인값:

- schema mock 응답 fallback extractor 확인: `BUY True json_object`
- WS fallback meta 확인: `BUY True http`
- buy-side timeout reject 확인: `DROP 0 True`
- env override 확인: `responses_ws True 4`

## 5. 테스트 상태

- 추가 테스트 파일:
  - `src/tests/test_ai_engine_openai_transport.py`
- 검증 항목:
  - endpoint schema wiring
  - JSON deterministic config scope
  - `previous_response_id` 기본 OFF
  - buy-side timeout reject
  - WS worker round-robin
  - WS -> HTTP fallback

제약:

- `.venv`에 `pytest`가 없어 실제 `pytest` 실행은 이번 턴에 수행하지 못했다.
- 확인 결과: `pytest_installed False`

## 6. 잔여 리스크

- WS worker 구현이 SDK의 low-level event path와 private connection attribute에 일부 의존한다.
  - 현재 구현은 `client.responses.connect()`를 우선 사용하지만, 내부 수신은 `_connection.recv(...)`를 사용한다.
  - SDK minor change 시 회귀 가능성이 있어 shadow-only 관측이 선행되어야 한다.
- 실제 live 부하에서 queue wait / reconnect storm / parse_fail 분포는 아직 검증 전이다.
- `pytest` 부재로 테스트 파일의 정식 회귀는 아직 CI 또는 서버 환경에서 다시 확인해야 한다.

## 7. 추천 검토 순서

1. `src/tests/test_ai_engine_openai_transport.py` 기준으로 schema/transport 계약 검토
2. `src/engine/ai_engine_openai.py`의 `_call_openai_safe()`, `OpenAIResponseRequest`, `OpenAIResponsesWSPool` 구현 검토
3. `docs/2026-05-04-stage2-todo-checklist.md`의 shadow pass/fail 기준 검토
4. 서버 환경에서 `pytest` 및 shadow 관측값 확인 후 main 병합 여부 결정

## 8. 다음 액션

- 서버 검토 단계에서는 아래를 우선 확인한다.
  - `request_id mismatch=0`
  - `late_discard=0`
  - `http fallback<=2%`
  - `parse_fail<=0.5%`
  - HTTP baseline 대비 roundtrip 개선 여부
- main 병합 전에는 `pytest` 가능한 환경에서 `src/tests/test_ai_engine_openai_transport.py`와 기존 OpenAI audit/config 테스트를 함께 재실행하는 것을 권장한다.
