# 2026-05-11 Stage2 To-Do Checklist

## 오늘 목적

- threshold-cycle은 장전 수동 승인 없이 `auto_bounded_live`로 무인 반영한다.
- 장후에는 daily EV 성과 리포트만 제출 기준으로 보며, Gemini/Claude pattern lab 결과는 EV report 요약으로만 포함한다.
- 남은 튜닝 관련 보강은 독립 report-only 관찰축으로 늘리지 않고, `threshold_cycle` source bundle / `statistical_action_weight` / `performance_tuning` / daily EV 자동화 체인의 입력 품질 개선으로만 처리한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN cron의 runtime env 생성과 봇 기동 시 source로만 수행한다.
- 조건 미달은 rollback이 아니라 calibration trigger다. safety breach만 `safety_revert_required=true`로 분리한다.
- 장전 수동 enable/hold checklist를 만들지 않는다. postclose 제출물은 `threshold_cycle_ev_YYYY-MM-DD.{json,md}`로 통일하고, pattern lab 상세는 별도 artifact 링크로만 둔다.
- 신규 튜닝 판단 항목은 수동 후속계획으로 분리하지 않는다. 새 threshold family가 필요하면 pattern lab `auto_family_candidate(allowed_runtime_apply=false)` 또는 threshold-cycle `calibration_candidates`로만 편입하고, runtime 적용은 기존 `auto_bounded_live` guard를 통과한 경우에만 허용한다.

## 장전 체크리스트 (08:50~09:00)

- 없음

## 장중 체크리스트 (09:00~15:20)

- 없음

## 장후 체크리스트 (16:00~17:30)

- [ ] `[ThresholdDailyEVReport0511] threshold-cycle 무인 반영 daily EV 성과 리포트 제출 확인` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [threshold_cycle_ev_report.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_ev_report.py), [scalping_pattern_lab_automation.py](/home/ubuntu/KORStockScan/src/engine/scalping_pattern_lab_automation.py), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py)
  - 판정 기준: `data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.{json,md}`가 생성되고, selected family/runtime_change, completed/open, win/loss, avg profit rate, realized PnL, submitted funnel, holding/exit latency, calibration decisions, pattern lab automation freshness/consensus/order 요약이 포함되어야 한다.
  - 범위: 장전 수동 승인, 수동 enable/hold 판정, 별도 관찰축 추가는 하지 않는다. 오류가 있으면 daily EV report의 `warnings`와 cron log/status로만 후속 원인을 분리한다.
  - 다음 액션: EV report 생성 정상 시 제출 완료로 닫는다. 누락 시 wrapper/cron/status 보강만 진행하고 threshold runtime 값을 장중 수동 변경하지 않는다.

- [ ] `[OpenAIThresholdCorrection0511] threshold AI correction OpenAI 라우팅/strict schema/guard 결과 확인` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~16:55`, `Track: RuntimeStability`)
  - Source: [README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [ai_response_contracts.py](/home/ubuntu/KORStockScan/src/engine/ai_response_contracts.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [run_threshold_cycle_calibration.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_calibration.sh)
  - 판정 기준: `threshold_cycle_ai_review_2026-05-11_{intraday,postclose}.{json,md}`의 `ai_provider_status.provider=openai`, 기본 모델 `gpt-5.5` 또는 fallback `gpt-5.4/gpt-5.4-mini`, `schema_name=threshold_ai_correction_v1`, `runtime_change=false`가 확인되어야 한다.
  - 자동화체인 연결: OpenAI correction은 AI reviewer + anomaly corrector proposal layer이며, threshold 적용 source of truth는 deterministic guard다. prompt contract는 영어 control prompt + 한국어 glossary + raw label 보존으로 고정한다.
  - 다음 액션: OpenAI 실패/parse reject가 있어도 deterministic calibration과 daily EV 생성을 실패시키지 않는다. 반복 실패 시 provider/키/schema incident로 분리하고 threshold 값을 장중 수동 변경하지 않는다.

- [ ] `[SAWOrderbookContext0511] statistical_action_weight SAW-6 orderbook context 자동화체인 입력 확장` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:15`, `Track: ScalpingLogic`)
  - Source: [2026-05-08-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-08-stage2-todo-checklist.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [performance_tuning_2026-05-08.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/performance_tuning_2026-05-08.json), [statistical_action_weight_2026-05-08.json](/home/ubuntu/KORStockScan/data/report/statistical_action_weight/statistical_action_weight_2026-05-08.json)
  - 판정 기준: 5/8 `StatActionAdvancedContext0508` 판정에 따라 readiness가 가장 높은 `SAW-6`만 report-only로 확장한다. 최소 필드는 `ofi_orderbook_micro_state`, threshold source, bucket, warning, micro VWAP 이탈, large sell/absorption proxy, join key coverage다.
  - 자동화체인 연결: 이 항목은 독립 관찰축이 아니라 `statistical_action_weight -> holding_exit_decision_matrix_advisory -> threshold_cycle_calibration -> threshold_cycle_ev` 입력 확장이다. runtime threshold, AI 응답, 주문/청산 행동을 직접 바꾸지 않고, candidate/readiness/calibration 근거만 machine-readable로 넘긴다.
  - 다음 액션: JSON/Markdown에 SAW-6 context 섹션이 생성되면 daily EV report 요약과 `holding_exit_decision_matrix_advisory` source metrics에 반영한다. 필드 누락이면 `instrumentation gap`으로 닫고 SAW-4/SAW-5를 대신 열지 않는다.

- [ ] `[OFIQPerformanceMarkdown0511] performance_tuning OFI/QI 자동화체인 stale guard 표면화` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: ScalpingLogic`)
  - Source: [2026-05-08-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-08-stage2-todo-checklist.md), [sniper_performance_tuning_report.py](/home/ubuntu/KORStockScan/src/engine/sniper_performance_tuning_report.py), [orderbook_stability_observer.py](/home/ubuntu/KORStockScan/src/trading/entry/orderbook_stability_observer.py), [performance_tuning_2026-05-08.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/performance_tuning_2026-05-08.json)
  - 판정 기준: 5/8 `OFIQExpansionLadder0508`에서 확정한 1순위 후속이다. `performance_tuning_YYYY-MM-DD.md`에 OFI/QI sample, state, threshold source, bucket, warning, symbol anomaly, `entry_ai_price_skip_policy`를 노출하고 2영업일 연속 표본 0 또는 핵심 필드 누락이면 `stale_context` warning을 출력한다.
  - 자동화체인 연결: 이 항목은 사람이 읽는 Markdown 보강만이 아니라 `performance_tuning`의 OFI/QI freshness와 stale warning을 daily EV 및 threshold-cycle source bundle이 소비할 수 있게 만드는 입력 품질 작업이다. prompt contract 변경, standalone OFI BUY/EXIT hard gate, bucket calibration ON은 열지 않는다.
  - 다음 액션: OFI/QI stale guard가 생성되면 `pre_submit_price_guard`, `score65_74_recovery_probe`, `holding_flow_ofi_smoothing`의 source metrics와 daily EV warning에 반영한다. 새 수동 workorder 대신 pattern lab order 또는 threshold-cycle candidate로만 다음 조치를 생성한다.
