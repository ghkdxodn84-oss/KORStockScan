# Code Improvement Workorder - 2026-05-14

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-14.json`
- swing_improvement_automation: `-`
- swing_pattern_lab_automation: `-`
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-14.json`
- threshold_cycle_calibration: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-05-14_postclose.json`
- generated_at: `2026-05-14T10:11:13+09:00`
- generation_id: `2026-05-14-80aaa3ea5857`
- source_hash: `80aaa3ea5857f83e8e43f51e93d843c03919164697bbe020ca446548da82c9c5`

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
- previous_generation_id: `2026-05-14-80aaa3ea5857`
- previous_source_hash: `80aaa3ea5857f83e8e43f51e93d843c03919164697bbe020ca446548da82c9c5`
- new_order_ids: `[]`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `2`
- scalping_source_order_count: `0`
- swing_source_order_count: `0`
- swing_lab_source_order_count: `0`
- threshold_ev_source_order_count: `2`
- panic_lifecycle_source_order_count: `2`
- selected_order_count: `2`
- decision_counts: `{'design_family_candidate': 2}`
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

### 1. `order_panic_sell_defense_lifecycle_transition_pack`

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
- expected_ev_effect: Use panic-sell simulation and post-sell rebound evidence to propose threshold/guard changes, then request explicit live-runtime approval without mutating exits automatically.
- evidence: `panic_state=NORMAL`, `stop_loss_exit_count=0`, `confirmation_eligible_exit_count=0`, `active_sim_probe_positions=10`, `post_sell_rebound_above_sell_10_20m_pct=0.0`, `microstructure_market_risk_state=NEUTRAL`, `microstructure_confirmed_risk_off_advisory=False`, `microstructure_portfolio_local_risk_off_only=False`, `market_breadth_followup_candidate=True`, `source_quality_blockers=[]`, `candidate_status={'panic_entry_freeze_guard': 'inactive_no_panic', 'panic_stop_confirmation': 'hold_no_eligible_exit', 'panic_rebound_probe': 'hold_until_recovery_confirmed', 'panic_attribution_pack': 'active_report_only'}`, `allowed_runtime_apply=false`
- next_postclose_metric: panic_sell_defense should expose simulation EV, rollback guard, approval artifact status, market/breadth confirmation, and candidate-specific threshold recommendations before any runtime transition.
- files_likely_touched: `src/engine/panic_sell_defense_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/plan-korStockScanPerformanceOptimization.rebase.md`
- acceptance_tests: `pytest panic sell defense/report lifecycle tests`, `pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`
- automation_reentry: Create report-only family metadata first; only later can auto_bounded_live consider it.

실행 기준:

- 새 family 후보 metadata와 report-only source를 설계한다.
- `allowed_runtime_apply=false`를 유지한다.
- sample floor, safety guard, target env key, tests가 닫히기 전 runtime 적용 금지.

### 2. `order_panic_buy_runner_tp_canary_lifecycle_pack`

- title: panic buy runner TP canary lifecycle pack
- decision: `design_family_candidate`
- decision_reason: finding needs family design; allowed_runtime_apply remains false until metadata/tests/guards are closed
- source_report_type: `threshold_cycle_calibration_source_bundle`
- lifecycle_stage: `holding_exit`
- target_subsystem: `panic_buying`
- route: `auto_family_candidate`
- mapped_family: `-`
- threshold_family: `panic_buy_runner_tp_canary`
- improvement_type: `runtime_transition_design`
- confidence: `consensus`
- priority: `7`
- runtime_effect: `False`
- expected_ev_effect: Use panic-buying TP counterfactuals to reduce missed upside versus full fixed-TP exits, while keeping hard/protect/emergency stops and order provenance guards dominant.
- evidence: `panic_buy_state=NORMAL`, `panic_buy_active_count=0`, `exhaustion_confirmed_count=0`, `tp_counterfactual_count=0`, `trailing_winner_count=0`, `candidate_status={'panic_buy_runner_tp_canary': 'hold_until_confirmed_panic_buy_with_tp_context'}`, `allowed_runtime_apply=false`
- next_postclose_metric: panic_buying should expose runner-vs-full-TP EV, MAE/giveback/sell-failure rollback guards, approval artifact status, and no live TP mutation before approval.
- files_likely_touched: `src/engine/panic_buying_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/plan-korStockScanPerformanceOptimization.rebase.md`
- acceptance_tests: `pytest src/tests/test_panic_buying_report.py`, `pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`
- automation_reentry: Create report-only family metadata first; only later can auto_bounded_live consider it.

실행 기준:

- 새 family 후보 metadata와 report-only source를 설계한다.
- `allowed_runtime_apply=false`를 유지한다.
- sample floor, safety guard, target env key, tests가 닫히기 전 runtime 적용 금지.

## 자동화체인 재투입

- 구현 결과는 `2026-05-15` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `paste generated markdown into a Codex session and request implementation`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
