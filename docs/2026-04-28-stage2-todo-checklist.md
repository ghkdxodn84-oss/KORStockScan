# 2026-04-28 Stage 2 To-Do Checklist

## 오늘 목적

- `Gemini(main)` live 기준 엔진의 `P2 response schema registry`를 endpoint별 계약 + fallback 단위로만 잠그고, 전역 교체는 금지한다.
- `DeepSeek(remote)`는 `gatekeeper structured-output`을 text report 유지 전제의 option 축으로만 검토하고, 계약/rollback이 없으면 착수하지 않는다.
- `holding cache`와 `Tool Calling`은 기대값 개선 근거와 운영 필요성이 없으면 설계 메모 또는 보류 판정으로만 닫는다.
- `P0/P1`에서 넣은 flag-off 변경은 실로그/테스트 acceptance를 깨지 않는지 확인하고, `P2+`는 live 엔진 분포 변경과 분리해 다룬다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 동일 단계 내 `1축 canary`만 허용한다. 진입병목축과 보유/청산축은 별개 단계이므로 병렬 canary가 가능하지만, 같은 단계 안에서는 canary 중복을 금지한다.
- 동일 단계 replacement는 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
- 단계 분리: 진입병목 canary와 보유/청산 canary는 조작점, 적용 시점, cohort tag, rollback guard가 완전히 분리되고 단계별 판정을 유지할 때만 `stage-disjoint concurrent canary`로 운영할 수 있다.
- 관찰창이 끝나면 `즉시 판정 -> 다음 축 즉시 착수`를 기본으로 한다. 이미 수집된 데이터로 닫을 수 있는 판정은 장후/익일로 미루지 않는다.
- `장후/익일/다음 장전` 이관은 예외사유 4종(`단일 조작점 미정`, `rollback guard 미문서화`, `restart/code-load 불가`, `운영 경계상 same-day 반영 불가`) 중 하나로만 허용한다. 막힌 조건과 다음 절대시각이 없으면 이관 판정은 무효다.
- PREOPEN은 전일에 이미 `단일 조작점 + rollback guard + 코드/테스트 + restart 절차`가 준비된 carry-over 축만 받는다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- live 승인, replacement, stage-disjoint 예외, 관찰 개시 판정에는 `cohort`를 같이 잠근다. 최소 `baseline cohort`, `candidate live cohort`, `observe-only cohort`, `excluded cohort`를 구분하고 `partial/full`, `initial/pyramid`, `fallback` 혼합 결론을 금지한다.
- `ApplyTarget`은 문서에 명시된 값만 사용하고, parser/workorder가 `remote`를 추정하지 않도록 유지한다.
- 다축 동시 변경 금지, 승인 전 `main` 실주문 변경 금지 규칙을 유지한다.

## 장후 체크리스트 (18:05~19:20)

- [x] `[FallbackSplit0428] fallback/split-entry 폐기 정합성 정리` (`Due: 2026-04-28`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:50`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`는 모든 실행축에서 제외 상태(`remove`)로 고정하고, `fallback_qty`는 historical guard 용어로만 남긴다.
  - why: 기준선 문서상 영구 폐기 축인데 runtime 분류표와 작업지시서에 `observe-only` 또는 `baseline-promote` 표현이 남아 있으면 재개 후보처럼 보인다.
  - 다음 액션: `remove / guarded-off / historical-only` 표현으로 같은 change set에서 문서 정합을 잠근다.

- [x] `[FallbackSplit0428] latency fallback split-entry code path hard-off 제거` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 09:10~09:30`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-27-stage2-todo-checklist.md)
  - 판정 기준: `CAUTION -> ALLOW_FALLBACK` 또는 scout/main fallback bundle이 실시간 주문 경로를 만들지 않아야 한다. `split_entry` follow-up runtime shadow도 기본 OFF여야 한다.
  - why: same-day 판정으로 entry 제출 회복과 무관한 축으로 닫혔고, partial/rebase 오염만 남긴다.
  - 다음 액션: deprecated reason/log는 historical trace로만 남기고 실전 경로는 reject로 닫는다.

- [x] `[FallbackSplit0428] 테스트·감시 지표 청소` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 09:40~10:20`, `Track: ScalpingLogic`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: fallback/split-entry 관련 테스트는 `deprecated reject` 또는 `historical helper`만 검증하도록 축소하고, runtime shadow 기본 OFF를 같이 검증한다.
  - why: 재개를 전제한 테스트/분류가 남아 있으면 운영 문서와 상충한다.
  - 검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/trading/tests/test_entry_orchestrator.py src/trading/tests/test_entry_policy.py src/tests/test_sniper_entry_latency.py src/tests/test_sniper_entry_metrics.py src/tests/test_split_entry_followup_audit.py src/tests/test_split_entry_followup_runtime.py`
    - `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_entry_latency.py src/engine/sniper_execution_receipts.py src/trading/entry/entry_orchestrator.py src/trading/entry/entry_policy.py`

- [x] `[FallbackSplit0428] 감리/보고 반영` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 17:40~18:00`, `Track: Plan`)
  - Source: [audit-reports/2026-04-27-entry-latency-single-axis-tuning-audit.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-27-entry-latency-single-axis-tuning-audit.md), [personal-decision-flow-notes.md](/home/ubuntu/KORStockScan/docs/personal-decision-flow-notes.md)
  - 판정 기준: `왜 제거되는지`, `무엇이 historical-only로 남는지`, `다음 관측포인트는 무엇인지`를 checklist와 audit 기준으로 고정한다.
  - why: 개인문서 단독 근거 사용 금지 원칙 때문에 최종 근거는 checklist/audit에 남아야 한다.

- [ ] `[QuoteFreshReview0428] quote_fresh composite 다음 판정 규칙 고정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:15`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [audit-reports/2026-04-27-entry-latency-composite-canary-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-27-entry-latency-composite-canary-audit-review.md)
  - 판정 기준: `latency_quote_fresh_composite`는 `signal/ws_age/ws_jitter/spread/quote_stale` 5개를 개별 축으로 해석하지 않고 묶음 ON/OFF로만 판정한다. 비교 baseline은 같은 bundle 내 `quote_fresh_composite_canary_applied=False` 표본으로 고정하고, baseline이 `N_min` 미달이면 방향성 판정으로 격하한다.
  - why: 복합축 이름으로 동일 단계 다중축 실험을 우회하면 원인귀속과 rollback 판단이 깨진다.
  - 다음 액션: 다음 판정 메모에는 임계값별 `분포 기준`, `예상 기각률`, `효과 부족 시 fallback 임계값`, `composite_no_recovery` guard를 함께 남긴다.

- [ ] `[ShadowDiff0428] postclose submitted/full/partial mismatch 재분해` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:15~18:30`, `Track: ScalpingLogic`)
  - Source: [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-27-stage2-todo-checklist.md)
  - 판정 기준: `deploy/run_tuning_monitoring_postclose.sh 2026-04-27` 재실행에서 나온 `data/analytics/shadow_diff_summary.json`의 `submitted_events jsonl=19 vs duckdb=17`, `full_fill_count jsonl=37 vs duckdb=31`, `partial_fill_count jsonl=30 vs duckdb=24` 차이를 이벤트 복원/집계 품질 관점에서 재분해하고, 누락 source가 `pipeline_events`, `post_sell`, 집계 SQL 중 어디인지 닫아야 한다.
  - why: pattern lab 재실행은 복구됐지만 funnel/fill count mismatch를 그대로 두면 다음 진입병목 판정의 baseline 품질이 흔들린다.
  - 다음 액션: 차이 원인을 닫은 뒤 shadow diff 기준선을 다시 갱신하고, 필요하면 parquet builder 또는 compare 쿼리 수정 작업으로 승격한다.

- [ ] `[GeminiP1Rollout0428] main Gemini JSON system_instruction/deterministic flag 실전 승인 판정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:05~18:20`, `Track: ScalpingLogic`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md)
  - 판정 기준: `GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED`, `GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED`는 코드상 guard가 준비됐더라도 기본값 `OFF`를 유지한다. `main` 실전 엔진에서 이 flag를 켜려면 `BUY/WAIT/DROP`, `HOLD/TRIM/EXIT`, `condition/eod` JSON contract 유지, rollback owner, `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort`, parse_fail/consecutive_failures/ai_disabled 관찰 필드가 같은 메모에 잠겨 있어야 한다.
  - why: Gemini는 현재 `main` 실전 기준 엔진이라 P1은 단순 코드 완료가 아니라 live 판정 분포를 바꾸는 canary 승인 작업이다.
  - 다음 액션: 승인되면 `2026-04-29 PREOPEN` replacement 또는 observe-only 반영 시각을 고정하고, 미승인이면 보류 사유 1개와 재판정 시각 1개를 남긴다.

- [ ] `[DeepSeekP1Rollout0428] remote DeepSeek context-aware backoff flag 실전 승인 판정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:30`, `Track: ScalpingLogic`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - 판정 기준: `DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED`는 코드상 guard가 준비됐더라도 기본값 `OFF`를 유지한다. `remote` 운용에서 flag를 켜려면 `live-sensitive cap <= 0.8s`, `report/eod cap`, jitter 상한, `api_call_lock` 장기 점유 여부, retry 이후 rate-limit/log acceptance를 함께 잠가야 한다.
  - why: DeepSeek는 `remote` 운용 엔진이라 P1 잔여작업은 구현이 아니라 실제 enable 판정과 운영 acceptance다.
  - 다음 액션: 승인되면 `remote observe-only` 또는 `remote canary-only` 1개 경로와 적용 시각을 고정하고, 미승인이면 막힌 조건과 재판정 시각을 남긴다.

- [ ] `[GeminiSchema0428] Gemini JSON endpoint schema registry 적용 범위 잠금` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:05~18:25`, `Track: ScalpingLogic`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md)
  - 판정 기준: `entry_v1`, `holding_exit_v1`, `overnight_v1`, `condition_entry_v1`, `condition_exit_v1`, `eod_top5_v1` 6개 endpoint를 분리하고, `response_schema` 실패 시 기존 `json.loads/raw regex fallback` 경로로 즉시 복귀할 수 있어야 한다. `system_instruction`/deterministic JSON config flag와 schema registry를 한 change set에서 묶어 global live 전환하지 않는다.
  - why: Gemini는 `main` 실전 기준 엔진이라 범용 `_call_gemini_safe()` 한 줄 변경으로 전 경로를 동시에 바꾸면 BUY/WAIT/DROP 분포와 parse_fail 축이 함께 흔들린다.
  - 다음 액션: schema registry가 준비되면 endpoint별 테스트 목록과 fallback 필드를 아래 항목에서 잠그고, 준비가 안 되면 막힌 이유 1개와 재시각 1개를 same-day 메모에 남긴다.

- [ ] `[GeminiSchema0428] Gemini schema/fallback 테스트 매트릭스 및 관찰 필드 잠금` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:25~18:40`, `Track: ScalpingLogic`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md)
  - 판정 기준: 최소 `entry/holding_exit/overnight/condition_entry/condition_exit/eod_top5` 계약 테스트, `parse_fail`, `consecutive_failures`, `ai_disabled`, `gatekeeper action_label`, `submitted/full/partial` 영향 관찰 필드를 같이 고정한다. live canary를 검토하려면 `flag default OFF`, `rollback owner`, `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort`가 문서에 잠겨 있어야 한다.
  - why: schema는 파싱만 바꾸는 게 아니라 장애 관측 축과 rollback 경계까지 같이 정하지 않으면 `main` live 엔진에서 원인귀속이 흐려진다.
  - 다음 액션: 조건이 충족되면 `2026-04-29 POSTCLOSE` canary 검토 슬롯을 열고, 미충족이면 same-day 보류로 닫는다.

- [ ] `[DeepSeekGatekeeper0428] DeepSeek gatekeeper structured-output option 축 판정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: ScalpingLogic`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - 판정 기준: `generate_realtime_report()`의 사람용 text report는 유지하고, `evaluate_realtime_gatekeeper()`에만 JSON option 경로를 검토한다. `flag default OFF`, JSON 실패 시 text fallback, `action_label/allow_entry/report/selected_mode/timing` contract 유지 테스트가 없으면 착수하지 않는다.
  - why: DeepSeek는 `remote` 운용 엔진이지만, gatekeeper structured-output은 퍼블릭 contract와 캐시 테스트를 건드려 진입 판단 분포를 바꿀 수 있다.
  - 다음 액션: 승인되면 `remote observe-only` 또는 `remote canary-only` 중 1개 경로만 택하고, 미승인이면 막힌 조건과 다음 절대시각을 남긴다.

- [ ] `[DeepSeekHolding0428] DeepSeek holding cache bucket 조정 근거 점검` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:55~19:10`, `Track: Plan`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - 판정 기준: `holding cache miss 증가 -> completed_valid 품질 개선` 근거가 있는지, `partial/full`, `initial/pyramid`, `missed_upside`, `exit quality` 분리 기준에서 gain이 있는지 먼저 확인한다. 근거가 없으면 `_compact_holding_ws_for_cache()` 버킷 축소는 same-day 보류로 닫는다.
  - why: holding cache 세분화는 비용/호출량을 늘릴 수 있지만 기대값 개선이 아직 고정되지 않았다.
  - 다음 액션: 승인 근거가 생기면 `2026-04-29 POSTCLOSE` 설계 슬롯으로 넘기고, 없으면 `보류 유지`로 닫는다.

- [ ] `[DeepSeekTooling0428] DeepSeek Tool Calling 필요성/범위 판정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 19:10~19:20`, `Track: Plan`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - 판정 기준: Tool Calling이 실제로 `JSON parse_fail`, contract drift, 운영 복잡도 감소에 기여하는지 판단하고, 아니면 설계 메모로만 남긴다. SDK/응답 schema/테스트/rollback 구조가 준비되지 않으면 구현 작업으로 승격하지 않는다.
  - why: 현재 Tool Calling은 기능 개선보다 code debt/설계 검토 성격이 강하다.
  - 다음 액션: 필요성이 약하면 backlog 관찰로만 남기고, 필요성이 강하면 별도 workorder 초안과 테스트 범위를 same-day 문서화한다.
