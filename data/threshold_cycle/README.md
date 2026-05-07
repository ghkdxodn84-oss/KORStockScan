# Threshold Cycle Operations

작성 기준: `2026-05-03 KST`

이 디렉토리는 threshold 후보 수집, 장후 리포트, 장전 apply plan을 저장한다. 현재 원칙은 `manifest_only`, `calibrated_apply_candidate`, `efficient_tradeoff_canary_candidate` artifact 생성까지이며, 장중 runtime threshold 자동 변경은 금지한다.

report 기반 자동화의 전체 추적성은 [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)를 기준으로 본다. 이 문서는 산출물별 producer/consumer와 현재 apply 단계만 설명하고, 미래 작업 owner는 날짜별 checklist가 소유한다.

## 운영 흐름

| 시점 | wrapper | 역할 | 산출물 |
|---|---|---|---|
| runtime | `src.utils.pipeline_event_logger` | threshold 후보 stage를 compact stream에 적재 | `threshold_events_YYYY-MM-DD.jsonl` |
| POSTCLOSE 16:10 | `deploy/run_threshold_cycle_postclose.sh` | raw pipeline event를 family partition으로 backfill하고 장후 report 생성 | `date=YYYY-MM-DD/family=*/part-*.jsonl`, `data/report/threshold_cycle_YYYY-MM-DD.json`, 파생 `statistical_action_weight`, `holding_exit_decision_matrix`, `threshold_cycle_cumulative` JSON/MD |
| INTRADAY 12:05 | `deploy/run_threshold_cycle_calibration.sh` | 기존 report source bundle을 읽어 장중 calibration artifact 생성 | `data/report/threshold_cycle_calibration/threshold_cycle_calibration_YYYY-MM-DD_intraday.json` |
| PREOPEN 07:35 | `deploy/run_threshold_cycle_preopen.sh` | 최신 threshold report를 읽어 apply plan 생성 | `apply_plans/threshold_apply_YYYY-MM-DD.json` |

## 현재 적용 정책

- `THRESHOLD_CYCLE_APPLY_MODE` 기본값은 `manifest_only`다.
- `threshold_cycle_preopen_apply`는 `manifest_only`, `calibrated_apply_candidate`, `efficient_tradeoff_canary_candidate`를 허용한다. 세 mode 모두 artifact 생성이며 장중 runtime 값을 자동 mutate하지 않는다.
- apply plan은 운영자가 볼 수 있는 적용 후보/금지 사유/safety guard/calibration trigger context를 남기는 artifact다.
- 목표 미달은 rollback이 아니라 다음 manifest의 `calibration_state=adjust_up|adjust_down|hold|hold_sample|hold_no_edge|freeze`로 처리한다.
- sample 부족은 live 전면 금지가 아니라 `cap 축소`, `hold_sample`, `max_step_per_day 축소` 중 하나로 처리한다.
- `safety_revert_required=true`는 hard/protect/emergency stop 지연, 주문 실패, receipt/provenance 손상, same-stage owner 충돌, severe loss guard 초과에만 쓴다.
- 실제 env/code 반영은 별도 승인된 family만 다음 장전 1회 bounded apply로 수행한다.
- calibration artifact는 매일 장중/장후 2회 생성한다. 장중 실행은 기존 보유/청산 report source를 요약하며 canonical postclose threshold report를 덮어쓰지 않는다.

## 주요 경로

| 경로 | 의미 |
|---|---|
| `threshold_events_YYYY-MM-DD.jsonl` | runtime compact event stream |
| `snapshots/pipeline_events_YYYY-MM-DD_*.jsonl` | POSTCLOSE collector가 live append 중인 raw 파일 대신 읽는 immutable source snapshot |
| `date=YYYY-MM-DD/family=*/part-*.jsonl` | family별 report 입력 partition |
| `checkpoints/YYYY-MM-DD.json` | incremental backfill resume/checkpoint |
| `apply_plans/threshold_apply_YYYY-MM-DD.json` | 장전 apply plan artifact |
| `data/report/threshold_cycle_YYYY-MM-DD.json` | 장후 canonical threshold report |
| `data/report/statistical_action_weight/statistical_action_weight_YYYY-MM-DD.{json,md}` | action weight 파생 artifact |
| `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_YYYY-MM-DD.{json,md}` | AI decision-support matrix 파생 artifact |
| `data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_YYYY-MM-DD.{json,md}` | 누적/rolling cohort 기반 threshold cycle 파생 artifact |

## 누적/rolling threshold cycle report

`threshold_cycle_cumulative` artifact는 daily report를 대체하지 않는다. 역할은 `daily`, `rolling`, `cumulative`가 같은 방향을 가리키는지 확인해 threshold 후보의 지속성을 보는 report-only 입력이다.

기본 구간:

- cumulative: `2026-04-21` 이후 `post_fallback_deprecation` 구간
- rolling: 최근 `5/10/20` calendar-day window
- completed 손익 기준: `COMPLETED + valid profit_rate`
- cohort: `all_completed_valid`, `normal_only`, `initial_only`, `pyramid_activated`, `reversal_add_activated`

금지선:

- 누적 평균 단독으로 live threshold mutation을 수행하지 않는다.
- full/partial fill split이 없는 누적 손익은 hard 승인 근거로 쓰지 않는다.
- `main_only`/runtime flag cohort/source provenance가 비어 있으면 방향성 판정으로 격하한다.
- 누적/rolling은 추천값 확정이 아니라 방향성과 step size 산정에만 사용한다.

## bounded calibration loop

`threshold_cycle_YYYY-MM-DD.json`은 기존 `apply_candidate_list` 외에 다음 섹션을 가진다.

- `calibration_candidates`: family별 `threshold_version`, target env keys, current/recommended/applied values, bounds, `max_step_per_day`, sample floor, confidence, `calibration_state`, `safety_revert_required`를 담는다.
- `calibration_source_bundle`: `data/report`의 기존 보유/청산 리포트 경로와 soft-stop tail/defer cost/trailing/safety 요약을 담는다.
- `post_apply_attribution`: threshold version별 applied/not-applied cohort key와 GOOD_EXIT/MISSED_UPSIDE/soft-stop tail/defer cost/safety breach metric 정의를 담는다.
- `safety_guard_pack`: 원복 후보를 safety breach로만 제한한다.
- `calibration_trigger_pack`: 목표 미달, 표본 부족, 방향성 불일치의 다음 calibration action을 담는다.

첫 bounded calibration family는 아래 묶음이다. 목적은 완벽한 threshold spot 탐색이 아니라 efficient trade-off 지점의 bounded live canary와 자동 calibration이다.

1. `score65_74_recovery_probe`: broad score threshold 완화가 아니라 score65~74, latency DANGER 제외, 수급/가속/micro-VWAP 유지, 1주/5만원 cap 후보
2. `bad_entry_refined_canary`: naive hard block 재개가 아니라 soft-stop tail/defer cost 감소 후보
3. `soft_stop_whipsaw_confirmation`
4. `holding_flow_ofi_smoothing`
5. `protect_trailing_smoothing`
6. `holding_exit_decision_matrix_advisory`: SAW `candidate_weight_source`가 만든 non-`no_clear_edge` matrix bucket만 advisory canary 후보
7. `trailing_continuation`: GOOD_EXIT 훼손 리스크가 커서 1차 loop에서는 `freeze/report_only_calibration`만 허용

soft-stop balanced 기준은 완벽한 승률이 아니라 trade-off 기준이다. GOOD_EXIT 훼손은 `+10%p`까지 허용하고, soft-stop 손실 tail 감소 또는 MISSED_UPSIDE 감소가 있으면 유지 또는 완만 조정 대상으로 본다.

새 관찰축 추가는 기본 금지다. follow-up이 어려운 신규 observe/report axis를 늘리지 않고 BUY 쪽 `buy_funnel_sentinel`, `sentinel_followup`, `wait6579_ev_cohort`, `missed_entry_counterfactual`, 보유/청산 쪽 `holding_exit_observation`, `post_sell_feedback`, `holding_exit_sentinel`, `trade_review`, decision-support 쪽 `holding_exit_decision_matrix`, `statistical_action_weight`의 기존 source를 calibration 입력으로 재사용한다. `preclose_sell_target`은 operator preclose review 산출물이며 tuning/calibration source가 아니다.

## statistical_action_weight 적용 범위

`statistical_action_weight`는 dynamic threshold를 직접 바꾸는 family가 아니라 action weight source다. 장후 `daily_threshold_cycle_report`가 가격대/거래량/시간대별 `exit_only`, `avg_down_wait`, `pyramid_wait`의 confidence-adjusted score와 `policy_hint`를 만들고, 같은 실행에서 `holding_exit_decision_matrix`가 이를 report-only matrix entry와 `prompt_hint`로 변환한다.

적용 단계:

1. `stat_action_decision_snapshot`와 completed/action join 품질을 누적한다.
2. `statistical_action_weight_YYYY-MM-DD.json/md`에서 sample floor, policy hint, `eligible_but_not_chosen` proxy를 확인한다.
3. `holding_exit_decision_matrix_YYYY-MM-DD.json/md`가 bucket별 `recommended_bias`를 만든다.
4. runtime 반영은 별도 advisory/live canary 승인 전까지 금지한다. 단, non-`no_clear_edge` bucket이 생기면 `holding_exit_decision_matrix_advisory`의 efficient trade-off calibration 후보로 자동 연결한다.

## 보호트레일링 평탄화 threshold family

`protect_trailing_smoothing` family는 `protect_trailing_smooth_hold`와 `protect_trailing_smooth_confirmed` stage를 수집한다.

관리 대상 값:

- `SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC`
- `SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC`
- `SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES`
- `SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO`
- `SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT`
- `SCALP_PROTECT_TRAILING_EMERGENCY_PCT`

런타임 override 키는 각각 `KORSTOCKSCAN_` prefix를 붙인 동일 이름이다. 단, 현재 apply mode는 `manifest_only`이므로 threshold-cycle은 장후 추천값과 다음 장전 apply plan만 생성하고, 봇 runtime 값을 자동 변경하지 않는다. live 반영은 별도 workorder, sample floor, rollback guard, env/code 반영, restart 절차가 닫힌 경우에만 허용한다.

## OFI AI smoothing threshold family

`entry_ofi_ai_smoothing` family는 `entry_ai_price_ofi_skip_demoted` stage를 중심으로 P2 raw `SKIP` demotion 표본을 수집한다. `holding_flow_ofi_smoothing` family는 `holding_flow_ofi_smoothing_applied`와 `holding_flow_override_force_exit` stage를 수집해 flow 내부 OFI debounce/confirm 및 force-exit 우선권을 분리한다.

관리 대상 후보값:

- `SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_MAX_CONFIDENCE`
- `OFI_AI_SMOOTHING_STALE_THRESHOLD_MS`
- `OFI_AI_SMOOTHING_PERSISTENCE_REQUIRED`
- `HOLDING_FLOW_OFI_BEARISH_CONFIRM_WORSEN_PCT`

두 family 모두 현재 apply mode는 artifact 기준이다. holding/exit 쪽 `holding_flow_ofi_smoothing`은 `calibrated_apply_candidate` 후보가 될 수 있지만, 승인 전에는 threshold-cycle 산출물이 env/code/runtime 값을 자동 변경하지 않는다. `SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED`는 기존대로 기본 OFF이며, ON 전환은 별도 workorder, manifest id/version, sample floor, fallback 급증 guard가 필요하다.

## Scale-in price guard threshold family

`scale_in_price_guard` family는 REVERSAL_ADD/PYRAMID 주문 직전 scale-in P1 resolver와 dynamic qty safety 표본을 수집한다.

수집 stage:

- `scale_in_price_resolved`
- `scale_in_price_guard_block`
- `scale_in_price_p2_observe`

관리 대상 후보값:

- `SCALPING_SCALE_IN_MAX_SPREAD_BPS`
- `SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS`
- `SCALPING_PYRAMID_MIN_AI_SCORE`
- `SCALPING_PYRAMID_MIN_BUY_PRESSURE`
- `SCALPING_PYRAMID_MIN_TICK_ACCEL`
- `SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP`

이 family는 resolved/block/P2 observe 건수, add_type, block_reason, qty_reason, P2 observe action, spread/micro-VWAP 분포, resolved-vs-curr, effective_qty를 장후 report 입력으로 남긴다. P2 `scale_in_price_v1`은 observe-only이며, threshold-cycle이 `SKIP`/`USE_DEFENSIVE`/`IMPROVE_LIMIT` 결과를 live 주문가나 주문 여부에 반영하지 않는다.

현재 apply mode는 `manifest_only` + `report_only_calibration`이다. `scale_in_price_guard`는 calibration candidate에 포함되지만, resolved/executed cohort가 없으면 `hold_sample`로만 출력한다. sample floor를 만족해도 별도 승인 전에는 threshold-cycle 산출물이 env/code/runtime 값을 자동 변경하지 않는다.

## 운영 판정 기준

1. `threshold_events`와 family partition은 canonical raw/compact data다. 사람이 읽는 판정은 `data/report/README.md`의 Markdown 생성 기준을 따른다.
2. `threshold_cycle_YYYY-MM-DD.json`은 top-level threshold 후보, calibration candidates, safety guard, calibration trigger를 담지만 현재 top-level Markdown은 없다. 운영자가 매일 직접 판정해야 하는 항목이면 `data/report/README.md`의 누락 후보로 승격하고 날짜별 checklist에 Markdown 생성 작업계획을 만든다.
3. `statistical_action_weight`, `holding_exit_decision_matrix`, `threshold_cycle_cumulative`는 report-only/decision-support artifact다. 자체 결과만으로 runtime 주문/청산 threshold를 변경하지 않는다.
4. POSTCLOSE collector는 기본적으로 live append 중인 `pipeline_events_YYYY-MM-DD.jsonl`을 직접 읽지 않고 immutable snapshot을 만든 뒤 backfill한다. `stopped_source_changed`가 발생하면 snapshot source로 재실행하고, report는 `checkpoint_completed=true`일 때만 완주 산출물로 본다.
5. IO guard 또는 availability guard로 backfill이 중단되면 같은 snapshot/checkpoint에서 chunk size를 낮춰 resume한다. 같은 날 무리한 raw full rebuild를 반복하지 않고 checkpoint, raw file size, paused reason을 report/checklist에 남긴다.
6. PREOPEN에는 전일 POSTCLOSE에서 생성된 report/apply plan 존재 여부와 `manifest_only` 상태만 확인한다. 같은 날 성과를 장전 통과조건으로 쓰지 않는다.
7. 자동 threshold 적용과 bot restart는 `report-based-automation-traceability.md`의 `R5` gate가 닫히기 전까지 구현 완료로 보지 않는다. `R6` post-apply attribution은 artifact schema가 있어도 applied cohort가 쌓이기 전에는 decision 완료로 보지 않는다.

## 금지 사항

- `ThresholdOpsTransition0506` acceptance 전 live threshold auto-apply 금지.
- `manifest_only` 또는 `calibrated_apply_candidate`가 아닌 apply mode를 임의 추가/사용 금지.
- family별 sample floor, safety guard, owner 없이 threshold를 runtime에 반영 금지.
- raw JSONL을 사람이 직접 해석해 승격/롤백 판정을 닫는 것 금지. 필요한 경우 Markdown/report artifact를 먼저 만든다.
