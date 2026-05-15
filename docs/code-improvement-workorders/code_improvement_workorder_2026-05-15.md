# Code Improvement Workorder - 2026-05-15

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-15.json`
- swing_improvement_automation: `-`
- swing_pattern_lab_automation: `-`
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json`
- threshold_cycle_calibration: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-05-15_postclose.json`
- pipeline_event_verbosity: `-`
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-05-15.json`
- codebase_performance_workorder: `-`
- generated_at: `2026-05-15T14:43:10+09:00`
- generation_id: `2026-05-15-c86461e801f4`
- source_hash: `c86461e801f412aa39be4bb430c3a08a0463c80ee39c69e5983ce061f047dbe0`

## 운영 원칙

- `runtime_effect=false` order만 구현 대상으로 본다.
- fallback 재개, shadow 재개, safety guard 우회는 구현하지 않는다.
- runtime 영향이 생길 수 있는 변경은 feature flag, threshold family metadata, provenance, safety guard를 같이 닫는다.
- 새 family는 `allowed_runtime_apply=false`에서 시작하고, 구현/테스트/guard 완료 후에만 auto_bounded_live 후보가 될 수 있다.
- 구현 후에는 관련 테스트와 parser 검증을 실행하고, 다음 postclose daily EV에서 metric을 확인한다.
- 같은 날짜 workorder를 재생성하면 `generation_id`와 `lineage` diff로 신규/삭제/판정변경 order를 먼저 확인한다.

## 2-Pass 실행 기준

- Pass 1: `implement_now` 중 instrumentation/report/provenance 구현만 먼저 수행한다.
- Regeneration: 관련 postclose report와 이 workorder를 재생성하고 `lineage` diff를 확인한다.
- Pass 2: 재생성 후 새로 생긴 `runtime_effect=false` order만 추가 구현한다.
- Final freeze: `generation_id`, `source_hash`, 신규/삭제/판정변경 order를 최종 보고에 남긴다.
- 권장 지시문: `implement_now를 2-pass로 처리: Pass1 instrumentation/report/provenance 구현, 관련 리포트 재생성 후 workorder diff 확인, 신규 runtime_effect=false 항목만 Pass2 구현, 마지막에 generation_id/source_hash 기준으로 final freeze 보고`

## Snapshot Lineage

- previous_exists: `True`
- previous_generation_id: `2026-05-15-1b3477b0c7f0`
- previous_source_hash: `1b3477b0c7f02aa106966407e781ce80b00d5ec3ede0025fb1cb4fe518b108a3`
- new_order_ids: `['order_panic_buying_source_quality_market_breadth_micro_coverage', 'order_panic_sell_defense_lifecycle_transition_pack', 'order_threshold_window_policy_source_snapshot_alignment']`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `5`
- scalping_source_order_count: `0`
- swing_source_order_count: `0`
- swing_lab_source_order_count: `0`
- threshold_ev_source_order_count: `5`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `2`
- codebase_performance_source_order_count: `0`
- panic_lifecycle_source_order_count: `2`
- selected_order_count: `5`
- decision_counts: `{'implement_now': 3, 'design_family_candidate': 1, 'defer_evidence': 1}`
- gemini_fresh: `None`
- claude_fresh: `None`
- swing_lifecycle_audit_available: `False`
- swing_pattern_lab_automation_available: `False`
- swing_pattern_lab_fresh: `None`
- swing_threshold_ai_status: `None`
- daily_ev_available: `True`

## Codex 실행 지시

아래 order를 위에서부터 순서대로 처리한다. 각 order는 `판정 -> 근거 -> 다음 액션`으로 닫고, 코드 변경 시 관련 문서와 테스트를 함께 갱신한다.

필수 검증:

```bash
PYTHONPATH=. .venv/bin/pytest -q <관련 테스트 파일>
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
git diff --check
```

threshold/postclose 체인 영향 시 추가 검증:

```bash
bash -n deploy/run_threshold_cycle_preopen.sh deploy/run_threshold_cycle_calibration.sh deploy/run_threshold_cycle_postclose.sh
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_threshold_cycle_ev_report.py
```

## Implementation Orders

### 1. `order_ai_source_quality_not_evaluated_provenance`

- title: AI source-quality not-evaluated provenance for cooldown and score50 paths
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `observation_source_quality_audit`
- lifecycle_stage: `source_quality_gate`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `-`
- confidence: `audit`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_source_quality_attribution_only
- evidence: `status=warning`, `event_count=596422`, `warning_stage_count=7`, `warning_stages=ai_confirmed,blocked_ai_score,wait65_79_ev_candidate,blocked_strength_momentum,blocked_overbought,swing_probe_state_persisted,scale_in_price_p2_observe`, `high_volume_no_source_field_stage_count=0`, `decision_authority=source_quality_only`, `runtime_effect=false`
- parity_contract: -
- next_postclose_metric: observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/observation_source_quality_audit.py`
- acceptance_tests: `pytest src/tests/test_observation_source_quality_audit.py src/tests/test_state_handler_fast_signatures.py`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 2. `order_swing_source_quality_micro_context_provenance`

- title: Swing source-quality micro context provenance
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `observation_source_quality_audit`
- lifecycle_stage: `source_quality_gate`
- target_subsystem: `runtime_instrumentation`
- route: `instrumentation_order`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `-`
- confidence: `audit`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: none_direct_source_quality_attribution_only
- evidence: `status=warning`, `event_count=596422`, `warning_stage_count=7`, `warning_stages=ai_confirmed,blocked_ai_score,wait65_79_ev_candidate,blocked_strength_momentum,blocked_overbought,swing_probe_state_persisted,scale_in_price_p2_observe`, `high_volume_no_source_field_stage_count=0`, `decision_authority=source_quality_only`, `runtime_effect=false`, `swing_warning_stages=swing_probe_state_persisted,scale_in_price_p2_observe`, `swing_probe_state_persisted:sample_count=77 missing_fields=metric_role,decision_authority,runtime_effect,forbidden_uses`, `scale_in_price_p2_observe:sample_count=22 missing_fields=orderbook_micro_ready,orderbook_micro_state,orderbook_micro_reason,orderbook_micro_snapshot_age_ms,orderbook_micro_observer_healthy`
- parity_contract: -
- next_postclose_metric: observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/observation_source_quality_audit.py`, `src/engine/build_code_improvement_workorder.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `pytest src/tests/test_observation_source_quality_audit.py src/tests/test_swing_model_selection_funnel_repair.py src/tests/test_build_code_improvement_workorder.py`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 3. `order_threshold_window_policy_source_snapshot_alignment`

- title: threshold window policy source snapshot alignment
- decision: `implement_now`
- decision_reason: instrumentation/provenance work can improve attribution without direct runtime mutation
- source_report_type: `threshold_cycle_calibration`
- lifecycle_stage: `threshold_cycle`
- target_subsystem: `threshold_cycle_report`
- route: `instrumentation_order`
- mapped_family: `-`
- threshold_family: `window_policy_registry`
- improvement_type: `source_quality_alignment`
- confidence: `consensus`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent daily-only or snapshot-only calibration blind spots by aligning rolling/cumulative source metrics, snapshot denominators, AI correction context, and EV/workorder rendering.
- evidence: `issue_counts={"rolling_source_snapshot_mismatch": 4}`, `affected_families=trailing_continuation,score65_74_recovery_probe,liquidity_gate_refined_candidate,overbought_gate_refined_candidate`, `family=trailing_continuation primary=rolling_10d state=freeze primary_sample=119 snapshot_sample=12 source_sample=119 issues=rolling_source_snapshot_mismatch`, `family=score65_74_recovery_probe primary=rolling_5d state=adjust_up primary_sample=189 snapshot_sample=0 source_sample=189 issues=rolling_source_snapshot_mismatch`, `family=liquidity_gate_refined_candidate primary=rolling_5d state=hold primary_sample=28009 snapshot_sample=0 source_sample=28009 issues=rolling_source_snapshot_mismatch`, `family=overbought_gate_refined_candidate primary=rolling_5d state=hold primary_sample=471261 snapshot_sample=0 source_sample=471261 issues=rolling_source_snapshot_mismatch`
- parity_contract: -
- next_postclose_metric: window_policy_audit should have no daily_only_leak or rolling_consumer_gap; rolling_source_snapshot_mismatch must be explained as rendering-only or eliminated.
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/threshold_cycle_ev_report.py`, `src/engine/build_code_improvement_workorder.py`, `data/threshold_cycle/README.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_daily_threshold_cycle_report.py src/tests/test_build_code_improvement_workorder.py`, `threshold_cycle_YYYY-MM-DD.json includes window_policy_audit and calibration_source_bundle_by_window lineage`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 4. `order_panic_sell_defense_lifecycle_transition_pack`

- title: panic sell defense lifecycle transition pack
- decision: `design_family_candidate`
- decision_reason: finding needs family design; allowed_runtime_apply remains false until metadata/tests/guards are closed
- source_report_type: `threshold_cycle_calibration_source_bundle`
- lifecycle_stage: `holding_exit`
- target_subsystem: `panic_sell_defense`
- route: `auto_family_candidate`
- mapped_family: `-`
- threshold_family: `panic_sell_defense`
- improvement_type: `runtime_transition_design`
- confidence: `consensus`
- priority: `6`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Use panic-sell simulation and post-sell rebound evidence to propose threshold/guard changes, then request explicit live-runtime approval without mutating exits automatically.
- evidence: `panic_state=PANIC_SELL`, `panic_regime_mode=PANIC_DETECTED`, `stop_loss_exit_count=3`, `confirmation_eligible_exit_count=2`, `active_sim_probe_positions=10`, `post_sell_rebound_above_sell_10_20m_pct=0.0`, `microstructure_market_risk_state=RISK_OFF`, `microstructure_confirmed_risk_off_advisory=True`, `microstructure_portfolio_local_risk_off_only=False`, `market_breadth_followup_candidate=False`, `source_quality_blockers=[]`, `candidate_status={'panic_entry_freeze_guard': 'report_only_candidate', 'panic_stop_confirmation': 'report_only_candidate', 'panic_rebound_probe': 'hold_until_recovery_confirmed', 'panic_attribution_pack': 'active_report_only'}`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: panic_sell_defense should expose simulation EV, rollback guard, approval artifact status, market/breadth confirmation, and candidate-specific threshold recommendations before any runtime transition.
- files_likely_touched: `src/engine/panic_sell_defense_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/plan-korStockScanPerformanceOptimization.rebase.md`
- acceptance_tests: `pytest panic sell defense/report lifecycle tests`, `pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`
- automation_reentry: Create report-only family metadata first; only later can auto_bounded_live consider it.

실행 기준:

- 새 family 후보 metadata와 report-only source를 설계한다.
- `allowed_runtime_apply=false`를 유지한다.
- sample floor, safety guard, target env key, tests가 닫히기 전 runtime 적용 금지.

### 5. `order_panic_buying_source_quality_market_breadth_micro_coverage`

- title: panic buying source-quality market breadth and micro coverage
- decision: `defer_evidence`
- decision_reason: route is not strong enough for immediate implementation
- source_report_type: `threshold_cycle_calibration_source_bundle`
- lifecycle_stage: `source_quality`
- target_subsystem: `panic_buying`
- route: `source_quality_blocker`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `source_quality_instrumentation`
- confidence: `consensus`
- priority: `7`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Route market breadth and micro coverage gaps as source-quality blockers before any panic-buying runtime candidate.
- evidence: `panic_buy_state=NORMAL`, `panic_buy_regime_mode=NORMAL`, `panic_buy_active_count=0`, `exhaustion_confirmed_count=0`, `tp_counterfactual_count=8`, `trailing_winner_count=4`, `market_wide_panic_buy_confirmed=False`, `market_breadth_risk_on_advisory=False`, `missing_orderbook_count=13`, `missing_trade_aggressor_count=13`, `source_quality_blockers=['panic_buy_orderbook_collector_coverage_gap']`, `candidate_status={'panic_buy_runner_tp_canary': 'hold_until_confirmed_panic_buy_with_tp_context'}`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: panic_buying source-quality blockers must be resolved or explicitly carried before runner TP approval is reviewed.
- files_likely_touched: `src/engine/panic_buying_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/plan-korStockScanPerformanceOptimization.rebase.md`, `docs/code-improvement-workorders/panic_buying_regime_mode_v2_2026-05-14.md`
- acceptance_tests: `pytest src/tests/test_panic_buying_report.py`, `pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`
- automation_reentry: Keep in generated workorder as deferred context and re-check after next daily EV report.

실행 기준:

- 구현하지 말고 부족한 evidence와 다음 확인 artifact를 명시한다.
- 필요한 경우 report warning 또는 다음 pattern lab 재평가 항목으로만 남긴다.

## 자동화체인 재투입

- 구현 결과는 `2026-05-16` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `paste generated markdown into a Codex session and request implementation`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
