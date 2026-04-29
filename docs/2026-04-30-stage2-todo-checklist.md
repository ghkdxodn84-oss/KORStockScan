# 2026-04-30 Stage2 To-Do Checklist

## 오늘 목적

- `pre-submit price guard`와 `price snapshot split`이 장전 restart 후 메인 런타임에 정상 로드됐는지 닫는다.
- `mechanical_momentum_latency_relief` 운영 override가 전일 장중 반영된 상태라면 장전에는 코드/런타임 provenance만 확인하고, 실전 성과는 장중 post-restart cohort로 분리한다.
- 이번주 다음 운영일은 `2026-05-01`이 아니라 `2026-05-04`다. KRX는 근로자의 날(5/1) 휴장이고, `2026-05-05` 어린이날도 휴장이므로 다음주 휴장 이월 항목은 `2026-05-06` checklist가 소유한다.
- 대한전선 진입가 후속조치는 신규 alpha 진입축이 아니라 비정상 저가 제출 차단과 감리 추적성 보강으로만 해석한다.
- `P0` 가드의 day-1 KPI와 rollback trigger를 장후 바로 잠가, 임의 임계값 고착을 막는다.
- `P1 resolver`와 `schema split`은 same-day live 확장이 아니라 observe/backtest ingress 조건 확정으로만 넘긴다.
- soft stop 감소 접근은 `micro grace 시간연장`보다 `REVERSAL_ADD 소형 canary`와 `bad_entry_block observe-only classifier`로 전략 가설을 분리한다.

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
- `mechanical_momentum_latency_relief`는 AI score 50/70 mechanical fallback 상태의 제출 drought를 푸는 entry 1축이다. `latency_signal_quality_quote_composite`, `latency_quote_fresh_composite`, legacy `other_danger/ws_jitter/spread` relief와 동시에 켜지 않으며, 장전에는 enable flag와 restart provenance만 확인한다.
- `REVERSAL_ADD`는 entry canary가 아니라 보유 중 `position_addition` canary다. `soft_stop_micro_grace`와 같은 보유 포지션을 건드리므로 cohort를 반드시 분리하고, `reversal_add_used` 이후 soft stop 악화가 보이면 즉시 OFF 후보로 본다.
- `bad_entry_block`은 observe-only다. `2026-04-30`에는 진입 자체를 막지 않고 `bad_entry_block_observed` 로그와 후속 soft stop/하드스탑/회복 여부만 본다.

## 장전 체크리스트 (08:45~08:55)

- [ ] `[MechanicalMomentumLatencyRelief0430-Preopen] mechanical_momentum_latency_relief 코드/런타임 로드 확인` (`Due: 2026-04-30`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: main bot PID와 `/proc/<pid>/environ` 또는 import check로 `latency_quote_fresh_composite=False`, `latency_signal_quality_quote_composite=False`, `mechanical_momentum_latency_relief=True` 로드 여부를 확인한다. threshold는 `signal_score<=75`, `latest_strength>=110`, `buy_pressure_10t>=50`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False`로 고정한다.
  - why: 이 축은 신규 alpha 확장이 아니라 제출 drought를 방치하지 않기 위한 운영 override다. PREOPEN에서는 same-day submitted/fill 성과가 아니라 단일축 로드와 rollback guard만 확인한다.
  - rollback guard: 장중 새 cohort에서 `budget_pass >= 150`인데 `submitted <= 2`면 효과 미약으로 OFF 검토를 연다. `pre_submit_price_guard_block_rate > 2.0%`, `fallback_regression > 0`, `normal_slippage_exceeded` 반복, 또는 canary cohort 일간 합산 손익이 당일 스캘핑 배정 NAV 대비 `<= -0.35%`이면 즉시 OFF 후보로 본다.
  - 다음 액션: 로드 확인 후 장중 `[MechanicalMomentumLatencyRelief0430-1000]`에서 `mechanical_momentum_relief_canary_applied`, `latency_mechanical_momentum_relief_normal_override`, `submitted/full/partial`, `COMPLETED + valid profit_rate`를 분리한다.

- [ ] `[DynamicEntryPriceP0Guard0430-Preopen] pre-submit price guard + price snapshot split 구현/검증` (`Due: 2026-04-30`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:55`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: main bot restart provenance를 확인하고, `SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED=True`, `SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS=80` 로드 여부와 `latency_pass/order_leg_request/order_bundle_submitted/pre_submit_price_guard_block` 가격 스냅샷 필드 기록 여부를 확인한다.
  - why: 대한전선 케이스는 신규 alpha canary가 아니라 비정상 저가 제출을 막는 안전가드와 감리 추적성 보강이다. PREOPEN에서는 same-day submitted/fill 성과가 아니라 코드 로드, restart, 이벤트 필드 기록 가능성만 확인한다.
  - 다음 액션: 장전 로드가 확인되면 장중에는 `pre_submit_price_guard_block` 발생 여부와 `submitted_order_price`, `best_bid_at_submit`, `price_below_bid_bps`, `resolution_reason` 품질만 관찰한다. 로드 실패 시 P0 guard를 OFF한 채로 두지 말고 restart/provenance 원인을 우선 수정한다.

- [ ] `[ReversalAddBadEntry0430-Preopen] REVERSAL_ADD 소형 canary 및 bad_entry_block observe-only 로드 확인` (`Due: 2026-04-30`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: main bot restart provenance를 확인하고 `REVERSAL_ADD_ENABLED=True`, `REVERSAL_ADD_MIN_QTY_FLOOR_ENABLED=True`, `REVERSAL_ADD_SIZE_RATIO=0.33`, `SCALP_BAD_ENTRY_BLOCK_OBSERVE_ENABLED=True` 로드 여부를 확인한다.
  - why: `micro grace 20초`만으로는 soft stop 감소 전략의 설득력이 약하다. `2026-04-30` 오전부터는 `유효 진입 초반 눌림 회수`와 `불량 진입 후보 분류`를 별도 가설로 관찰해야 한다.
  - rollback guard: `reversal_add_used` 후 `scalp_soft_stop_pct` 전환이 발생하거나, `reversal_add` 체결 cohort의 `COMPLETED + valid profit_rate` 평균이 `<= -0.30%`이면 장중 OFF 후보로 본다. `bad_entry_block`은 observe-only라 주문 차단이나 청산 변경을 하지 않는다.
  - 다음 액션: 로드 확인 후 장중 `[ReversalAddBadEntry0430-1030]`에서 `reversal_add_candidate`, `reversal_add_used`, `scale_in_executed add_type=AVG_DOWN`, `bad_entry_block_observed`, 후속 `soft_stop/trailing/COMPLETED`를 분리한다.

## 장중 체크리스트 (09:00~15:20)

- [ ] `[MechanicalMomentumLatencyRelief0430-1000] mechanical_momentum_latency_relief 10시 1차 판정` (`Due: 2026-04-30`, `Slot: INTRADAY`, `TimeWindow: 10:00~10:15`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `09:00~10:00` 또는 새 restart 이후 창 기준 `budget_pass`, `mechanical_momentum_relief_canary_applied`, `latency_mechanical_momentum_relief_normal_override`, `submitted`, `full_fill`, `partial_fill`, `pre_submit_price_guard_block`, `fallback_regression=0`를 확인한다. `full fill`과 `partial fill`은 분리한다.
  - why: 이 축은 거래수 회복을 위한 운영 override라 오전 1시간 안에 최소 방향성은 나와야 한다. `submitted`가 움직이지 않으면 같은 날 추가 유지 근거가 약하다.
  - 다음 액션: 제출 회복이 있으면 12시 full 창으로 유지판정하고, `budget_pass >= 150`인데 `submitted <= 2`면 장중 OFF/다음축 재분해를 연다.

- [ ] `[ReversalAddBadEntry0430-1030] REVERSAL_ADD/bad_entry_block 오전 1차 관찰` (`Due: 2026-04-30`, `Slot: INTRADAY`, `TimeWindow: 10:30~10:45`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `09:00~10:30` 창에서 `reversal_add_candidate`, `reversal_add_blocked_reason`, `scale_in_executed add_type=AVG_DOWN`, `reversal_add_used`, `bad_entry_block_observed`, `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `COMPLETED + valid profit_rate`를 분리한다.
  - why: `2026-04-30` 오전을 단순 진단으로 허비하지 않기 위해, 유효 진입의 초반 눌림은 소형 추가매수로 실험하고 never-green/AI fade는 observe-only로 분류한다.
  - 다음 액션: `REVERSAL_ADD` 체결이 1건 이상이면 해당 record를 장중 anchor case로 고정하고 이후 soft stop 여부를 추적한다. 후보만 있고 체결이 없으면 `zero_qty`, `position_at_cap`, `supply_conditions_not_met`, `ai_not_recovering` 중 어느 blocker인지 닫는다. `bad_entry_block_observed`가 3건 이상이면 장후 classifier 승격 표본으로 보낸다.

## 장후 체크리스트 (16:00~20:00)

- [ ] `[DynamicEntryPriceP0Guard0430-Postclose] P0 guard KPI/rollback 1차 점검` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:20`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md), [2026-04-29-daehan-cable-entry-price-audit-followup.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-followup.md)
  - 판정 기준: same-day `pre_submit_price_guard_block_rate`, 전략별 제출 시도 수, `(best_bid - submitted_price)/best_bid` 분포 `p99`, `block 없이 통과한 deep bid` 재발 여부를 확인한다. 일간 차단율 `>0.5%`면 review trigger, `>2.0%`면 rollback 또는 threshold 완화 검토, `=0%`면 가드 비활성/로깅 누락 점검으로 닫는다.
  - why: P0는 가드를 켰다는 사실만으로 충분하지 않다. 운영 기준에서는 가드가 `너무 많이 막는지`, `아예 안 막는지`, `본 사고 유형을 실제로 막았는지`를 day-1부터 같이 봐야 한다.
  - 다음 액션: 차단율이 과도하면 `80bps` 임계를 provisional 값으로 재조정하고, 무차단 재발이 있으면 임계 강화 또는 resolver 우선 구현 검토로 승격한다. 전략별 표본이 부족하면 `2026-05-06` 분포 부록 항목과 연결해 rolling 7d 기준으로 재판정한다.

- [ ] `[CodeDebt0430] shadow/canary/cohort 런타임 분류/정리 판정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:35`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 대한전선 후속조치와 `pre-submit price guard`를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 중 변동이 필요한 항목이 있는지 닫고, entry price 후속 검증에 쓰는 cohort도 `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort / rollback owner / cross-contamination check`로 잠근다.
  - why: 이번 P0는 신규 alpha canary가 아니라 BUY 제출 안전가드다. cohort 분류를 문서와 같이 잠가야 `P0 guard`, `P1 resolver`, `P2 microstructure`가 서로 섞이지 않는다.
  - 실행 메모 (`2026-04-30 사후 rebasing`): code-review change set 기준으로 `RECEIPT_LOCK` 분리, `target_stock snapshot 전달`, `_sanitize_pending_add_states` 부작용 제거, startup 명시 sanitize, `describe_scale_in_qty` 규칙 테이블화, `holding elapsed` 공용 파서 정리, `handle_watching_state` 1차 분해, receipt 평균가 canonical(`round(..., 4)`) 정리, `_find_execution_target` 우선순위 테스트 고정, `ENTRY_LOCK/state_lock/RECEIPT_LOCK fallback` ownership 주석 반영까지 끝났다. 다만 이 항목의 본래 목적은 runtime cohort 분류와 롤아웃 가이드 잠금이므로, 코드 반영만으로 완료 처리하지 않고 `운영상 lock ownership guide + cohort 문서화`가 남은 상태로 유지한다.
  - 다음 액션: 상태 변경이 있으면 checklist와 관련 기준문서에 함께 반영하고, 변경이 없으면 `변동 없음`과 근거를 남긴다.

- [ ] `[GeminiSchemaIngress0430] Gemini flag-off schema registry 로드/contract 관찰` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~16:55`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-gemini-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/2026-04-29-gemini-enable-acceptance-spec.md), [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md)
  - 판정 기준: `GEMINI_RESPONSE_SCHEMA_REGISTRY_ENABLED=False` 기본값 유지, 6개 endpoint `schema_name` 연결 유지, `json.loads -> regex fallback` 회귀 없음, `test_ai_engine_api_config/test_ai_engine_cache` 통과 여부를 확인한다. `GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED`, `GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED`, `GEMINI_RESPONSE_SCHEMA_REGISTRY_ENABLED` live enable은 이 항목에서 켜지 않는다.
  - why: `main` Gemini는 실전 기준 엔진이라 오늘 반영한 묶음은 live enable이 아니라 flag-off load/contract 관찰 대상이다.
  - 다음 액션: 로드와 테스트가 정상이고 parse_fail 증가 근거가 없으면 `flag-off 유지 / 관찰 완료`로 닫는다. live enable 검토는 별도 canary 항목을 새로 만들어야 한다.

- [ ] `[DeepSeekRemoteAcceptance0430] DeepSeek retry acceptance log field 관찰` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:15`, `Track: Plan`)
  - Source: [2026-04-29-deepseek-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/2026-04-29-deepseek-enable-acceptance-spec.md), [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - 판정 기준: `DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED=False` 기본값 유지, retry 발생 시 `retry_acceptance={context_aware_backoff_enabled, live_sensitive, max_sleep_sec, lock_scope}` 로그 필드가 남는지 확인한다. gatekeeper structured-output은 여전히 `flag-off + text fallback + contract test` 없이는 구현 승격하지 않는다.
  - why: DeepSeek는 `remote` 경로라 오늘 반영한 묶음은 enable이 아니라 retry acceptance 관찰성 보강이다.
  - 다음 액션: 로그 필드가 확인되면 `flag-off 유지 / 관찰 완료`로 닫는다. retry 표본이 없으면 코드 로드와 테스트만 확인하고 다음 retry 발생 시 확인으로 이관한다.

- [ ] `[GeminiSchemaContractCarry0430] Gemini schema contract 충돌 항목 최종 판정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:35`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md](/home/ubuntu/KORStockScan/docs/2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `holding_exit_v1.action.enum`이 `HOLD/TRIM/EXIT`으로 정렬되고 `ai_engine.py:957` 정규화 경로와 충돌하지 않는지 확인한다. `eod_top5_v1` 필수 항목에 `rank`, `close_price`가 반영된 상태에서 `condition_*` 파싱 테스트가 무결한지, `test_ai_engine_api_config` 전체 통과를 확인한다.
  - why(필수): 실전 enable 시 `holding_exit_v1` 값 미스매칭은 `action_v2` fallback 오인을 유발해 관측 실패를 만들 수 있다.
  - 다음 액션: 정합성 확인 후 [2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md](/home/ubuntu/KORStockScan/docs/2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md) 기준 close 처리하고, 추적성 로그에서 동일 건(holding_exit/eod_top5)만 따로 추적해 잔차가 있는지 확인한다.

- [ ] `[DeepSeekAcceptanceCarry0430] DeepSeek retry acceptance 단일 스냅샷 경로 점검` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 17:35~17:55`, `Track: Plan`)
  - Source: [2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md](/home/ubuntu/KORStockScan/docs/2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md), [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - 판정 기준: `_build_retry_acceptance_snapshot()`과 `_call_deepseek_safe()`에서 `live_sensitive` 계산이 중복 없이 일관되게 유지되는지 확인하고, retry 외 경로의 노이즈 증분이 없는지 코드/테스트로 입증한다.
  - why(권장): 현재는 저위험 정합성 개선이므로, `2026-04-30` 장후 창에서 코드 정리 여유를 두고 패치 대기 가능하다.
  - 다음 액션: 중복 계산이 제거되면 `flag-off acceptance` 목표 유지 상태로 코드 정리 PR을 한 번에 반영한다.

- [ ] `[DeepSeekInterfaceGap0430] DeepSeek 공통 인터페이스 일치 점검` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 17:55~18:10`, `Track: Plan`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md), [2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md](/home/ubuntu/KORStockScan/docs/2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md)
  - 판정 기준: `GeminiSniperEngine`에만 존재하는 `analyze_condition_target`, `evaluate_condition_gatekeeper`를 호출부 관점에서 점검해 DeepSeek에서 동일 호출 패턴이 필요한지, 필요 시 wrapper/adapter 없이 진행 중인 caller를 분리하는지 확인한다.
  - why(권장): 인터페이스 차이는 즉시 장애보다 운영 관측 경로 혼재를 유발할 수 있으나, 현재는 증상성이 낮아 우선 순위 낮음.
  - 다음 액션: 공통 caller에서 실제 동시 호출이 확인되면 다음 운영일인 `2026-05-04`로 follow-up 축으로 넘기고, 아니면 관찰-only로 종료한다.

- [ ] `[TrailingContinuation0430] trailing continuation EV 재판정 및 candidate 승격 여부 확정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:25`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `제룡전기(033100)` trailing 익절, `덕산하이메탈(077360)` trailing 후 same-symbol reentry, 당일 `post_sell_evaluation` 생성 표본을 묶어 `GOOD_EXIT/MISSED_UPSIDE`, `same_symbol reentry`, `mfe_10m`, `peak-to-exit giveback`를 비교한다. 그 결과를 기준으로 `trailing_continuation_micro_canary`를 여전히 `2순위 candidate`로 둘지, `soft_stop_rebound_split` 다음 active 후보로 끌어올릴지 확정한다.
  - why: Rebase에는 trailing EV 문제가 이미 포함돼 있지만, 현재는 observe/candidate 단계에 머물러 있다. `제룡전기`처럼 추가매수 후 소폭 이익 잠금이 나온 표본과 `덕산하이메탈`처럼 trailing 후 고가 재진입이 뒤따른 표본을 같이 봐야 과보수 여부를 단일 사례 오판 없이 닫을 수 있다.
  - 다음 액션: `MISSED_UPSIDE + same_symbol reentry`가 반복되면 다음 운영일인 `2026-05-04` checklist에 trailing 전용 observe-only 또는 canary 준비항목을 올린다. 반대로 `GOOD_EXIT` 우세면 trailing은 2순위 candidate로 유지하고 soft stop 축을 계속 우선한다.

- [ ] `[ExecutionReceiptBinding0430] WS 실제체결 order-binding 누락과 계좌동기화 의존도 점검` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 18:25~18:40`, `Track: RuntimeStability`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `ORDER_NOTICE_BOUND -> WS 실제체결 -> active order binding` 경로에서 `EXEC_IGNORED`가 왜 발생하는지 `BUY`/`SELL`를 분리해 재현 로그와 코드 조건을 대조하고, `BROKER_RECOVER`/`정기 동기화 COMPLETED 강제전환` 의존도를 계량화한다.
  - why: `SK이노베이션(096770)`은 `2026-04-29 13:28:19 BUY`, `15:06:28 SELL` 모두 `WS 실제체결`이 들어왔는데 active order binding이 붙지 않아 `EXEC_IGNORED`로 빠졌고, 상태 복구를 `BROKER_RECOVER`와 `정기 계좌동기화`가 대신했다. 이 경로가 반복되면 보유/청산 판단보다 먼저 runtime truth 품질이 흔들린다.
  - 다음 액션: 원인이 order number binding timing/race면 runtime fix 후보로, 단순 log visibility 문제면 observe-only로 분리한다. 결과에 따라 다음 운영일인 `2026-05-04` checklist에 patch 또는 관찰축을 올린다.

- [ ] `[ShadowDiffSyntheticExclusion0430] historical shadow diff TEST synthetic row 제외 규칙 확정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `2026-04-27` historical mismatch의 주원인으로 확인된 `record_id=1 / TEST(123456)` synthetic `position_rebased_after_fill`를 비교 리포트에서 어떤 필터로 안정적으로 제외할지 규칙을 고정하고, raw/analytics/report 경로가 같은 exclusion rule을 쓰는지 확인한다.
  - why: same-day 장후 판정으로 원인은 닫혔지만, exclusion rule이 문서/집계에 고정되지 않으면 이후 historical `submitted/full/partial` 비교가 다시 오염된다.
  - 다음 액션: exclusion rule이 확정되면 다음 historical report부터 기본 적용하고, 미확정이면 observe-only 임시 필터라도 먼저 잠근다.

- [ ] `[ReentryPriceEscalationSample0430] same-day reentry price escalation 표본 추가 수집` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 18:55~19:10`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `same record_id 기준 1차 submitted 후 미체결/만료 -> 2차 submitted 가격 상승` 케이스를 1일 더 누적해 표본이 `3건 이상` 되는지 확인하고, `덕산하이메탈(077360)` anchor case가 일반 패턴인지 개별 예외인지 닫는다.
  - why: 2026-04-29는 `덕산하이메탈` 1건만 남아 일반화에 표본이 부족했다.
  - 다음 액션: 표본이 3건 이상이면 observe-only 축으로 승격하고, 계속 1~2건이면 anchor case 유지로 끝낸다.

- [ ] `[SoftStopReboundSplit0430] soft stop rebound/recovery recapture 표본으로 micro grace 후속축 재판정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 19:10~19:25`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `올릭스(226950) GOOD_EXIT`, `덕산하이메탈(077360) NEUTRAL + reentry escalation`, `지앤비에스 에코(382800) same-day 고가 재진입 체결 + 익절`, `코오롱(002020) soft stop 후 고가 재진입 제출`을 묶어 `rebound_above_sell`, `rebound_above_buy`, `mfe_10m`, `same_symbol_soft_stop_cooldown_would_block`, `recovery recapture`를 비교한다. 그 결과를 기준으로 `soft_stop_micro_grace` 유지, `soft_stop_micro_grace_extend` standby 유지, 또는 `recovery recapture` observe-only 라벨/로그 보강 중 하나를 닫는다.
  - why: Rebase 기준 보유/청산 1순위는 여전히 `soft_stop_rebound_split`이며, 2026-04-29 표본은 `정당 컷`, `혼합형 rebound`, `same-day 회수형 recovery recapture`가 함께 나왔다. 지금 단계에서 바로 live 파라미터를 더 열면 원인귀속이 흐려지고, 반대로 이 표본을 독립 분해하지 않으면 EV 훼손 패턴을 놓칠 수 있다.
  - 다음 액션: `MISSED_UPSIDE/recovery recapture`가 누적되면 다음 운영일인 `2026-05-04` checklist에 `observe-only label/log patch` 또는 `extend acceptance` 항목을 올린다. `GOOD_EXIT` 우세면 live 파라미터는 그대로 두고 `soft_stop_micro_grace`만 유지한다.

- [ ] `[ReversalAddBadEntry0430-Postclose] REVERSAL_ADD 소형 canary와 bad_entry_block classifier 장후 판정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 19:25~19:45`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `reversal_add_used` cohort와 비사용 후보를 분리해 `full/partial`, `initial/pyramid`, `soft_stop`, `trailing`, `COMPLETED + valid profit_rate`, `post_sell outcome`을 비교한다. `bad_entry_block_observed`는 후속 `soft_stop/hard_stop/GOOD_EXIT/MISSED_UPSIDE` 분포만 보고 실전 차단 승격 여부를 판단한다.
  - why: 이 항목의 목적은 soft stop을 몇 초 늦추는 것이 아니라, `유효 진입 회수`와 `불량 진입 회피` 중 어느 전략이 EV 개선 가능성이 큰지 고르는 것이다.
  - 다음 액션: `REVERSAL_ADD`가 손익/soft stop tail을 악화시키면 OFF하고 classifier 관찰만 유지한다. `bad_entry_block` 후보가 반복적으로 손실로 끝나면 다음 운영일 `2026-05-04`에 live entry block 후보를 별도 단일축으로 올린다.

- [ ] `[InitialQtyCap3Share0430-Postclose] 스캘핑 신규 BUY 3주 cap 전환 승인조건 판정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 19:45~20:00`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: 2주 cap cohort의 `initial_entry_qty_cap_applied`, `initial-only`, `pyramid-activated`, `ADD_BLOCKED reason=zero_qty`, `full_fill`, `partial_fill`, `soft_stop`, `COMPLETED + valid profit_rate`, `same-symbol reentry`, `order_failed`를 재집계한다. `3주 cap`은 `mechanical_momentum_latency_relief` entry canary와 같은 단계 live 변경이므로, 제출 회복과 P0 price guard가 안정적이고 soft stop tail이 악화되지 않은 경우에만 익일 이후 canary 후보로 본다.
  - why: 2주 cap은 `buy_qty=1 -> pyramid zero_qty` 왜곡을 줄이는 임시 운영가드로 승인됐지만, 3주 확대는 exposure와 soft stop tail을 직접 키운다. submitted 회복이 관찰 중인 상태에서 수량축을 바로 올리면 entry 효과와 holding/exit 손실 tail 원인귀속이 섞인다.
  - 다음 액션: 승인조건을 만족하면 다음 운영일인 `2026-05-04`에 `3주 cap canary` 항목을 새로 만들고, 미충족이면 `2주 cap 유지`로 닫는다. live 전환 방식은 `KORSTOCKSCAN_SCALPING_INITIAL_ENTRY_MAX_QTY=3` 또는 상수 변경 중 하나로 고정하되, 같은 날 다른 entry live 축과 병행하지 않는다.
