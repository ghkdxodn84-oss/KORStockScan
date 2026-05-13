# Report-Based Automation Traceability

기준일: `2026-05-12 KST`

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

`2026-05-12`부터 postclose chain은 direct predecessor artifact 계약을 갖는다. 후행 단계는 직전 JSON/Markdown artifact가 없거나 JSON 검증이 끝나지 않으면 `THRESHOLD_CYCLE_ARTIFACT_WAIT_SEC` 동안 대기하고, timeout 시 fail-closed한다. workorder source용 `threshold_cycle_ev` pre-pass와 workorder summary refresh용 post-pass를 분리하며, 최종 `threshold_cycle_postclose_verification`이 latest `START` 이후 wait/fail/timeout과 workorder `generation_id/source_hash/lineage`를 자동 점검한다. 같은 날짜 재생성 판정은 `mtime`이 아니라 `generation_id`, `source_hash`, `lineage.{new,removed,decision_changed}_order_ids`를 우선한다.

## 2. 산출물 추적성

| 산출물 | Producer | Consumer | 현재 단계 | 다음 owner | 누락 방지 확인 |
| --- | --- | --- | --- | --- | --- |
| `data/threshold_cycle/date=YYYY-MM-DD/family=*/part-*.jsonl` | `backfill_threshold_cycle_events` | `daily_threshold_cycle_report` | `R0_collect` | `ThresholdCollectorIO0506` | immutable snapshot source, checkpoint, read bytes, availability guard |
| `data/report/threshold_cycle_YYYY-MM-DD.json` | `daily_threshold_cycle_report` | `threshold_cycle_preopen_apply`, operator review | `R1_daily_report` | `ThresholdOpsTransition0506` | apply candidate, trade lifecycle attribution, calibration candidates, safety guard, calibration trigger, post-apply attribution, warnings |
| `data/report/threshold_cycle_calibration/threshold_cycle_calibration_YYYY-MM-DD_{intraday,postclose}.json` | `daily_threshold_cycle_report` | operator review, next preopen manifest review | `R4_preopen_apply_candidate` artifact | `ThresholdCalibrationLoop0508`, `EfficientTradeoffCalibration0508` | calibration source bundle, candidate state, safety guard, no runtime mutation |
| `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_YYYY-MM-DD_{intraday,postclose}.{json,md}` | `daily_threshold_cycle_report` via threshold cron wrappers | next preopen auto bounded apply guard | `R4_preopen_apply_candidate` support artifact | `ThresholdAICorrectionCron0508`, `ThresholdUnattendedApply0508` | OpenAI correction proposal, strict schema parse, family bounds/max-step guard, sample-window guard, AI 단독 runtime_change=false |
| `data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_YYYY-MM-DD.{json,md}` | `scalping_pattern_lab_automation` | daily EV report, future implementation order queue | `R6_post_apply_attribution` support artifact | `PatternLabAutomation0508` | Gemini/Claude freshness, consensus findings, existing family inputs, auto family candidates(`allowed_runtime_apply=false`), code improvement orders(`runtime_effect=false`) |
| `data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_YYYY-MM-DD.{json,md}` | `swing_pattern_lab_automation` | daily EV report, code improvement workorder, swing approval/source-quality review | `R6_post_apply_attribution` support artifact | `SwingPatternLabAutomation0512` | DeepSeek payload schema, `analysis_window.start == target_date == end`, data-quality warnings, `source_quality_blocked_families`, `runtime_effect=false` orders |
| `data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_YYYY-MM-DD.{json,md}` | `daily_threshold_cycle_report` | operator review, threshold candidate persistence check | `R2_cumulative_report` | `CumulativeThresholdCycleReport0504-Postclose`, `ThresholdOpsTransition0506` | daily/rolling/cumulative 방향성 일치 여부 |
| `data/report/statistical_action_weight/statistical_action_weight_YYYY-MM-DD.{json,md}` | `daily_threshold_cycle_report` | action weight review, ADM ladder, threshold-cycle source bundle | `R1_daily_report` | `StatActionWeight0506`, `StatActionMarkdown0506`, `StatActionEligibleOutcome0507`, `EfficientTradeoffCalibration0508` | bucket sample floor, policy_hint, data completeness, `eligible_but_not_chosen` report-only proxy, candidate_weight_source count |
| `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_YYYY-MM-DD.{json,md}` | `daily_threshold_cycle_report` | ADM advisory canary/live-readiness, threshold-cycle source bundle | `R1_daily_report` | `AIDecisionMatrix0506`, `EfficientTradeoffCalibration0508` | matrix_version, hard_veto, prompt_hint, non-no_clear_edge bucket count |
| `data/report/buy_funnel_sentinel/buy_funnel_sentinel_YYYY-MM-DD.{json,md}` | `buy_funnel_sentinel` | operator intraday review, threshold/anomaly routing | `R1_daily_report` | `BuyFunnelSentinel0506-Intraday`, `SentinelThresholdFeedback0507-Intraday`, `SentinelTelegramRemoval0508` | classification, baseline comparison, forbidden auto mutation, no Telegram alert |
| `data/report/holding_exit_sentinel/holding_exit_sentinel_YYYY-MM-DD.{json,md}` | `holding_exit_sentinel` | operator intraday review, holding/exit anomaly routing | `R1_daily_report` | `HoldingExitSentinel0506-Intraday`, `SentinelThresholdFeedback0507-Intraday`, `SentinelTelegramRemoval0508` | classification, holding/exit conversion, forbidden auto mutation, no Telegram alert |
| `data/report/panic_sell_defense/panic_sell_defense_YYYY-MM-DD.{json,md}` | `panic_sell_defense_report` | operator intraday/postclose review, threshold-cycle source bundle candidate | `R1_daily_report` | `PanicSellDefenseReportOnly0512` | `panic_state`, stop-loss cluster, real/non-real split, active sim/probe provenance, post-sell rebound, forbidden runtime mutation |
| `data/report/panic_buying/panic_buying_YYYY-MM-DD.{json,md}` | `panic_buying_report` | operator intraday/postclose review, threshold-cycle source bundle context | `R1_daily_report` | `PanicBuyingReportOnly0513` | `panic_buy_state`, active/exhausted symbol split, TP counterfactual, `panic_buy_runner_tp_canary`, forbidden runtime mutation |
| `tmp/monitor_snapshot_completion_YYYY-MM-DD_PROFILE.json` | `run_monitor_snapshot_safe.sh` | cron/admin completion check, web async refresh status | `R0_collect` | `MonitorSnapshotAsyncCompletion0507` | async worker pid, result file, status, skip/failure reason, log path |
| `data/report/tuning_monitoring/status/tuning_monitoring_postclose_YYYY-MM-DD.json` | `run_tuning_monitoring_postclose.sh` | postclose monitoring chain health check | `R0_collect` | `TuningMonitoringPostcloseFallback0507` | lock/retry status, per-step exit code, failed step, command provenance |
| `data/ipo_listing_day/status/ipo_listing_day_YYYY-MM-DD.status.json` | `run_ipo_listing_day_autorun.sh` | operator IPO run audit. YAML 존재 시만 별도 real-order runner 실행 | IPO_YAML_GATED_REAL_ORDER | `IpoListingDayYamlGatedAutorun0510` | missing YAML skip, STOP skip, dry-select result, lock/status/log path. threshold-cycle/daily EV consumer 금지 |
| `data/threshold_cycle/apply_plans/threshold_apply_YYYY-MM-DD.json` | `threshold_cycle_preopen_apply` | preopen bot start workflow | `R5_bounded_calibrated_apply` | `ThresholdUnattendedApply0508` | apply_mode, auto_apply_decisions, selected family, runtime env, safety guard, calibration trigger, same-stage owner rule |
| `data/threshold_cycle/runtime_env/threshold_runtime_env_YYYY-MM-DD.{env,json}` | `threshold_cycle_preopen_apply` | `src/run_bot.sh` | `R5_bounded_calibrated_apply` | `ThresholdUnattendedApply0508` | env override provenance, selected family, source report, generated_at |
| `data/report/threshold_cycle_ev/threshold_cycle_ev_YYYY-MM-DD.{json,md}` | `threshold_cycle_ev_report` | postclose daily EV submission | `R6_post_apply_attribution` | `ThresholdDailyEVReport0508` | selected families, completed valid PnL, entry funnel, holding/exit latency, calibration decisions, pattern lab automation summary |
| `data/report/runtime_approval_summary/runtime_approval_summary_YYYY-MM-DD.{json,md}` | `runtime_approval_summary` | operator postclose review, next checklist, approval/workorder triage | `R6_post_apply_attribution` read-only summary | `RuntimeApprovalSummary0512` | `warnings`, scalping selected count, swing requested/approved/blocked, `runtime_mutation_allowed=false`; flow 조정/차단 권한 없음 |
| `data/report/plan_rebase_daily_renewal/plan_rebase_daily_renewal_YYYY-MM-DD.{json,md}` | `plan_rebase_daily_renewal` | Plan Rebase/prompt/AGENTS daily renewal proposal review | `R6_post_apply_attribution` proposal-only artifact | `PlanRebaseDailyRenewal0513` | postclose source bundle 기반 bounded renewal proposal, `document_mutation_allowed=false`, `runtime_mutation_allowed=false`, no file mutation |
| `data/report/code_improvement_workorder/code_improvement_workorder_YYYY-MM-DD.json` + `docs/code-improvement-workorders/code_improvement_workorder_YYYY-MM-DD.md` | `build_code_improvement_workorder` | Codex implementation session, operator triage | implementation-intake artifact | `CodeImprovementWorkorderReview0512` | `generation_id`, `source_hash`, `lineage`, `decision_counts`, `runtime_effect=false`, `allowed_runtime_apply=false`; 생성만으로 repo/runtime 수정 금지 |
| `data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_YYYY-MM-DD.{json,md}` | `verify_threshold_cycle_postclose_chain` | postclose chain health review, workorder regeneration safety | chain verification artifact | `PostcloseChainVerification0512` | latest `START` 이후 predecessor wait/fail/timeout count, direct artifact presence, workorder `generation_id/source_hash/lineage` diff |
| `data/runtime/update_kospi_status/update_kospi_YYYY-MM-DD.json` | `update_kospi.py` | error detector artifact freshness, operator 21:00 data chain review | EOD data-chain status artifact | `RunbookOps` | `status`, `failed_steps`, `warning_steps`, `db_state.latest_quote_date`, recovered/manual recovery steps; `completed_with_warnings`는 DB 적재와 후속 추천/리포트 실패를 분리 |
| threshold version attribution section | `daily_threshold_cycle_report`, `threshold_cycle_ev_report` | post-apply attribution | `R6_post_apply_attribution` active | `ThresholdDailyEVReport0508` | threshold_version, applied/not-applied cohort key, calibration_state, safety_revert_required, daily EV |
| entry passive probe lifecycle events | `sniper_state_handlers` | `backfill_threshold_cycle_events`, `daily_threshold_cycle_report`, daily EV report | `R0_collect -> R6_post_apply_attribution` | `PassiveEntryProbeLifecycle0508` | `entry_order_lifecycle=passive_probe`, bid-1tick adjusted price, submit revalidation age, timeout cancel request/confirm provenance |
| `trade_lifecycle_attribution` section | `daily_threshold_cycle_report` | threshold calibration, AI correction input, daily EV report | `R2_candidate_context -> R6_post_apply_attribution` | `TradeLifecycleAttribution0508` | entry submit/cancel, holding 후보 신호, exit rule/source, post-sell outcome을 `record_id`로 join한 family 공통 전중후 유형 |

## 2.1 Postclose Chain Contract

`deploy/run_threshold_cycle_postclose.sh`의 최신 순서는 아래 계약을 따른다.

1. `swing_daily_simulation_report`를 먼저 생성하고, `swing_lifecycle_audit`/`swing_runtime_approval`은 해당 JSON/Markdown이 존재하고 JSON 검증이 끝난 뒤에만 실행한다.
2. `daily_threshold_cycle_report`는 immutable snapshot/checkpoint를 우선 사용한다. 같은 날짜 retry는 기존 snapshot/checkpoint를 재사용하고 중복 snapshot retention을 정리한다.
3. `threshold_cycle_ev` pre-pass를 생성해 workorder source로 사용한다.
4. `build_code_improvement_workorder`가 code improvement JSON/Markdown을 생성한다.
5. `threshold_cycle_ev` post-pass를 다시 생성해 workorder summary와 source-quality blocker를 refresh한다.
6. `runtime_approval_summary`는 refreshed EV/workorder가 닫힌 뒤에만 실행한다.
7. `plan_rebase_daily_renewal`은 `runtime_approval_summary` 이후 Plan Rebase/prompt/AGENTS 갱신 제안 artifact만 만든다. 기본은 `proposal_only`이며 `document_mutation_allowed=false`, `runtime_mutation_allowed=false`다.
8. 다음 영업일 checklist를 생성한다.
9. `threshold_cycle_postclose_verification`이 최신 run의 predecessor wait/fail/timeout과 workorder lineage를 기록한다.

2026-05-12 기준 검증 결과는 `threshold_cycle_postclose_verification_2026-05-12` `status=pass`, `predecessor_wait_count=0`, `timeout_count=0`, workorder `generation_id=2026-05-12-5abbfc31939d`, `source_hash=5abbfc31939dffedcaab60313d1641234dbc026363b0f2842778d63b45f9440a`, `lineage.new_order_ids=[]`, `lineage.removed_order_ids=[]`, `lineage.decision_changed_order_ids=[]`다.

## 2.2 Source-Quality as Automation Input

report-only 산출물은 runtime mutation 권한이 없지만, source-quality 값은 자동화 체인의 입력으로 사용될 수 있다. 2026-05-12부터 `swing_pattern_lab_automation`/`threshold_cycle_ev`/workorder는 OFI/QI `stale_missing_flag`를 단일 boolean이 아니라 reason과 unique record 기준으로 노출한다.

| 항목 | 최신 처리 |
| --- | --- |
| `micro_missing` / `micro_stale` / `observer_unhealthy` / `micro_not_ready` / `state_insufficient` | DeepSeek fact/payload, swing lifecycle audit, threshold EV, workorder evidence에 reason count로 표면화 |
| unique record count | stage 반복 이벤트와 독립 record를 분리해 `stale_missing_unique_record_count`로 사용 |
| `source_quality_blocked_families` | `swing_scale_in_ofi_qi_confirmation`, `swing_scale_in_real_canary_phase0` 같은 family의 approval/workorder blocker 입력으로 사용 |
| 금지선 | source-quality blocker만으로 runtime threshold/order mutation 금지. approval artifact 또는 family guard 없이 live env apply 금지 |

2026-05-12 기준 `threshold_cycle_ev`의 남은 source-quality warning은 `OFI/QI stale/missing ratio: 0.0776 (9/116); reasons: micro_missing=9, observer_unhealthy=3, micro_not_ready=9, state_insufficient=9`다. 이는 DB/추천 실패가 아니라 scale-in micro-context source-quality blocker다.

## 2.3 Metric Decision Contract

자동화 체인이 소비하는 새 관찰지표와 새 report section은 생성 시점에 판정 계약을 함께 선언해야 한다. 계약이 없으면 해당 지표는 `instrumentation_gap` 또는 `source_quality_blocker`로만 라우팅하고, threshold candidate, approval request, runtime env apply 입력으로 쓰지 않는다.

필수 필드는 아래와 같다.

| 필드 | 의미 |
| --- | --- |
| `metric_role` | 지표의 판정 역할. 아래 role taxonomy 중 하나 이상을 명시한다 |
| `metric_definition` | 분자/분모, 집계 단위, 포함/제외 조건, provenance field |
| `decision_authority` | `real_only`, `main_only_completed`, `sim_equal_weight`, `probe_observe_only`, `combined_diagnostic`, `source_quality_only`, `counterfactual_only` 중 하나 |
| `window_policy` | `daily_only`, `rolling_3d`, `rolling_5d`, `rolling_10d`, `cumulative_since_owner_start`, `post_apply_version_window`, `same_day_intraday_light` 중 primary/secondary window |
| `sample_floor` | hard 판정 최소 표본과 denominator. 표본 미달 시 `hold_sample` 또는 `report_only_calibration`으로 fail-closed |
| `primary_decision_metric` | 자동화 판정에 쓰는 단일 primary metric. EV 계열이면 필드명을 EV로 명확히 쓴다 |
| `secondary_diagnostics` | win rate, blocker share, active recovery, funnel count처럼 primary를 보조하는 지표 |
| `source_quality_gate` | freshness, missing, duplicate, stage provenance, real/sim/probe split 조건 |
| `runtime_effect` | 기본값은 `runtime_effect=false`. runtime 변경 가능 시 approval artifact, env key, rollback guard, same-stage owner rule을 함께 명시 |
| `forbidden_uses` | 단독 live 승인, real-like EV 합산, daily-only apply 등 금지 사용처 |

`metric_role` taxonomy는 아래 기준으로 고정한다.

| metric_role | 판정 용도 | 금지선 |
| --- | --- | --- |
| `primary_ev` | 기대값/순이익 개선 여부의 primary 판정. `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct` 중 하나로 명명한다 | `win_rate` 또는 단순 합산값으로 대체 금지 |
| `diagnostic_win_rate` | 방향성/일관성/꼬리 리스크 보조 진단 | 단독 approval/live/canary 승격 금지 |
| `funnel_count` | 참여율, blocker, coverage, submitted drought 판단 | 손익 edge 또는 live 승인 근거로 단독 사용 금지 |
| `safety_veto` | severe loss, 주문 실패, provenance 손상, hard/protect/emergency stop 지연 차단 | 기대값 개선 지표로 사용 금지 |
| `source_quality_gate` | stale/missing/duplicate/provenance 품질 gate | edge 또는 threshold 추천값으로 사용 금지 |
| `active_unrealized` | open sim/probe 회복률, active position context | closed EV로 해석하거나 realized PnL과 합산 금지 |
| `execution_quality_real_only` | 브로커 체결/취소/receipt 품질 | sim/probe/combined 진단으로 대체 금지 |
| `sim_probe_ev` | sim/probe equal-weight 기대값 관찰 | real execution 품질 또는 실주문 전환 근거로 단독 사용 금지 |

window 해석은 아래처럼 분리한다.

| window_policy | 허용 용도 |
| --- | --- |
| `daily_only` | incident, safety veto, freshness/source-quality, same-day operational trigger. edge apply 승인에는 단독 사용 금지 |
| `rolling_3d` / `rolling_5d` / `rolling_10d` | 방향성 지속성, step size, candidate persistence |
| `cumulative_since_owner_start` | owner/canary baseline 누적 성과와 rollback guard 판정 |
| `post_apply_version_window` | threshold version별 applied/not-applied attribution |
| `same_day_intraday_light` | Sentinel/ops 상태 확인. threshold/live candidate 승격 금지 |

판정 규칙은 다음을 따른다.

1. `win_rate`는 `diagnostic_win_rate`다. 기대값/순이익 목표의 primary 판정은 `primary_ev`가 맡는다.
2. 단순 손익 합산은 EV가 아니다. 필드명은 `simple_sum_profit_pct`로 쓰고, EV 판정 필드는 `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct` 중 하나를 사용한다.
3. `sim_equal_weight`, `probe_observe_only`, `counterfactual_only`, `combined_diagnostic` 권한 지표는 source bundle, approval request, workorder evidence에는 들어갈 수 있지만 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
4. `daily`, `rolling`, `cumulative`가 필요한 family에서 daily-only 악화/개선은 safety veto 또는 calibration trigger로만 쓰고, edge apply 승인은 rolling/cumulative와 source-quality gate가 닫힌 뒤에만 허용한다.
5. 새 관찰지표가 위 필드를 갖지 않으면 자동화 체인은 `hold_sample`, `hold_no_edge`, `source_quality_blocker`, `instrumentation_gap` 중 하나로 닫고 threshold mutation을 만들지 않는다.

새 관찰지표 onboarding은 아래 10개 항목이 모두 닫힌 뒤에만 자동화 source bundle에 편입한다.

| 항목 | 필수 결정 |
| --- | --- |
| 1 | `metric_role` |
| 2 | `decision_authority` |
| 3 | `window_policy` |
| 4 | `primary_decision_metric`과 `secondary_diagnostics` 분리 |
| 5 | `sample_floor`와 denominator |
| 6 | source-quality/provenance gate |
| 7 | forbidden automation / forbidden live uses |
| 8 | consumer와 owner |
| 9 | JSON/Markdown field names |
| 10 | fail-closed behavior |

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

### 3.1 Panic Sell Defense Routing Standard

| panic_state | 기본 라우팅 | threshold-cycle 연결 조건 | 금지된 자동변경 |
| --- | --- | --- | --- |
| `NORMAL` | no-action | 없음 | 없음 |
| `PANIC_SELL` | 신규 live 진입 완화 금지 후보, stop-loss cluster attribution | V2 1차 후보는 `panic_entry_freeze_guard`다. approval artifact, rollback guard, runtime env key가 닫힌 뒤 다음 장전 pre-submit freeze canary로만 검토한다. `panic_stop_confirmation`은 후순위 | score threshold 완화, stop-loss 완화, 자동매도, bot restart |
| `RECOVERY_WATCH` | 회복 evidence 관찰, missed upside/방어효과 분리 | active sim/probe 평균 미실현 수익률 또는 post-sell rebound가 유지되고 provenance pass일 때 report-only 후보 유지 | live threshold mutation, 스윙 실주문 전환 |
| `RECOVERY_CONFIRMED` | `panic_rebound_probe` 후보 검토 | sim/probe only, `actual_order_submitted=false`, `broker_order_forbidden=true`, 장후 attribution과 다음 장전 bounded guard 필요 | broker order 제출, approval artifact 없는 swing real canary |

`panic_sell_defense_report`는 장중 cron으로 5분 주기 생성하고, `2026-05-13`부터 `run_threshold_cycle_postclose.sh`가 threshold-cycle canonical report 생성 직전에 한 번 더 재생성한다. 이 postclose 재생성은 `panic_sell_state_detector`의 microstructure risk-off/recovery signal, stop-loss cluster, active sim/probe recovery, post-sell rebound를 같은 source bundle에 고정하기 위한 것이며 runtime mutation 권한은 없다.

`micro_cusum_observer`는 OFI z-score CUSUM과 2-of-N micro consensus를 `source_quality_gate` / `source_quality_only` / `intraday_observe_only` 계약으로만 노출한다. `primary_decision_metric`이 아니며 `runtime_threshold_apply`, 주문 제출, 자동매도/자동매수, bot restart, provider route 변경 근거로 사용할 수 없다.

`panic_entry_freeze_guard`의 approval artifact 후보는 `data/threshold_cycle/approvals/panic_entry_freeze_guard_YYYY-MM-DD.json`이다. artifact가 없으면 env key를 쓰지 않고, artifact가 있어도 적용 범위는 scalping `entry_pre_submit` 신규 BUY 차단 후보로 제한한다. 기존 보유 청산, stop-loss, trailing, 스윙 실주문에는 영향을 주지 않는다. 상세 workorder는 [panic_entry_freeze_guard_v2_2026-05-13](./code-improvement-workorders/panic_entry_freeze_guard_v2_2026-05-13.md)를 기준으로 한다.

`panic_buying_report`는 장중 cron으로 2분 offset 주기 생성하고, `2026-05-13`부터 `run_threshold_cycle_postclose.sh`가 threshold-cycle canonical report 생성 직전에 한 번 더 재생성한다. 이 postclose 재생성은 `panic_buying_state_detector`의 panic-buy/exhaustion signal과 fixed TP 대비 runner opportunity를 같은 source bundle에 고정하기 위한 것이며 TP/trailing/주문/threshold/provider mutation 권한은 없다.

Panic Telegram 안내는 report 결과의 상태 전환만 소비한다. `notify_panic_state_transition`은 `tmp/panic_state_telegram_notify_state.json`으로 직전 상태를 저장하고, 패닉셀/패닉바잉의 시작과 해제에만 사용자 친화 문구를 보낸다. runtime wrapper 기본 수신자는 전체 등록 사용자이며, `PANIC_*_DRY_RUN=1` 또는 수동 `--audience admin --force` 테스트는 admin only다. 이 알림은 `R1_daily_report` 안내이며 주문/threshold/runtime guard 변경 권한이 없다.

## 4. auto bounded calibration gate

`R5_bounded_calibrated_apply`는 완전 무인으로 실행하되 아래 조건을 deterministic guard와 AI correction guard가 매일 자동 확인한다.

1. 후보 family별 sample floor와 current/recommended diff가 report에 존재한다.
2. `daily`, `rolling`, `cumulative`가 같은 방향을 가리키고, 그 방향은 `diagnostic_win_rate`나 `simple_sum_profit_pct`가 아니라 family 계약의 `primary_ev` metric으로 확인된다.
3. `main-only`, `normal_only`, `post_fallback_deprecation` cohort를 분리할 수 있다.
4. full fill과 partial fill이 섞여 있으면 손익 결론을 hard 승인 근거로 쓰지 않는다.
5. 같은 stage의 live owner가 하나만 존재한다.
6. safety guard owner, env key, 봇 기동 시 runtime env source 절차가 문서화되어 있다.
7. apply plan은 장중 mutation이 아니라 다음 장전 runtime env manifest로만 반영된다.
8. 적용 후 threshold version별 post-apply attribution과 daily EV report가 생성된다.
9. 조건 미달은 다음 manifest의 `calibration_state`로 조정한다. safety guard 위반 시에만 `safety_revert_required=true`로 원복 후보 처리한다.

현재 auto-bounded calibration 후보군은 `score65_74_recovery_probe`, `soft_stop_whipsaw_confirmation`, `holding_flow_ofi_smoothing`, `protect_trailing_smoothing`, `holding_exit_decision_matrix_advisory`, `bad_entry_refined_canary` 등이다. 단, 후보군에 있다는 사실은 apply 승인과 다르다. `bad_entry_refined_canary`는 2026-05-12 기준 joined lifecycle 표본 부족으로 observe-only hold이며, `trailing_continuation`은 GOOD_EXIT 훼손 리스크가 커서 report/calibration만 수행하고 live apply는 후순위로 둔다. calibration source는 `threshold_cycle` compact event와 함께 `data/report`의 BUY source(`buy_funnel_sentinel`, `wait6579_ev_cohort`, `missed_entry_counterfactual`, `performance_tuning`), 보유/청산 source(`holding_exit_observation`, `post_sell_feedback`, `trade_review`, `holding_exit_sentinel`), decision-support source(`holding_exit_decision_matrix`, `statistical_action_weight`) 요약을 사용한다. `sentinel_followup`은 2026-05-07 단발 Markdown follow-up으로 현재 source bundle에서 제외한다. `preclose_sell_target`은 2026-05-10 제거되어 source bundle과 traceability inventory에서 제외한다.

`calibration_source_bundle.report_only_cleanup_audit`는 source bundle consumer가 없는 report-only/legacy 산출물을 매 실행마다 `source_quality_gate`로 감사한다. 현재 관리 대상은 `sentinel_followup`, policy-disabled `server_comparison`, 정기 full snapshot에서 제외된 legacy `add_blocked_lock`, 제거된 `preclose_sell_target`이다. `cleanup_candidate_count > 0`이면 source-quality warning과 정리 후보로 표면화하지만, 이 audit는 `source_quality_only`이며 runtime threshold, 주문, 자동매수/자동매도, bot restart, provider route 변경 권한이 없다.

2026-05-12 postclose 기준 `runtime_approval_summary`는 `warnings=[]`, `runtime_mutation_allowed=false`, `scalping_items=12`, `scalping_selected_auto_bounded_live=2`, `swing_requested=2`, `swing_approved=0`이다. 다음 장전 apply 후보는 deterministic/AI/same-stage guard가 닫힌 family만 인정하고, 스윙 approval request는 별도 approval artifact 없이는 env apply 대상이 아니다.

`pre_submit_price_guard` family에는 `entry_ai_price_canary_applied`, `latency_pass`, `order_bundle_submitted` 외에 `entry_submit_revalidation_warning`, `entry_submit_revalidation_block`, `entry_order_cancel_requested`, `entry_order_cancel_confirmed`, `entry_order_cancel_failed`를 포함한다. `WAIT+score>=75+DANGER+1주 cap+USE_DEFENSIVE` 주문은 새 runtime family가 아니라 같은 entry price owner 내부 `passive_probe` lifecycle로 보며, bid-1tick 조정과 30초 timeout/cancel provenance를 daily EV attribution 입력으로만 사용한다. `passive_probe` 제출 직전 revalidation에서 `stale_context_or_quote`가 확인되면 브로커 제출 전 `entry_submit_revalidation_block`으로 차단하고 `actual_order_submitted=false`를 남긴다.

## 5. 금지선

- 누적 평균 단독으로 live threshold를 적용하지 않는다.
- report-only 산출물 이름에 `apply_ready=True`가 있어도 `auto_bounded_live`의 deterministic/AI/same-stage owner guard를 통과하기 전에는 runtime 변경으로 해석하지 않는다.
- 장중 threshold runtime mutation은 열지 않는다. 적용 단위는 장후 산출 -> 다음 장전 apply plan -> 장후 attribution이다.
- Project/Calendar owner가 없는 미래 자동화 작업은 유효한 next action으로 보지 않는다.
- Sentinel abnormal alert를 즉시 threshold 완화/강화, fallback 재개, 자동 매도, cache TTL mutation, bot restart로 연결하지 않는다.
- postclose collector가 live `pipeline_events_YYYY-MM-DD.jsonl` 대신 immutable snapshot을 읽어 `checkpoint_completed=true`를 만들더라도, 이는 R0/R1 수집 안정화일 뿐 auto bounded apply 통과로 보지 않는다.
- IPO listing-day autorun status는 YAML-gated 실주문 실행 감사용이다. 결과를 threshold-cycle calibration, daily EV, scalping/swing runtime threshold 입력으로 자동 소비하지 않는다.
- `runtime_approval_summary`는 read-only 요약 artifact다. `runtime_mutation_allowed=false`일 때는 flow 조정, 주문 차단, threshold mutation 권한이 없다.
- `plan_rebase_daily_renewal`은 proposal-only 문서 갱신 제안이다. 생성만으로 Plan Rebase, prompt, AGENTS.md, checklist, runtime env를 수정하지 않는다.
- 같은 날짜 workorder 재생성 여부를 `mtime`만으로 판정하지 않는다. `generation_id/source_hash/lineage` diff가 source of truth다.
- `update_kospi_status.completed_with_warnings`는 DB 적재 실패와 동일하지 않다. `failed_steps`를 확인해 `recommend_daily_v2`, dashboard upload, swing daily reports 같은 후행 step 실패를 분리한다.
- `_error.log` 파일명만 보고 모든 `DB` 문자열을 DB 장애로 분류하지 않는다. `log_scanner`는 ERROR/CRITICAL/traceback/exception/에러/오류/실패 후보 라인만 incident 후보로 본다.
- `win_rate`, `simple_sum_profit_pct`, `active_unrealized`, `combined_diagnostic`, `counterfactual_only` 지표는 단독으로 runtime apply, 실주문 전환, threshold 완화/강화 승인 근거가 될 수 없다.
- `metric_role`, `decision_authority`, `window_policy`가 없는 새 관찰지표는 threshold candidate가 아니라 instrumentation/source-quality backlog로만 본다.

## 6. 다음 추적 항목

미래 작업의 실행 owner는 날짜별 checklist가 소유한다. 현재 연결 owner는 [2026-05-13-stage2-todo-checklist.md](./2026-05-13-stage2-todo-checklist.md)의 장전/장중/장후 자동 생성 항목이며, 이전 완료 기록은 [2026-05-12-stage2-todo-checklist.md](./2026-05-12-stage2-todo-checklist.md)의 `PostcloseAutomationHealthCheck20260512`, `CodeImprovementWorkorderReview0512`, `LogScannerDbErrorBurstFalsePositive0512`를 증적으로 본다.
