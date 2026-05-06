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
| `R4_preopen_apply_candidate` | pending acceptance | owner/rollback/sample floor가 닫힌 후보만 장전 적용 대상으로 분류한다 | 직접 변경 전 단계 |
| `R5_live_threshold_apply` | blocked | env/code 반영, restart, runtime provenance까지 자동화한다 | 있음 |
| `R6_post_apply_attribution` | pending acceptance | threshold version별 실적, rollback guard, 다음 weight 조정 근거를 장후 제출한다 | 없음 |

현재 허용선은 `R3_manifest_only`까지다. `R5_live_threshold_apply`는 `ThresholdOpsTransition0506` acceptance와 별도 workorder가 없으면 열지 않는다. Sentinel 이상치는 자동 튜닝 명령이 아니라 report/playbook 라우팅 입력이다. 반복 이상치만 `threshold-family candidate`로 연결하고, 운영장애는 incident playbook, 로그 누락은 instrumentation backlog, 정상 변동은 no-action으로 분리한다.

## 2. 산출물 추적성

| 산출물 | Producer | Consumer | 현재 단계 | 다음 owner | 누락 방지 확인 |
| --- | --- | --- | --- | --- | --- |
| `data/threshold_cycle/date=YYYY-MM-DD/family=*/part-*.jsonl` | `backfill_threshold_cycle_events` | `daily_threshold_cycle_report` | `R0_collect` | `ThresholdCollectorIO0506` | immutable snapshot source, checkpoint, read bytes, availability guard |
| `data/report/threshold_cycle_YYYY-MM-DD.json` | `daily_threshold_cycle_report` | `threshold_cycle_preopen_apply`, operator review | `R1_daily_report` | `ThresholdOpsTransition0506` | apply candidate, rollback guard, warnings |
| `data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_YYYY-MM-DD.{json,md}` | `daily_threshold_cycle_report` | operator review, threshold candidate persistence check | `R2_cumulative_report` | `CumulativeThresholdCycleReport0504-Postclose`, `ThresholdOpsTransition0506` | daily/rolling/cumulative 방향성 일치 여부 |
| `data/report/statistical_action_weight/statistical_action_weight_YYYY-MM-DD.{json,md}` | `daily_threshold_cycle_report` | action weight review, ADM ladder | `R1_daily_report` | `StatActionWeight0506`, `StatActionMarkdown0506` | bucket sample floor, policy_hint, data completeness |
| `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_YYYY-MM-DD.{json,md}` | `daily_threshold_cycle_report` | ADM ladder | `R1_daily_report` | `AIDecisionMatrix0506` | matrix_version, hard_veto, prompt_hint |
| `data/report/preclose_sell_target/preclose_sell_target_YYYY-MM-DD.{json,md}` | `preclose_sell_target_report` | operator preclose review, holding/overnight decision support, future threshold/ADM context | `R1_daily_report` | `PrecloseSellTargetRevival0506-Intraday` | `policy_status=report_only`, `live_runtime_effect=false`, AI/Telegram/cron acceptance 분리 |
| `data/report/buy_funnel_sentinel/buy_funnel_sentinel_YYYY-MM-DD.{json,md}` | `buy_funnel_sentinel` | Telegram admin alert, operator intraday review, threshold/anomaly routing | `R1_daily_report` | `BuyFunnelSentinel0506-Intraday`, `SentinelThresholdFeedback0507-Intraday` | classification, baseline comparison, forbidden auto mutation |
| `data/report/holding_exit_sentinel/holding_exit_sentinel_YYYY-MM-DD.{json,md}` | `holding_exit_sentinel` | Telegram admin alert, operator intraday review, holding/exit anomaly routing | `R1_daily_report` | `HoldingExitSentinel0506-Intraday`, `SentinelThresholdFeedback0507-Intraday` | classification, holding/exit conversion, forbidden auto mutation |
| `tmp/monitor_snapshot_completion_YYYY-MM-DD_PROFILE.json` | `run_monitor_snapshot_safe.sh` | cron/admin completion check, web async refresh status | `R0_collect` | `MonitorSnapshotAsyncCompletion0507` | async worker pid, result file, status, skip/failure reason, log path |
| `data/report/tuning_monitoring/status/tuning_monitoring_postclose_YYYY-MM-DD.json` | `run_tuning_monitoring_postclose.sh` | postclose monitoring chain health check | `R0_collect` | `TuningMonitoringPostcloseFallback0507` | lock/retry status, per-step exit code, failed step, command provenance |
| `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json` | `threshold_cycle_preopen_apply` | preopen operator/bot start workflow | `R3_manifest_only` | `ThresholdOpsTransition0506` | apply_mode, blocked reason, owner_rule |
| threshold version attribution report | 미구현 | post-apply attribution | `R6_post_apply_attribution` pending | `ThresholdOpsTransition0506` 후속 | threshold_version, applied/not-applied cohort, rollback guard |
| auto apply/restart wrapper | 미구현 | preopen automation | `R5_live_threshold_apply` blocked | 별도 workorder 필요 | env provenance, restart result, rollback command |

## 3. 자동 threshold 적용 acceptance gate

`R5_live_threshold_apply`로 넘어가려면 아래가 모두 checklist에 닫혀야 한다.

1. 후보 family별 sample floor와 current/recommended diff가 report에 존재한다.
2. `daily`, `rolling`, `cumulative`가 같은 방향을 가리킨다.
3. `main-only`, `normal_only`, `post_fallback_deprecation` cohort를 분리할 수 있다.
4. full fill과 partial fill이 섞여 있으면 손익 결론을 hard 승인 근거로 쓰지 않는다.
5. 같은 stage의 live owner가 하나만 존재한다.
6. rollback owner, rollback command, env key, restart 필요 여부가 문서화되어 있다.
7. apply plan은 장중 mutation이 아니라 다음 장전 immutable manifest로만 반영된다.
8. 적용 후 threshold version별 post-apply attribution report가 생성된다.
9. rollback guard 위반 시 자동 적용을 멈추고 `manifest_only`로 복귀한다.

## 4. 금지선

- 누적 평균 단독으로 live threshold를 적용하지 않는다.
- report-only 산출물 이름에 `apply_ready=True`가 있어도 이 문서의 `R5` gate를 통과하기 전에는 runtime 변경으로 해석하지 않는다.
- `ThresholdOpsTransition0506` 전에는 bot restart 자동화와 live threshold mutation을 열지 않는다.
- Project/Calendar owner가 없는 미래 자동화 작업은 유효한 next action으로 보지 않는다.
- Sentinel abnormal alert를 즉시 threshold 완화/강화, fallback 재개, 자동 매도, cache TTL mutation, bot restart로 연결하지 않는다.
- postclose collector가 live `pipeline_events_YYYY-MM-DD.jsonl` 대신 immutable snapshot을 읽어 `checkpoint_completed=true`를 만들더라도, 이는 R0/R1 수집 안정화일 뿐 R5 live apply 승인으로 보지 않는다.

## 5. 다음 추적 항목

미래 작업의 실행 owner는 날짜별 checklist가 소유한다. 현재 연결 owner는 [2026-05-06-stage2-todo-checklist.md](./2026-05-06-stage2-todo-checklist.md)의 `ReportAutomationTraceability0506`이다.
