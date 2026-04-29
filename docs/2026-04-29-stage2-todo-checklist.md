# 2026-04-29 Stage2 To-Do Checklist

## 오늘 목적

- `latency_quote_fresh_composite` OFF 반영과 restart provenance를 장전 기준으로 확인한다.
- EC2 인스턴스가 `m7g.xlarge`로 상향 완료됐으므로 `runtime basis shift day`로 분리해 CPU/메모리 영향과 전략 효과를 섞지 않는다.
- `ShadowDiff0428`의 두 갈래 원인(`2026-04-28 parquet 미생성`, `2026-04-27 submitted/full/partial mismatch`)을 재검증한다.
- 스캘핑 신규 BUY `initial_entry_qty_cap`은 임시 `2주 cap`으로 완화하고, `initial-only`와 `pyramid-activated`를 계속 분리해 `zero_qty` 왜곡이 줄었는지 본다.
- `씨아이에스(222080)` micro grace 개입 표본의 전일 post-sell 평가는 장전부터 확인하고, 평가가 있으면 `soft_stop_micro_grace_extend` 후보를 장전 기준으로 다시 본다.
- `follow-through failure`는 observe-only backtrace와 스키마 구현 범위만 유지하고 live 축 승격은 보류한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 동일 단계 내 `1축 canary`만 허용한다. 진입병목축과 보유/청산축은 별개 단계이므로 병렬 canary가 가능하지만, 같은 단계 안에서는 canary 중복을 금지한다.
- 동일 단계 replacement는 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- `latency_signal_quality_quote_composite`는 `ShadowDiff` 재검증 전에는 auto-ON 하지 않는다. 단, `2026-04-29 12:21 KST` 사용자 운영 override로 제출 drought 지속 방치가 불허돼 same-day 1축 replacement로 ON 했다. 이후 판정은 hard baseline이 아니라 post-restart cohort 기준으로 분리한다.
- EC2 인스턴스 상향 직후 하루는 `QuoteFresh`, `latency_state_danger`, `gatekeeper_eval_ms_p95`를 전략 개선이 아니라 `infra basis shift` 후보로 먼저 본다.
- `soft_stop_micro_grace_extend`는 `씨아이에스(222080)` post-sell 평가 확인 전에는 승인하지 않는다.
- 전일 post-sell evaluation 존재 여부만 확인하면 되는 항목은 장후로 넘기지 않고 PREOPEN에서 먼저 닫는다. evaluation이 없으면 `candidate 존재`, `evaluation 생성 경로`, `막힌 원인`을 남긴 뒤에만 장중/장후로 이관한다.
- `initial_entry_qty_cap` 완화는 `1주 -> 2주` 단일축 조정으로만 본다. same-day에 `pyramid floor`나 추가 포지션 비율 축을 같이 열지 않는다.

## 장전 체크리스트 (08:30~09:00)

- [x] `[VMPerfRebase0429-Preopen] EC2 m7g.xlarge 변경 provenance 및 CPU/메모리 기준선 재확인` (`Due: 2026-04-29`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: RuntimeStability`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: `instance type`, `uname -m`, `nproc`, `MemAvailable`, `SwapUsed`, `load average`, main bot PID `/proc/<pid>/environ` 증적을 남기고, 오늘은 `runtime basis shift day`인지 여부를 확정한다.
  - 실행 메모 (`2026-04-28`, 사용자 확인): EC2 인스턴스 변경은 이미 `m7g.xlarge`로 완료됐다.
  - 실행 메모 (`2026-04-29 08:20 KST`): main `bot_main.py` PID는 `7042`, 시작시각은 `2026-04-29 07:56:00 KST`였다. `restart.flag`는 없었고 `/proc/7042/environ`에는 `KORSTOCKSCAN_*` override가 보이지 않아 코드 기본값 경로로 동작 중이다. 런타임 증적은 `uname -m=aarch64`, `nproc=4`, `MemAvailable=11726 MiB`, `SwapUsed=0 MiB`, `load average=0.86/0.83/0.75`였다.
  - 판정 결과: `완료 / runtime basis shift day 유지`
  - why: `t4g.medium -> m7g.xlarge` 변경 완료 직후 첫 거래일은 `QuoteFresh`와 `latency` 계열 baseline을 기존 거래일과 직접 비교하면 infra 효과와 전략 효과가 섞인다.
  - 근거: `aarch64 + 4 vCPU + 15.6 GiB 메모리 + swap unused` 증적이 모두 장전 시점에서 확인됐고, 봇도 `2026-04-29 07:56:00 KST`에 새 PID로 올라와 PREOPEN 범위의 provenance 요건을 충족했다. 오늘 수치는 전략 개선 근거가 아니라 `infra basis shift` 분리표의 기준값으로만 써야 한다.
  - 테스트/검증:
    - `ps -eo pid,lstart,cmd | rg 'bot_main.py|python .*bot_main'`
    - `tr '\0' '\n' < /proc/7042/environ | rg 'KORSTOCKSCAN_|SCALP_|GEMINI|DEEPSEEK'`
    - `uname -m`
    - `nproc`
    - `free -m`
    - `uptime`
  - 다음 액션: 장전에는 변경 여부 재판정이 아니라 provenance/리소스 증적만 남기고, 장중/장후 `QuoteFresh`는 `infra basis shift` 분리표와 함께 본다.

- [x] `[ShadowDiff0429-Preopen] 2026-04-28 parquet/duckdb rebuild 및 shadow diff 재검증` (`Due: 2026-04-29`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:42`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `data/analytics/parquet/pipeline_events/date=2026-04-28`, `post_sell/date=2026-04-28` partition이 생성되고 `submitted/full/partial` diff가 어디까지 줄었는지 확인한다.
  - 실행 메모 (`2026-04-29 08:20~08:21 KST`): `.venv`에서 `build_tuning_monitoring_parquet --dataset pipeline_events --single-date 2026-04-28`와 `--dataset post_sell --single-date 2026-04-28`를 재실행했다. 결과는 `pipeline_events_20260428.parquet=660,682 rows`, `post_sell_20260428.parquet=6 rows`였고 `data/analytics/parquet/pipeline_events/date=2026-04-28`, `post_sell/date=2026-04-28` partition이 모두 생성됐다.
  - 판정 결과: `부분완료 / 2026-04-28 diff 해소, 2026-04-27 historical mismatch 잔존`
  - why: `QuoteFresh` hard baseline은 `ShadowDiff` 미해소 상태에서 다시 승격할 수 없다.
  - 근거: rebuild 후 `compare_tuning_shadow_diff --start 2026-04-28 --end 2026-04-28`는 `all_match=true`로 `submitted=7`, `full_fill=9`, `partial_fill=3`까지 맞았다. 반면 `2026-04-27` 단독 비교는 여전히 `latency_block -3`, `full_fill -9`, `partial_fill -9`가 남아 `2026-04-27~2026-04-28` 합산 `all_match=false`였다. 즉 PREOPEN carry-over의 핵심인 `2026-04-28 parquet 미생성`은 해소됐지만, hard baseline 승격을 막던 historical 잔차는 아직 닫히지 않았다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python -m src.engine.build_tuning_monitoring_parquet --dataset pipeline_events --single-date 2026-04-28`
    - `PYTHONPATH=. .venv/bin/python -m src.engine.build_tuning_monitoring_parquet --dataset post_sell --single-date 2026-04-28`
    - `PYTHONPATH=. .venv/bin/python -m src.engine.compare_tuning_shadow_diff --start 2026-04-28 --end 2026-04-28`
    - `PYTHONPATH=. .venv/bin/python -m src.engine.compare_tuning_shadow_diff --start 2026-04-27 --end 2026-04-27`
    - `PYTHONPATH=. .venv/bin/python -m src.engine.compare_tuning_shadow_diff --start 2026-04-27 --end 2026-04-28`
  - 다음 액션: 미해소면 parquet builder/compare query 수정 항목으로 승격하고, 해소면 `QuoteFresh` 기준선 문구를 다시 잠근다.

- [ ] `[ShadowDiff0429-PostcloseRootCause] 2026-04-27 historical submitted/fill mismatch 원인분리` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~18:50`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `2026-04-28` parquet 미생성 이슈와 분리된 `2026-04-27 historical` 잔차만 대상으로 `latency_block -3`, `full_fill -9`, `partial_fill -9`의 원인이 `stale parquet`, `builder dedupe`, `compare metric 정의`, `raw stage 품질` 중 어디인지 닫는다.
  - why: PREOPEN 기준선 차단 요인은 같은 이름의 `ShadowDiff`라도 이미 `2026-04-28 freshness`와 `2026-04-27 historical`로 갈라졌다. 이 둘을 다시 합치면 `QuoteFresh` baseline 재승격 판단이 계속 흐려진다.
  - 다음 액션: 원인이 `builder/compare`면 same-day patch 후보로 승격하고, `raw stage 품질`이면 event restoration 감리로 분리한다. 미해소 시에도 `2026-04-28 all_match=true`와 `2026-04-27 residual`을 별도 문구로 고정한다.

- [x] `[SoftStopCIS0429-Preopen] 씨아이에스 micro grace post-sell 평가 및 extend 후보 장전 재판정` (`Due: 2026-04-29`, `Slot: PREOPEN`, `TimeWindow: 08:42~08:52`, `Track: Plan`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정 기준: `씨아이에스(222080)`의 `post_sell_evaluation`이 생성됐는지 먼저 확인하고, 있으면 `good_cut / whipsaw / ambiguous` 라벨과 `mfe/rebound`를 확인해 `soft_stop_micro_grace_extend` 후보 유지/폐기/보류를 닫는다.
  - 실행 메모 (`2026-04-29 08:19 KST`): `data/post_sell/post_sell_evaluations_2026-04-28.jsonl`에 `씨아이에스(222080)` 평가가 생성돼 있었다. 해당 표본은 `sell_time=12:35:05`, `profit_rate=-1.83%`, `outcome=MISSED_UPSIDE`, `rebound_above_sell=True`, `rebound_above_buy=False`, `metrics_10m.mfe_pct=0.98`, `hit_up_05=True`, `hit_up_10=False`였다.
  - 판정 결과: `완료 / extend 후보 유지, live 승인 보류`
  - why: 이 항목은 전일 `post_sell_evaluation` 확인 작업이므로 장후까지 기다릴 이유가 없다. 오전 거래가 몰리는 날에는 장전 후보 판정이 되어야 보유/청산축 원인귀속이 덜 흔들린다.
  - 근거: `씨아이에스`는 `micro grace` 개입 후에도 실제 청산은 `-1.83%`였지만, 매도가 위로는 10분 내 재상회했고 `+0.5%` 반등도 찍었다. 다만 `buy_price` 회복과 `+1.0%` 반등은 모두 실패해 `good_cut`로는 닫히지 않는다. 즉 기대값 관점에서는 `whipsaw/ambiguous` 쪽 증거가 생겨 `soft_stop_micro_grace_extend` 후보는 유지되지만, single-sample이라 같은 PREOPEN에 곧바로 live ON 할 수준은 아니다.
  - 테스트/검증:
    - `rg -n "222080|씨아이에스|MISSED_UPSIDE|rebound_above_sell|hit_up_05|hit_up_10" data/post_sell/post_sell_evaluations_2026-04-28.jsonl data/post_sell/post_sell_candidates_2026-04-28.jsonl -S`
  - 다음 액션: evaluation이 있으면 장전 판정을 닫고, 없으면 `candidate 존재`, `evaluation 생성 경로`, `막힌 원인`을 남긴 뒤 `12:00` 재확인 또는 장후 이관 여부를 구체적으로 정한다.

- [x] `[QuoteFreshComposite0429-PreopenOff] latency_quote_fresh_composite OFF/restart 반영 확인` (`Due: 2026-04-29`, `Slot: PREOPEN`, `TimeWindow: 08:52~09:00`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `latency_quote_fresh_composite` OFF 값이 env/runtime provenance(`/proc/<pid>/environ` 또는 동등 증적)와 restart 결과에 실제 반영됐는지 확인한다.
  - 실행 메모 (`2026-04-29 08:20 KST`): 최초 확인 시 main `bot_main.py` PID는 `7042`, 시작시각은 `2026-04-29 07:56:00 KST`였고 `restart.flag`는 존재하지 않았다. `/proc/7042/environ`에는 관련 `KORSTOCKSCAN_*` override가 없었고 코드 기본값 [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:174) 도 `SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=True`라서, `2026-04-28 16:08 KST` OFF 판정이 런타임 설정까지는 내려오지 못한 상태였다.
  - 실행 메모 (`2026-04-29 08:29 KST`): 코드 기본값을 `False`로 내리고 `restart.flag`를 생성한 뒤 우아한 재시작을 수행했다. 이후 `restart.flag`는 소모됐고 새 main PID는 `9267`, 시작시각은 `2026-04-29 08:29:27 KST`였다. `logs/bot_history.log`에는 `08:29:36 KST` 기준 스캐너 재기동과 메인 루프 재진입 로그가 남았다.
  - 판정 결과: `완료 / OFF 반영 및 restart provenance 확보`
  - why: same-day 판정은 `OFF`로 닫혔고, carry-over는 장전 provenance가 있어야만 유효하다.
  - 근거: PREOPEN 범위에서는 same-day `submitted/fill`이 아니라 `OFF 값 + restart 반영`만 보면 된다. 현재는 새 PID `9267`가 `SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False` 기본값을 읽는 코드로 다시 올라왔고, 예비축 `SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED`도 여전히 `False`라서 동일 단계 replacement 순서를 다시 맞췄다.
  - 테스트/검증:
    - `ps -eo pid,lstart,cmd | rg 'bot_main.py|python .*bot_main'`
    - `tail -n 80 logs/bot_history.log`
    - `tr '\0' '\n' < /proc/7042/environ | rg 'KORSTOCKSCAN_|SCALP_'`
    - [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:174)
  - 다음 액션: 장중에는 예비축 자동 ON 없이 baseline 관찰만 유지한다. 신규 entry 축 검토는 `[QuoteFreshBackupComposite0429-1220]`에서 `ShadowDiff`와 VM basis shift 판정 이후에만 다시 연다.

## 장중 체크리스트 (09:00~15:20)

- [x] `[EntryBottleneckVmShift0429-1000] VM 변경 후 진입병목 infra basis shift 1차 점검` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 10:00~10:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: `gatekeeper_eval_ms_p95`, `latency_state_danger / budget_pass`, `ws_age`, `ws_jitter`, `budget_pass_to_submitted_rate`, `full_fill`, `partial_fill`를 기존 `QuoteFresh` 결과와 분리해 본다.
  - why: 인스턴스 상향 직후 첫 1시간은 전략 canary보다 런타임 처리속도 개선 신호가 먼저 움직일 수 있다.
  - 실행 메모 (`2026-04-29 10:02~10:05 KST`): 표준 경로로 `h1000 (09:00:00~10:00:00)` offline bundle을 다시 생성하고 같은 워크스페이스에서 analyzer를 실행했다. 결과는 `budget_pass=3529`, `submitted=2`, `budget_pass_to_submitted_rate=0.0567%`, `latency_state_danger=2961 (83.9048%)`, `full_fill=1`, `partial_fill=0`, `fallback_regression=0`, `signal_quality_quote_composite_candidate_events=11`이었다. raw 재계산 기준 `gatekeeper_eval_ms_p95=10823.4ms (samples=7)`, `ws_age_ms_p95=655.8`, `ws_jitter_ms_p95=813.4`, `latency_state_danger` subset `ws_age_ms_p95=734.0`, `ws_jitter_ms_p95=823.0`였다.
  - 판정 결과: `완료 / infra-only improvement 후보, baseline reset 불가`
  - 근거: `gatekeeper_eval_ms_p95`는 `15,900ms` guard 아래이고 최근 reference로 써오던 `2026-04-27` `13,238.9ms`보다 낮아져 런타임 처리속도 개선 신호는 보인다. 동시에 `latency_state_danger share`도 `2026-04-28 h1000`의 `1120 / 1223 = 91.6%` 대비 오늘 `83.9%`로 낮아졌다. 그러나 같은 `09:00~10:00` 창의 제출 전환율은 `2026-04-28 h1000` `1 / 1223 = 0.0818%`보다 오늘 `2 / 3529 = 0.0567%`로 더 낮고, `ws_age/ws_jitter p95`도 여전히 `655.8ms / 813.4ms`로 quote freshness residual이 크다. 즉 `p95`와 `danger share` 개선은 보이지만 `submitted/full/partial`이 baseline reset을 말할 만큼 회복했다고 보기는 어렵다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-29 --slot-label h1000 --evidence-cutoff 10:00:00`
    - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/run_local_canary_bundle_analysis.py --bundle-dir tmp/offline_live_canary_exports/2026-04-29/h1000 --output-dir tmp/offline_live_canary_exports/2026-04-29/h1000/results --since 09:00:00 --until 10:00:00 --label h1000`
    - `tmp/offline_live_canary_exports/2026-04-29/h1000/results/entry_quote_fresh_composite_summary_h1000.json`
    - `tmp/offline_live_canary_exports/2026-04-29/h1000/results/live_canary_combined_summary_h1000.json`
    - `PYTHONPATH=. .venv/bin/python` raw 집계로 `09:00:00~10:00:00` 창 `gatekeeper_eval_ms_p95`, `ws_age_ms_p95`, `ws_jitter_ms_p95`를 재계산했다.
  - 다음 액션: `latency_state_danger`와 `gatekeeper_eval_ms_p95`만 개선되고 `submitted/full/partial`이 안 움직이면 `infra-only improvement`로 분리한다. 오전 거래가 충분히 몰렸으면 `[EntryBottleneckVmShift0429-1200Final]`에서 장후 대기 없이 baseline reset 여부를 닫는다.

- [x] `[EntryBottleneckVmShift0429-1200Final] VM 변경 후 진입병목 infra basis shift 12시 최종확정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: `09:00~12:00` 또는 12시 full snapshot 기준 `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger share`, `gatekeeper_eval_ms_p95`, `ws_age`, `ws_jitter`, `full_fill`, `partial_fill`, `ShadowDiff`를 보고 `VM 이후 baseline reset`, `infra-only improvement`, `기존 baseline 유지`, `판정유예` 중 하나로 닫는다.
  - why: 오전 거래가 집중되는 구조라면 12시 full snapshot이 `VM basis shift`의 1차 최종판정 창이다. 같은 데이터를 장후까지 기다리면 다음 entry 축 착수가 불필요하게 밀린다.
  - 실행 메모 (`2026-04-29 12:09~12:14 KST`): 표준 경로로 `h1200 (09:00:00~12:00:00)` offline bundle을 생성하고 analyzer를 재실행했다. 결과는 `budget_pass=9040`, `submitted=6`, `budget_pass_to_submitted_rate=0.0664%`, `latency_state_danger=8192 (90.6195%)`, `full_fill_events=21`, `partial_fill_events=18`, `fallback_regression=0`, `signal_quality_quote_composite_candidate_events=11`, `direction_only_reason=submitted_orders<20, baseline<50`였다. raw 재계산 기준 `budget_pass=9041`, `submitted=6`, `latency_state_danger=8193`, `gatekeeper_eval_ms_p95=11096.0ms (samples=17)`, `ws_age_ms_p95=766.0`, `ws_jitter_ms_p95=1009.0`, `danger subset ws_age/ws_jitter p95=811.0/1019.0`였다.
  - 판정 결과: `완료 / infra-only improvement`
  - 근거: `budget_pass_to_submitted_rate=0.0664%`는 `2026-04-28 same-day raw 0.082%`와 `2026-04-27 reference 0.1%` 모두 밑돌아 제출 회복 근거가 없다. 반면 `gatekeeper_eval_ms_p95=11096.0ms`는 `2026-04-27 reference 13238.9ms`보다 낮고, `latency_state_danger share=90.6%`도 `2026-04-28 same-day 96.0%`보다 낮아 런타임 측면 개선 신호는 남는다. 즉 `submitted/full/partial` 동반 회복 없는 `p95/latency_state_danger` 개선이므로 `VM 이후 baseline reset`이 아니라 `infra-only improvement`로 분리하는 것이 맞다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-29 --slot-label h1200 --evidence-cutoff 12:00:00`
    - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/run_local_canary_bundle_analysis.py --bundle-dir tmp/offline_live_canary_exports/2026-04-29/h1200 --output-dir tmp/offline_live_canary_exports/2026-04-29/h1200/results --since 09:00:00 --until 12:00:00 --label h1200`
    - `tmp/offline_live_canary_exports/2026-04-29/h1200/results/entry_quote_fresh_composite_summary_h1200.json`
    - `PYTHONPATH=. .venv/bin/python` raw 집계로 `09:00:00~12:00:00` 창 `budget_pass/submitted/latency_state_danger/gatekeeper_eval_ms_p95/ws_age/ws_jitter` 재확인
  - 다음 액션: entry 단계는 계속 live 축 공백 상태로 두고, 예비축 검토는 `[QuoteFreshBackupComposite0429-1220]`에서 data-quality gate와 replacement 절차 기준으로만 다시 닫는다.

## 장중 설계/후속 체크리스트 (12:20~14:20)

- [x] `[QuoteFreshBackupComposite0429-1220] latency_signal_quality_quote_composite 활성화 조건 12시 재판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 12:20~12:35`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `latency_quote_fresh_composite OFF/restart` 반영, `ShadowDiff` 재검증, `[EntryBottleneckVmShift0429-1200Final]`의 VM basis shift 판정을 확인한 뒤에만 예비축 ON 가능 여부를 닫는다.
  - why: 예비축 활성화 조건은 12시 VM/baseline 판정 이후 바로 판단 가능하다. 장후까지 기다리면 다음 entry 축 착수가 밀린다.
  - 실행 메모 (`2026-04-29 10:08 KST`): `09:00~10:00` 창 제출전환율이 `0.0567% (2/3529)`로 여전히 낮아 same-slot 조기 replacement 가능성을 다시 검토했다. 그러나 오늘 강제 규칙은 `latency_signal_quality_quote_composite`를 `ShadowDiff` 재검증 전 auto-ON 금지로 잠그고 있고, `h1000` summary도 `submitted_orders<20`, `baseline<50`, `signal_quality_quote_composite_candidate_events=11`만 보여줄 뿐 실제 recovery evidence는 아직 부족하다.
  - 조기판정 메모: `지금 즉시 ON 보류`
  - 근거: 오늘은 `runtime basis shift day`라 `gatekeeper_eval_ms_p95`와 `latency_state_danger share` 개선이 infra 효과인지 전략 효과인지 `12:00` 누적창에서 먼저 분리해야 한다. 또한 `2026-04-27 historical ShadowDiff` 잔차가 남아 있어 hard baseline 승격도 아직 불가하다. 따라서 `10시 전환율 미회복`만으로 예비축을 즉시 여는 것은 same-day replacement 승인 절차와 data-quality gate를 동시에 건너뛰는 셈이다.
  - 실행 메모 (`2026-04-29 12:14 KST`): `QuoteFresh OFF/restart provenance`는 이미 장전에 확보됐고, `h1200` summary에서도 `submitted_orders=6`, `budget_pass_to_submitted_rate=0.0664%`, `signal_quality_quote_composite_candidate_events=11`, `direction_only_reason=submitted_orders<20, baseline<50`였다. same-day `ShadowDiff`는 available 상태지만 historical `2026-04-27` 잔차는 여전히 남아 있다.
  - 판정 결과: `완료 / 운영 override로 ON 승인`
  - 근거: `[EntryBottleneckVmShift0429-1200Final]`이 `infra-only improvement`로 닫혀 전략 recovery 증거가 없고, 예비축 후보 이벤트도 `11건`에 그쳐 문서 기준으로는 미승인이었다. 그러나 사용자 운영판정에서 `BUY 신호 대비 submitted 급감`, `보유청산 튜닝 표본 고갈`, `진입병목 형상 유지 불허`가 명시돼, hard baseline 승격이 아니라 EV/거래수 회복을 우선하는 운영 override로 재판정했다. 동일 entry 단계의 기존 축 `latency_quote_fresh_composite`는 이미 OFF + restart 완료 상태이므로 same-day 1축 replacement 원칙은 유지한다.
  - 실행 메모 (`2026-04-29 12:21 KST`): [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:182)에서 `SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=True`로 전환하고 `restart.flag`를 생성했다. `restart.flag`는 소모됐고 main PID는 `9267 -> 30566`, 새 PID 시작시각은 `2026-04-29 12:21:28 KST`였다. threshold는 기존 예비축 정의 그대로 `signal>=90`, `latest_strength>=110`, `buy_pressure_10t>=65`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False`다.
  - 테스트/검증:
    - `tmp/offline_live_canary_exports/2026-04-29/h1200/results/entry_quote_fresh_composite_summary_h1200.json`
    - `tmp/offline_live_canary_exports/2026-04-29/h1200/results/live_canary_combined_summary_h1200.json`
    - PREOPEN provenance: main PID `9267`, `latency_quote_fresh_composite OFF + restart.flag 소모`
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_entry_latency.py -k "signal_quality_quote_composite"`
  - 다음 액션: `restart.flag`로 새 PID를 확인하고, 이후 cohort에서는 `latency_signal_quality_quote_composite_normal_override`, `signal_quality_quote_composite_canary_applied`, `submitted/full/partial`, `COMPLETED + valid profit_rate`, `fallback_regression=0`를 분리한다. post-restart `budget_pass >= 150`인데 `submitted <= 2`면 축 효과 미약으로 장후 rollback 검토를 연다.

- [x] `[InitialQtyCap0429-1235] 스캘핑 신규 BUY 2주 cap 완화 후 initial/pyramid 12시 1차 판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 12:35~12:50`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `initial_entry_qty_cap_applied cap_qty=2` runtime 증적, `initial-only` vs `pyramid-activated` 표본, `ADD_BLOCKED reason=zero_qty`, `position_rebased_after_fill`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`를 분리해 본다.
  - why: 오전 거래가 몰리면 12시까지 cap 완화가 `PYRAMID zero_qty` 왜곡을 줄였는지 1차 방향성은 볼 수 있다. full-day 손익 확정은 장후까지 기다릴 수 있지만, 구조적 zero_qty 여부는 장중에도 판단 가능하다.
  - 실행 메모 (`2026-04-29 12:18~12:21 KST`): raw `pipeline_events_2026-04-29.jsonl` 기준 `09:00~12:00` 창 `initial_entry_qty_cap_applied(cap_qty=2, applied=True)=6 events / 5 records`였다. 대상은 `올릭스(226950)`, `덕산하이메탈(077360, 2회)`, `비츠로테크(042370)`, `삼표시멘트(038500)`, `대한전선(001440)`였다. 같은 창에서 `pyramid_activated=0`, `ADD_BLOCKED reason=zero_qty=0`였고, cap cohort completed-valid는 `올릭스 -1.57`, `덕산하이메탈 -1.50`, `삼표시멘트 +0.65` 3건이었다.
  - 판정 결과: `완료 / 방향성 유지, 장후 보정 이관`
  - 근거: `2주 cap` runtime 증적은 충분하고 `zero_qty`가 오전 창에 0건이라 최소한 `1주 cap -> zero_qty 왜곡` 완화 방향은 맞다. 다만 `pyramid_activated`가 아직 0건이라 `initial-only`와 `pyramid-activated` 분리효과를 hard하게 닫을 표본은 없다. `completed_valid_avg_profit_rate`도 cap cohort 3건 평균 `-0.8067%`로 EV 개선을 말할 단계가 아니므로, 12시에는 `유지 방향성만 확인`하고 장후 보정으로 넘기는 것이 맞다.
  - 테스트/검증:
    - `rg -n '\"stage\": \"initial_entry_qty_cap_applied\"|\"stage\": \"pyramid_activated\"|\"stage\": \"add_blocked\"' data/pipeline_events/pipeline_events_2026-04-29.jsonl`
    - `PYTHONPATH=. .venv/bin/python` raw cohort 집계로 `cap_qty=2`, `pyramid_activated`, `zero_qty`, `completed_valid profit_rate` 확인
  - 다음 액션: `[InitialQtyCap0429-PostcloseFallback]`에서 full-day 기준으로 `initial-only` vs `pyramid-activated`, `zero_qty`, `COMPLETED + valid profit_rate`를 다시 닫는다. same-day에 `pyramid floor`나 cap 추가 완화는 열지 않는다.

- [x] `[FollowThroughSchema0429-1250] follow-through observe-only 스키마 구현 범위 재판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 12:50~13:05`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `체결 후 30초/1분/3분 가격`, `AI velocity`, `MFE/MAE`, `호가/직전 거래량`, `시장/섹터 동조성` 중 어디까지를 `post_sell/snapshot`로 먼저 넣을지 구현 범위를 닫는다.
  - why: 이 항목은 전일 월간 backfill과 기존 후보 3건 기반의 observe-only 설계 범위다. 당일 종가가 필요하지 않으므로 장후까지 미룰 이유가 없다.
  - 실행 메모 (`2026-04-29 12:24 KST`): `2026-04-28` carry-over 문맥과 `tmp/monthly_backfill/april_follow_through_backfill_through_0428.{md,json}`를 다시 확인했다. 월간 lightweight backfill 기준 `valid_completed_trades=237`, `soft_stop_rows=64`, `follow_through_failure candidate_count=3`였고, 전일 checklist는 이미 `체결 후 30초/1분/3분 가격`, `AI score velocity`, `MFE/MAE`, `체결 시점 호가 잔량 비율`, `직전 거래량`, `시장/섹터 동조성`을 observe-only 후보 필드로 고정해 둔 상태였다.
  - 판정 결과: `완료 / observe-only 스키마 범위 고정, live 승격 보류`
  - 근거: 월간 후보가 `3건`뿐이라 `follow-through failure`는 아직 live 축이 아니라 observe-only backtrace가 먼저다. 따라서 구현 범위는 전일 잠근 6개 필드로 유지하고, 저장 우선순위도 `post_sell + snapshot 우선, raw pipeline 보강 후순위`로 고정하는 것이 맞다. 표본 1건 또는 same-day 사례만으로 정책 변경 근거로 쓰지 않는다는 guard도 그대로 유지한다.
  - 테스트/검증:
    - `tmp/monthly_backfill/april_follow_through_backfill_through_0428.md`
    - `tmp/monthly_backfill/april_follow_through_backfill_through_0428.json`
    - [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md:357)
    - [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md:370)
  - 다음 액션: 다음 구현 change set에서는 `post_sell/snapshot` 스키마 보강만 올리고, `follow-through failure` live 후보 재판정은 표본 `20건` 도달 전까지 열지 않는다.

- [ ] `[SignalQualityQuoteComposite0429-PostRestart] latency_signal_quality_quote_composite 운영 override 후 post-restart cohort 1차 점검` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 13:05~13:25`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `restart.flag` 이후 새 PID 기준 `SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=True` 로드 여부, `latency_signal_quality_quote_composite_normal_override`, `signal_quality_quote_composite_canary_applied`, `submitted`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`, `fallback_regression=0`를 확인한다.
  - why: 이번 ON은 hard baseline 승격이 아니라 사용자 운영 override다. 따라서 기존 `h1200` baseline과 합치지 말고 post-restart cohort만 분리해 기대값/거래수 회복 여부를 봐야 한다.
  - rollback guard: post-restart `budget_pass >= 150`인데 `submitted <= 2`면 효과 미약으로 장후 rollback 검토를 연다. `fallback_regression > 0`, `normal_slippage_exceeded` 반복, 또는 canary cohort 일간 합산 손익이 당일 스캘핑 배정 NAV 대비 `<= -0.35%`이면 즉시 OFF 후보로 본다.
  - 다음 액션: 13:25까지 표본이 부족하면 장후 같은 항목에 `표본 부족`, `막힌 원인`, `다음 판정시각`을 남긴다.

- [ ] `[GeminiEngineCarry0429-1305] Gemini P1/P2 live 승인 전제와 schema 매트릭스 carry-over 판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 13:05~13:20`, `Track: ScalpingLogic`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - Owner: `Codex`
  - 판정 기준: `GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED`, `GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED`의 `flag default OFF` 유지 여부, `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort`, parse_fail/consecutive_failures/ai_disabled 관찰 메모, 그리고 `entry/holding_exit/overnight/condition_entry/condition_exit/eod_top5` schema/fallback 테스트 매트릭스 초안이 같은 문서에 잠겼는지 본다.
  - 실전 enable acceptance 정의:
    - `flag default OFF`와 rollback owner가 문서/코드에 함께 잠겨 있다.
    - `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort`가 명시돼 있다.
    - `parse_fail`, `consecutive_failures`, `ai_disabled`, `gatekeeper action_label`, `submitted/full/partial` 관찰 필드가 고정돼 있다.
    - 최소 `entry/holding_exit/overnight/condition_entry/condition_exit/eod_top5` endpoint별 fallback/test matrix 초안이 있다.
    - 위 4개 중 1개라도 비면 `실전 enable 미승인`으로 본다.
  - why: 이 항목은 엔진 설계/acceptance 정리라 종가 데이터가 필요하지 않다. 12시 운영 판정 후 바로 정리해도 된다.
  - 산출물: `Gemini enable acceptance 메모 1건`, `6 endpoint schema/fallback/test matrix 초안 1건`, `다음 change set 범위(main observe-only vs canary-only) 1건`
  - 다음 액션: acceptance가 잠기면 `2026-04-30 PREOPEN/POSTCLOSE` observe-only 또는 canary 검토 슬롯으로 넘기고, 안 잠기면 빠진 항목 1개와 완료 목표시각 1개를 같은 항목에 남긴다.

- [ ] `[GeminiSchemaBuild0429-1320] Gemini 6 endpoint schema registry/fallback/test matrix 초안 작성` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 13:20~13:45`, `Track: ScalpingLogic`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_gemini_engine_review.md)
  - Owner: `Codex`
  - 판정 기준: `entry_v1`, `holding_exit_v1`, `overnight_v1`, `condition_entry_v1`, `condition_exit_v1`, `eod_top5_v1` 각각에 대해 `schema scope`, `fallback path`, `required tests`, `observe fields`, `rollback point`가 표 형태로 초안화된다.
  - why: “없어서 보류”를 반복하지 않으려면 schema registry의 실제 설계 산출물을 먼저 만들어야 하며, 이 작업은 장후 데이터가 필요하지 않다.
  - 다음 액션: 초안이 나오면 `2026-04-30` 구현 change set owner/순서를 고정하고, 초안이 안 나오면 막힌 endpoint와 원인 1개씩 기록한다.

- [ ] `[DeepSeekEngineCarry0429-1345] DeepSeek P1/P2/P3 acceptance/backlog carry-over 판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 13:45~14:00`, `Track: Plan`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - Owner: `Codex`
  - 판정 기준: `DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED`의 `remote` live-sensitive acceptance(`api_call_lock`, rate-limit/log acceptance, observe-only/canary-only 경로), gatekeeper structured-output의 `flag-off + text fallback + contract test`, holding cache bucket 축소의 EV 근거, Tool Calling backlog 유지 여부를 한 묶음으로 확인한다.
  - 실전 enable acceptance 정의:
    - backoff 축: `live-sensitive cap <= 0.8s`, `report/eod cap`, `api_call_lock` worst-case, retry 후 rate-limit/log acceptance가 문서에 잠겨 있다.
    - gatekeeper structured-output 축: `flag default OFF`, text fallback, `action_label/allow_entry/report/selected_mode/timing` contract test가 있다.
    - holding cache 축: `completed_valid`, `partial/full`, `initial/pyramid`, `missed_upside`, `exit quality` 기준의 EV 근거가 있다.
    - Tool Calling 축: 퍼블릭 schema/fallback/테스트/rollback 구조가 없으면 구현 승격 금지다.
    - 위 조건이 안 맞으면 `remote 실전 enable 미승인` 또는 `backlog 유지`로 닫는다.
  - why: 04-28 판정 기준 DeepSeek 잔여축은 전부 실전 acceptance 또는 설계/backlog 범위이고, 장후 데이터가 필요한 항목이 아니다.
  - 산출물: `DeepSeek enable acceptance 메모 1건`, `backoff acceptance 표 1건`, `gatekeeper structured-output 설계 전제 1건`, `holding cache/Tool Calling backlog 결론 1건`
  - 다음 액션: acceptance가 생기면 `2026-04-30` change set 슬롯으로 넘기고, 없으면 빠진 acceptance 항목과 완료 목표시각을 같은 항목에 남긴다.

- [ ] `[DeepSeekAcceptanceBuild0429-1400] DeepSeek 실전 enable acceptance/spec 메모 작성` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 14:00~14:20`, `Track: Plan`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/workorder_deepseek_engine_review.md)
  - Owner: `Codex`
  - 판정 기준: `context-aware backoff`, `gatekeeper structured-output`, `holding cache`, `Tool Calling` 각각에 대해 `enable acceptance`, `not now reason`, `required proof`, `next implementation slot`이 문서화된다.
  - why: DeepSeek 잔여축은 코드보다 운영 acceptance가 먼저라, 설계/승인 메모를 장후까지 미루지 않고 고정해야 더 이상 공회전하지 않는다.
  - 다음 액션: 메모가 나오면 `2026-04-30` 구현/비구현 축을 갈라 배치하고, 없으면 빠진 증거와 담당 change set을 남긴다.

## 장후 보정 체크리스트 (18:30~19:00)

- [x] `[ProjectCarryover0428-Reconcile0429] 2026-04-28 POSTCLOSE carry-over 6건 source checklist 완료상태 재확인` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~18:40`, `Track: Plan`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: Project에 `Todo`로 남아 있더라도 source owner인 `2026-04-28 checklist`에서 `[HoldingExitPostclose0428]`, `[QuoteFreshPostclose0428]`, `[QuoteFreshReview0428]`, `[QuoteFreshBackupComposite0428]`, `[ShadowDiff0428]`, `[SoftStopGraceExtend0428]`가 이미 `[x]`인지 먼저 확인하고, source 기준 완료/보류 판정과 Project 상태의 불일치 여부를 분리한다.
  - why: Plan Rebase와 날짜별 checklist 기준에서는 실행 판정의 소유권이 source checklist에 있다. Project만 stale하면 같은 작업을 중복 수행하는 대신 source truth와 drift를 먼저 잠가야 한다.
  - 실행 메모 (`2026-04-29 18:34 KST`): `docs/2026-04-28-stage2-todo-checklist.md`를 다시 확인한 결과 6개 carry-over 항목이 모두 `[x]`였다. source 판정은 `HoldingExitPostclose0428=directional_only 유지`, `QuoteFreshPostclose0428=OFF`, `QuoteFreshReview0428=규칙 고정 완료`, `QuoteFreshBackupComposite0428=보류`, `ShadowDiff0428=미해소/원인위치 분리 완료`, `SoftStopGraceExtend0428=보류`였다. parser 기준으로도 `DOC_CHECKLIST_PATH=docs/2026-04-28-stage2-todo-checklist.md DOC_BACKLOG_TODAY=2026-04-28 ... --print-backlog-only` 출력에 이 6개 항목은 포함되지 않았다.
  - 판정 결과: `완료 / source checklist 기준 기처리, Project stale drift`
  - 근거: `workorder Source/Section`이 가리키는 원문 checklist가 이미 완료 상태이고, 관련 산출물(`holding_exit_observation_2026-04-28.json`, `post_sell_*_2026-04-28.jsonl`, `shadow_diff_summary`)도 남아 있다. 오늘 추가로 닫을 분석 실체는 없고, 현재 이슈는 Project 상태가 source와 어긋난 운영 drift다.
  - 테스트/검증:
    - `sed -n '320,490p' docs/2026-04-28-stage2-todo-checklist.md`
    - `env DOC_CHECKLIST_PATH=docs/2026-04-28-stage2-todo-checklist.md DOC_BACKLOG_TODAY=2026-04-28 PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only`
  - 다음 액션: source checklist를 기준으로 Project 상태를 재동기화한다. 추가 분석이 아니라 stale Todo 정리가 목적이므로, 같은 6건을 오늘 다시 실행하지 않는다.

- [x] `[EntryBottleneckVmShift0429-PostcloseFallback] VM 변경 후 진입병목 12시 미확정 시 보정 판정` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~18:45`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: `[EntryBottleneckVmShift0429-1200Final]`이 `ShadowDiff`, fresh 로그 미확보, 오전 표본 부족 중 하나로 못 닫혔을 때만 same-day `gatekeeper_eval_ms_p95`, `latency_state_danger share`, `budget_pass_to_submitted_rate`, `full_fill`, `partial_fill`, `ShadowDiff`를 재확인한다.
  - why: VM basis shift는 12시 확정을 기본으로 하고, 장후 항목은 미확정 보정용이다.
  - 실행 메모 (`2026-04-29 12:14 KST`): `[EntryBottleneckVmShift0429-1200Final]`이 same-day `infra-only improvement`로 이미 닫혔다.
  - 판정 결과: `해당 없음`
  - 근거: 장후 fallback은 12시 판정 미확정 보정용인데, 이번에는 fresh bundle과 raw 재집계가 모두 확보돼 12시 창에서 직접 닫혔다.
  - 테스트/검증:
    - `[EntryBottleneckVmShift0429-1200Final]` same-day 근거 재사용
  - 다음 액션: 없음.

- [ ] `[InitialQtyCap0429-PostcloseFallback] 스캘핑 신규 BUY 2주 cap 표본부족 시 장후 보정 판정` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 18:45~19:00`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `[InitialQtyCap0429-1235]`에서 표본 부족 또는 fresh 로그 미확보로 못 닫힌 경우에만 full-day `initial_entry_qty_cap_applied cap_qty=2`, `initial-only` vs `pyramid-activated`, `ADD_BLOCKED reason=zero_qty`, `position_rebased_after_fill`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`를 재확인한다.
  - why: 2주 cap의 구조적 효과는 12시 1차 판정을 기본으로 하고, 장후 항목은 표본부족/미확정 보정용이다.
  - 다음 액션: 12시에 닫혔으면 `해당 없음`으로 완료 처리한다. 장후까지 봐도 표본이 없으면 `표본 부족 유지`로 닫고 cap 추가 완화나 pyramid floor는 열지 않는다.

- [ ] `[SoftStopOliX0429-Postclose] 올릭스(226950) soft stop post-sell 라벨 및 micro grace 품질 판정` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 19:00~19:15`, `Track: Plan`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `올릭스(226950)` `record_id=4240`의 `post_sell_evaluation` 생성 여부를 확인하고, 생성되면 `good_cut / whipsaw / ambiguous`, `rebound_above_sell`, `rebound_above_buy`, `mfe_10m`, `same_symbol_soft_stop_cooldown_would_block`를 확인해 `soft_stop_micro_grace` 개입 품질을 닫는다.
  - why: same-day raw 기준으로는 `soft_stop_micro_grace`가 약 `27초` 개입한 뒤 `scalp_soft_stop_pct -1.57%`로 종료됐지만, 아직 `post_sell_evaluation`이 없어 기대값 판단을 hard하게 닫을 수 없다.
  - 다음 액션: evaluation이 생성되면 `씨아이에스`와 별도 표본으로 분리해 `micro grace 개입 실패/whipsaw/ambiguous` 중 하나로 닫는다. 장후에도 evaluation이 없으면 생성 경로와 막힌 원인을 함께 기록한다.

- [x] `[EntryPriceDaehanCable0429-Postclose] 대한전선(001440) submitted-but-unfilled 진입가 cap/timeout 적정성 판정` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 19:15~19:30`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-daehan-cable-entry-price-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-review.md), [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md)
  - 판정 기준: `대한전선(001440)` `record_id=4219`의 `entry_armed target_buy_price=48800`, `latency_pass normal_defensive_order_price=50400`, `best_bid/best_ask=50500/50900`, `order_bundle_submitted order_price=48800`, `BUY_ORDERED timeout_sec=1200` 증적을 기준으로, 미체결 원인이 `radar target cap 과도`, `round-figure avoidance`, `BUY_ORDERED timeout 과장`, `유동성/호가 추종 실패` 중 어디인지 닫는다.
  - why: same-day raw 기준 이 케이스는 `latency SAFE + submitted 성공`인데도 실주문가가 최우선 호가에서 3% 이상 아래로 내려가 체결 가능성이 사실상 없었다. 이는 entry drought와 별개로 `진입가 산정/timeout` 기대값 누수를 만들 수 있다.
  - 판정 결과: 완료 / `price cap authority conflict + timeout branch misuse + snapshot ambiguity`
  - 근거: 현재 코드상 `normal_defensive_order_price=50400` 산출 후 `target_buy_price=48800`이 `min(defensive_order_price, target_buy_price)`로 최종 주문가를 낮춘다. `best_bid=50500` 대비 하향 괴리는 약 `337bps`로, 유동성 부족보다 가격결정 권한 충돌이 미체결의 직접 원인이다.
  - 다음 액션: P0는 `pre-submit sanity guard + pipeline_events 가격 스냅샷 분리`로 즉시 보강한다. P1 `strategy-aware resolver/SCALPING timeout table`과 P2 `microstructure-adaptive band/reprice loop`는 별도 승인축으로 이관한다.
  - 테스트/검증: `src/tests/test_sniper_entry_latency.py`, `src/tests/test_sniper_scale_in.py`에 대한전선형 cap/guard 케이스를 추가한다.

- [ ] `[DynamicEntryPriceP0Guard0430-Preopen] pre-submit price guard + price snapshot split 구현/검증` (`Due: 2026-04-30`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:55`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: main bot restart provenance를 확인하고, `SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED=True`, `SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS=80` 로드 여부와 `latency_pass/order_leg_request/order_bundle_submitted/pre_submit_price_guard_block` 가격 스냅샷 필드 기록 여부를 확인한다.
  - why: 대한전선 케이스는 신규 alpha canary가 아니라 비정상 저가 제출을 막는 안전가드와 감리 추적성 보강이다. PREOPEN에서는 same-day submitted/fill 성과가 아니라 코드 로드, restart, 이벤트 필드 기록 가능성만 확인한다.
  - 다음 액션: 장전 로드가 확인되면 장중에는 `pre_submit_price_guard_block` 발생 여부와 `submitted_order_price`, `best_bid_at_submit`, `price_below_bid_bps`, `resolution_reason` 품질만 관찰한다. 로드 실패 시 P0 guard를 OFF한 채로 두지 말고 restart/provenance 원인을 우선 수정한다.

- [ ] `[DynamicEntryPriceP0Guard0430-Postclose] P0 guard KPI/rollback 1차 점검` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:20`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md), [2026-04-29-daehan-cable-entry-price-audit-followup.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-followup.md)
  - 판정 기준: same-day `pre_submit_price_guard_block_rate`, 전략별 제출 시도 수, `(best_bid - submitted_price)/best_bid` 분포 `p99`, `block 없이 통과한 deep bid` 재발 여부를 확인한다. 일간 차단율 `>0.5%`면 review trigger, `>2.0%`면 rollback 또는 threshold 완화 검토, `=0%`면 가드 비활성/로깅 누락 점검으로 닫는다.
  - why: P0는 가드를 켰다는 사실만으로 충분하지 않다. 운영 기준에서는 가드가 `너무 많이 막는지`, `아예 안 막는지`, `본 사고 유형을 실제로 막았는지`를 day-1부터 같이 봐야 한다.
  - 다음 액션: 차단율이 과도하면 `80bps` 임계를 provisional 값으로 재조정하고, 무차단 재발이 있으면 임계 강화 또는 resolver 우선 구현 검토로 승격한다. 전략별 표본이 부족하면 `2026-05-05` 분포 부록 항목과 연결해 rolling 7d 기준으로 재판정한다.

- [ ] `[SoftStopDuksan0429-Postclose] 덕산하이메탈(077360) soft stop post-sell 라벨 및 micro grace 품질 판정` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 19:15~19:30`, `Track: Plan`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `덕산하이메탈(077360)` `record_id=4246`의 `post_sell_evaluation` 생성 여부를 확인하고, 생성되면 `good_cut / whipsaw / ambiguous`, `rebound_above_sell`, `rebound_above_buy`, `mfe_10m`, `same_symbol_soft_stop_cooldown_would_block`를 확인해 `soft_stop_micro_grace` 개입 품질을 닫는다.
  - why: same-day raw 기준으로는 `soft_stop_micro_grace`가 약 `20초` 개입했지만 `peak_profit=-0.23`, `profit_rate=-1.50%`, `current_ai_score 85 -> 29` 하락 상태로 종료돼, 반등 누락인지 정당 컷인지 `post_sell_evaluation` 없이는 hard EV 판정을 닫을 수 없다.
  - 다음 액션: evaluation이 생성되면 `올릭스`, `씨아이에스`와 분리된 표본으로 `good_cut / whipsaw / ambiguous`를 닫는다. 장후에도 evaluation이 없으면 생성 경로와 막힌 원인을 함께 기록한다.

- [ ] `[AICacheCohort0429-Postclose] gatekeeper/holding AI cache hit vs miss 영향도 관찰축 판정` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 19:30~19:50`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `gatekeeper_cache=fast_reuse/hit/miss`, `ai_cache=hit/miss`, `ai_holding_skip_unchanged`를 코호트로 분리해 `submitted`, `budget_pass_to_submitted_rate`, `full_fill`, `partial_fill`, `soft_stop`, `COMPLETED + valid profit_rate` 차이를 확인하고, `보조지표 유지`, `고우선 observe-only 축 승격`, `독립 canary 후보 준비` 중 하나로 닫는다.
  - why: 현재 문서상 `gatekeeper_fast_reuse`는 종료된 보조 진단축이지만, 캐시/재사용 로직은 지연과 재평가 빈도에 영향을 주므로 submitted/EV에 대한 간접 영향도가 무시할 수준은 아니다. 다만 아직 `submitted/full/partial` 직접 회복 근거가 없어 same-day live 승격보다 영향도 관찰축으로 먼저 분리하는 것이 맞다.
  - 다음 액션: cache 코호트 차이가 `submitted` 또는 `soft_stop/EV`에 실제로 연결되면 다음 checklist에서 독립 observe-only 항목이나 canary 준비항목으로 승격한다. 차이가 없으면 rebase 문서의 `보조 진단 지표` 위치를 유지한다.

- [ ] `[ReentryPriceEscalation0429-Postclose] 덕산하이메탈(077360) 1차 미체결 후 2차 재진입가 상승 케이스 분석축 승격` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 19:50~20:10`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `덕산하이메탈(077360)` `record_id=4246`에서 `1차 submitted 17330 -> 미체결`, `2차 submitted/fill 18030`, `재진입가 상승폭 +700원 (+4.0%)`, `peak_profit=-0.23`, `soft_stop -1.50%`를 기준 케이스로 고정하고, 이 형상을 `entry price escalation after miss` 분석축으로 유지할지 여부를 닫는다.
  - why: 이 케이스는 단순 슬리피지 문제가 아니라 `1차 미체결 뒤 더 높은 가격을 다시 허용한 재진입 구조`가 EV를 훼손했을 가능성을 보여준다. 현재 entry 관찰축에는 `re-arm/reprice escalation`이 별도 고정돼 있지 않아, 같은 종류의 손실 표본을 다시 놓칠 수 있다.
  - 다음 액션: 장후에 동일 거래일 표본을 모아 `price guard 문제`, `target_buy_price 재산정 문제`, `re-arm 허용폭 문제` 중 어디가 주된 축인지 분리하고, 필요하면 익일 checklist에 observe-only 또는 canary 준비항목으로 승격한다.

- [ ] `[ReentryPriceEscalationSample0429-Postclose] 동일 거래일 1차 미체결 후 2차 재진입가 상승폭 표본 수집` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~20:30`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `data/pipeline_events/pipeline_events_2026-04-29.jsonl`에서 같은 `record_id` 기준 `1차 order_bundle_submitted` 이후 미체결 또는 `entry_armed_expired_after_wait`가 발생하고, 이후 `2차 order_bundle_submitted` 또는 fill이 이어진 종목을 수집해 `1차 target/order price`, `2차 target/order price`, `상승폭(원/%), full/partial fill`, `COMPLETED + valid profit_rate`, `soft_stop 여부`를 표로 정리한다.
  - why: 덕산하이메탈 단일 사례만으로는 구조 문제를 일반화할 수 없다. 같은 날 표본을 모으면 `고점 추격형 재진입`이 반복되는지, 아니면 개별 종목 예외인지 구분할 수 있다.
  - 다음 액션: 표본이 3건 이상이면 다음 checklist에 `reentry_price_escalation observe-only` 축을 올리고, 표본이 부족하면 오늘 사례를 anchor case로만 유지한다.
