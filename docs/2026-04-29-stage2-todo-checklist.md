# 2026-04-29 Stage2 To-Do Checklist

## 오늘 목적

- `latency_quote_fresh_composite` OFF 반영과 restart provenance를 장전 기준으로 확인한다.
- EC2 인스턴스가 `m7g.xlarge`로 상향 완료됐으므로 `runtime basis shift day`로 분리해 CPU/메모리 영향과 전략 효과를 섞지 않는다.
- `ShadowDiff0428`의 두 갈래 원인(`2026-04-28 parquet 미생성`, `2026-04-27 submitted/full/partial mismatch`)을 재검증한다.
- 스캘핑 신규 BUY `initial_entry_qty_cap`은 임시 `2주 cap`으로 완화하고, `initial-only`와 `pyramid-activated`를 계속 분리해 `zero_qty` 왜곡이 줄었는지 본다.
- `씨아이에스(222080)` micro grace 개입 표본의 전일 post-sell 평가는 장전부터 확인하고, 평가가 있으면 `soft_stop_micro_grace_extend` 후보를 장전 기준으로 다시 본다.
- `follow-through failure`는 observe-only backtrace와 스키마 구현 범위만 유지하고 live 축 승격은 보류한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 동일 단계 내 `1축 canary`만 허용한다. 진입병목축과 보유/청산축은 별개 단계이므로 병렬 canary가 가능하지만, 같은 단계 안에서는 canary 중복을 금지한다.
- 동일 단계 replacement는 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- `latency_signal_quality_quote_composite`는 `ShadowDiff` 재검증 전에는 auto-ON 하지 않는다.
- EC2 인스턴스 상향 직후 하루는 `QuoteFresh`, `latency_state_danger`, `gatekeeper_eval_ms_p95`를 전략 개선이 아니라 `infra basis shift` 후보로 먼저 본다.
- `soft_stop_micro_grace_extend`는 `씨아이에스(222080)` post-sell 평가 확인 전에는 승인하지 않는다.
- 전일 post-sell evaluation 존재 여부만 확인하면 되는 항목은 장후로 넘기지 않고 PREOPEN에서 먼저 닫는다. evaluation이 없으면 `candidate 존재`, `evaluation 생성 경로`, `막힌 원인`을 남긴 뒤에만 장중/장후로 이관한다.
- `initial_entry_qty_cap` 완화는 `1주 -> 2주` 단일축 조정으로만 본다. same-day에 `pyramid floor`나 추가 포지션 비율 축을 같이 열지 않는다.

## 장전 체크리스트 (08:30~09:00)

- [ ] `[VMPerfRebase0429-Preopen] EC2 m7g.xlarge 변경 provenance 및 CPU/메모리 기준선 재확인` (`Due: 2026-04-29`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: RuntimeStability`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: `instance type`, `uname -m`, `nproc`, `MemAvailable`, `SwapUsed`, `load average`, main bot PID `/proc/<pid>/environ` 증적을 남기고, 오늘은 `runtime basis shift day`인지 여부를 확정한다.
  - 실행 메모 (`2026-04-28`, 사용자 확인): EC2 인스턴스 변경은 이미 `m7g.xlarge`로 완료됐다.
  - why: `t4g.medium -> m7g.xlarge` 변경 완료 직후 첫 거래일은 `QuoteFresh`와 `latency` 계열 baseline을 기존 거래일과 직접 비교하면 infra 효과와 전략 효과가 섞인다.
  - 다음 액션: 장전에는 변경 여부 재판정이 아니라 provenance/리소스 증적만 남기고, 장중/장후 `QuoteFresh`는 `infra basis shift` 분리표와 함께 본다.

- [ ] `[ShadowDiff0429-Preopen] 2026-04-28 parquet/duckdb rebuild 및 shadow diff 재검증` (`Due: 2026-04-29`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:42`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `data/analytics/parquet/pipeline_events/date=2026-04-28`, `post_sell/date=2026-04-28` partition이 생성되고 `submitted/full/partial` diff가 어디까지 줄었는지 확인한다.
  - why: `QuoteFresh` hard baseline은 `ShadowDiff` 미해소 상태에서 다시 승격할 수 없다.
  - 다음 액션: 미해소면 parquet builder/compare query 수정 항목으로 승격하고, 해소면 `QuoteFresh` 기준선 문구를 다시 잠근다.

- [ ] `[SoftStopCIS0429-Preopen] 씨아이에스 micro grace post-sell 평가 및 extend 후보 장전 재판정` (`Due: 2026-04-29`, `Slot: PREOPEN`, `TimeWindow: 08:42~08:52`, `Track: Plan`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정 기준: `씨아이에스(222080)`의 `post_sell_evaluation`이 생성됐는지 먼저 확인하고, 있으면 `good_cut / whipsaw / ambiguous` 라벨과 `mfe/rebound`를 확인해 `soft_stop_micro_grace_extend` 후보 유지/폐기/보류를 닫는다.
  - why: 이 항목은 전일 `post_sell_evaluation` 확인 작업이므로 장후까지 기다릴 이유가 없다. 오전 거래가 몰리는 날에는 장전 후보 판정이 되어야 보유/청산축 원인귀속이 덜 흔들린다.
  - 다음 액션: evaluation이 있으면 장전 판정을 닫고, 없으면 `candidate 존재`, `evaluation 생성 경로`, `막힌 원인`을 남긴 뒤 `12:00` 재확인 또는 장후 이관 여부를 구체적으로 정한다.

- [ ] `[QuoteFreshComposite0429-PreopenOff] latency_quote_fresh_composite OFF/restart 반영 확인` (`Due: 2026-04-29`, `Slot: PREOPEN`, `TimeWindow: 08:52~09:00`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `latency_quote_fresh_composite` OFF 값이 env/runtime provenance(`/proc/<pid>/environ` 또는 동등 증적)와 restart 결과에 실제 반영됐는지 확인한다.
  - why: same-day 판정은 `OFF`로 닫혔고, carry-over는 장전 provenance가 있어야만 유효하다.
  - 다음 액션: 반영 완료면 장중에는 예비축 자동 ON 없이 baseline 관찰만 유지하고, 미반영이면 즉시 provenance/restart 경로를 다시 본다.

## 장중 체크리스트 (09:00~15:20)

- [ ] `[EntryBottleneckVmShift0429-1000] VM 변경 후 진입병목 infra basis shift 1차 점검` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 10:00~10:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: `gatekeeper_eval_ms_p95`, `latency_state_danger / budget_pass`, `ws_age`, `ws_jitter`, `budget_pass_to_submitted_rate`, `full_fill`, `partial_fill`를 기존 `QuoteFresh` 결과와 분리해 본다.
  - why: 인스턴스 상향 직후 첫 1시간은 전략 canary보다 런타임 처리속도 개선 신호가 먼저 움직일 수 있다.
  - 다음 액션: `latency_state_danger`와 `gatekeeper_eval_ms_p95`만 개선되고 `submitted/full/partial`이 안 움직이면 `infra-only improvement`로 분리한다. 오전 거래가 충분히 몰렸으면 `[EntryBottleneckVmShift0429-1200Final]`에서 장후 대기 없이 baseline reset 여부를 닫는다.

- [ ] `[EntryBottleneckVmShift0429-1200Final] VM 변경 후 진입병목 infra basis shift 12시 최종확정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: `09:00~12:00` 또는 12시 full snapshot 기준 `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger share`, `gatekeeper_eval_ms_p95`, `ws_age`, `ws_jitter`, `full_fill`, `partial_fill`, `ShadowDiff`를 보고 `VM 이후 baseline reset`, `infra-only improvement`, `기존 baseline 유지`, `판정유예` 중 하나로 닫는다.
  - why: 오전 거래가 집중되는 구조라면 12시 full snapshot이 `VM basis shift`의 1차 최종판정 창이다. 같은 데이터를 장후까지 기다리면 다음 entry 축 착수가 불필요하게 밀린다.
  - 다음 액션: `submitted/full/partial`까지 같이 회복되면 `VM 이후 baseline reset` 후보를 즉시 잠그고, `p95/latency_state_danger`만 개선되면 `infra-only improvement`로 분리한다. `ShadowDiff` 또는 fresh 로그 미확보로 못 닫을 때만 막힌 조건과 재시각을 남긴다.

## 장중 설계/후속 체크리스트 (12:20~14:20)

- [ ] `[QuoteFreshBackupComposite0429-1220] latency_signal_quality_quote_composite 활성화 조건 12시 재판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 12:20~12:35`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `latency_quote_fresh_composite OFF/restart` 반영, `ShadowDiff` 재검증, `[EntryBottleneckVmShift0429-1200Final]`의 VM basis shift 판정을 확인한 뒤에만 예비축 ON 가능 여부를 닫는다.
  - why: 예비축 활성화 조건은 12시 VM/baseline 판정 이후 바로 판단 가능하다. 장후까지 기다리면 다음 entry 축 착수가 밀린다.
  - 다음 액션: 승인 시 `기존 축 OFF -> restart.flag -> 새 축 ON` 절차를 같은 문서에 잠그고, 미승인 시 standby 유지로 닫는다. `ShadowDiff` 또는 restart provenance가 막히면 막힌 조건과 재시각을 남긴다.

- [ ] `[InitialQtyCap0429-1235] 스캘핑 신규 BUY 2주 cap 완화 후 initial/pyramid 12시 1차 판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 12:35~12:50`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `initial_entry_qty_cap_applied cap_qty=2` runtime 증적, `initial-only` vs `pyramid-activated` 표본, `ADD_BLOCKED reason=zero_qty`, `position_rebased_after_fill`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`를 분리해 본다.
  - why: 오전 거래가 몰리면 12시까지 cap 완화가 `PYRAMID zero_qty` 왜곡을 줄였는지 1차 방향성은 볼 수 있다. full-day 손익 확정은 장후까지 기다릴 수 있지만, 구조적 zero_qty 여부는 장중에도 판단 가능하다.
  - 다음 액션: `zero_qty`가 줄고 `pyramid-activated` 표본이 회복되면 `2주 cap 유지` 방향으로 잠그고, 표본이 없으면 장후 보정 항목으로 넘긴다. 여전히 `zero_qty`가 반복되면 `pyramid floor` 또는 cap 추가 완화가 아니라 원인 분해 문서화를 먼저 올린다.

- [ ] `[FollowThroughSchema0429-1250] follow-through observe-only 스키마 구현 범위 재판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 12:50~13:05`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `체결 후 30초/1분/3분 가격`, `AI velocity`, `MFE/MAE`, `호가/직전 거래량`, `시장/섹터 동조성` 중 어디까지를 `post_sell/snapshot`로 먼저 넣을지 구현 범위를 닫는다.
  - why: 이 항목은 전일 월간 backfill과 기존 후보 3건 기반의 observe-only 설계 범위다. 당일 종가가 필요하지 않으므로 장후까지 미룰 이유가 없다.
  - 다음 액션: 승인되면 구현 항목으로 승격하고, 미승인이면 수동 감리만 유지한다.

- [ ] `[GeminiEngineCarry0429-1305] Gemini P1/P2 live 승인 전제와 schema 매트릭스 carry-over 판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 13:05~13:20`, `Track: ScalpingLogic`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - Owner: `Codex`
  - 판정 기준: `GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED`, `GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED`의 `flag default OFF` 유지 여부, `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort`, parse_fail/consecutive_failures/ai_disabled 관찰 메모, 그리고 `entry/holding_exit/overnight/condition_entry/condition_exit/eod_top5` schema/fallback 테스트 매트릭스 초안이 같은 문서에 잠겼는지 본다.
  - 실전 enable acceptance 정의:
    - `flag default OFF`와 rollback owner가 문서/코드에 함께 잠겨 있다.
    - `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort`가 명시돼 있다.
    - `parse_fail`, `consecutive_failures`, `ai_disabled`, `gatekeeper action_label`, `submitted/full/partial` 관찰 필드가 고정돼 있다.
    - 최소 `entry/holding_exit/overnight/condition_entry/condition_exit/eod_top5` endpoint별 fallback/test matrix 초안이 있다.
    - 위 4개 중 1개라도 비면 `실전 enable 미승인`으로 본다.
  - why: 이 항목은 엔진 설계/acceptance 정리라 종가 데이터가 필요하지 않다. 12시 운영 판정 후 바로 정리해도 된다.
  - 산출물: `Gemini enable acceptance 메모 1건`, `6 endpoint schema/fallback/test matrix 초안 1건`, `다음 change set 범위(main observe-only vs canary-only) 1건`
  - 다음 액션: acceptance가 잠기면 `2026-04-30 PREOPEN/POSTCLOSE` observe-only 또는 canary 검토 슬롯으로 넘기고, 안 잠기면 빠진 항목 1개와 완료 목표시각 1개를 같은 항목에 남긴다.

- [ ] `[GeminiSchemaBuild0429-1320] Gemini 6 endpoint schema registry/fallback/test matrix 초안 작성` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 13:20~13:45`, `Track: ScalpingLogic`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md)
  - Owner: `Codex`
  - 판정 기준: `entry_v1`, `holding_exit_v1`, `overnight_v1`, `condition_entry_v1`, `condition_exit_v1`, `eod_top5_v1` 각각에 대해 `schema scope`, `fallback path`, `required tests`, `observe fields`, `rollback point`가 표 형태로 초안화된다.
  - why: “없어서 보류”를 반복하지 않으려면 schema registry의 실제 설계 산출물을 먼저 만들어야 하며, 이 작업은 장후 데이터가 필요하지 않다.
  - 다음 액션: 초안이 나오면 `2026-04-30` 구현 change set owner/순서를 고정하고, 초안이 안 나오면 막힌 endpoint와 원인 1개씩 기록한다.

- [ ] `[DeepSeekEngineCarry0429-1345] DeepSeek P1/P2/P3 acceptance/backlog carry-over 판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 13:45~14:00`, `Track: Plan`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - Owner: `Codex`
  - 판정 기준: `DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED`의 `remote` live-sensitive acceptance(`api_call_lock`, rate-limit/log acceptance, observe-only/canary-only 경로), gatekeeper structured-output의 `flag-off + text fallback + contract test`, holding cache bucket 축소의 EV 근거, Tool Calling backlog 유지 여부를 한 묶음으로 확인한다.
  - 실전 enable acceptance 정의:
    - backoff 축: `live-sensitive cap <= 0.8s`, `report/eod cap`, `api_call_lock` worst-case, retry 후 rate-limit/log acceptance가 문서에 잠겨 있다.
    - gatekeeper structured-output 축: `flag default OFF`, text fallback, `action_label/allow_entry/report/selected_mode/timing` contract test가 있다.
    - holding cache 축: `completed_valid`, `partial/full`, `initial/pyramid`, `missed_upside`, `exit quality` 기준의 EV 근거가 있다.
    - Tool Calling 축: 퍼블릭 schema/fallback/테스트/rollback 구조가 없으면 구현 승격 금지다.
    - 위 조건이 안 맞으면 `remote 실전 enable 미승인` 또는 `backlog 유지`로 닫는다.
  - why: 04-28 판정 기준 DeepSeek 잔여축은 전부 실전 acceptance 또는 설계/backlog 범위이고, 장후 데이터가 필요한 항목이 아니다.
  - 산출물: `DeepSeek enable acceptance 메모 1건`, `backoff acceptance 표 1건`, `gatekeeper structured-output 설계 전제 1건`, `holding cache/Tool Calling backlog 결론 1건`
  - 다음 액션: acceptance가 생기면 `2026-04-30` change set 슬롯으로 넘기고, 없으면 빠진 acceptance 항목과 완료 목표시각을 같은 항목에 남긴다.

- [ ] `[DeepSeekAcceptanceBuild0429-1400] DeepSeek 실전 enable acceptance/spec 메모 작성` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 14:00~14:20`, `Track: Plan`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - Owner: `Codex`
  - 판정 기준: `context-aware backoff`, `gatekeeper structured-output`, `holding cache`, `Tool Calling` 각각에 대해 `enable acceptance`, `not now reason`, `required proof`, `next implementation slot`이 문서화된다.
  - why: DeepSeek 잔여축은 코드보다 운영 acceptance가 먼저라, 설계/승인 메모를 장후까지 미루지 않고 고정해야 더 이상 공회전하지 않는다.
  - 다음 액션: 메모가 나오면 `2026-04-30` 구현/비구현 축을 갈라 배치하고, 없으면 빠진 증거와 담당 change set을 남긴다.

## 장후 보정 체크리스트 (18:30~19:00)

- [ ] `[EntryBottleneckVmShift0429-PostcloseFallback] VM 변경 후 진입병목 12시 미확정 시 보정 판정` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~18:45`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: `[EntryBottleneckVmShift0429-1200Final]`이 `ShadowDiff`, fresh 로그 미확보, 오전 표본 부족 중 하나로 못 닫혔을 때만 same-day `gatekeeper_eval_ms_p95`, `latency_state_danger share`, `budget_pass_to_submitted_rate`, `full_fill`, `partial_fill`, `ShadowDiff`를 재확인한다.
  - why: VM basis shift는 12시 확정을 기본으로 하고, 장후 항목은 미확정 보정용이다.
  - 다음 액션: 12시에 닫혔으면 이 항목은 `해당 없음`으로 완료 처리한다. 12시에 못 닫혔으면 막힌 조건 해소 여부를 확인해 `기존 baseline 유지`, `VM 이후 baseline reset`, `infra-only improvement`, `판정유예` 중 하나로 닫는다.

- [ ] `[InitialQtyCap0429-PostcloseFallback] 스캘핑 신규 BUY 2주 cap 표본부족 시 장후 보정 판정` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 18:45~19:00`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `[InitialQtyCap0429-1235]`에서 표본 부족 또는 fresh 로그 미확보로 못 닫힌 경우에만 full-day `initial_entry_qty_cap_applied cap_qty=2`, `initial-only` vs `pyramid-activated`, `ADD_BLOCKED reason=zero_qty`, `position_rebased_after_fill`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`를 재확인한다.
  - why: 2주 cap의 구조적 효과는 12시 1차 판정을 기본으로 하고, 장후 항목은 표본부족/미확정 보정용이다.
  - 다음 액션: 12시에 닫혔으면 `해당 없음`으로 완료 처리한다. 장후까지 봐도 표본이 없으면 `표본 부족 유지`로 닫고 cap 추가 완화나 pyramid floor는 열지 않는다.
