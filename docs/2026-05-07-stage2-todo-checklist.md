# 2026-05-07 Stage2 To-Do Checklist

## 오늘 목적

- `statistical_action_weight` 2차 고급축 중 `SAW-3 eligible_but_not_chosen` 후행 성과 연결을 설계한다.
- 선택된 행동만 보는 selection bias를 줄이고, 물타기/불타기/청산 후보의 기회비용을 후행 MFE/MAE로 복원할 수 있는지 판정한다.
- AI 보유/청산 판단에 `holding_exit_decision_matrix`를 shadow prompt context로 주입할 수 있는지 확인한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- `statistical_action_weight`는 report-only/decision-support 축이며 직접 runtime threshold나 주문 행동을 바꾸지 않는다.
- `holding_exit_decision_matrix`는 장중 self-updating 금지다. 전일 장후 산정 matrix를 다음 장전 로드하고 장중에는 immutable context로만 쓴다.
- `AI decision matrix`는 `ADM-1 report-only -> ADM-2 shadow prompt -> ADM-3 advisory nudge -> ADM-4 weighted live -> ADM-5 policy gate` 순서로만 전환한다. 5/7의 허용 범위는 ADM-2 설계이며 live AI 응답 변경은 금지한다.
- `preclose_sell_target`는 5/6 P1 report-only dry-run 통과 후에도 AI/Telegram acceptance, cron 등록, threshold/ADM consumer 연결을 분리한다. 자동 주문, live threshold mutation, bot restart와 연결하지 않는다.
- `BUY Funnel Sentinel`과 `HOLD/EXIT Sentinel`은 detection/report-only 운영 감시축이다. 매일 산출물과 Telegram false-positive/false-negative를 보고 신규 이상치 후보를 backlog에 추가하되, 자동 score/threshold/청산/재시작 변경은 금지한다. 반복 이상치는 `incident`, `threshold-family 후보`, `instrumentation gap`, `normal drift` 중 하나로 분류하고, threshold-cycle에는 sample floor와 rollback owner가 있는 후보만 연결한다.
- 후행 성과 연결은 `COMPLETED + valid profit_rate`와 분리해 보고, full/partial fill은 합치지 않는다.
- raw full scan 반복은 금지하고 compact partition/checkpoint 경로만 사용한다.
- daily 정기작업은 cron 발화 성공과 산출물 완성 성공을 분리해 검증한다. 실패 재시도/lock/status manifest/운영 알림이 없는 작업은 live 전략 변경과 별개인 RuntimeStability backlog로 관리한다.

## 장전 체크리스트 (08:50~09:00)

- [ ] `[Wait6579RecoveryProbePreopen0507] score65_74 recovery probe 로드 확인 및 live enable/hold 판정` (`Due: 2026-05-07`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: ScalpingLogic`)
  - Source: [2026-05-06-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-06-stage2-todo-checklist.md), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [wait6579_ev_cohort_2026-05-06.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/wait6579_ev_cohort_2026-05-06.json)
  - 판정 기준: `AI_SCORE65_74_RECOVERY_PROBE_ENABLED=False` 기본값과 env override 미설정 상태를 먼저 확인한다. live enable은 별도 사용자 승인 또는 명시된 preopen 판정 없이는 금지한다.
  - live enable 조건: 1주/5만원 cap, score65~74, fallback score 50 제외, latency DANGER 제외, buy_pressure/tick_accel/micro_vwap gate, `score65_74_recovery_probe` 및 `wait6579_probe_canary_applied` 로그가 모두 유지되어야 한다.
  - rollback guard: `submitted/full/partial`, `COMPLETED + valid profit_rate`, soft_stop tail, missed/avoided counterfactual을 장중 Sentinel/장후 threshold-cycle과 분리해 본다. broad score threshold 완화, fallback 재개, spread cap 완화는 이 항목에서 금지한다.

- [ ] `[SoftStopWhipsawConfirmationPreopen0507] soft_stop whipsaw confirmation 로드 확인 및 live enable/hold 판정` (`Due: 2026-05-07`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [2026-05-06-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-06-stage2-todo-checklist.md), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [holding_exit_observation_2026-05-06.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/holding_exit_observation_2026-05-06.json)
  - 판정 기준: `SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=False` 기본값과 env override 미설정 상태를 먼저 확인한다. live enable은 별도 사용자 승인 또는 명시된 preopen 판정 없이는 금지한다.
  - live enable 조건: hard/protect stop 우선, emergency stop 우선, base grace 종료 후 1회 confirmation cap, `rebound_above_sell/buy`, `flow_state`, `additional_worsen`, expired stage 로그가 유지되어야 한다.
  - rollback guard: sell receipt/completed, same-symbol reentry loss, GOOD_EXIT/MISSED_UPSIDE, soft stop tail 악화 여부를 본다. 자동 청산 변경, hard/protect stop 완화, holding_flow override mutation은 이 항목에서 금지한다.

## 장중 체크리스트 (09:00~15:20)

- [ ] `[SentinelDiscoveryLoop0507-Intraday] BUY/HOLD-EXIT Sentinel 신규 이상치 후보 발굴 및 운영 메시지 품질 점검` (`Due: 2026-05-07`, `Slot: INTRADAY`, `TimeWindow: 15:20~15:40`, `Track: RuntimeStability`)
  - Source: [buy_funnel_sentinel.py](/home/ubuntu/KORStockScan/src/engine/buy_funnel_sentinel.py), [holding_exit_sentinel.py](/home/ubuntu/KORStockScan/src/engine/holding_exit_sentinel.py), [buy_funnel_sentinel report](/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel), [holding_exit_sentinel report](/home/ubuntu/KORStockScan/data/report/holding_exit_sentinel), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: 당일 `BUY Funnel Sentinel`과 `HOLD/EXIT Sentinel`의 primary/secondary 분포, Telegram 발송 횟수, false-positive 의심, 운영자가 수동으로 발견한 병목과의 불일치를 점검한다. 후보는 `신규 classification`, `기존 classification threshold 조정`, `메시지 포맷 개선`, `데이터/로그 누락` 중 하나로 분류한다.
  - 신규 후보 seed: entry는 `entry_armed_expiry_spike`, `buy_signal_telegram_only_no_order`, `price_resolver_skip_cluster`, `quote_stale_runtime_ops`를 검토한다. holding/exit는 `exit_signal_no_receipt`, `holding_flow_defer_worsen_cluster`, `ai_holding_cache_miss_spike`, `soft_stop_rebound_intraday`, `trailing_missed_upside_intraday`, `sell_order_market_closed_cluster`를 검토한다.
  - 운영 규칙: Sentinel 개선은 감지/리포트/알림 계층만 수정한다. score threshold 완화, spread cap 완화, fallback 재개, 자동 매도, holding threshold mutation, bot restart는 별도 단일축 workorder와 rollback guard 없이는 금지한다.
  - 다음 액션: 채택 후보는 날짜별 checklist 신규 항목 또는 Plan Rebase sentinel backlog 문장으로 반영하고 parser 검증을 실행한다. 미채택 후보는 false-positive 사유와 추가 필요 로그를 문서화한다.

- [ ] `[SentinelThresholdFeedback0507-Intraday] Sentinel 이상치의 threshold-cycle 연결/비연결 라우팅 표준화` (`Due: 2026-05-07`, `Slot: INTRADAY`, `TimeWindow: 15:40~15:55`, `Track: RuntimeStability`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [buy_funnel_sentinel.py](/home/ubuntu/KORStockScan/src/engine/buy_funnel_sentinel.py), [holding_exit_sentinel.py](/home/ubuntu/KORStockScan/src/engine/holding_exit_sentinel.py)
  - 판정 기준: 각 Sentinel classification을 `incident/playbook`, `threshold-cycle family candidate`, `instrumentation/logging backlog`, `normal drift/no action` 중 하나로 매핑한다. `UPSTREAM_AI_THRESHOLD`, `LATENCY_DROUGHT`, `PRICE_GUARD_DROUGHT`, `HOLD_DEFER_DANGER`, `SOFT_STOP_WHIPSAW`, `TRAILING_EARLY_EXIT`, `AI_HOLDING_OPS`, `RUNTIME_OPS`별 sample floor, 반복 기준, owner 문서, 금지된 자동변경을 표로 닫는다.
  - why: 이상치를 매번 관찰만 하면 tuning이 끝나지 않는다. 반대로 이상치마다 즉시 threshold를 바꾸면 원인귀속과 rollback guard가 깨진다. 따라서 Sentinel은 자동 튜너가 아니라 threshold-cycle 후보 생성과 incident playbook 분기를 담당한다.
  - 다음 액션: threshold 후보는 `R3_manifest_only`까지만 연결하고, R5 live mutation은 `ThresholdOpsTransition` acceptance와 별도 rollback guard가 없으면 금지한다. instrumentation gap은 다음 거래일 logging workorder로, incident는 사용자 승인 playbook으로 분리한다.

## 장후 체크리스트 (16:00~18:30)

- [ ] `[StatActionEligibleOutcome0507] SAW-3 eligible-but-not-chosen 후행 MFE/MAE 연결 설계` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:30`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: `stat_action_decision_snapshot`의 `eligible_actions/rejected_actions/chosen_action`을 후행 quote/position outcome과 연결해 `post_decision_mfe`, `post_decision_mae`, `missed_upside`, `avoided_loss`를 계산할 수 있는지 확인한다. join key, time horizon, quote source, compact partition read cap, selection-bias caveat를 같이 잠근다.
  - why: 선택된 행동의 realized PnL만 보면 “하지 않은 물타기/불타기/청산”의 기대값을 복원할 수 없다. 이 축이 열려야 행동가중치가 단순 사후 평균이 아니라 기회비용까지 반영한다.
  - 다음 액션: 연결 가능하면 Markdown 리포트에 `eligible_but_not_chosen` 섹션을 추가하고, 불가능하면 누락 필드와 추가 snapshot 필드를 명시한다.

- [ ] `[AIDecisionMatrixShadow0507] ADM-2 holding/exit shadow prompt matrix 주입 설계` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~17:00`, `Track: AIPrompt`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py)
  - 판정 기준: `holding_exit_decision_matrix`를 `prompt_profile=holding` 경로에 shadow-only context로 넣는 설계를 확정한다. legacy/adapter의 `prompt_profile=exit`는 별도 프롬프트가 아니라 holding route alias로만 본다. 확인 항목은 token budget, cache key 영향, matrix_version provenance, Gemini/OpenAI/DeepSeek parity, `action_label/confidence/reason` drift 로그다. live AI 응답 변경은 금지한다.
  - ON/OFF 기준: `ADM-1 report-only`는 ON, `ADM-2 shadow prompt`는 이 항목에서 ON 후보로 설계, `ADM-3 advisory nudge`, `ADM-4 weighted live`, `ADM-5 policy gate`는 OFF 유지다. ADM-3 이상은 별도 checklist에서 `COMPLETED + valid profit_rate`, `GOOD_EXIT/MISSED_UPSIDE`, soft stop tail, 추가매수 기회비용의 비악화가 확인될 때만 연다.
  - why: threshold 산정 결과가 AI 보유/청산 판단에 쓰이려면 사람이 보는 리포트만으로는 부족하다. 다만 첫 단계는 AI 판단 변경이 아니라 동일 장면에서 matrix context가 응답을 어떻게 바꾸는지 shadow diff로 봐야 한다.
  - 다음 액션: shadow diff가 안정적이면 `ADM-3 observe-only nudge`로 넘어가고, 불안정하면 prompt_hint 표현/토큰 범위부터 줄인다.

- [ ] `[PrecloseSellTargetAITelegram0507] preclose sell target AI/Telegram acceptance 분리 검증` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:20`, `Track: Plan`)
  - Source: [preclose-sell-target-revival-plan.md](/home/ubuntu/KORStockScan/docs/preclose-sell-target-revival-plan.md), [2026-05-06-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-06-stage2-todo-checklist.md), [preclose_sell_target_report.py](/home/ubuntu/KORStockScan/src/scanners/preclose_sell_target_report.py)
  - 판정 기준: 5/6 P1 산출물의 `policy_status=report_only`, `live_runtime_effect=false`, `automation_stage=R1_daily_report`를 유지한 채 AI 호출 가능성, 응답 JSON contract, Telegram 전송 대상을 각각 분리 검증한다. 실패 시 AI key/SDK, schema parse, Telegram publish 중 어느 축인지 분리하고 cron 등록은 보류한다.
  - 다음 액션: AI/Telegram acceptance가 통과하면 cron 등록 검토로 넘기되, 자동 주문/threshold mutation과 연결하지 않는다.

- [ ] `[PrecloseSellTargetCron0507] preclose sell target report-only cron 등록 여부 판정` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 17:20~17:35`, `Track: RuntimeStability`)
  - Source: [preclose-sell-target-revival-plan.md](/home/ubuntu/KORStockScan/docs/preclose-sell-target-revival-plan.md), [data/report/README.md](/home/ubuntu/KORStockScan/data/report/README.md), [deploy/run_preclose_sell_target_report.sh](/home/ubuntu/KORStockScan/deploy/run_preclose_sell_target_report.sh)
  - 판정 기준: cron 등록은 `--no-ai --no-telegram` report-only 또는 AI/Telegram acceptance 후 별도 profile 중 하나로만 승인한다. 실행 시간, lock/cooldown 필요 여부, 로그 경로, 실패 알림, holiday skip을 문서화한다.
  - 다음 액션: 승인 시 deploy/cron 문서와 wrapper를 같은 change set으로 맞추고, 미승인 시 수동 실행 명령만 유지한다.

- [ ] `[PrecloseSellTargetConsumer0507] preclose sell target threshold/ADM consumer 연결 범위 확정` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 17:35~17:50`, `Track: Plan`)
  - Source: [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [data/report/README.md](/home/ubuntu/KORStockScan/data/report/README.md), [preclose-sell-target-revival-plan.md](/home/ubuntu/KORStockScan/docs/preclose-sell-target-revival-plan.md)
  - 판정 기준: `data/report/preclose_sell_target/preclose_sell_target_YYYY-MM-DD.json`을 threshold/ADM/swing trailing에서 어떤 단계(`operator review`, `shadow context`, `manifest_only`)까지 소비할지 고정한다. R5 live threshold apply, 자동 주문, bot restart는 금지한다.
  - 다음 액션: consumer가 필요하면 schema field와 consumer owner를 추가 checklist로 분리하고, 필요 없으면 report-only 운영자 검토 산출물로 유지한다.

- [x] `[MonitorSnapshotAsyncCompletion0507] monitor snapshot async completion/failure propagation 보강` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 17:50~18:10`, `Track: RuntimeStability`)
  - Source: [run_monitor_snapshot_cron.sh](/home/ubuntu/KORStockScan/deploy/run_monitor_snapshot_cron.sh), [run_monitor_snapshot_incremental_cron.sh](/home/ubuntu/KORStockScan/deploy/run_monitor_snapshot_incremental_cron.sh), [run_monitor_snapshot_safe.sh](/home/ubuntu/KORStockScan/deploy/run_monitor_snapshot_safe.sh), [monitor_snapshot_runner.py](/home/ubuntu/KORStockScan/src/engine/monitor_snapshot_runner.py)
  - 판정 기준: cron wrapper가 async dispatch만 성공하고 실제 snapshot worker 실패를 놓칠 수 있는지 확인한다. 필요한 경우 `run_id`, expected output manifest, completion marker, stale/incomplete alert, retry/cooldown 경계를 추가한다.
  - 다음 액션: 보강은 산출물 완성/실패 가시성까지만 허용한다. snapshot 결과로 score threshold, spread cap, bot restart를 자동 실행하지 않는다.
  - 반영: `run_monitor_snapshot_safe.sh`에 `MONITOR_SNAPSHOT_ASYNC_WAIT_SEC` 완료 대기 옵션을 추가했다. full snapshot cron은 기본 `1200초` 대기로 async worker 종료를 기다리고, worker 실패/timeout/unknown artifact는 cron exit code로 전파한다. cooldown/lock/preopen/existing manifest skip도 JSON completion artifact에 `status=skipped`, `reason`을 남긴다.
  - 검증: `bash -n deploy/run_monitor_snapshot_cron.sh deploy/run_monitor_snapshot_incremental_cron.sh deploy/run_monitor_snapshot_safe.sh` 통과. cooldown skip 경로에서 async worker completion artifact가 `status=skipped`, `reason=cooldown_active`로 생성되고 wrapper exit code 0을 반환하는 것을 확인했다.

- [x] `[TuningMonitoringPostcloseFallback0507] tuning monitoring postclose lock/retry/status manifest 보강` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:30`, `Track: RuntimeStability`)
  - Source: [run_tuning_monitoring_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_tuning_monitoring_postclose.sh), [build_tuning_monitoring_parquet.py](/home/ubuntu/KORStockScan/src/engine/build_tuning_monitoring_parquet.py), [compare_tuning_shadow_diff.py](/home/ubuntu/KORStockScan/src/engine/compare_tuning_shadow_diff.py)
  - 판정 기준: parquet build, shadow diff, Gemini lab, Claude lab 각 step을 독립 status로 남기고 중간 실패 시 후속 step 차단이 적절한지 판정한다. lock, retry, fail-closed summary, Telegram/admin alert 필요 여부를 함께 확인한다.
  - 다음 액션: 구현 시 status manifest와 retry wrapper는 RuntimeStability 산출물로만 본다. lab/report 결과를 live threshold mutation으로 연결하지 않는다.
  - 반영: `run_tuning_monitoring_postclose.sh`에 lock, per-step retry, fail-closed exit propagation, status manifest를 추가했다. 산출물은 `data/report/tuning_monitoring/status/tuning_monitoring_postclose_YYYY-MM-DD.json`이며, 각 step은 `started/success/failed`, attempt, exit_code, command를 남긴다.
  - 검증: `bash -n deploy/run_tuning_monitoring_postclose.sh` 통과. `TUNING_MONITORING_DRY_RUN=1 TUNING_MONITORING_MAX_RETRIES=1 deploy/run_tuning_monitoring_postclose.sh 2026-05-06`에서 6개 step, 12개 started/success event와 최종 `status=success` manifest 생성을 확인했다.
