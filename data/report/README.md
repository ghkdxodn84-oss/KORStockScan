# Report Directory Inventory

작성 기준: `2026-05-03 KST`

이 디렉토리는 운영/감리용 산출물을 저장한다. 기본 원칙은 JSON/JSONL을 canonical data로 두고, 사람이 장후 판정에 바로 읽어야 하는 항목만 Markdown 리포트로 별도 생성한다.

report 산출물이 자동 threshold 적용, bot restart, post-apply attribution으로 이어지는 전체 추적성은 [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)를 기준으로 확인한다.

## Bucket Runtime Calibration ON 기준

`SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED`는 현재 기본값 `False`다. 즉, OFI/QI는 P2 내부 live 입력 feature로 계속 사용되지만 bucket별 threshold는 아직 runtime에 적용하지 않는다.

ON 가능한 시점은 다음 조건이 모두 닫힌 뒤다.

| 조건 | 현재 상태 |
|---|---|
| `data/config/ofi_bucket_threshold_manifest.json` 존재 | 완료. 초기 manifest는 global threshold와 동일값 |
| `OrderbookMicroP2Canary0504-Postclose` provenance 점검 | 2026-05-04 POSTCLOSE 예정 |
| `ThresholdOpsTransition0506` acceptance | 2026-05-06 POSTCLOSE 예정 |
| bucket별 sample floor 충족 | 미확정. manifest의 `min_bucket_samples`, `min_symbol_samples` 기준 필요 |
| 별도 workorder/체크리스트에서 단일 조작점과 rollback owner 확정 | 미확정 |
| env/code 반영 후 restart | 미실행 |

따라서 현재 기준 ON 예정일은 고정되어 있지 않다. 가장 빠른 검토 지점은 `2026-05-06 POSTCLOSE`의 `ThresholdOpsTransition0506` 이후이며, 실제 ON은 별도 승인된 workorder에서 `KORSTOCKSCAN_SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED=true`와 restart를 통해서만 가능하다.

## 현재 정기 Markdown 리포트

| 리포트 | 경로 패턴 | 생성 주체 | 주기/트리거 | 상태 |
|---|---|---|---|---|
| Server Comparison | `data/report/server_comparison/server_comparison_YYYY-MM-DD.md` | `src.engine.log_archive_service._save_server_comparison_artifacts` | full monitor snapshot에서 server comparison이 enabled일 때 | 정기 경로 존재. 최근 기본 wrapper는 `MONITOR_SNAPSHOT_SKIP_SERVER_COMPARISON=1`이라 자동 생성이 정책상 꺼질 수 있음 |
| Statistical Action Weight | `data/report/statistical_action_weight/statistical_action_weight_YYYY-MM-DD.md` | `src.engine.daily_threshold_cycle_report` | `deploy/run_threshold_cycle_postclose.sh` 장후 실행 | 2026-04-30, 2026-05-01 생성 확인 |
| Holding/Exit Decision Matrix | `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_YYYY-MM-DD.md` | `src.engine.daily_threshold_cycle_report` | `deploy/run_threshold_cycle_postclose.sh` 장후 실행 | 2026-04-30, 2026-05-01 생성 확인 |
| Preclose Sell Target | `data/report/preclose_sell_target/preclose_sell_target_YYYY-MM-DD.md` | `src.scanners.preclose_sell_target_report` | `deploy/run_preclose_sell_target_report.sh YYYY-MM-DD --no-ai --no-telegram`로 1차 검증 후 정기화 판단 | 재개 준비. canonical JSON과 같은 디렉터리에 생성하며 현재는 report-only |

## 비정기/legacy Markdown

| 리포트 | 경로 | 비고 |
|---|---|---|
| Preclose Sell Target legacy root | `data/report/preclose_sell_target_YYYY-MM-DD.md` | 2026-04-15 단발 산출물 경로. 재개 후에는 호환성 Markdown으로만 유지하고 canonical 산출물은 `data/report/preclose_sell_target/`를 사용 |
| Add Blocked Lock Markdown | `data/report/monitor_snapshots/add_blocked_lock_2026-04-16.md` | legacy 단발 산출물로 보이며 최근 snapshot 체인에서는 JSON만 생성됨 |

## 정기 JSON Snapshot

`deploy/run_monitor_snapshot_cron.sh` 또는 `deploy/run_monitor_snapshot_incremental_cron.sh`는 wrapper를 통해 아래 snapshot JSON을 생성한다.

| profile | 생성 JSON |
|---|---|
| `full` | `trade_review`, `performance_tuning`, `wait6579_ev_cohort`, `post_sell_feedback`, `missed_entry_counterfactual`, `holding_exit_observation`, `add_blocked_lock`, `monitor_snapshot_manifest` |
| `intraday_light` | `trade_review`, `performance_tuning`, `wait6579_ev_cohort`, `monitor_snapshot_manifest` |

저장 경로는 `data/report/monitor_snapshots/{kind}_YYYY-MM-DD.json`이며 오래된 파일은 `.json.gz`로 압축될 수 있다. 이 계열은 API/dashboard/snapshot용 canonical JSON이며, 현재 설계상 전부 Markdown을 생성하지는 않는다.

## 정기 JSON/JSONL 산출물

| 산출물 | 경로 패턴 | 생성 주체 | 현재 Markdown |
|---|---|---|---|
| Daily Report | `data/report/report_YYYY-MM-DD.json` | `src.engine.daily_report_service` | 없음 |
| Threshold Cycle Report | `data/report/threshold_cycle_YYYY-MM-DD.json` | `src.engine.daily_threshold_cycle_report` | 없음. 단, 파생 Markdown 3종 생성 |
| Cumulative Threshold Cycle Report | `data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_YYYY-MM-DD.json` | `src.engine.daily_threshold_cycle_report` | `data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_YYYY-MM-DD.md` |
| Preclose Sell Target | `data/report/preclose_sell_target/preclose_sell_target_YYYY-MM-DD.json` | `src.scanners.preclose_sell_target_report` | `data/report/preclose_sell_target/preclose_sell_target_YYYY-MM-DD.md` |
| Threshold Compact Events | `data/threshold_cycle/date=YYYY-MM-DD/family=*/part-*.jsonl`, `data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl` | `src.engine.backfill_threshold_cycle_events` | 없음 |
| Pipeline Events | `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl` | runtime pipeline event writer | 없음 |
| Gatekeeper Snapshots | `data/gatekeeper/gatekeeper_snapshots_YYYY-MM-DD.jsonl` | gatekeeper snapshot writer | 없음 |
| Post-sell Candidates/Evaluations | `data/post_sell/post_sell_candidates_YYYY-MM-DD.jsonl`, `data/post_sell/post_sell_evaluations_YYYY-MM-DD.jsonl` | post-sell feedback collector | 없음 |

## Markdown 누락 후보

아래는 JSON/JSONL canonical data가 있는데, 현재 운영자가 바로 읽는 Markdown 리포트가 없는 항목이다. “모든 JSON에 Markdown이 없어 문제”라는 뜻은 아니며, 장후 판정/감리 효율 관점의 후보 목록이다.

| 우선순위 | 누락 후보 | 근거 | 권고 |
|---:|---|---|---|
| 1 | `threshold_cycle_YYYY-MM-DD.md` | `threshold_cycle_YYYY-MM-DD.json`은 apply candidate, rollback guard, threshold snapshot을 직접 담지만 top-level Markdown은 없다. 현재는 `statistical_action_weight`와 `holding_exit_decision_matrix` Markdown만 파생 생성된다. | 장후 운영자가 threshold 후보와 적용 금지 사유를 한 장으로 보는 Markdown 추가 권고 |
| 2 | `performance_tuning_YYYY-MM-DD.md` | `performance_tuning_YYYY-MM-DD.json`은 gatekeeper, holding, dual persona, OFI bucket/source 분포까지 포함하는 핵심 장후 판정 snapshot이다. Markdown이 없어 감리/운영자가 JSON을 직접 열어야 한다. | 핵심 metrics/breakdowns/watch_items 중심 Markdown 추가 권고 |
| 3 | `trade_review_YYYY-MM-DD.md` | `trade_review_YYYY-MM-DD.json`은 `COMPLETED + valid profit_rate`, open/entered rows의 기준 snapshot이다. | full/partial, completed/open, valid profit basis 요약 Markdown 추가 권고 |
| 4 | `holding_exit_observation_YYYY-MM-DD.md` | holding/exit 감리와 `GOOD_EXIT/MISSED_UPSIDE` 해석에 쓰이는 JSON만 존재한다. | soft stop/rebound/post-sell 요약 Markdown 추가 권고 |
| 5 | `post_sell_feedback_YYYY-MM-DD.md` | post-sell 후보/평가 JSON은 있으나 장후 사람이 읽는 요약이 없다. | missed upside, good exit, extra upside 중심 Markdown 추가 권고 |
| 6 | `missed_entry_counterfactual_YYYY-MM-DD.md` | 미진입 기회비용 분석 JSON만 존재한다. | latency/liquidity/AI threshold/overbought blocker별 Markdown 추가 권고 |
| 7 | `wait6579_ev_cohort_YYYY-MM-DD.md` | WAIT 65~79 EV cohort JSON만 존재한다. 현재 owner가 약해졌지만 prompt/score 재판정 감사에는 유용하다. | 필요 시 archive 성격 Markdown 또는 dashboard-only 유지 결정 |
| 8 | `add_blocked_lock_YYYY-MM-DD.md` | 최근 JSON은 계속 있으나 Markdown은 2026-04-16 legacy 단발만 있다. | 추가매수 blocker가 active owner일 때만 Markdown 재개 |
| 9 | `daily_report_YYYY-MM-DD.md` | `report_YYYY-MM-DD.json`은 web/API/Flutter 소비용 구조화 리포트다. | 운영자 장후 판정용으로는 우선순위 낮음. dashboard-only 유지 가능 |

## 정상적으로 Markdown 제외해도 되는 항목

| 항목 | 제외 사유 |
|---|---|
| `monitor_snapshot_manifest_YYYY-MM-DD_profile.json` | snapshot 검증/압축/중복 방지용 manifest다. 사람이 읽는 판정 리포트가 아니다. |
| `pipeline_events_YYYY-MM-DD.jsonl` | raw event stream이다. Markdown은 파생 리포트에서 생성해야 한다. |
| `gatekeeper_snapshots_YYYY-MM-DD.jsonl` | raw snapshot stream이다. Markdown은 gatekeeper/performance 파생 리포트에서 생성해야 한다. |
| `post_sell_candidates/evaluations_YYYY-MM-DD.jsonl` | raw collector output이다. Markdown은 post-sell feedback 파생 리포트에서 생성해야 한다. |
| `threshold_cycle/date=*/family=*/part-*.jsonl` | compact partition이다. Markdown은 threshold cycle report에서 생성해야 한다. |

## 현재 파일 기준 확인 요약

- Markdown 정기 산출물: server comparison, statistical action weight, holding/exit decision matrix, cumulative threshold cycle.
- JSON snapshot 정기 산출물: monitor snapshots 7종, daily report, threshold cycle report.
- Markdown 누락 최우선 후보: `threshold_cycle`, `performance_tuning`, `trade_review`.
- OFI bucket runtime calibration은 현재 OFF이며, 2026-05-06 이후 별도 승인 없이는 ON하지 않는다.

## 누적/rolling threshold cycle report

`threshold_cycle_cumulative`는 daily report의 당일 판정을 누적/rolling 표본과 대조하기 위한 report-only 산출물이다. 기본 누적 시작점은 `2026-04-21` fallback 폐기 이후이며, rolling window는 최근 `5/10/20` calendar day다.

운영 해석 원칙:

- `COMPLETED + valid profit_rate`만 손익 표본으로 사용한다.
- `all_completed_valid`, `normal_only`, `initial_only`, `pyramid_activated`, `reversal_add_activated`를 분리한다.
- full/partial fill split이 없는 누적 손익은 hard 승인 근거로 쓰지 않는다.
- daily, rolling, cumulative가 같은 방향을 가리킬 때만 다음 checklist의 threshold 후보로 넘긴다.
- 이 산출물은 runtime change, bot restart, live threshold auto-mutation을 수행하지 않는다.
- 자동 threshold 적용과 적용 후 version attribution은 `report-based-automation-traceability.md`의 `R5/R6` gate가 별도 checklist owner로 닫힌 뒤에만 구현 완료로 본다.

## Preclose Sell Target 재개 기준

`preclose_sell_target`는 2026-04-15 legacy 단발 산출물에서 report-only 구조화 산출물로 재개한다. 현재 허용 단계는 `R1_daily_report`이며 live runtime effect는 없다.

운영 해석 원칙:

- canonical data는 `data/report/preclose_sell_target/preclose_sell_target_YYYY-MM-DD.json`이다.
- Markdown은 운영자 검토용이며 자동화 소비자는 JSON만 읽는다.
- 검증은 먼저 `deploy/run_preclose_sell_target_report.sh YYYY-MM-DD --no-ai --no-telegram`로 수행한다.
- cron 등록, AI/Telegram enable, threshold/ADM 소비자 연결은 각각 별도 checklist owner가 닫힌 뒤 진행한다.
- 별도 acceptance 없이 이 리포트를 live threshold mutation, bot restart, 자동 주문 제출 근거로 쓰지 않는다.
