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
- threshold_cycle_ev: `-`
- threshold_cycle_calibration: `-`
- pipeline_event_verbosity: `-`
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-05-15.json`
- codebase_performance_workorder: `-`
- generated_at: `2026-05-15T11:55:28+09:00`
- generation_id: `2026-05-15-6cb38b561ab7`
- source_hash: `6cb38b561ab716ec5785eba6485a02cff5ecd94a3743bcc89bbfda43615e2854`

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

- previous_exists: `False`
- previous_generation_id: `-`
- previous_source_hash: `-`
- new_order_ids: `['order_ai_source_quality_not_evaluated_provenance', 'order_high_volume_diagnostic_stage_contract_labels']`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `2`
- scalping_source_order_count: `0`
- swing_source_order_count: `0`
- swing_lab_source_order_count: `0`
- threshold_ev_source_order_count: `2`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `2`
- codebase_performance_source_order_count: `0`
- panic_lifecycle_source_order_count: `0`
- selected_order_count: `2`
- decision_counts: `{'implement_now': 2}`
- gemini_fresh: `None`
- claude_fresh: `None`
- swing_lifecycle_audit_available: `False`
- swing_pattern_lab_automation_available: `False`
- swing_pattern_lab_fresh: `None`
- swing_threshold_ai_status: `None`
- daily_ev_available: `False`

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
- evidence: `status=warning`, `event_count=457732`, `warning_stage_count=5`, `warning_stages=ai_confirmed,blocked_ai_score,wait65_79_ev_candidate,blocked_strength_momentum,blocked_overbought`, `high_volume_no_source_field_stage_count=8`, `decision_authority=source_quality_only`, `runtime_effect=false`
- parity_contract: -
- next_postclose_metric: observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/observation_source_quality_audit.py`
- acceptance_tests: `pytest src/tests/test_observation_source_quality_audit.py src/tests/test_state_handler_fast_signatures.py`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

### 2. `order_high_volume_diagnostic_stage_contract_labels`

- title: High-volume diagnostic stage metric contract labels
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
- evidence: `status=warning`, `event_count=457732`, `warning_stage_count=5`, `warning_stages=ai_confirmed,blocked_ai_score,wait65_79_ev_candidate,blocked_strength_momentum,blocked_overbought`, `high_volume_no_source_field_stage_count=8`, `decision_authority=source_quality_only`, `runtime_effect=false`, `gap_stages=strength_momentum_observed,blocked_swing_score_vpw,blocked_swing_gap,strength_momentum_pass,blocked_liquidity,dynamic_vpw_override_pass,first_ai_wait,swing_probe_state_persisted`
- parity_contract: -
- next_postclose_metric: observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count
- files_likely_touched: `src/engine/sniper_state_handlers.py`, `src/engine/observation_source_quality_audit.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `pytest src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py`
- automation_reentry: After implementation, next postclose report must show source freshness or warning reduction.

실행 기준:

- instrumentation/provenance/report source 보강을 우선 구현한다.
- runtime 판단값을 직접 바꾸지 않는다.
- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.

## 자동화체인 재투입

- 구현 결과는 `2026-05-16` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `paste generated markdown into a Codex session and request implementation`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
