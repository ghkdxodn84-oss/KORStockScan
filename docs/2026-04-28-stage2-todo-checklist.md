# 2026-04-28 Stage 2 To-Do Checklist

## 오늘 목적

- `soft_stop_micro_grace`를 `09:00~15:00` 시간단위로 관찰하고, hard stop 전환/미체결/동일종목 재진입 손실 악화가 있으면 즉시 OFF 판정한다.
- `latency_quote_fresh_composite`를 `09:00~15:00` 시간단위로 관찰하고, `same bundle + canary_applied=False` baseline 기준 제출 회복 여부를 닫는다.
- 진입병목 예비 검증축은 `latency_signal_quality_quote_composite` 하나만 준비하고, 현 entry canary가 실패하기 전에는 live ON 하지 않는다.
- 보유/청산 추가 조정 파라미터는 `soft_stop_micro_grace_extend` 하나만 준비하고, 20초 기본축의 비악화가 확인되기 전에는 live ON 하지 않는다.
- `latency_quote_fresh_composite`와 `soft_stop_micro_grace` 장중 판정에 fresh 로그가 없으면 `offline_live_canary_bundle` 서버 export와 사용자 로컬 analyzer 산출물로 같은 시간대 판정을 닫는다.
- `latency_quote_fresh_composite`와 `soft_stop_micro_grace`는 `09:00~15:00` 시간단위로 판정하고, 표본 부족 외의 보류 결론은 금지한다.
- `orderbook_stability_observation`은 `FR_10s`, `quote_age_p50/p90`, `print_quote_alignment` 관찰지표만 기록한다. 현재 진입병목 해소 전에는 live gate/canary로 쓰지 않는다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 동일 단계 내 `1축 canary`만 허용한다. 진입병목축과 보유/청산축은 별개 단계이므로 병렬 canary가 가능하지만, 같은 단계 안에서는 canary 중복을 금지한다.
- 동일 단계 replacement는 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
- 단계 분리: 진입병목 canary와 보유/청산 canary는 조작점, 적용 시점, cohort tag, rollback guard가 완전히 분리되고 단계별 판정을 유지할 때만 `stage-disjoint concurrent canary`로 운영할 수 있다.
- 관찰창이 끝나면 `즉시 판정 -> 다음 축 즉시 착수`를 기본으로 한다. 이미 수집된 데이터로 닫을 수 있는 판정은 장후/익일로 미루지 않는다.
- `장후/익일/다음 장전` 이관은 예외사유 4종(`단일 조작점 미정`, `rollback guard 미문서화`, `restart/code-load 불가`, `운영 경계상 same-day 반영 불가`) 중 하나로만 허용한다. 막힌 조건과 다음 절대시각이 없으면 이관 판정은 무효다.
- PREOPEN은 전일에 이미 `단일 조작점 + rollback guard + 코드/테스트 + restart 절차`가 준비된 carry-over 축만 받는다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- live 승인, replacement, stage-disjoint 예외, 관찰 개시 판정에는 `cohort`를 같이 잠근다. 최소 `baseline cohort`, `candidate live cohort`, `observe-only cohort`, `excluded cohort`를 구분하고 `partial/full`, `initial/pyramid`, `fallback` 혼합 결론을 금지한다.
- `ApplyTarget`은 문서에 명시된 값만 사용하고, parser/workorder가 `remote`를 추정하지 않도록 유지한다.
- 다축 동시 변경 금지, 승인 전 `main` 실주문 변경 금지 규칙을 유지한다.
- `orderbook_stability_observed`는 observe-only 이벤트다. `unstable_quote_observed=True`여도 주문 차단, scout-only 전환, position cap 변경을 하지 않는다.

## 장중 live canary offline bundle 판정 템플릿

- fresh 로그가 Codex 작업환경에 없으면 서버에서 아래 명령으로 lightweight bundle만 생성한다.
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1000 --evidence-cutoff 10:00:00`
- 사용자는 로컬 PC에서 아래 형식으로 analyzer를 실행해 결과 JSON/MD를 전달한다.
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1000\offline_live_canary_exports\2026-04-28\h1000" --since 09:00:00 --until 10:00:00 --label h1000`
- 시간대 label/window는 `h0900 09:00~10:00`, `h1000 09:00~10:00`, `h1100 10:00~11:00`, `h1200 11:00~12:00`, `h1300 12:00~13:00`, `h1400 13:00~14:00`, `h1500 14:00~15:00`로 맞춘다.
- 산출물은 `entry_quote_fresh_composite_summary_<label>.json/.md`, `soft_stop_micro_grace_summary_<label>.json/.md`, `live_canary_combined_summary_<label>.json/.md`를 기준으로 판정한다.
- 운영 원칙:
  - `09:10 KST` 전후 1차 점검은 가능하면 직접 로그/집계로 먼저 닫고, fresh 로그 접근이 막힐 때만 `h0900` bundle을 만든다.
  - `10:00 KST` 이후 시간단위 점검은 offline bundle 기본으로 보고, heavy snapshot/report builder 호출 없이 cutoff export만 사용한다.
  - `slot_label`은 `판정 시각 기준`이다. 따라서 `h1000`은 `10:00 KST`에 닫는 `09:00~10:00` 구간 bundle이다.

### 시간대별 서버 export 명령

- `09:10 KST` 필요시 1차 점검:
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h0900 --evidence-cutoff 10:00:00`
- `10:00 KST` 점검:
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1000 --evidence-cutoff 10:00:00`
- `11:00 KST` 점검:
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1100 --evidence-cutoff 11:00:00`
- `12:00 KST` 점검:
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1200 --evidence-cutoff 12:00:00`
- `13:00 KST` 점검:
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1300 --evidence-cutoff 13:00:00`
- `14:00 KST` 점검:
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1400 --evidence-cutoff 14:00:00`
- `15:00 KST` 점검:
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1500 --evidence-cutoff 15:00:00`

### 시간대별 로컬 analyzer 명령

- `09:10 KST` 필요시 1차 점검:
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h0900\offline_live_canary_exports\2026-04-28\h0900" --since 09:00:00 --until 10:00:00 --label h0900`
- `10:00 KST` 점검:
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1000\offline_live_canary_exports\2026-04-28\h1000" --since 09:00:00 --until 10:00:00 --label h1000`
- `11:00 KST` 점검:
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1100\offline_live_canary_exports\2026-04-28\h1100" --since 10:00:00 --until 11:00:00 --label h1100`
- `12:00 KST` 점검:
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1200\offline_live_canary_exports\2026-04-28\h1200" --since 11:00:00 --until 12:00:00 --label h1200`
- `13:00 KST` 점검:
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1300\offline_live_canary_exports\2026-04-28\h1300" --since 12:00:00 --until 13:00:00 --label h1300`
- `14:00 KST` 점검:
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1400\offline_live_canary_exports\2026-04-28\h1400" --since 13:00:00 --until 14:00:00 --label h1400`
- `15:00 KST` 점검:
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1500\offline_live_canary_exports\2026-04-28\h1500" --since 14:00:00 --until 15:00:00 --label h1500`

## 장전 체크리스트 (08:50~09:00)

- [x] `[SoftStopGrace0428-Preopen] soft_stop_micro_grace runtime/env/log 준비 확인` (`Due: 2026-04-28`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: `SCALP_SOFT_STOP_MICRO_GRACE_ENABLED`, `restart.flag` 반영 여부, `soft_stop_micro_grace` 로그 필드 기록 가능 여부를 확인한다.
  - 완료근거: live flag/env, `restart.flag` 반영 여부, `soft_stop_micro_grace` 로그 필드 기록 가능 여부.
  - 다음 액션: 실패 시 09:00 관찰 시작 전 `OFF 유지` 또는 `재기동 필요` 중 하나로 닫는다.
  - 실행 메모 (`2026-04-28 07:54 KST`): 후행 확인 기준 현재 main `bot_main.py` PID는 `136356`이며 시작시각은 `2026-04-28 07:40:01 KST`다. `restart.flag` 실파일은 비어 있어 미반영 재기동 요청이 남아 있지 않다.
  - 근거: [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py) 에서 `SCALP_SOFT_STOP_MICRO_GRACE_ENABLED=True`, `SEC=20`, `EMERGENCY_PCT=-2.0` 기본값이 고정돼 있고, [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:3878) 는 `soft_stop_micro_grace` stage에 `profit_rate`, `soft_stop_pct`, `emergency_pct`, `elapsed_sec`, `grace_sec`, `extension_used`, `exit_rule_candidate`를 기록한다.
  - 검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py -k "soft_stop_micro_grace"` -> `3 passed`
  - 다음 액션: 재기동 없이 장중 판정은 `[SoftStopGrace0428-0900]` 이후 시간대 점검으로 이어가고, rollback guard 발동 시에만 `SCALP_SOFT_STOP_MICRO_GRACE_ENABLED=False -> restart.flag` 순서로 OFF 한다.

- [x] `[QuoteFreshComposite0428-Preopen] latency_quote_fresh_composite runtime/env/log 준비 확인` (`Due: 2026-04-28`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 5-parameter bundle rule, active flag, `canary_applied` cohort tag, `fallback_regression=0` 확인.
  - 완료근거: bundle rule/env, cohort tag 기록 가능 여부, fallback 회귀 없음.
  - 다음 액션: 실패 시 09:00 관찰 시작 전 `OFF 유지` 또는 `재기동 필요` 중 하나로 닫는다.
  - 실행 메모 (`2026-04-28 07:54 KST`): 후행 확인 기준 현재 main `bot_main.py` PID는 `136356`이며 시작시각은 `2026-04-28 07:40:01 KST`다. `restart.flag` 실파일은 없고 `/proc/136356/environ`에도 관련 override가 없어 코드 기본값 경로로 동작한다.
  - 근거: [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:174) 에서 `SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=True` 기본값이 고정돼 있다. [src/engine/sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py:205) 는 `signal>=88`, `quote_stale=False`, `ws_age<=950ms`, `ws_jitter<=450ms`, `spread<=0.0075`, `danger_reasons subset=quote freshness family`를 묶음으로 검사하고, 통과 시 `quote_fresh_composite_canary_applied`와 `latency_quote_fresh_composite_normal_override`를 남긴다.
  - 검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_entry_latency.py -k "quote_fresh_composite_canary"` -> `2 passed`
  - 다음 액션: 재기동 없이 장중 판정은 `[QuoteFreshComposite0428-0900]` 이후 시간대 점검으로 이어가고, `fallback_regression` 또는 `composite_no_recovery`가 확인되면 `OFF -> restart.flag -> replacement 승인` 순서로만 교체한다.

## 장중 체크리스트 (09:00~15:20)

- [ ] `[SoftStopGrace0428-0900] soft_stop_micro_grace 09시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 09:00~09:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `same_symbol_reentry_loss_count`, `emergency_pct <= -2.0`, `fallback_regression=0`.
  - hard pass/fail 전제: `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort`의 `COMPLETED + valid profit_rate >= 10`.
  - 판정: 전제 충족 + 손실 tail 감소 + hard stop/동일종목 손실 비악화면 `유지`, 전제 충족 + hard stop 전환/동일종목 손실/미체결 악화면 `OFF`, 전제 미충족이면 `보류`.
  - 다음 액션: `유지`는 다음 시간 점검 계속, `OFF`는 `SCALP_SOFT_STOP_MICRO_GRACE_ENABLED=False` 및 재기동 필요 여부 기록, `보류`는 누적 표본 부족 수치와 다음 점검시각 기록.

- [ ] `[QuoteFreshComposite0428-0900] latency_quote_fresh_composite 09시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 09:10~09:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `full_fill`, `partial_fill`, `quote_fresh_composite_canary_applied=True/False`, `ShadowDiff0428`, `fallback_regression=0`.
  - hard pass/fail 전제: `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소.
  - 성공 기준: `budget_pass_to_submitted_rate >= baseline +1.0%p`, `latency_state_danger / budget_pass` baseline 대비 `-5.0%p` 이상 개선, `submitted -> full_fill + partial_fill` 전환율 baseline 대비 `-2.0%p` 이내.
  - 판정: 전제 충족 + 성공 기준 충족은 `유지`, 전제 충족 + `composite_no_recovery`는 `OFF 또는 다음 독립축 교체`, 전제 미충족은 `direction-only 보류`.
  - 다음 액션: `유지`는 다음 시간 점검 계속, `OFF`는 5개 파라미터 묶음 전체 OFF, `교체`는 새 workorder와 rollback guard 필요, `direction-only 보류`는 표본 부족 수치와 다음 점검시각 기록.

- [ ] `[SoftStopGrace0428-1000] soft_stop_micro_grace 10시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 10:00~10:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1000`, `09:00:00~10:00:00`
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `same_symbol_reentry_loss_count`, `emergency_pct <= -2.0`, `fallback_regression=0`.
  - hard pass/fail 전제: `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort`의 `COMPLETED + valid profit_rate >= 10`.
  - 판정/다음 액션: `유지`, `OFF`, `보류` 중 하나로 닫고, `보류` 시에도 다음 1시간 점검 또는 OFF/교체 액션을 기록한다.

- [ ] `[QuoteFreshComposite0428-1000] latency_quote_fresh_composite 10시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 10:10~10:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1000`, `09:00:00~10:00:00`
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `full_fill`, `partial_fill`, `quote_fresh_composite_canary_applied=True/False`, `ShadowDiff0428`, `fallback_regression=0`.
  - hard pass/fail 전제: `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소.
  - 판정/다음 액션: 성공 기준 충족 시 `유지`, `composite_no_recovery`면 `OFF 또는 다음 독립축 교체`, 전제 미충족이면 `direction-only 보류`와 2영업일 유효기간 및 다음 점검시각을 기록한다.

- [ ] `[OrderbookStability0428-1000] orderbook_stability_observation 10시 반영 확인` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 10:20~10:30`, `Track: ScalpingLogic`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1000`, `09:00:00~10:00:00`
  - 완료근거: fresh 또는 pipeline 로그에 `stage=orderbook_stability_observed`가 실제 기록되고, `entry_quote_fresh_composite_summary_h1000`에 `orderbook_stability` 섹션이 생성되며, `unstable_quote_observed_count/share`, `unstable_reason_breakdown`, `unstable_vs_submitted`, `unstable_vs_fill`, `unstable_vs_latency_danger`가 확인된다.
  - 판정: observe-only 로그/summary가 모두 생성되면 `반영 완료`, 로그 또는 summary 둘 중 하나라도 누락이면 `재점검 필요`, 둘 다 누락이면 `재기동 후 미반영 조사`.
  - 다음 액션: `반영 완료`여도 live gate 승격은 금지하고 관찰 표본만 누적한다. `재점검 필요` 또는 `미반영 조사`면 프로세스 재기동 시각, 첫 발생 로그 시각, bundle 경로를 함께 기록한다.

- [ ] `[SoftStopGrace0428-1100] soft_stop_micro_grace 11시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 11:00~11:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1100`, `10:00:00~11:00:00`
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `same_symbol_reentry_loss_count`, `emergency_pct <= -2.0`, `fallback_regression=0`.
  - hard pass/fail 전제: `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort`의 `COMPLETED + valid profit_rate >= 10`.
  - 판정/다음 액션: `유지`, `OFF`, `보류` 중 하나로 닫고, hard stop 전환/동일종목 손실/미체결 악화는 즉시 OFF 후보로 기록한다.

- [ ] `[QuoteFreshComposite0428-1100] latency_quote_fresh_composite 11시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 11:10~11:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1100`, `10:00:00~11:00:00`
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `full_fill`, `partial_fill`, `quote_fresh_composite_canary_applied=True/False`, `ShadowDiff0428`, `fallback_regression=0`.
  - hard pass/fail 전제: `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소.
  - 판정/다음 액션: 성공 기준 충족 시 `유지`, `composite_no_recovery`면 5개 파라미터 묶음 전체 OFF 또는 새 독립축 workorder 생성, 전제 미충족이면 표본 부족 수치와 다음 점검시각 기록.

- [ ] `[SoftStopGrace0428-1200] soft_stop_micro_grace 12시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1200`, `11:00:00~12:00:00`
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `same_symbol_reentry_loss_count`, `emergency_pct <= -2.0`, `fallback_regression=0`.
  - hard pass/fail 전제: `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort`의 `COMPLETED + valid profit_rate >= 10`.
  - 판정/다음 액션: 전제 충족 시 `유지` 또는 `OFF`, 전제 미충족 시 `보류`와 13:00 재판정 기록.

- [ ] `[QuoteFreshComposite0428-1200] latency_quote_fresh_composite 12시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 12:10~12:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1200`, `11:00:00~12:00:00`
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `full_fill`, `partial_fill`, `quote_fresh_composite_canary_applied=True/False`, `ShadowDiff0428`, `fallback_regression=0`.
  - hard pass/fail 전제: `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소.
  - 판정/다음 액션: 성공 기준 충족 시 `유지`, `composite_no_recovery`면 `OFF 또는 다음 독립축 교체`, direction-only는 2영업일 유효기간과 다음 점검시각을 기록한다.

- [ ] `[SoftStopGrace0428-1300] soft_stop_micro_grace 13시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 13:00~13:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1300`, `12:00:00~13:00:00`
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `same_symbol_reentry_loss_count`, `emergency_pct <= -2.0`, `fallback_regression=0`.
  - hard pass/fail 전제: `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort`의 `COMPLETED + valid profit_rate >= 10`.
  - 판정/다음 액션: `유지`, `OFF`, `보류` 중 하나로 닫고, `same_symbol_reentry_loss_count` 악화 시 soft_stop 축과 분리한 후속 후보를 기록한다.

- [ ] `[QuoteFreshComposite0428-1300] latency_quote_fresh_composite 13시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 13:10~13:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1300`, `12:00:00~13:00:00`
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `full_fill`, `partial_fill`, `quote_fresh_composite_canary_applied=True/False`, `ShadowDiff0428`, `fallback_regression=0`.
  - hard pass/fail 전제: `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소.
  - 판정/다음 액션: 성공 기준 충족 시 `유지`, `fallback_regression >= 1`이면 즉시 OFF/회귀조사, 전제 미충족 시 direction-only와 다음 점검시각 기록.

- [ ] `[SoftStopGrace0428-1400] soft_stop_micro_grace 14시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 14:00~14:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1400`, `13:00:00~14:00:00`
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `same_symbol_reentry_loss_count`, `emergency_pct <= -2.0`, `fallback_regression=0`.
  - hard pass/fail 전제: `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort`의 `COMPLETED + valid profit_rate >= 10`.
  - 판정/다음 액션: 15시 최종판정 전 `유지`, `OFF`, `보류` 임시판정을 기록하고, OFF 필요 시 재기동 필요 여부를 먼저 정리한다.

- [ ] `[QuoteFreshComposite0428-1400] latency_quote_fresh_composite 14시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 14:10~14:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1400`, `13:00:00~14:00:00`
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `full_fill`, `partial_fill`, `quote_fresh_composite_canary_applied=True/False`, `ShadowDiff0428`, `fallback_regression=0`.
  - hard pass/fail 전제: `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소.
  - 판정/다음 액션: 15시 최종판정 전 `유지`, `OFF`, `교체`, `direction-only 보류` 임시판정을 기록하고, 부분 적용 금지를 재확인한다.

- [ ] `[SoftStopGrace0428-1500] soft_stop_micro_grace 15시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 15:00~15:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1500`, `14:00:00~15:00:00`
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `same_symbol_reentry_loss_count`, `emergency_pct <= -2.0`, `fallback_regression=0`.
  - hard pass/fail 전제: `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort`의 `COMPLETED + valid profit_rate >= 10`.
  - 판정/다음 액션: `유지`, `OFF`, `보류` 중 하나로 닫고, 보류 시 누적 표본 부족 수치와 `2026-04-29 10:00` 재판정 조건을 기록한다.

- [ ] `[QuoteFreshComposite0428-1500] latency_quote_fresh_composite 15시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 15:10~15:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1500`, `14:00:00~15:00:00`
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `full_fill`, `partial_fill`, `quote_fresh_composite_canary_applied=True/False`, `ShadowDiff0428`, `fallback_regression=0`.
  - hard pass/fail 전제: `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소.
  - 판정/다음 액션: `유지`, `OFF`, `다음 독립축 교체`, `direction-only 보류` 중 하나로 닫고, direction-only는 2영업일 내 재판정 및 미재판정 자동 OFF를 기록한다.

- [ ] `[SoftStopGrace0428-Final1500] soft_stop_micro_grace 15시 종합판정` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 15:00~15:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정 기준: 결과는 `유지`, `OFF`, `표본부족으로 2026-04-29 10:00 재판정` 중 하나만 허용한다.
  - 완료근거: 09:00~15:00 누적 표본 수, hard stop 전환/동일종목 손실/미체결 악화 여부, `fallback_regression=0`.
  - 다음 액션: 표본부족 재판정은 누적 표본 수와 `2026-04-29 10:00 KST` 절대시각을 함께 기록한다.

- [ ] `[QuoteFreshComposite0428-Final1500] latency_quote_fresh_composite 15시 종합판정` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 15:10~15:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정 기준: 결과는 `유지`, `OFF`, `다음 독립축 교체`, `direction-only로 2026-04-29 10:00 재판정` 중 하나만 허용한다.
  - 완료근거: same bundle baseline, `submitted_orders`, `latency_state_danger`, fill quality, `ShadowDiff0428`, `fallback_regression=0`.
  - 다음 액션: `direction-only`는 `2영업일 내 재판정, 미재판정 시 자동 OFF` 규칙을 명시한다. `OFF/교체` 시 예비축은 `latency_signal_quality_quote_composite`만 검토하고, 기존 5개 파라미터 부분 적용은 금지한다.

## 장후 체크리스트 (18:05~19:20)

- [ ] `[HoldingExitPostclose0428] soft_stop/trailing/same_symbol 장후 분해` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 17:40~18:00`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `trailing`, `same_symbol_reentry`, `hard_stop_auxiliary`를 분리하고 full/partial, initial/pyramid 합산 결론을 금지한다.
  - 완료근거: soft_stop/trailing/same_symbol/hard_stop_auxiliary 분리표, `COMPLETED + valid profit_rate`, full/partial 분리, missed_upside/opportunity cost 분리.
  - 다음 액션: `2026-04-29` 유지/OFF/재판정 중 하나를 checklist에 자동 파싱 가능한 항목으로 생성한다.

- [ ] `[QuoteFreshPostclose0428] quote_fresh composite 장후 baseline/guard 정리` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:15`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [audit-reports/2026-04-27-entry-latency-composite-canary-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-27-entry-latency-composite-canary-audit-review.md)
  - 판정 기준: same bundle baseline, reference baseline, `ShadowDiff0428`, `composite_no_recovery`, `loss_cap`, `partial_fill_ratio`, `fallback_regression`을 분리 정리한다.
  - 완료근거: `quote_fresh_composite_canary_applied=True/False` baseline 비교, `2026-04-27 15:00` reference와 hard baseline 분리, guard별 발동 여부.
  - 다음 액션: `2026-04-29` 유지/OFF/교체/재판정 중 하나를 checklist에 자동 파싱 가능한 항목으로 생성한다.

- [ ] `[QuoteFreshBackupComposite0428] latency_signal_quality_quote_composite 예비 검증축 활성화 조건 검토` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:15~18:25`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정 기준: `latency_quote_fresh_composite`가 `composite_no_recovery` 또는 direction-only expiry로 종료될 때만 예비축을 검토한다. 조건은 `signal>=90`, `latest_strength>=110`, `buy_pressure_10t>=65`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False`, `fallback_regression=0`으로 고정한다.
  - 완료근거: `signal_quality_quote_composite_candidate_events`, `submitted/full/partial`, `latency_state_danger`, `ShadowDiff0428`, `fallback_regression` 분리표.
  - 다음 액션: 승인 시 `SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False`, `SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=True`, `restart.flag`, rollback guard를 자동 파싱 가능한 2026-04-29 항목으로 생성한다. 미승인 시 새 독립축 후보를 별도 workorder로 분리한다.

- [ ] `[SoftStopGraceExtend0428] soft_stop_micro_grace_extend 추가 조정 파라미터 활성화 조건 검토` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:25~18:35`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정 기준: 기본 `soft_stop_micro_grace 20초`가 hard stop/동일종목 손실/미체결을 악화시키지 않았지만 반등 포착이 부족한 경우에만 `extend_sec=10`, `extend_buffer_pct=0.20`, `emergency_pct=-2.0`을 검토한다.
  - 완료근거: `soft_stop_micro_grace_events`, `extension_used`, `scalp_hard_stop_pct`, `emergency_stop_events`, `same_symbol_reentry_loss_count`, `post_sell_soft_stop_rebound_above_sell_10m`, `mfe_ge_0_5`.
  - 다음 액션: 승인 시 `SCALP_SOFT_STOP_MICRO_GRACE_EXTEND_ENABLED=True`, `restart.flag`, OFF guard를 2026-04-29 항목으로 생성한다. 미승인 시 20초 기본축 유지/OFF/별도 보유청산 후보 중 하나로 닫는다.

- [x] `[FallbackSplit0428] fallback/split-entry 폐기 정합성 정리` (`Due: 2026-04-28`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:50`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`는 모든 실행축에서 제외 상태(`remove`)로 고정하고, `fallback_qty`는 historical guard 용어로만 남긴다.
  - why: 기준선 문서상 영구 폐기 축인데 runtime 분류표와 작업지시서에 `observe-only` 또는 `baseline-promote` 표현이 남아 있으면 재개 후보처럼 보인다.
  - 다음 액션: `remove / guarded-off / historical-only` 표현으로 같은 change set에서 문서 정합을 잠근다.

- [x] `[FallbackSplit0428] latency fallback split-entry code path hard-off 제거` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 09:10~09:30`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-27-stage2-todo-checklist.md)
  - 판정 기준: `CAUTION -> ALLOW_FALLBACK` 또는 scout/main fallback bundle이 실시간 주문 경로를 만들지 않아야 한다. `split_entry` follow-up runtime shadow도 기본 OFF여야 한다.
  - why: same-day 판정으로 entry 제출 회복과 무관한 축으로 닫혔고, partial/rebase 오염만 남긴다.
  - 다음 액션: deprecated reason/log는 historical trace로만 남기고 실전 경로는 reject로 닫는다.

- [x] `[FallbackSplit0428] 테스트·감시 지표 청소` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 09:40~10:20`, `Track: ScalpingLogic`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: fallback/split-entry 관련 테스트는 `deprecated reject` 또는 `historical helper`만 검증하도록 축소하고, runtime shadow 기본 OFF를 같이 검증한다.
  - why: 재개를 전제한 테스트/분류가 남아 있으면 운영 문서와 상충한다.
  - 검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/trading/tests/test_entry_orchestrator.py src/trading/tests/test_entry_policy.py src/tests/test_sniper_entry_latency.py src/tests/test_sniper_entry_metrics.py src/tests/test_split_entry_followup_audit.py src/tests/test_split_entry_followup_runtime.py`
    - `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_entry_latency.py src/engine/sniper_execution_receipts.py src/trading/entry/entry_orchestrator.py src/trading/entry/entry_policy.py`

- [x] `[FallbackSplit0428] 감리/보고 반영` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 17:40~18:00`, `Track: Plan`)
  - Source: [audit-reports/2026-04-27-entry-latency-single-axis-tuning-audit.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-27-entry-latency-single-axis-tuning-audit.md), [personal-decision-flow-notes.md](/home/ubuntu/KORStockScan/docs/personal-decision-flow-notes.md)
  - 판정 기준: `왜 제거되는지`, `무엇이 historical-only로 남는지`, `다음 관측포인트는 무엇인지`를 checklist와 audit 기준으로 고정한다.
  - why: 개인문서 단독 근거 사용 금지 원칙 때문에 최종 근거는 checklist/audit에 남아야 한다.

- [ ] `[QuoteFreshReview0428] quote_fresh composite 다음 판정 규칙 고정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:15`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [audit-reports/2026-04-27-entry-latency-composite-canary-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-27-entry-latency-composite-canary-audit-review.md)
  - 판정 기준: `latency_quote_fresh_composite`는 `signal/ws_age/ws_jitter/spread/quote_stale` 5개를 개별 축으로 해석하지 않고 묶음 ON/OFF로만 판정한다. `ws_age만 유지` 같은 부분 적용은 금지한다. primary baseline은 같은 bundle 내 `quote_fresh_composite_canary_applied=False`, `normal_only`, `post_fallback_deprecation` 표본으로 고정하고, baseline이 `N_min` 미달이거나 `submitted_orders < 20`이거나 `ShadowDiff0428` 미해소면 방향성 판정으로 격하한다. `ShadowDiff0428`은 submitted/full/partial 집계의 live runtime 경로와 offline bundle 경로 간 차이가 `1건 이내`로 좁혀진 상태를 뜻한다.
  - why: 복합축 이름으로 동일 단계 다중축 실험을 우회하면 원인귀속과 rollback 판단이 깨진다.
  - hard pass/fail 전제조건:
    - `submitted_orders >= 20`
    - baseline 표본 `>= N_min`
    - `ShadowDiff0428` 해소
  - 도달목표:
    - primary: `budget_pass_to_submitted_rate >= baseline +1.0%p`
    - secondary: `latency_state_danger / budget_pass` 비율 `-5.0%p` 이상 개선 and `full_fill + partial_fill`의 `submitted` 대비 전환율이 baseline 대비 `-2.0%p` 이내
  - 감리 검토 포인트:
    - 비교 baseline이 `same bundle + canary_applied=False`로 잠겼는지
    - `2026-04-27 15:00 offline bundle`은 참고선이고 hard pass/fail 기준선이 아니라는 점이 분리됐는지
    - `composite_no_recovery`, `loss_cap`, `partial_fill_ratio`, `normal_slippage_exceeded`, `fallback_regression` guard가 성공 기준과 섞이지 않고 분리 기재됐는지
    - baseline 부족, `submitted_orders < 20`, 또는 `ShadowDiff0428` 미해소 시 `direction-only` 판정으로 격하하고 `2영업일` 내 재판정, 미재판정 시 자동 OFF 규칙이 남아 있는지
  - 다음 액션: 다음 판정 메모에는 임계값별 `분포 기준`, `예상 기각률`, `효과 부족 시 fallback 임계값`, `composite_no_recovery` guard를 함께 남긴다.
  - fresh 로그 없음 대응: 같은 시각 `offline_live_canary_bundle`을 생성하고 사용자 로컬 산출물의 `entry_quote_fresh_composite_summary_<label>`로 `submitted/full/partial`, `latency_state_danger`, `fallback_regression_count`, `shadow_diff_status`, `direction_only_reason`을 확인한다.

- [ ] `[ShadowDiff0428] postclose submitted/full/partial mismatch 재분해` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:15~18:30`, `Track: ScalpingLogic`)
  - Source: [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-27-stage2-todo-checklist.md)
  - 판정 기준: `deploy/run_tuning_monitoring_postclose.sh 2026-04-27` 재실행에서 나온 `data/analytics/shadow_diff_summary.json`의 `submitted_events jsonl=19 vs duckdb=17`, `full_fill_count jsonl=37 vs duckdb=31`, `partial_fill_count jsonl=30 vs duckdb=24` 차이를 이벤트 복원/집계 품질 관점에서 재분해하고, 누락 source가 `pipeline_events`, `post_sell`, 집계 SQL 중 어디인지 닫아야 한다.
  - why: pattern lab 재실행은 복구됐지만 funnel/fill count mismatch를 그대로 두면 다음 진입병목 판정의 baseline 품질이 흔들린다.
  - 다음 액션: 차이 원인을 닫은 뒤 shadow diff 기준선을 다시 갱신하고, 필요하면 parquet builder 또는 compare 쿼리 수정 작업으로 승격한다.

- [ ] `[GeminiP1Rollout0428] main Gemini JSON system_instruction/deterministic flag 실전 승인 판정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:05~18:20`, `Track: ScalpingLogic`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md)
  - 판정 기준: `GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED`, `GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED`는 코드상 guard가 준비됐더라도 기본값 `OFF`를 유지한다. `main` 실전 엔진에서 이 flag를 켜려면 `BUY/WAIT/DROP`, `HOLD/TRIM/EXIT`, `condition/eod` JSON contract 유지, rollback owner, `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort`, parse_fail/consecutive_failures/ai_disabled 관찰 필드가 같은 메모에 잠겨 있어야 한다.
  - why: Gemini는 현재 `main` 실전 기준 엔진이라 P1은 단순 코드 완료가 아니라 live 판정 분포를 바꾸는 canary 승인 작업이다.
  - 다음 액션: 승인되면 `2026-04-29 PREOPEN` replacement 또는 observe-only 반영 시각을 고정하고, 미승인이면 보류 사유 1개와 재판정 시각 1개를 남긴다.

- [ ] `[DeepSeekP1Rollout0428] remote DeepSeek context-aware backoff flag 실전 승인 판정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:30`, `Track: ScalpingLogic`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - 판정 기준: `DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED`는 코드상 guard가 준비됐더라도 기본값 `OFF`를 유지한다. `remote` 운용에서 flag를 켜려면 `live-sensitive cap <= 0.8s`, `report/eod cap`, jitter 상한, `api_call_lock` 장기 점유 여부, retry 이후 rate-limit/log acceptance를 함께 잠가야 한다.
  - why: DeepSeek는 `remote` 운용 엔진이라 P1 잔여작업은 구현이 아니라 실제 enable 판정과 운영 acceptance다.
  - 다음 액션: 승인되면 `remote observe-only` 또는 `remote canary-only` 1개 경로와 적용 시각을 고정하고, 미승인이면 막힌 조건과 재판정 시각을 남긴다.

- [ ] `[GeminiSchema0428] Gemini JSON endpoint schema registry 적용 범위 잠금` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:05~18:25`, `Track: ScalpingLogic`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md)
  - 판정 기준: `entry_v1`, `holding_exit_v1`, `overnight_v1`, `condition_entry_v1`, `condition_exit_v1`, `eod_top5_v1` 6개 endpoint를 분리하고, `response_schema` 실패 시 기존 `json.loads/raw regex fallback` 경로로 즉시 복귀할 수 있어야 한다. `system_instruction`/deterministic JSON config flag와 schema registry를 한 change set에서 묶어 global live 전환하지 않는다.
  - why: Gemini는 `main` 실전 기준 엔진이라 범용 `_call_gemini_safe()` 한 줄 변경으로 전 경로를 동시에 바꾸면 BUY/WAIT/DROP 분포와 parse_fail 축이 함께 흔들린다.
  - 다음 액션: schema registry가 준비되면 endpoint별 테스트 목록과 fallback 필드를 아래 항목에서 잠그고, 준비가 안 되면 막힌 이유 1개와 재시각 1개를 same-day 메모에 남긴다.

- [ ] `[GeminiSchema0428] Gemini schema/fallback 테스트 매트릭스 및 관찰 필드 잠금` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:25~18:40`, `Track: ScalpingLogic`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md)
  - 판정 기준: 최소 `entry/holding_exit/overnight/condition_entry/condition_exit/eod_top5` 계약 테스트, `parse_fail`, `consecutive_failures`, `ai_disabled`, `gatekeeper action_label`, `submitted/full/partial` 영향 관찰 필드를 같이 고정한다. live canary를 검토하려면 `flag default OFF`, `rollback owner`, `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort`가 문서에 잠겨 있어야 한다.
  - why: schema는 파싱만 바꾸는 게 아니라 장애 관측 축과 rollback 경계까지 같이 정하지 않으면 `main` live 엔진에서 원인귀속이 흐려진다.
  - 다음 액션: 조건이 충족되면 `2026-04-29 POSTCLOSE` canary 검토 슬롯을 열고, 미충족이면 same-day 보류로 닫는다.

- [ ] `[DeepSeekGatekeeper0428] DeepSeek gatekeeper structured-output option 축 판정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: ScalpingLogic`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - 판정 기준: `generate_realtime_report()`의 사람용 text report는 유지하고, `evaluate_realtime_gatekeeper()`에만 JSON option 경로를 검토한다. `flag default OFF`, JSON 실패 시 text fallback, `action_label/allow_entry/report/selected_mode/timing` contract 유지 테스트가 없으면 착수하지 않는다.
  - why: DeepSeek는 `remote` 운용 엔진이지만, gatekeeper structured-output은 퍼블릭 contract와 캐시 테스트를 건드려 진입 판단 분포를 바꿀 수 있다.
  - 다음 액션: 승인되면 `remote observe-only` 또는 `remote canary-only` 중 1개 경로만 택하고, 미승인이면 막힌 조건과 다음 절대시각을 남긴다.

- [ ] `[DeepSeekHolding0428] DeepSeek holding cache bucket 조정 근거 점검` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:55~19:10`, `Track: Plan`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - 판정 기준: `holding cache miss 증가 -> completed_valid 품질 개선` 근거가 있는지, `partial/full`, `initial/pyramid`, `missed_upside`, `exit quality` 분리 기준에서 gain이 있는지 먼저 확인한다. 근거가 없으면 `_compact_holding_ws_for_cache()` 버킷 축소는 same-day 보류로 닫는다.
  - why: holding cache 세분화는 비용/호출량을 늘릴 수 있지만 기대값 개선이 아직 고정되지 않았다.
  - 다음 액션: 승인 근거가 생기면 `2026-04-29 POSTCLOSE` 설계 슬롯으로 넘기고, 없으면 `보류 유지`로 닫는다.

- [ ] `[DeepSeekTooling0428] DeepSeek Tool Calling 필요성/범위 판정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 19:10~19:20`, `Track: Plan`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - 판정 기준: Tool Calling이 실제로 `JSON parse_fail`, contract drift, 운영 복잡도 감소에 기여하는지 판단하고, 아니면 설계 메모로만 남긴다. SDK/응답 schema/테스트/rollback 구조가 준비되지 않으면 구현 작업으로 승격하지 않는다.
  - why: 현재 Tool Calling은 기능 개선보다 code debt/설계 검토 성격이 강하다.
  - 다음 액션: 필요성이 약하면 backlog 관찰로만 남기고, 필요성이 강하면 별도 workorder 초안과 테스트 범위를 same-day 문서화한다.
