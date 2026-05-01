# 2026-05-04 Stage2 To-Do Checklist

## 오늘 목적

- `ai_engine_openai.py`가 `ai_engine.py`와 같은 endpoint schema registry/contract 기준을 따르는지 장전 로드로 닫는다.
- `OpenAI Responses WS`는 live 전환이 아니라 `shadow-first flag-off` 기준으로 queue/timeout/fallback/request_id 정합성만 관찰한다.
- phase1 WS 범위는 `analyze_target`, `analyze_target_shadow_prompt`, `condition_entry`, `condition_exit`로만 잠그고 `realtime_report/gatekeeper/overnight/EOD`는 HTTP 유지로 분리한다.
- BUY-side timeout/parse failure/late response는 `DROP/SKIP` 보수 폴백으로만 처리하고, `previous_response_id`는 종목 간 상태 오염 방지 차원에서 금지한다.
- `soft_stop_expert_defense v2`는 `2026-04-30` same-day 수집 후 기본 OFF다. 다음 보유/청산 신규 owner는 v2 재가동이 아니라 `GOOD_EXIT` 제거를 피하는 refined `bad_entry` canary다.
- 스캘핑 신규 BUY 최대매수가능 주수는 `1주 cap`이다. 5/4 장전에는 `SCALPING_INITIAL_ENTRY_MAX_QTY=1` 로드와 env override 오염 여부를 확인한다.
- 물타기/불타기 `MAX_*_COUNT`는 더 이상 runtime blocker가 아니라 attribution counter다. 반복 추가매수 리스크는 enable flag, cooldown, pending order, position cap, protection 재설정, near-close gate로 제한한다.
- `stat_action_decision_snapshot`은 observe-only다. live 판단 변경 없이 HOLDING 의사결정 순간의 후보/선택/차단 행동을 compact stream에 남긴다.
- threshold cycle은 `07:35 PREOPEN apply manifest`, `16:10 POSTCLOSE collector/report`가 자동 실행된다. 5/6 운영전환 acceptance 전까지 live runtime mutation은 `manifest_only`다.

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
- `bad_entry` 신규 canary는 naive block 금지다. `2026-04-30` 장후에 코드/테스트는 준비했고, 5/4 장전에는 런타임 로드와 cohort tag만 확인한다.
- threshold 자동화는 장전 manifest와 장후 report 생성까지만 허용한다. `ThresholdOpsTransition0506` 전에는 자동 threshold live 적용이나 봇 재기동 정책 변경을 열지 않는다.

## 장전 체크리스트 (08:15~08:55)

- [ ] `[RuntimeFlagInventory0504-Preopen] ON/OFF runtime flag inventory 및 OFF축 ON 기준 로드 확인` (`Due: 2026-05-04`, `Slot: PREOPEN`, `TimeWindow: 08:15~08:20`, `Track: RuntimeStability`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `2026-05-01` 기준 runtime ON/OFF 스냅샷과 실제 `TradingConfig`/env override를 비교한다. 실주문 영향 ON, observe/report-only ON, guarded-off/OFF를 구분하고, OFF 축은 owner/cohort/rollback/restart 기준 없이 장전 임의 ON 금지로 잠근다.
  - 현재 실주문 영향 ON: `mechanical_momentum_latency_relief`, `soft_stop_micro_grace`, `REVERSAL_ADD`, `bad_entry_refined_canary`, `initial_entry_qty_cap_1share`, `pre_submit_price_guard`, `partial_fill_ratio_guard`, `dynamic_vpw`, `dynamic_strength_relief`, `SCALPING_ENABLE_PYRAMID`.
  - 현재 observe/report-only ON: `stat_action_decision_snapshot`, `statistical_action_weight`, `holding_exit_decision_matrix`, `threshold_cycle manifest/report`, `hard_time_stop_shadow`, `same_symbol_soft_stop_cooldown_shadow`, `partial_only_timeout_shadow`, `SCALP_LOSS_FALLBACK observe-only`.
  - 현재 OFF/guarded-off: `soft_stop_expert_defense v2`, `soft_stop_micro_grace_extend`, `latency_quote_fresh_composite`, `latency_signal_quality_quote_composite`, `latency_spread_relief`, `latency_ws_jitter_relief`, `latency_other_danger_relief`, `latency_guard_canary`, `latency_fallback/split_entry`, generic `SCALPING_ENABLE_AVG_DOWN`, `SCALPING_PYRAMID_ZERO_QTY_STAGE1`, `OpenAI Responses WS`, `OpenAI dual persona`, `OpenAI schema registry/deterministic config`.
  - 다음 액션: OFF 축을 켜야 한다면 이 항목에서 바로 ON하지 않고, 해당 축별 ON 시점/기준을 [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)의 `0.1 Runtime ON/OFF 스냅샷`과 대조해 단일축 checklist 항목으로 분리한다.

- [ ] `[StatActionDecisionSnapshot0504-Preopen] 행동 후보 decision snapshot observe-only 로드 확인` (`Due: 2026-05-04`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:25`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [threshold_cycle_registry.py](/home/ubuntu/KORStockScan/src/utils/threshold_cycle_registry.py), [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md)
  - 판정 기준: `STAT_ACTION_DECISION_SNAPSHOT_ENABLED=True`, `STAT_ACTION_DECISION_SNAPSHOT_MIN_INTERVAL_SEC=30` 기본 로드와 env override 오염 여부를 확인한다. stage `stat_action_decision_snapshot`은 family `statistical_action_weight`로 compact 적재되어야 한다.
  - why: 통계 행동가중치는 실제 선택 행동만으로는 selection bias가 커진다. HOLDING 판단 순간의 `eligible_actions`, `rejected_actions`, `chosen_action`, 수익률/고점/AI/수급/호가 상태를 같이 남겨야 `exit_now`, `avg_down_wait`, `pyramid_wait`, `hold_wait`의 counterfactual 근거가 생긴다.
  - 다음 액션: 장중에는 live 행동 변경 없이 snapshot 적재 여부와 IO 증가만 확인한다. 과다 적재가 보이면 env로 interval을 늘리거나 snapshot을 OFF한다.

- [ ] `[ScaleInCountGateRemoval0504-Preopen] 물타기/불타기 count gate 제거 로드 확인` (`Due: 2026-05-04`, `Slot: PREOPEN`, `TimeWindow: 08:25~08:30`, `Track: ScalpingLogic`)
  - Source: [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `avg_down_count`/`pyramid_count`가 주문 가능 여부를 막지 않고 집계/귀속값으로만 남는지 확인한다. `SCALPING_ENABLE_AVG_DOWN`, `SCALPING_ENABLE_PYRAMID`, `SWING_ENABLE_AVG_DOWN`, `SWING_ENABLE_PYRAMID`는 enable/disable owner로만 본다.
  - why: `REVERSAL_ADD`와 `PYRAMID` 실행 표본이 count cap에 막히면 데이터 기반 threshold/weight 산정이 공회전한다. 다만 반복 주문 리스크는 count가 아니라 cooldown, pending order, position cap, protection 재설정 실패 fail-closed로 제한한다.
  - 다음 액션: 로드 확인 후 후보가 계속 0이면 count가 아니라 `pnl/hold/supply/qty/position_cap/cooldown/pending/protection` blocker로 분해한다.

- [ ] `[BadEntryRefinedCanary0504-Preopen] refined bad_entry canary 설계/로드 승인` (`Due: 2026-05-04`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:40`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-30-stage2-todo-checklist.md), [personal-decision-flow-notes.md](/home/ubuntu/KORStockScan/docs/personal-decision-flow-notes.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: `soft_stop_expert_defense v2` 기본 OFF를 확인하고, `bad_entry_block_observed` 2026-04-30 최종 outcome(`unique 32`, 후행 sell completed `30`, 평균 `-0.961%`, 손실 `22/30`, soft stop `20/30`, GOOD_EXIT `13`)을 기준으로 naive block이 아니라 refined canary 조건을 잠근다.
  - 구현 상태 (`2026-04-30 장후`): `src/utils/constants.py` 기본값으로 `SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED=True`, `held_sec>=180`, `profit_rate<=-1.16`, `peak_profit<=+0.05`, `AI<=45`, `recovery_prob_shadow<=0.30`을 반영했다. `src/engine/sniper_state_handlers.py`는 `scalp_bad_entry_refined_canary`를 `soft_stop` 전 조기정리 rule로 적용하고, `bad_entry_refined_candidate`/`bad_entry_refined_exit` stage를 남긴다.
  - refined canary 확정조건: `held_sec>=180`, `profit_rate<=-1.16`, `peak_profit<=+0.05`, `AI<=45`를 기본 anchor로 두고, `recovery_prob_shadow<=0.30` 또는 thesis invalidation/adverse fill 동반 시에만 live 후보로 본다. `current_ai_score` 회복, positive peak 확대, `REVERSAL_ADD/POST_ADD_EVAL`, active sell pending, emergency/hard stop, 기존 soft stop zone은 제외한다.
  - why: v2는 absorption 유예 성공 표본이 없어 지속하지 않는다. 그러나 bad-entry 후보군은 비후보보다 손익과 soft stop 전환이 나빠 EV 개선 후보가 맞으므로, `GOOD_EXIT` 제거를 피하는 더 좁은 단일축 canary가 시급하다.
  - rollback guard: canary 적용 cohort의 `COMPLETED + valid profit_rate` 평균이 비적용 후보보다 `-0.20%p` 이상 악화, `GOOD_EXIT/MISSED_UPSIDE` would-have-been 증가, `sell_order_failed`, `reversal_add_used` 혼입 1건 이상이면 즉시 OFF한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py -k 'bad_entry_refined or bad_entry_block_observe or soft_stop_micro_grace'` -> `6 passed`
  - 다음 액션: 장전에는 코드 구현이 아니라 `TradingConfig`/env override 로드, `soft_stop_expert_defense=False`, `bad_entry_refined=True`, cohort tag/event stage 적재 여부만 확인한다. 미승인 시 observe-only 유지가 아니라 즉시 threshold/refined rule을 다시 좁힌다.

- [ ] `[OpenAIParity0504-Preopen] OpenAI schema registry/transport flag 로드 확인` (`Due: 2026-05-04`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:50`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-openai-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/2026-04-30-openai-enable-acceptance-spec.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: `OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED`, `OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED`, `OPENAI_TRANSPORT_MODE`, `OPENAI_RESPONSES_WS_ENABLED`, `OPENAI_PREVIOUS_RESPONSE_ID_ENABLED=False`가 코드/런타임 provenance로 확인되고, endpoint별 schema 매핑(`entry/holding_exit/overnight/condition/eod`)이 테스트 기준과 일치한다.
  - why: OpenAI parity는 live alpha 확장이 아니라 계약 정합성과 transport provenance 잠금이 먼저다.
  - cohort: `baseline cohort=OpenAI HTTP live contract`, `candidate live cohort=none`, `observe-only cohort=openai_responses_ws_shadow_flag_off`, `excluded cohort=realtime_report/gatekeeper/overnight/EOD text path`, `rollback owner=OPENAI_TRANSPORT_MODE`, `cross-contamination check=entry transport 결과를 gatekeeper/eod 판정에 합산 금지`
  - 다음 액션: 로드 확인 후 장중에는 WS enable이 아니라 shadow-only queue/timeout/fallback 관찰로 이어가고, `JSON deterministic config`/`schema registry`는 계속 flag-off acceptance로만 유지한다.

## 장중 체크리스트 (10:00~10:20)

- [ ] `[BadEntryRefinedCanary0504-1030] refined bad_entry canary 1차 health check` (`Due: 2026-05-04`, `Slot: INTRADAY`, `TimeWindow: 10:30~10:45`, `Track: ScalpingLogic`)
  - Source: [2026-05-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-04-stage2-todo-checklist.md), [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-30-stage2-todo-checklist.md)
  - 판정 기준: 적용 시 `bad_entry_refined_candidate`, `bad_entry_refined_exit`, 후보별 `exclusion_reason`, 후속 `soft_stop/trailing/COMPLETED + valid profit_rate`, `GOOD_EXIT/MISSED_UPSIDE` would-have-been, `REVERSAL_ADD` 혼입을 확인한다. 미적용 시 후보가 왜 0인지 threshold/gate/blocker를 분해한다.
  - why: 2026-04-30에 `REVERSAL_ADD` 체결 0과 v2 OFF가 확인됐으므로, 다음 보유/청산 owner가 또 관찰만 반복되면 soft stop tail을 줄이지 못한다.
  - 다음 액션: 후보가 있으나 적용 0이면 같은 날 threshold/gate를 재분해하고, 적용 후 손실/GOOD_EXIT 제거 신호가 있으면 즉시 OFF한다.

- [ ] `[OpenAIResponsesWS0504-Intraday] OpenAI Responses WS shadow queue/timeout/fallback 1차 판정` (`Due: 2026-05-04`, `Slot: INTRADAY`, `TimeWindow: 10:00~10:20`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-openai-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/2026-04-30-openai-enable-acceptance-spec.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `openai_ws_requests`, `openai_ws_completed`, `openai_ws_timeout_reject`, `openai_ws_late_discard`, `openai_ws_parse_fail`, `openai_ws_http_fallback`, `openai_ws_request_id_mismatch`, `openai_ws_queue_wait_ms`, `openai_ws_roundtrip_ms`를 shadow-only로 확인한다. `request_id_mismatch=0`, `late_discard=0`이 아니면 same-day live 검토 금지다.
  - why: 초당 반복 판단에서는 성능보다 먼저 request/response 정합성과 늦은 응답 폐기가 닫혀야 한다.
  - cohort: `baseline cohort=HTTP responses hot path`, `candidate live cohort=none`, `observe-only cohort=openai_responses_ws_shadow_flag_off`, `excluded cohort=full/partial fill 및 COMPLETED 손익 직접 판정`, `rollback owner=OPENAI_RESPONSES_WS_ENABLED`, `cross-contamination check=WS shadow 결과를 제출/체결 EV와 직접 합산 금지`
  - 다음 액션: `http fallback<=2%`, `parse_fail<=0.5%`, `timeout_reject_rate<=1%`가 아니면 POSTCLOSE에 shadow 유지/원인분해만 남기고, `previous_response_id` 재사용 검토는 backlog로 유지한다.

## 장후 체크리스트 (16:20~16:40)

- [ ] `[BadEntryRefinedCanary0504-Postclose] refined bad_entry canary keep/OFF 판정` (`Due: 2026-05-04`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:20`, `Track: ScalpingLogic`)
  - Source: [2026-05-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-04-stage2-todo-checklist.md), [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-30-stage2-todo-checklist.md)
  - 판정 기준: canary 적용/비적용 refined bad-entry 후보를 `COMPLETED + valid profit_rate`, `soft_stop`, `trailing`, `GOOD_EXIT`, `MISSED_UPSIDE`, `same-symbol reentry`, `sell_order_failed`로 비교한다. `full/partial`, `initial/pyramid`, `REVERSAL_ADD` 체결 포지션은 합산하지 않는다.
  - why: refined canary는 v2 계층화 전략의 다음 실행축이다. 성공 여부는 단순 손실 축소가 아니라 winner 제거 없이 bad-entry 손실 tail을 줄였는지로 닫아야 한다.
  - 다음 액션: keep이면 다음 운영일 baseline 승격이 아니라 1일 추가 canary로 유지하고, OFF면 `adverse fill detector` 또는 `MAE/MFE quantile stop` 중 다음 계층을 단일축 후보로 재선정한다.

- [ ] `[OpenAIResponsesWS0504-Postclose] OpenAI transport shadow 유지/교체 판정` (`Due: 2026-05-04`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:40`, `Track: Plan`)
  - Source: [2026-04-30-openai-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/2026-04-30-openai-enable-acceptance-spec.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: HTTP baseline 대비 `openai_ws_roundtrip_ms p50` 개선 여부, `request_id_mismatch=0`, `late_discard=0`, `http fallback<=2%`, `parse_fail<=0.5%`, `timeout_reject_rate<=1%`를 닫는다. 하나라도 미충족이면 `observe-only 유지`로 고정한다.
  - why: 이번 change set의 목적은 live 전환이 아니라 동일 계약 parity와 shadow transport 안정성 확인이다.
  - cohort: `baseline cohort=OpenAI HTTP`, `candidate live cohort=none`, `observe-only cohort=openai_responses_ws_shadow_flag_off`, `excluded cohort=Gemini/DeepSeek routing 비교`, `rollback owner=OPENAI_TRANSPORT_MODE + OPENAI_RESPONSES_WS_ENABLED`, `cross-contamination check=transport 판정과 strategy alpha 판정 분리`
  - 다음 액션: 변경이 있으면 checklist와 [2026-04-30-openai-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/2026-04-30-openai-enable-acceptance-spec.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)를 같이 갱신하고, parser 검증 후 사용자 수동 sync 명령 1개만 남긴다.
