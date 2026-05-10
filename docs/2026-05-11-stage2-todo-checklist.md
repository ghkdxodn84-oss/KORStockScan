# 2026-05-11 Stage2 To-Do Checklist

## 오늘 목적

- threshold-cycle은 장전 수동 승인 없이 `auto_bounded_live`로 무인 반영한다.
- 장후에는 daily EV 성과 리포트만 제출 기준으로 보며, Gemini/Claude pattern lab 결과는 EV report 요약으로만 포함한다.
- 남은 튜닝 관련 보강은 독립 report-only 관찰축으로 늘리지 않고, `threshold_cycle` source bundle / `statistical_action_weight` / `performance_tuning` / daily EV 자동화 체인의 입력 품질 개선으로만 처리한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN cron의 runtime env 생성과 봇 기동 시 source로만 수행한다.
- 조건 미달은 rollback이 아니라 calibration trigger다. safety breach만 `safety_revert_required=true`로 분리한다.
- 장전 수동 enable/hold checklist를 만들지 않는다. postclose 제출물은 `threshold_cycle_ev_YYYY-MM-DD.{json,md}`로 통일하고, pattern lab 상세는 별도 artifact 링크로만 둔다.
- 신규 튜닝 판단 항목은 수동 후속계획으로 분리하지 않는다. 새 threshold family가 필요하면 pattern lab `auto_family_candidate(allowed_runtime_apply=false)` 또는 threshold-cycle `calibration_candidates`로만 편입하고, runtime 적용은 기존 `auto_bounded_live` guard를 통과한 경우에만 허용한다.

## 장전 체크리스트 (08:50~09:00)

- 신규 수동 enable/hold 작업 없음.
- Runbook 운영 확인은 [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md) `장전 확인 절차`와 `build_codex_daily_workorder --slot PREOPEN`의 `PreopenAutomationHealthCheckYYYYMMDD` 블록을 기준으로 본다.
- 확인 범위: `threshold_cycle_preopen_cron.log`, apply plan, runtime env JSON, `src/run_bot.sh` runtime env source 여부, tmux `bot` 기동 상태. 실패 시 수동 env override가 아니라 blocked reason과 same-stage owner 충돌을 확인한다.

## 장중 체크리스트 (09:00~15:20)

- 신규 수동 runtime 변경 작업 없음.
- Runbook 운영 확인은 [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md) `장중 확인 절차`와 `build_codex_daily_workorder --slot INTRADAY`의 `IntradayAutomationHealthCheckYYYYMMDD` 블록을 기준으로 본다.
- 확인 범위: BUY/HOLD-EXIT Sentinel, intraday calibration, pipeline/threshold event append, 스윙 dry-run provenance. Sentinel/calibration 결과로 당일 threshold, provider routing, 스윙 주문 guard를 변경하지 않는다.

## 장후 체크리스트 (16:00~18:30)

- Runbook 운영 확인은 [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md) `장후 확인 절차`와 `build_codex_daily_workorder --slot POSTCLOSE`의 `PostcloseAutomationHealthCheckYYYYMMDD` 블록을 기준으로 본다.
- 아래 체크박스는 runbook 반복 확인이 아니라 2026-05-11에 소유자가 필요한 구현/판정/재확인 작업만 남긴다.

- [x] `[PrecloseSellTargetDecommission0510] preclose sell target 기능 제거 및 sim 알림 admin-only 전환` (`Due: 2026-05-10`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py), [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py)
  - 영향도: `preclose_sell_target`은 operator preclose review 전용이고 tuning/calibration source가 아니므로 제거 영향은 15:00 cron, wrapper/status manifest, detector cron inventory, 문서 inventory에 한정한다. 과거 `data/report/preclose_sell_target*` 산출물은 2026-05-10 사용자 요청으로 삭제했다.
  - 실행 메모: `src.scanners.preclose_sell_target_report`, wrapper, 테스트, detector registry, crontab `PRECLOSE_SELL_TARGET_1500` 경로를 제거했다. 스윙 dry-run 및 스캘핑 live simulator 관련 텔레그램 audience는 `ADMIN_ONLY`로 강제한다.
  - 유지 가드: threshold-cycle source bundle, daily EV, statistical action weight, ADM ladder는 `preclose_sell_target`을 입력으로 쓰지 않는다. sim/combined EV는 기존대로 report/calibration 입력이며, sim 알림만 VIP에서 제외한다.

- [x] `[PositionSizingCapRemoval0509] 신규 BUY/REVERSAL_ADD/PYRAMID 1주 수량 cap 제거 반영` (`Due: 2026-05-09`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py)
  - 실행 메모: 사용자 지시로 신규 BUY `SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED=False`, `SCALPING_INITIAL_ENTRY_MAX_QTY=0`을 기본값으로 전환하고, 추가매수 `SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP=0`과 wait6579 probe `AI_WAIT6579_PROBE_CANARY_MAX_QTY=0`을 수량 cap 없음으로 해석하도록 변경했다.
  - 유지 가드: `SCALPING_MAX_BUY_BUDGET_KRW`, `MAX_POSITION_PCT`, scale-in P1 price resolver, pending/cooldown/protection guard, PYRAMID evidence gate는 유지한다. `ws_data.curr` 직접 지정가 제출 금지는 유지한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py src/tests/test_daily_threshold_cycle_report.py src/tests/test_state_handler_fast_signatures.py` 대상으로 회귀 확인한다.

- [x] `[PositionSizingCapRestore0509] 스캘핑 1주 수량 cap 복귀 및 해제 승인 기준 자동화체인 편입` (`Due: 2026-05-09`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [threshold_cycle_ev_report.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_ev_report.py)
  - 실행 메모: 후속 사용자 지시로 신규 BUY `SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED=True`, `SCALPING_INITIAL_ENTRY_MAX_QTY=1`, wait6579 probe `AI_WAIT6579_PROBE_CANARY_MAX_QTY=1`, 추가매수 `SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP=1`을 기본값으로 복귀했다.
  - 해제 기준: 완벽한 spot 탐색이 아니라 EV 중심 trade-off 기준이다. hard floor는 `normal_only COMPLETED valid >=30`, cap-reduced sample `>=5`, submitted `>=15`, avg profit `>=+0.10%`, downside p10 `>=-2.00%`, order failure rate `<=10%`만 둔다. 그 위에서 avg profit, win rate, full-fill quality, downside tail, order failure, soft-stop tail, cap opportunity를 가중한 `tradeoff_score >=0.70`이면 승인 요청을 생성한다.
  - 자동화체인 연결: 기준 충족 시 `calibration_candidates`의 `calibration_state=approval_required`, `human_approval_required=true`와 daily EV `approval_requests`/preopen apply `approval_requests`에 사용자 승인 요청만 생성한다. 자동 runtime env apply는 금지한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py src/tests/test_daily_threshold_cycle_report.py src/tests/test_state_handler_fast_signatures.py`, parser 검증으로 확인한다.

- [x] `[ScalpAiBuyAllLiveSimulator0511] 스캘핑 AI BUY 전체 대상 실시간 simulator 구현` (`Due: 2026-05-11`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [sniper_performance_tuning_report.py](/home/ubuntu/KORStockScan/src/engine/sniper_performance_tuning_report.py), [threshold_cycle_ev_report.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_ev_report.py)
  - 실행 메모: `SCALP_LIVE_SIMULATOR_ENABLED=True` 기본 ON으로 스캘핑 AI/Gatekeeper BUY 확정 지점에서 `scalp_ai_buy_all` sim 포지션을 종목당 1개 생성한다. 브로커 매수/매도/추가매수 접수는 차단하고, quote-based full-fill v1로 BUY/scale-in/sell을 가상 체결한다.
  - 데이터/WS: open sim state는 `data/runtime/scalp_live_simulator_state.json`에 저장/복원한다. active sim target은 Kiwoom WS prune에서 active consumer로 보며 `scalp_sim_*`, `actual_order_submitted=false`, `calibration_authority=equal_weight`를 pipeline event에 남긴다.
  - 자동화체인 연결: threshold-cycle/daily EV/performance tuning은 sim completed rows를 `real`/`sim`/`combined`로 분리 표시하되 combined를 실매매 동급 calibration 입력으로 사용한다. 장중 runtime threshold mutation 금지는 유지한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scalp_live_simulator.py`, parser 검증으로 확인한다.

- [x] `[SwingModelSelectionFunnelRepair0509] 스윙 모델 추천 생성 정상화 및 선정 funnel 진단 병합 구현` (`Due: 2026-05-09`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: ScalpingLogic`)
  - Source: [recommend_daily_v2.py](/home/ubuntu/KORStockScan/src/model/recommend_daily_v2.py), [common_v2.py](/home/ubuntu/KORStockScan/src/model/common_v2.py), [final_ensemble_scanner.py](/home/ubuntu/KORStockScan/src/scanners/final_ensemble_scanner.py), [swing_selection_funnel_report.py](/home/ubuntu/KORStockScan/src/engine/swing_selection_funnel_report.py)
  - 실행 메모: 운영 추천 floor를 상승장 `0.35`/하락장 `0.40`으로 명시하고, 후보 0건 시 `score top10`을 정식 추천 CSV로 저장하지 않도록 분리했다. 추천 CSV에는 `selection_mode`, `floor_used`, `safe_pool_count`, `score_rank`, `meta_score` provenance를 남긴다.
  - 유지 가드: Gatekeeper, swing gap guard, market regime hard block, 예산/주문 safety는 완화하지 않았다. 스캐너는 `score`를 확률로 쓰지 않고 `hybrid_mean`을 `prob`로 적재한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_performance_tuning_report.py::test_swing_daily_summary_includes_market_regime_and_blockers src/tests/test_position_tag_normalization.py`, 임시 출력 경로 추천 재생성, 2026-05-08 pipeline raw/unique funnel 재집계로 확인했다.

- [x] `[SwingModelTrainingSimulationReview0509] v2 학습모델 유지성 검토 및 스윙 일일 시뮬레이션 리포트 추가` (`Due: 2026-05-09`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: ScalpingLogic`)
  - Source: [backtest_v2.py](/home/ubuntu/KORStockScan/src/model/backtest_v2.py), [swing_daily_simulation_report.py](/home/ubuntu/KORStockScan/src/engine/swing_daily_simulation_report.py), [run_swing_daily_simulation_report.sh](/home/ubuntu/KORStockScan/deploy/run_swing_daily_simulation_report.sh), [update_kospi.py](/home/ubuntu/KORStockScan/src/utils/update_kospi.py)
  - 실행 메모: `backtest_v2`를 package/script 양쪽 실행에서 import 가능하게 정리하고, 추천 CSV의 실전 후보만 next-session open entry / TP·SL·TIME 기준으로 매일 시뮬레이션하는 JSON/Markdown 리포트를 추가했다. fallback/diagnostic 후보는 simulation book에서 제외한다.
  - 판정 메모: 현재 코드 기준 재생성한 `data/backtest_trades_v2.csv`는 `2026-01-02~2026-03-16` 123건, win rate `47.15%`, 평균 net `+1.51%`, 누적 net `+185.32%`다. 다만 검증 구간이 3/16에서 끊겨 4~5월 활황 구간을 포함하지 않으므로, 현 모델은 후보 생성 canary로 유지하되 실전 확대 전 재학습/forward 검증 owner가 필요하다. 일일 리포트는 runtime 주문/threshold를 바꾸지 않는 `runtime_change=false` 산출물이다.
  - 검증: 스윙 시뮬레이션 단위 테스트, `compileall`, 2026-05-08 추천/백테스트 재생성 및 리포트 생성으로 확인한다.

- [x] `[SwingModelRetrainAutomation0511] 스윙 ML v2 재학습/상승장 특화모델 자동 판정 체인 구현` (`Due: 2026-05-11`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: ScalpingLogic`)
  - Source: [auto_retrain_pipeline.sh](/home/ubuntu/KORStockScan/auto_retrain_pipeline.sh), [common_v2.py](/home/ubuntu/KORStockScan/src/model/common_v2.py), [train_meta_model_v2.py](/home/ubuntu/KORStockScan/src/model/train_meta_model_v2.py), [recommend_daily_v2.py](/home/ubuntu/KORStockScan/src/model/recommend_daily_v2.py), [swing_retrain_pipeline.py](/home/ubuntu/KORStockScan/src/model/swing_retrain_pipeline.py)
  - 실행 메모: `bull_specialist_mode=enabled|disabled|hold_current`를 추가하고, `disabled`에서는 `bx/bl`을 `hx/hl`로 중립화해 `META_FEATURES` schema를 유지한다. 재학습은 staging output dir에서 수행한 뒤 guard 통과 시 모델 artifact만 자동 승격하고, smoke 실패 시 backup에서 rollback한다.
  - 상승장 기간 판정: `swing_bull_period_ai_review`가 AI strict JSON 또는 deterministic fallback 제안을 받아 DB 범위, 최소 기간/표본, label safety guard를 검증한다. guard 실패 시 `hold_current`로 닫는다.
  - 유지 가드: 자동 승격은 스윙 ML artifact 교체만 뜻한다. `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`, `actual_order_submitted=false`, one-share real canary 별도 approval, OpenAI/Gemini live routing 금지는 유지한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_retrain_automation.py`, error detector coverage, parser 검증으로 확인한다.

- [x] `[SwingRuntimeDryRunSimulation0509] 스윙 추천 후 장중 매매로직 dry-run 시뮬레이션 보강` (`Due: 2026-05-09`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: ScalpingLogic`)
  - Source: [swing_daily_simulation_report.py](/home/ubuntu/KORStockScan/src/engine/swing_daily_simulation_report.py), [test_swing_model_selection_funnel_repair.py](/home/ubuntu/KORStockScan/src/tests/test_swing_model_selection_funnel_repair.py)
  - 실행 메모: 단순 next-open TP/SL 시뮬레이션을 `runtime_order_dry_run_daily_proxy`로 바꿔, 스윙 gap guard, bull regime block, runtime score proxy, 전략별 비중, `describe_buy_capacity` 수량 산출, 최유리지정가 `order_type_code=6`, 주문 미전송 `actual_order_submitted=false`, hard stop/target/trailing/time stop 청산 규칙을 리포트에 남기도록 했다.
  - 유지 가드: 실제 브로커 주문은 전송하지 않는다. 과거 일봉만으로는 Gatekeeper AI/틱/호가/radar score를 완전 replay할 수 없으므로 `gatekeeper_mode=dry_run_assumed_pass`와 `entry_runtime_score_source=daily_proxy_from_hybrid_mean_score_rank` provenance를 명시한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `compileall`, `git diff --check`로 확인한다.

- [x] `[SwingLiveOrderDryRunRuntime0511] 스윙 장중 live 로직 주문 미전송 관찰모드 구현` (`Due: 2026-05-11`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: ScalpingLogic`)
  - Source: [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [swing_selection_funnel_report.py](/home/ubuntu/KORStockScan/src/engine/swing_selection_funnel_report.py), [test_swing_model_selection_funnel_repair.py](/home/ubuntu/KORStockScan/src/tests/test_swing_model_selection_funnel_repair.py)
  - 실행 메모: 스윙 `WATCHING -> gatekeeper -> market regime -> budget -> latency/price guard -> order request` 로직은 그대로 실행하고, 브로커 `send_buy_order`/`send_smart_sell_order`/스윙 추가매수 전송만 `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED` 기본 ON에서 차단한다. 런타임 상태는 in-memory `HOLDING/COMPLETED`로 진행해 매도 판단까지 관찰한다.
  - 관찰 stage: `swing_sim_buy_order_assumed_filled`, `swing_sim_holding_started`, `swing_sim_order_bundle_assumed_filled`, `swing_sim_scale_in_order_assumed_filled`, `swing_sim_sell_order_assumed_filled`를 pipeline event로 남기고, 실제 제출 stage인 `order_bundle_submitted`/`sell_order_sent`와 분리한다.
  - 유지 가드: gap guard, Gatekeeper, market regime hard block, 예수금/수량/latency/price/pause guard는 완화하지 않는다. 실제 주문 전송만 제외하며 이벤트에 `actual_order_submitted=false`, `simulation_owner=SwingLiveOrderDryRunSimulation0511`을 남긴다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `compileall`, `git diff --check`로 확인한다.

- [x] `[SwingLiveDryRunReportCron0511] 스윙 live 주문 dry-run 장후 보고서 자동 생성 cron 등록` (`Due: 2026-05-11`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: ScalpingLogic`)
  - Source: [run_swing_live_dry_run_report.sh](/home/ubuntu/KORStockScan/deploy/run_swing_live_dry_run_report.sh), [install_swing_live_dry_run_cron.sh](/home/ubuntu/KORStockScan/deploy/install_swing_live_dry_run_cron.sh), [swing_selection_funnel_report.py](/home/ubuntu/KORStockScan/src/engine/swing_selection_funnel_report.py), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 실행 메모: 매 영업일 `15:45 KST`에 `SWING_LIVE_DRY_RUN_POSTCLOSE` cron이 `swing_selection_funnel_report`를 실행해 `data/report/swing_selection_funnel/swing_selection_funnel_YYYY-MM-DD.{json,md}`와 status JSON을 생성하도록 등록했다.
  - 유지 가드: 자동 보고서는 report-only이며 runtime threshold, gatekeeper, gap guard, 주문 safety를 변경하지 않는다. 실제 주문 제출 stage와 simulation stage는 리포트에서 분리한다.
  - 검증: `bash -n deploy/run_swing_live_dry_run_report.sh deploy/install_swing_live_dry_run_cron.sh`, wrapper smoke, crontab 등록, parser 검증으로 확인한다.

- [x] `[SwingLifecycleSelfImprovementChain0511] 스윙 선정-진입-보유-추가매수-청산 자가개선 자동화체인 구현` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: 15:45~16:10`, `Track: ScalpingLogic`)
  - Source: [swing_lifecycle_audit.py](/home/ubuntu/KORStockScan/src/engine/swing_lifecycle_audit.py), [build_code_improvement_workorder.py](/home/ubuntu/KORStockScan/src/engine/build_code_improvement_workorder.py), [run_swing_live_dry_run_report.sh](/home/ubuntu/KORStockScan/deploy/run_swing_live_dry_run_report.sh), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 실행 메모: 스윙 `selection -> db_load -> entry -> holding -> scale_in -> exit -> attribution` lifecycle audit, proposal-only swing threshold AI review, `swing_improvement_automation` order 생성을 추가했다. `build_code_improvement_workorder`는 scalping pattern lab order와 swing lifecycle order를 같은 Codex 작업지시서에 병합한다.
  - 유지 가드: 스윙 gap/protection/market regime/예산/주문 safety는 완화하지 않는다. 생성 order는 `runtime_effect=false`이며 실제 live 변경은 사용자가 생성된 workorder를 Codex에 수동으로 넣어 별도 구현 요청할 때만 진행한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py src/tests/test_build_code_improvement_workorder.py`, `bash -n deploy/run_swing_live_dry_run_report.sh deploy/run_threshold_cycle_postclose.sh`, parser 검증으로 확인한다.

- [x] `[SwingRuntimeApproval0511] 스윙 자동 분석·후보 생성·승인 요청 dry-run live 전환` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:30`, `Track: ScalpingLogic`)
  - Source: [swing_lifecycle_audit.py](/home/ubuntu/KORStockScan/src/engine/swing_lifecycle_audit.py), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [threshold_cycle_ev_report.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_ev_report.py), [error_detector_coverage.py](/home/ubuntu/KORStockScan/src/engine/error_detector_coverage.py), [artifact_freshness.py](/home/ubuntu/KORStockScan/src/engine/error_detectors/artifact_freshness.py)
  - 실행 메모: `swing_runtime_approval` artifact를 추가해 스윙 후보 schema를 `proposal|approval_required|approved_live|hold_sample|hold_no_edge|freeze`로 확장했다. hard floor 통과 후 `overall_ev 45% + downside_tail 20% + participation/funnel 15% + regime_robustness 10% + attribution_quality 10%` trade-off score `>=0.68`이면 `approval_required` 요청을 만든다.
  - 자동화체인 연결: `approval_required`만으로는 env를 쓰지 않는다. 사용자가 `data/threshold_cycle/approvals/swing_runtime_approvals_YYYY-MM-DD.json` approval artifact를 남긴 경우에만 다음 장전 preopen apply가 `approved_live` env override를 생성하며, `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`를 강제한다.
  - 유지 가드: 이번 live는 스윙 dry-run 내부 threshold/logic 반영만 뜻한다. 브로커 주문 접수는 계속 차단하고 `actual_order_submitted=false` provenance를 유지한다. 1차 env 대상은 `swing_model_floor`, `swing_selection_top_k`, `swing_gatekeeper_reject_cooldown`, `swing_market_regime_sensitivity`이며, `AVG_DOWN`, `PYRAMID`, exit OFI/QI smoothing, AI contract 변경은 approval request까지만 허용한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_threshold_cycle_ev_report.py src/tests/test_error_detector_coverage.py src/tests/test_error_detector_artifact_freshness.py`, parser 검증으로 확인한다.

- [x] `[SwingOneShareRealCanaryPolicy0511] 스윙 1주 real canary approval-required 축 문서화` (`Due: 2026-05-11`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md), [swing_lifecycle_audit.py](/home/ubuntu/KORStockScan/src/engine/swing_lifecycle_audit.py), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [threshold_cycle_ev_report.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_ev_report.py), [README.md](/home/ubuntu/KORStockScan/README.md), [README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md)
  - 실행 메모: 스윙 sim/combined가 채우지 못하는 broker execution 품질을 수집하기 위해 `swing_one_share_real_canary`를 별도 approval-required real-canary 후보로 정의했다. 이는 스윙 전체 dry-run 해제가 아니라 승인된 극소수 후보만 1주 실제 BUY/SELL을 보내는 phase0 계획이다.
  - phase0 guard: `qty=1`, `max_new_entries_per_day=1`, `max_open_positions=3`, `max_total_notional_krw=300000`, same-symbol active 1개, AVG_DOWN/PYRAMID/scale-in 실주문 금지, 승인 후보의 BUY와 해당 청산 SELL만 실제 주문 허용으로 잠근다.
  - 자동화체인 연결: `swing_runtime_approval` JSON의 `real_canary_policy.policy_id=swing_one_share_real_canary_phase0`에 `real_order_allowed_actions=["BUY_INITIAL","SELL_CLOSE"]`, `sim_only_actions=["AVG_DOWN","PYRAMID","SCALE_IN"]`, `blocked_real_order_actions`와 rollback trigger를 machine-readable로 남긴다. `threshold_cycle_preopen_apply` manifest와 daily EV report도 이 policy를 그대로 노출한다.
  - 시작 조건: `swing_runtime_approval` hard floor와 EV trade-off 통과, 별도 사용자 real-canary approval artifact, 장전 preopen apply, DB load/instrumentation/fallback contamination/severe downside/same-stage conflict 없음이 모두 필요하다.
  - rollback guard: approval artifact 밖 실주문 1건, qty > 1, global dry-run 해제, receipt/order number mismatch, sell failure, price guard breach, daily/open/notional cap 초과, `actual_order_submitted` provenance 누락이다. 통과해도 스윙 전체 실주문 전환은 별도 2차 계획/승인 없이는 금지한다.

- [ ] `[ThresholdDailyEVReport0511] threshold-cycle 무인 반영 daily EV 성과 리포트 제출 확인` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [threshold_cycle_ev_report.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_ev_report.py), [scalping_pattern_lab_automation.py](/home/ubuntu/KORStockScan/src/engine/scalping_pattern_lab_automation.py), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py)
  - 판정 기준: `data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.{json,md}`가 생성되고, selected family/runtime_change, completed/open, win/loss, avg profit rate, realized PnL, submitted funnel, holding/exit latency, calibration decisions, pattern lab automation freshness/consensus/order 요약이 포함되어야 한다.
  - 범위: 장전 수동 승인, 수동 enable/hold 판정, 별도 관찰축 추가는 하지 않는다. 오류가 있으면 daily EV report의 `warnings`와 cron log/status로만 후속 원인을 분리한다.
  - 다음 액션: EV report 생성 정상 시 제출 완료로 닫는다. 누락 시 wrapper/cron/status 보강만 진행하고 threshold runtime 값을 장중 수동 변경하지 않는다.

- [ ] `[OpenAIThresholdCorrection0511] threshold AI correction OpenAI 라우팅/strict schema/guard 결과 확인` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~16:55`, `Track: RuntimeStability`)
  - Source: [README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [ai_response_contracts.py](/home/ubuntu/KORStockScan/src/engine/ai_response_contracts.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [run_threshold_cycle_calibration.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_calibration.sh)
  - 판정 기준: `threshold_cycle_ai_review_2026-05-11_{intraday,postclose}.{json,md}`의 `ai_provider_status.provider=openai`, 기본 모델 `gpt-5.5` 또는 fallback `gpt-5.4/gpt-5.4-mini`, `schema_name=threshold_ai_correction_v1`, `runtime_change=false`가 확인되어야 한다.
  - 자동화체인 연결: OpenAI correction은 AI reviewer + anomaly corrector proposal layer이며, threshold 적용 source of truth는 deterministic guard다. prompt contract는 영어 control prompt + 한국어 glossary + raw label 보존으로 고정한다.
  - 다음 액션: OpenAI 실패/parse reject가 있어도 deterministic calibration과 daily EV 생성을 실패시키지 않는다. 반복 실패 시 provider/키/schema incident로 분리하고 threshold 값을 장중 수동 변경하지 않는다.

- [ ] `[SAWOrderbookContext0511] statistical_action_weight SAW-6 orderbook context 자동화체인 입력 확장` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:15`, `Track: ScalpingLogic`)
  - Source: [2026-05-08-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-08-stage2-todo-checklist.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [performance_tuning_2026-05-08.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/performance_tuning_2026-05-08.json), [statistical_action_weight_2026-05-08.json](/home/ubuntu/KORStockScan/data/report/statistical_action_weight/statistical_action_weight_2026-05-08.json)
  - 판정 기준: 5/8 `StatActionAdvancedContext0508` 판정에 따라 readiness가 가장 높은 `SAW-6`만 report-only로 확장한다. 최소 필드는 `ofi_orderbook_micro_state`, threshold source, bucket, warning, micro VWAP 이탈, large sell/absorption proxy, join key coverage다.
  - 자동화체인 연결: 이 항목은 독립 관찰축이 아니라 `statistical_action_weight -> holding_exit_decision_matrix_advisory -> threshold_cycle_calibration -> threshold_cycle_ev` 입력 확장이다. runtime threshold, AI 응답, 주문/청산 행동을 직접 바꾸지 않고, candidate/readiness/calibration 근거만 machine-readable로 넘긴다.
  - 다음 액션: JSON/Markdown에 SAW-6 context 섹션이 생성되면 daily EV report 요약과 `holding_exit_decision_matrix_advisory` source metrics에 반영한다. 필드 누락이면 `instrumentation gap`으로 닫고 SAW-4/SAW-5를 대신 열지 않는다.

- [ ] `[OFIQPerformanceMarkdown0511] performance_tuning OFI/QI 자동화체인 stale guard 표면화` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: ScalpingLogic`)
  - Source: [2026-05-08-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-05-08-stage2-todo-checklist.md), [sniper_performance_tuning_report.py](/home/ubuntu/KORStockScan/src/engine/sniper_performance_tuning_report.py), [orderbook_stability_observer.py](/home/ubuntu/KORStockScan/src/trading/entry/orderbook_stability_observer.py), [performance_tuning_2026-05-08.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/performance_tuning_2026-05-08.json)
  - 판정 기준: 5/8 `OFIQExpansionLadder0508`에서 확정한 1순위 후속이다. `performance_tuning_YYYY-MM-DD.md`에 OFI/QI sample, state, threshold source, bucket, warning, symbol anomaly, `entry_ai_price_skip_policy`를 노출하고 2영업일 연속 표본 0 또는 핵심 필드 누락이면 `stale_context` warning을 출력한다.
  - 자동화체인 연결: 이 항목은 사람이 읽는 Markdown 보강만이 아니라 `performance_tuning`의 OFI/QI freshness와 stale warning을 daily EV 및 threshold-cycle source bundle이 소비할 수 있게 만드는 입력 품질 작업이다. prompt contract 변경, standalone OFI BUY/EXIT hard gate, bucket calibration ON은 열지 않는다.
  - 다음 액션: OFI/QI stale guard가 생성되면 `pre_submit_price_guard`, `score65_74_recovery_probe`, `holding_flow_ofi_smoothing`의 source metrics와 daily EV warning에 반영한다. 새 수동 workorder 대신 pattern lab order 또는 threshold-cycle candidate로만 다음 조치를 생성한다.

- [x] `[SwingPatternLabPhase3P1Instrumentation0511] 스윙 lifecycle 관찰축 및 추천-DB 적재 gap 보강` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:55`, `Track: ScalpingLogic`)
  - Source: [workorder-deepseek-swing-pattern-lab-phase3-remaining.md](/home/ubuntu/KORStockScan/docs/workorder-deepseek-swing-pattern-lab-phase3-remaining.md), [swing_lifecycle_audit.py](/home/ubuntu/KORStockScan/src/engine/swing_lifecycle_audit.py), [final_ensemble_scanner.py](/home/ubuntu/KORStockScan/src/scanners/final_ensemble_scanner.py), [swing_selection_funnel_report.py](/home/ubuntu/KORStockScan/src/engine/swing_selection_funnel_report.py)
  - 판정 기준: Phase3 workorder §3.2~§3.3의 P1 범위만 처리한다. stage별 raw/unique count, `instrumentation_gap`, simulation stage와 실제 주문 stage 분리, 추천 CSV row와 DB inserted count divergence reason을 추가한다.
  - 범위: 스윙 live 주문, Gatekeeper, market regime hard block, gap/protection guard, 예산/주문 safety, model floor, threshold runtime 값은 변경하지 않는다. DB load gap은 선정-적재 병목 진단 근거로만 쓴다.
  - 완료 메모: `swing_lifecycle_audit`와 `swing_selection_funnel_report`에 `recommendation_db_load.db_load_gap`, `db_load_skip_reason`, `db_load_error`, selection mode provenance를 추가했다. `swing_improvement_automation` DB gap order evidence와 EV summary에도 같은 사유가 전파된다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_build_code_improvement_workorder.py src/tests/test_threshold_cycle_ev_report.py`, `PYTHONPATH=. .venv/bin/python -m compileall -q src/engine`, `git diff --check`.

- [x] `[SwingPatternLabPhase3P2ReportOnlyFamily0511] 스윙 AI contract 및 AVG_DOWN/PYRAMID report-only family 설계` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: 17:55~18:15`, `Track: ScalpingLogic`)
  - Source: [workorder-deepseek-swing-pattern-lab-phase3-remaining.md](/home/ubuntu/KORStockScan/docs/workorder-deepseek-swing-pattern-lab-phase3-remaining.md), [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [ai_response_contracts.py](/home/ubuntu/KORStockScan/src/engine/ai_response_contracts.py), [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py)
  - 판정 기준: Phase3 workorder §3.4~§3.5의 P2 범위만 처리한다. AI prompt/입출력 inventory, schema valid rate, disagreement, latency/cost, `AVG_DOWN/PYRAMID/NONE`, add trigger/price policy/ratio/post-add outcome을 report-only로 남긴다.
  - 범위: OpenAI/DeepSeek/Gemini live routing, prompt 실제 교체, 주문 여부, 수량, 가격, threshold runtime 값은 변경하지 않는다. 모든 신규 family 후보는 `runtime_effect=false`, `allowed_runtime_apply=false`다.
  - 완료 메모: lifecycle event 요약에 `ai_contract_metrics`와 `scale_in_observation`을 추가했다. `schema_valid_rate`, parse fail, disagreement, latency/cost, prompt/model 분포와 `AVG_DOWN/PYRAMID/NONE`, add trigger, price policy, add ratio, post-add outcome, zero-sample reason이 report-only로 남는다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_model_selection_funnel_repair.py`, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py`.

- [ ] `[SwingPatternLabPhase3P3FreshDeepSeekReentry0511] fresh single-day DeepSeek re-entry 조건 확인` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: 18:15~18:30`, `Track: ScalpingLogic`)
  - Source: [workorder-deepseek-swing-pattern-lab-phase3-remaining.md](/home/ubuntu/KORStockScan/docs/workorder-deepseek-swing-pattern-lab-phase3-remaining.md), [run_all.sh](/home/ubuntu/KORStockScan/analysis/deepseek_swing_pattern_lab/run_all.sh), [swing_pattern_lab_automation.py](/home/ubuntu/KORStockScan/src/engine/swing_pattern_lab_automation.py), [build_code_improvement_workorder.py](/home/ubuntu/KORStockScan/src/engine/build_code_improvement_workorder.py), [threshold_cycle_ev_report.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_ev_report.py)
  - 판정 기준: `run_manifest.json`의 `analysis_window.start == target_date == end`와 필수 output 3종 JSON/schema 유효성을 확인한다. fresh 조건 미충족 시 `deepseek_lab_available=false`, `swing_lab_source_order_count=0`, `code_improvement_order_count=0`이어야 한다.
  - 범위: DeepSeek finding은 fresh single-day 조건이 닫힌 경우에만 `design_family_candidate` 또는 report-only order로 재진입한다. stale/range/malformed output은 warning만 남기고 workorder order로 승격하지 않는다.
  - 다음 액션: fresh 조건이 닫히면 다음 `code_improvement_workorder_YYYY-MM-DD.md`에 source/stage/family가 보존되는지 확인한다. fresh가 아니면 warning과 artifact link만 daily EV에 남긴다.
