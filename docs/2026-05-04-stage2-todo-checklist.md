# 2026-05-04 Stage2 To-Do Checklist

## 오늘 목적

- `ai_engine_openai.py`가 `ai_engine.py`와 같은 endpoint schema registry/contract 기준을 따르는지 장전 로드로 닫는다.
- `OpenAI Responses WS`는 live 전환이 아니라 `shadow-first flag-off` 기준으로 queue/timeout/fallback/request_id 정합성만 관찰한다.
- phase1 WS 범위는 `analyze_target`, `analyze_target_shadow_prompt`, `condition_entry`, `condition_exit`로만 잠그고 `realtime_report/gatekeeper/overnight/EOD`는 HTTP 유지로 분리한다.
- BUY-side timeout/parse failure/late response는 `DROP/SKIP` 보수 폴백으로만 처리하고, `previous_response_id`는 종목 간 상태 오염 방지 차원에서 금지한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 동일 단계 내 `1축 canary`만 허용한다. 진입병목축과 보유/청산축은 별개 단계이므로 병렬 canary가 가능하지만, 같은 단계 안에서는 canary 중복을 금지한다.
- 동일 단계 replacement는 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
- 관찰창이 끝나면 `즉시 판정 -> 다음 축 즉시 착수`를 기본으로 한다. 이미 수집된 데이터로 닫을 수 있는 판정은 장후/익일로 미루지 않는다.
- `장후/익일/다음 장전` 이관은 예외사유 4종(`단일 조작점 미정`, `rollback guard 미문서화`, `restart/code-load 불가`, `운영 경계상 same-day 반영 불가`) 중 하나로만 허용한다. 막힌 조건과 다음 절대시각이 없으면 이관 판정은 무효다.
- PREOPEN은 전일에 이미 `단일 조작점 + rollback guard + 코드/테스트 + restart 절차`가 준비된 carry-over 축만 받는다.
- 일정은 모두 `YYYY-MM-DD KST`, `Slot`, `TimeWindow`로 고정한다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- live 승인, replacement, stage-disjoint 예외, 관찰 개시 판정에는 `cohort`를 같이 잠근다. 최소 `baseline cohort`, `candidate live cohort`, `observe-only cohort`, `excluded cohort`를 구분하고 `partial/full`, `initial/pyramid`, `fallback` 혼합 결론을 금지한다.
- `ApplyTarget`은 문서에 명시된 값만 사용하고, parser/workorder가 `remote`를 추정하지 않도록 유지한다.
- 다축 동시 변경 금지, 승인 전 `main` 실주문 변경 금지 규칙을 유지한다.
- `openai_responses_ws_shadow_flag_off`는 `observe-only`다. `request_id mismatch`, `late discard`, `http fallback`, `timeout reject`는 shadow 판정 근거로만 쓰고 실주문 go/no-go에는 직접 사용하지 않는다.

## 장전 체크리스트 (08:40~08:55)

- [ ] `[OpenAIParity0504-Preopen] OpenAI schema registry/transport flag 로드 확인` (`Due: 2026-05-04`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:50`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/windy80xyt/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [workorder-shadow-canary-runtime-classification.md](/home/windy80xyt/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: `OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED`, `OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED`, `OPENAI_TRANSPORT_MODE`, `OPENAI_RESPONSES_WS_ENABLED`, `OPENAI_PREVIOUS_RESPONSE_ID_ENABLED=False`가 코드/런타임 provenance로 확인되고, endpoint별 schema 매핑(`entry/holding_exit/overnight/condition/eod`)이 테스트 기준과 일치한다.
  - why: OpenAI parity는 live alpha 확장이 아니라 계약 정합성과 transport provenance 잠금이 먼저다.
  - cohort: `baseline cohort=OpenAI HTTP live contract`, `candidate live cohort=none`, `observe-only cohort=openai_responses_ws_shadow_flag_off`, `excluded cohort=realtime_report/gatekeeper/overnight/EOD text path`, `rollback owner=OPENAI_TRANSPORT_MODE`, `cross-contamination check=entry transport 결과를 gatekeeper/eod 판정에 합산 금지`
  - 다음 액션: 로드 확인 후 장중에는 WS enable이 아니라 shadow-only queue/timeout/fallback 관찰로 이어간다.

## 장중 체크리스트 (10:00~10:20)

- [ ] `[OpenAIResponsesWS0504-Intraday] OpenAI Responses WS shadow queue/timeout/fallback 1차 판정` (`Due: 2026-05-04`, `Slot: INTRADAY`, `TimeWindow: 10:00~10:20`, `Track: ScalpingLogic`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/windy80xyt/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/windy80xyt/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `openai_ws_requests`, `openai_ws_completed`, `openai_ws_timeout_reject`, `openai_ws_late_discard`, `openai_ws_parse_fail`, `openai_ws_http_fallback`, `openai_ws_request_id_mismatch`, `openai_ws_queue_wait_ms`, `openai_ws_roundtrip_ms`를 shadow-only로 확인한다. `request_id_mismatch=0`, `late_discard=0`이 아니면 same-day live 검토 금지다.
  - why: 초당 반복 판단에서는 성능보다 먼저 request/response 정합성과 늦은 응답 폐기가 닫혀야 한다.
  - cohort: `baseline cohort=HTTP responses hot path`, `candidate live cohort=none`, `observe-only cohort=openai_responses_ws_shadow_flag_off`, `excluded cohort=full/partial fill 및 COMPLETED 손익 직접 판정`, `rollback owner=OPENAI_RESPONSES_WS_ENABLED`, `cross-contamination check=WS shadow 결과를 제출/체결 EV와 직접 합산 금지`
  - 다음 액션: `http fallback<=2%`, `parse_fail<=0.5%`, `timeout_reject_rate<=1%`가 아니면 POSTCLOSE에 shadow 유지/원인분해만 남긴다.

## 장후 체크리스트 (16:20~16:40)

- [ ] `[OpenAIResponsesWS0504-Postclose] OpenAI transport shadow 유지/교체 판정` (`Due: 2026-05-04`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:40`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/windy80xyt/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: HTTP baseline 대비 `openai_ws_roundtrip_ms p50` 개선 여부, `request_id_mismatch=0`, `late_discard=0`, `http fallback<=2%`, `parse_fail<=0.5%`, `timeout_reject_rate<=1%`를 닫는다. 하나라도 미충족이면 `observe-only 유지`로 고정한다.
  - why: 이번 change set의 목적은 live 전환이 아니라 동일 계약 parity와 shadow transport 안정성 확인이다.
  - cohort: `baseline cohort=OpenAI HTTP`, `candidate live cohort=none`, `observe-only cohort=openai_responses_ws_shadow_flag_off`, `excluded cohort=Gemini/DeepSeek routing 비교`, `rollback owner=OPENAI_TRANSPORT_MODE + OPENAI_RESPONSES_WS_ENABLED`, `cross-contamination check=transport 판정과 strategy alpha 판정 분리`
  - 다음 액션: 변경이 있으면 checklist와 [workorder-shadow-canary-runtime-classification.md](/home/windy80xyt/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)를 같이 갱신하고, parser 검증 후 사용자 수동 sync 명령 1개만 남긴다.
