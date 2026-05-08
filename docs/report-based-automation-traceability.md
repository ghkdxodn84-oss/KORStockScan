# Report-Based Automation Traceability

기준일: `2026-05-04 KST`

이 문서는 report 기반 자동화가 누락되지 않도록 `산출물 -> 소비자 -> 적용 단계 -> owner`를 추적하는 registry다. 최종 목표는 기대값/순이익 극대화지만, report 산출물이 곧바로 runtime threshold 변경으로 이어지지는 않는다.

## 1. 자동화 단계

| 단계 | 상태 | 의미 | live 영향 |
| --- | --- | --- | --- |
| `R0_collect` | active | runtime compact event, DB completed trade, monitor snapshot을 수집한다 | 없음 |
| `R1_daily_report` | active | 당일 threshold/report-only 산출물을 만든다 | 없음 |
| `R2_cumulative_report` | active | 누적/rolling cohort 산출물을 만든다 | 없음 |
| `R3_manifest_only` | active | 다음 장전 apply plan artifact를 만든다 | 없음 |
| `R4_preopen_apply_candidate` | active | owner/safety guard/sample floor가 닫힌 후보를 `manifest_only`, `calibrated_apply_candidate`, `efficient_tradeoff_canary_candidate`로 분류한다 | 직접 변경 전 단계 |
| `R5_bounded_calibrated_apply` | active | deterministic guard + AI correction guard를 통과한 family를 다음 장전 1회 runtime env로 자동 반영한다. 조건 미달은 rollback이 아니라 calibration trigger다 | 있음 |
| `R6_post_apply_attribution` | active | threshold version별 applied/not-applied cohort와 daily EV performance report를 장후 제출한다 | 없음 |

현재 허용선은 완전 무인 `auto_bounded_live`다. calibration은 매일 `intraday`, `postclose` 2회 생성하고, preopen cron은 전일 report + AI correction guard를 읽어 다음 장전 runtime env를 만든다. env/code hot mutation은 하지 않고, 봇은 기동 시 당일 runtime env를 source한다. safety breach가 아닌 목표 미달은 `calibration_state=adjust_up|adjust_down|hold|hold_sample|hold_no_edge|freeze`로 처리하고, `rollback/safety_revert_required`는 hard/protect/emergency stop 지연, 주문 실패, provenance 손상, same-stage owner 충돌, severe loss guard 초과에만 쓴다. Sentinel 이상치는 자동 튜닝 명령이 아니라 기존 report source bundle 입력이다. 반복 이상치를 이유로 새 관찰축을 늘리지 않고, 운영장애는 incident playbook, 로그 누락은 instrumentation backlog, 정상 변동은 no-action으로 분리한다.

## 2. 산출물 추적성

| 산출물 | Producer | Consumer | 현재 단계 | 다음 owner | 누락 방지 확인 |
| --- | --- | --- | --- | --- | --- |
| `data/threshold_cycle/date=YYYY-MM-DD/family=*/part-*.jsonl` | `backfill_threshold_cycle_events` | `daily_threshold_cycle_report` | `R0_collect` | `ThresholdCollectorIO0506` | immutable snapshot source, checkpoint, read bytes, availability guard |
| `data/report/threshold_cycle_YYYY-MM-DD.json` | `daily_threshold_cycle_report` | `threshold_cycle_preopen_apply`, operator review | `R1_daily_report` | `ThresholdOpsTransition0506` | apply candidate, trade lifecycle attribution, calibration candidates, safety guard, calibration trigger, post-apply attribution, warnings |
| `data/report/threshold_cycle_calibration/threshold_cycle_calibration_YYYY-MM-DD_{intraday,postclose}.json` | `daily_threshold_cycle_report` | operator review, next preopen manifest review | `R4_preopen_apply_candidate` artifact | `ThresholdCalibrationLoop0508`, `EfficientTradeoffCalibration0508` | calibration source bundle, candidate state, safety guard, no runtime mutation |
| `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_YYYY-MM-DD_{intraday,postclose}.{json,md}` | `daily_threshold_cycle_report` via threshold cron wrappers | next preopen auto bounded apply guard | `R4_preopen_apply_candidate` support artifact | `ThresholdAICorrectionCron0508`, `ThresholdUnattendedApply0508` | cron 기본 Gemini proposal 연동, strict schema parse, family bounds/max-step guard, sample-window guard, AI 단독 runtime_change=false |
| `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.{json,md}` | `scalping_pattern_lab_automation` | daily EV report, future implementation order queue | `R6_post_apply_attribution` support artifact | `PatternLabAutomation0508` | Gemini/Claude freshness, consensus findings, existing family inputs, auto family candidates(`allowed_runtime_apply=false`), code improvement orders(`runtime_effect=false`) |
| `data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_YYYY-MM-DD.{json,md}` | `daily_threshold_cycle_report` | operator review, threshold candidate persistence check | `R2_cumulative_report` | `CumulativeThresholdCycleReport0504-Postclose`, `ThresholdOpsTransition0506` | daily/rolling/cumulative 방향성 일치 여부 |
| `data/report/statistical_action_weight/statistical_action_weight_YYYY-MM-DD.{json,md}` | `daily_threshold_cycle_report` | action weight review, ADM ladder, threshold-cycle source bundle | `R1_daily_report` | `StatActionWeight0506`, `StatActionMarkdown0506`, `StatActionEligibleOutcome0507`, `EfficientTradeoffCalibration0508` | bucket sample floor, policy_hint, data completeness, `eligible_but_not_chosen` report-only proxy, candidate_weight_source count |
| `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_YYYY-MM-DD.{json,md}` | `daily_threshold_cycle_report` | ADM advisory canary/live-readiness, threshold-cycle source bundle | `R1_daily_report` | `AIDecisionMatrix0506`, `EfficientTradeoffCalibration0508` | matrix_version, hard_veto, prompt_hint, non-no_clear_edge bucket count |
| `data/report/preclose_sell_target/preclose_sell_target_YYYY-MM-DD.{json,md}` | `preclose_sell_target_report` | operator preclose review. holding/overnight decision support, future threshold/ADM context는 후보만 유지 | `R1_daily_report` | `PrecloseSellTargetRevival0506-Intraday`, `PrecloseSellTargetAIRecovery0508`, `PrecloseSellTargetCronWrapper0508` | `policy_status=report_only`, `live_runtime_effect=false`, AI/Telegram/cron acceptance 분리. 5/7 Gemini key fallback 성공, Telegram 실제 전송/15:00 cron 등록 반영, consumer 범위는 operator review까지만 승인 |
| `data/report/preclose_sell_target/status/preclose_sell_target_YYYY-MM-DD.status.json` | `run_preclose_sell_target_report.sh` | cron/manual wrapper health check | `R0_collect` | `PrecloseSellTargetCron0507`, `PrecloseSellTargetCronWrapper0508` | lock/status/log path/weekend guard, runtime_change=false, cron registration은 별도 승인 필요 |
| `data/report/buy_funnel_sentinel/buy_funnel_sentinel_YYYY-MM-DD.{json,md}` | `buy_funnel_sentinel` | operator intraday review, threshold/anomaly routing | `R1_daily_report` | `BuyFunnelSentinel0506-Intraday`, `SentinelThresholdFeedback0507-Intraday`, `SentinelTelegramRemoval0508` | classification, baseline comparison, forbidden auto mutation, no Telegram alert |
| `data/report/holding_exit_sentinel/holding_exit_sentinel_YYYY-MM-DD.{json,md}` | `holding_exit_sentinel` | operator intraday review, holding/exit anomaly routing | `R1_daily_report` | `HoldingExitSentinel0506-Intraday`, `SentinelThresholdFeedback0507-Intraday`, `SentinelTelegramRemoval0508` | classification, holding/exit conversion, forbidden auto mutation, no Telegram alert |
| `tmp/monitor_snapshot_completion_YYYY-MM-DD_PROFILE.json` | `run_monitor_snapshot_safe.sh` | cron/admin completion check, web async refresh status | `R0_collect` | `MonitorSnapshotAsyncCompletion0507` | async worker pid, result file, status, skip/failure reason, log path |
| `data/report/tuning_monitoring/status/tuning_monitoring_postclose_YYYY-MM-DD.json` | `run_tuning_monitoring_postclose.sh` | postclose monitoring chain health check | `R0_collect` | `TuningMonitoringPostcloseFallback0507` | lock/retry status, per-step exit code, failed step, command provenance |
| `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json` | `threshold_cycle_preopen_apply` | preopen bot start workflow | `R5_bounded_calibrated_apply` | `ThresholdUnattendedApply0508` | apply_mode, auto_apply_decisions, selected family, runtime env, safety guard, calibration trigger, same-stage owner rule |
| `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.{env,json}` | `threshold_cycle_preopen_apply` | `src/run_bot.sh` | `R5_bounded_calibrated_apply` | `ThresholdUnattendedApply0508` | env override provenance, selected family, source report, generated_at |
| `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.{json,md}` | `threshold_cycle_ev_report` | postclose daily EV submission | `R6_post_apply_attribution` | `ThresholdDailyEVReport0508` | selected families, completed valid PnL, entry funnel, holding/exit latency, calibration decisions, pattern lab automation summary |
| threshold version attribution section | `daily_threshold_cycle_report`, `threshold_cycle_ev_report` | post-apply attribution | `R6_post_apply_attribution` active | `ThresholdDailyEVReport0508` | threshold_version, applied/not-applied cohort key, calibration_state, safety_revert_required, daily EV |
| entry passive probe lifecycle events | `sniper_state_handlers` | `backfill_threshold_cycle_events`, `daily_threshold_cycle_report`, daily EV report | `R0_collect -> R6_post_apply_attribution` | `PassiveEntryProbeLifecycle0508` | `entry_order_lifecycle=passive_probe`, bid-1tick adjusted price, submit revalidation age, timeout cancel request/confirm provenance |
| `trade_lifecycle_attribution` section | `daily_threshold_cycle_report` | threshold calibration, AI correction input, daily EV report | `R2_candidate_context -> R6_post_apply_attribution` | `TradeLifecycleAttribution0508` | entry submit/cancel, holding 후보 신호, exit rule/source, post-sell outcome을 `record_id`로 join한 family 공통 전중후 유형 |

## 3. Sentinel Routing Standard

| Sentinel classification | 기본 라우팅 | threshold-cycle 연결 조건 | 금지된 자동변경 |
| --- | --- | --- | --- |
| `UPSTREAM_AI_THRESHOLD` | score50/wait65_74 cohort review, single-axis canary 후보 검토 | `COMPLETED + valid profit_rate`, missed/avoided counterfactual, sample floor, rollback owner가 모두 닫힌 별도 workorder | score threshold 완화, fallback 재개 |
| `LATENCY_DROUGHT` | latency 원인분해, quote freshness/SAFE normal submit 직전 수급 fade review | 두산 rollback 이후에는 spread cap 자동완화 금지. 반복성과 price/latency blocker attribution이 분리될 때만 `R3_manifest_only` 후보 | spread cap 완화, bot restart |
| `PRICE_GUARD_DROUGHT` | price resolver/guard attribution review | guard family sample floor와 fill quality rollback owner가 닫힌 경우만 `R3_manifest_only` 후보 | entry/scale-in guard runtime mutation |
| `HOLD_DEFER_DANGER` | holding_flow_override defer cost/worsen floor review | sell receipt/completed, GOOD_EXIT/MISSED_UPSIDE, defer worsen floor가 daily/rolling/cumulative에서 같은 방향일 때만 후보 | 자동 매도, holding_flow_override mutation |
| `SOFT_STOP_WHIPSAW` | soft stop rebound/tail report-only review | same-stage owner 충돌 해소, sample floor, rollback command가 닫힌 다음 장전 단일 owner 후보 | hard/protect stop 완화, 자동 청산 변경 |
| `TRAILING_EARLY_EXIT` | trailing missed-upside/winner wide-window review | protect/trailing family owner와 rollback guard가 닫힌 `R3_manifest_only` 후보 | trailing threshold runtime mutation |
| `AI_HOLDING_OPS` | AI cache/Tier provenance instrumentation backlog | threshold-cycle 직결 금지. cache 변경은 별도 AI ops workorder 필요 | AI cache TTL mutation, provider routing 변경 |
| `RUNTIME_OPS` | incident/playbook, stale pipeline/cron/runtime health check | threshold-cycle 직결 금지 | bot restart 자동 실행 |
| `NORMAL` | no-action | 없음 | 없음 |

Sentinel routing은 [2026-05-07 checklist](./2026-05-07-stage2-todo-checklist.md) `SentinelThresholdFeedback0507-Intraday`에서 표준화했다. `2026-05-08`부터 Sentinel Telegram 알림과 날짜별 notify state는 삭제됐고, report JSON/Markdown 생성과 classification 갱신만 매 실행 유지한다.

## 4. auto bounded calibration gate

`R5_bounded_calibrated_apply`는 완전 무인으로 실행하되 아래 조건을 deterministic guard와 AI correction guard가 매일 자동 확인한다.

1. 후보 family별 sample floor와 current/recommended diff가 report에 존재한다.
2. `daily`, `rolling`, `cumulative`가 같은 방향을 가리킨다.
3. `main-only`, `normal_only`, `post_fallback_deprecation` cohort를 분리할 수 있다.
4. full fill과 partial fill이 섞여 있으면 손익 결론을 hard 승인 근거로 쓰지 않는다.
5. 같은 stage의 live owner가 하나만 존재한다.
6. safety guard owner, env key, 봇 기동 시 runtime env source 절차가 문서화되어 있다.
7. apply plan은 장중 mutation이 아니라 다음 장전 runtime env manifest로만 반영된다.
8. 적용 후 threshold version별 post-apply attribution과 daily EV report가 생성된다.
9. 조건 미달은 다음 manifest의 `calibration_state`로 조정한다. safety guard 위반 시에만 `safety_revert_required=true`로 원복 후보 처리한다.

첫 bounded calibration family는 `score65_74_recovery_probe`, `bad_entry_refined_canary`, `soft_stop_whipsaw_confirmation`, `holding_flow_ofi_smoothing`, `protect_trailing_smoothing`, `holding_exit_decision_matrix_advisory`다. `trailing_continuation`은 GOOD_EXIT 훼손 리스크가 커서 1차 loop에서는 report/calibration만 수행하고 live apply는 후순위로 둔다. calibration source는 `threshold_cycle` compact event와 함께 `data/report`의 BUY source(`buy_funnel_sentinel`, `sentinel_followup`, `wait6579_ev_cohort`, `missed_entry_counterfactual`, `performance_tuning`), 보유/청산 source(`holding_exit_observation`, `post_sell_feedback`, `trade_review`, `holding_exit_sentinel`), decision-support source(`holding_exit_decision_matrix`, `statistical_action_weight`) 요약을 사용한다. `preclose_sell_target`은 operator review 산출물이며 tuning/calibration source가 아니다.

`pre_submit_price_guard` family에는 `entry_ai_price_canary_applied`, `latency_pass`, `order_bundle_submitted` 외에 `entry_submit_revalidation_warning`, `entry_order_cancel_requested`, `entry_order_cancel_confirmed`, `entry_order_cancel_failed`를 포함한다. `WAIT+score>=75+DANGER+1주 cap+USE_DEFENSIVE` 주문은 새 runtime family가 아니라 같은 entry price owner 내부 `passive_probe` lifecycle로 보며, bid-1tick 조정과 30초 timeout/cancel provenance를 daily EV attribution 입력으로만 사용한다.

## 5. 금지선

- 누적 평균 단독으로 live threshold를 적용하지 않는다.
- report-only 산출물 이름에 `apply_ready=True`가 있어도 `auto_bounded_live`의 deterministic/AI/same-stage owner guard를 통과하기 전에는 runtime 변경으로 해석하지 않는다.
- 장중 threshold runtime mutation은 열지 않는다. 적용 단위는 장후 산출 -> 다음 장전 apply plan -> 장후 attribution이다.
- Project/Calendar owner가 없는 미래 자동화 작업은 유효한 next action으로 보지 않는다.
- Sentinel abnormal alert를 즉시 threshold 완화/강화, fallback 재개, 자동 매도, cache TTL mutation, bot restart로 연결하지 않는다.
- postclose collector가 live `pipeline_events_YYYY-MM-DD.jsonl` 대신 immutable snapshot을 읽어 `checkpoint_completed=true`를 만들더라도, 이는 R0/R1 수집 안정화일 뿐 auto bounded apply 통과로 보지 않는다.

## 6. 다음 추적 항목

미래 작업의 실행 owner는 날짜별 checklist가 소유한다. 현재 연결 owner는 [2026-05-06-stage2-todo-checklist.md](./2026-05-06-stage2-todo-checklist.md)의 `ReportAutomationTraceability0506`이다.
