# Position Sizing Dynamic Formula Workorder

기준일: `2026-05-14 KST`
owner: `position_sizing_dynamic_formula`
상태: `p1_report_source_bundle_active_runtime_effect_false`

## 1. 목적

`position_sizing_dynamic_formula`는 실주문 동적수량 산식 자체를 튜닝하는 별도 owner다. `position_sizing_cap_release`가 1주 cap 해제 승인요청을 맡는 반면, 이 owner는 cap 안팎에서 사용할 수량 산식의 입력, 품질, EV, approval schema를 정의한다.

이번 workorder는 문서/산출물 계약을 여는 단계이며 runtime threshold, 주문 수량 guard, cap, provider, bot restart를 변경하지 않는다.

## 2. 입력 계약

산식 후보는 아래 입력을 명시해야 한다.

| 입력 | 의미 | source 후보 |
| --- | --- | --- |
| `score` | AI/Gatekeeper confidence 또는 recommendation score | `pipeline_events`, `buy_funnel_sentinel`, `wait6579_ev_cohort` |
| `strategy` | `SCALPING`, `KOSPI_ML`, `KOSDAQ_ML`, scale-in arm | `recommendation_history`, runtime event |
| `volatility` | 최근 intraday 변동성, gap, range | market snapshot, performance tuning |
| `liquidity` | 거래대금, 체결강도, 호가 잔량/깊이 | scanner/runtime market data |
| `spread` | submit 직전 spread bps | pre-submit/scale-in price guard event |
| `price_band` | 가격대 bucket | runtime quote/recommendation |
| `recent_loss` | 최근 closed loss, severe downside, stop cluster | completed trade, sentinel, panic source bundle |
| `portfolio_exposure` | open position count/notional, same-symbol exposure | runtime state, account/order state |

필수 provenance는 아래 필드를 포함한다.

- `position_sizing_formula_owner=position_sizing_dynamic_formula`
- `formula_version`
- `formula_mode=report_only|approval_required|approved_live`
- `input_score`
- `input_strategy`
- `input_volatility_bucket`
- `input_liquidity_bucket`
- `input_spread_bps`
- `input_price_band`
- `input_recent_loss_bucket`
- `input_portfolio_exposure_bucket`
- `baseline_qty`
- `candidate_qty`
- `effective_qty`
- `qty_cap_applied`
- `qty_cap_reason`
- `actual_order_submitted`
- `budget_authority`

## 3. Source Bundle

1차 source bundle은 새 standalone 관찰축을 늘리지 않고 기존 산출물을 재사용한다.

| source | 용도 | 필수 gate |
| --- | --- | --- |
| `threshold_cycle.calibration_source_bundle.completed_by_source.real` | real-only closed EV와 downside | `COMPLETED + valid profit_rate` only |
| `buy_funnel_sentinel` | entry blocker, submitted drought, score/strategy funnel | report-only, source freshness |
| `wait6579_ev_cohort` | score 65~79 missed/probe EV | `actual_order_submitted=false` 분리 |
| `missed_entry_counterfactual` | missed upside와 candidate sizing 기회비용 | counterfactual-only |
| `scalp_sim_ev_midcheck` | sim/probe qty source와 active/open split | sim/probe 권한 분리 |
| `holding_exit_sentinel` | stop/exit pressure와 non-real split | real/non-real split pass |
| `panic_sell_defense` | recent loss/source-quality blocker | market context와 real/non-real split pass |
| `scale_in_price_guard` source metrics | spread/stale quote/scale-in price quality | execution-quality real-only guard |

## 4. Sample Floor

초기 판정은 `report_only_design`으로 시작한다.

| stage | sample floor | denominator | 판정 |
| --- | --- | --- | --- |
| `design_ready` | 0 | source contract present | 문서/스키마 검증만 가능 |
| `report_only_candidate` | 30 | real completed valid, normal-only | 산식 후보 점수화 가능 |
| `approval_required` | 60 | real completed valid + candidate provenance rows | 사용자 approval request 생성 가능 |
| `approved_live_candidate` | 100 | post-apply version window real rows | 다음 장전 apply 후보 검토 가능 |

sim/probe/counterfactual rows는 sample floor 보조 가속 입력으로만 쓰며, real denominator를 대체하지 않는다.

## 5. Primary Metric

primary metric은 아래 둘 중 하나만 사용한다.

- `notional_weighted_ev_pct`
- `source_quality_adjusted_ev_pct`

보조 진단:

- `diagnostic_win_rate`
- `submitted_count`
- `full_fill_rate`
- `order_failure_rate`
- `p10_profit_rate`
- `p90_loss_tail_pct`
- `cap_reduced_opportunity_count`
- `missed_upside_notional_krw`

금지:

- `win_rate` 단독 승인
- `simple_sum_profit_pct`를 EV로 사용
- sim/probe equal-weight EV 단독으로 실주문 확대 승인

## 6. Approval Artifact Schema

실주문 수량 확대 또는 산식 live 적용은 아래 artifact가 있어야 한다.

path:

```text
data/threshold_cycle/approvals/position_sizing_dynamic_formula_YYYY-MM-DD.json
```

required fields:

```json
{
  "approval_id": "position_sizing_dynamic_formula_YYYY-MM-DD",
  "approval_date": "YYYY-MM-DD",
  "owner": "position_sizing_dynamic_formula",
  "approved_by": "operator",
  "approval_scope": "report_only|bounded_live_canary",
  "formula_version": "position_sizing_dynamic_formula:v1",
  "max_qty_cap": 1,
  "max_notional_krw": 3000000,
  "allowed_strategies": ["SCALPING"],
  "sample_floor_passed": false,
  "primary_metric": "notional_weighted_ev_pct",
  "primary_metric_value": null,
  "source_quality_passed": false,
  "same_stage_owner_guard_passed": false,
  "rollback_guard": {
    "order_failure_rate_max_pct": 10.0,
    "p10_profit_rate_floor_pct": -2.0,
    "severe_loss_count_max": 0,
    "receipt_provenance_required": true
  },
  "runtime_apply_allowed": false
}
```

`runtime_apply_allowed=true`는 `approval_scope=bounded_live_canary`, source-quality pass, same-stage owner guard pass, rollback guard pass가 모두 닫힌 경우에만 허용한다.

## 7. Implementation Phases

1. `P0_contract_only` - 완료 (`2026-05-14`)
   - 이 문서와 traceability/threshold README 계약 유지.
   - runtime effect 없음.
2. `P1_report_source_bundle` - 완료 (`2026-05-14`)
   - `daily_threshold_cycle_report`에 `position_sizing_dynamic_formula` metadata와 source metrics를 report-only로 추가.
   - candidate qty와 baseline qty provenance만 산출.
3. `P2_runtime_approval_summary` - 미착수
   - 조건 충족 시 approval request만 생성.
   - env override와 주문 수량 변경은 생성하지 않음.
4. `P3_preopen_apply_guard` - 미착수
   - approval artifact loader와 fail-closed guard 추가.
   - 기본값은 `runtime_apply_allowed=false`.
5. `P4_bounded_live_canary` - 미착수
   - 별도 사용자 승인 뒤 다음 장전 canary로만 검토.

## 7.1 P1 구현 기록

- implemented_at: `2026-05-14 KST`
- 구현: `daily_threshold_cycle_report`의 `CALIBRATION_FAMILY_METADATA`와 threshold snapshot에 `position_sizing_dynamic_formula`를 추가했다.
- 산출물: `data/report/threshold_cycle_YYYY-MM-DD.json`의 `threshold_snapshot.position_sizing_dynamic_formula`와 `calibration_candidates[]`에 report-only 후보가 생성된다.
- runtime 권한: `allowed_runtime_apply=false`, `runtime_change=false`, `apply_mode=report_only_calibration`.
- denominator: `sample_count`는 real `COMPLETED + valid profit_rate` normal-only row만 사용한다. sim/probe/counterfactual sizing event는 `sim_probe_sizing_event_count`와 `qty_source_counts`로만 노출하며 sample floor를 대체하지 않는다.
- 2026-05-14 재생성 확인: `real_completed_valid=4`, `sample_floor=30`, `sizing_event_count=3`, `source_quality_passed=false`, `calibration_state=hold_sample`, `allowed_runtime_apply=false`.

## 8. Forbidden Uses

- 장중 runtime threshold/order mutation 금지.
- sim/probe/counterfactual 단독 실주문 cap 해제 금지.
- `position_sizing_cap_release` approval을 `position_sizing_dynamic_formula` approval로 재사용 금지.
- 스윙 dry-run approval을 스캘핑 수량 확대 approval로 재사용 금지.
- provider route 확인을 수량 산식 변경 근거로 사용 금지.
- bot restart를 산식 승인 근거로 사용 금지.

## 9. 테스트 기준

구현 단계에서 필요한 최소 테스트:

- `daily_threshold_cycle_report` metadata/source bundle 테스트
- real/sim/probe denominator 분리 테스트
- `primary_metric` 명명/EV contract 테스트
- approval artifact missing fail-closed 테스트
- same-stage owner conflict 테스트
- rollback guard breach 테스트
- parser 검증과 `git diff --check`
