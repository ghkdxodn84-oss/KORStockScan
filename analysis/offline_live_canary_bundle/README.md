# Offline Live Canary Bundle

`offline_live_canary_bundle`은 장중 Codex 작업환경에 fresh 로그가 없을 때 사용자 로컬 PC에서 같은 서버 export 묶음을 분석하기 위한 lightweight standby diagnostic/report-only 번들이다. live threshold, 주문, 청산 판단을 직접 변경하지 않는다.

기존 `offline_gatekeeper_fast_reuse_bundle` 전용 codebase는 retired/deprecated 상태이며, legacy `gatekeeper_fast_reuse`/`entry_latency_offline` summary compatibility는 이 bundle의 선택적 진단 섹션으로 통합한다.

## 서버 Export

서버에서는 heavy snapshot/report builder를 호출하지 않고 파일 copy와 `pipeline_events` cutoff filtering만 수행한다. 번들 안의 `jsonl` 계열은 기본적으로 `.jsonl.gz`로 압축 저장한다.

```bash
PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py \
  --target-date 2026-04-28 \
  --slot-label h1000 \
  --evidence-cutoff 10:00:00
```

기본 출력 위치:

```text
tmp/offline_live_canary_exports/2026-04-28/h1000/
```

포함 대상:

- `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl.gz`
- `data/post_sell/post_sell_candidates_*.jsonl.gz`
- `data/post_sell/post_sell_evaluations_*.jsonl.gz`
- `data/report/monitor_snapshots/performance_tuning_YYYY-MM-DD.json`
- `data/report/monitor_snapshots/trade_review_YYYY-MM-DD.json`
- `data/report/monitor_snapshots/holding_exit_observation_*.json`
- `data/report/monitor_snapshots/manifests/*YYYY-MM-DD*.json`
- `data/gatekeeper/gatekeeper_snapshots_YYYY-MM-DD.jsonl.gz` if exists

없는 파일은 실패가 아니라 `bundle_manifest.json.missing_files`에 기록한다.

`bundle_manifest.json`에는 고정 canary명 `axes` 대신 `diagnostic_sections`를 기록한다.

- `entry_quote_fresh_composite`
- `soft_stop_micro_grace`
- `legacy_gatekeeper_fast_reuse`
- `entry_latency_offline`

## 로컬 PC 실행

로컬 PC에는 `slot_label`별 **bundle 루트 디렉토리 전체**를 그대로 복사한다.  
요약 파일만 따로 옮기면 stale 판정이 재발할 수 있으므로 아래 구조가 통째로 있어야 한다.

필수 복사 원본:

```text
/home/ubuntu/KORStockScan/tmp/offline_live_canary_exports/2026-04-28/h1200/
```

권장 로컬 대상:

```text
C:\KORStockScanV2\downloads\h1200\offline_live_canary_exports\2026-04-28\h1200\
```

복사 후 최소 확인 파일:

- `bundle_manifest.json`
- `data\pipeline_events\pipeline_events_2026-04-28.jsonl.gz`
- `data\report\monitor_snapshots\trade_review_2026-04-28.json` 또는 `.json.gz`
- `data\report\monitor_snapshots\performance_tuning_2026-04-28.json` 또는 `.json.gz`

실행 전제:

- Windows 로컬 repo 루트는 `C:\KORStockScanV2`
- `(.venv)`가 이미 활성화된 콘솔에서 실행
- `--bundle-dir`에는 반드시 실제 `...\h1200` 루트를 넣고, `results` 폴더를 넣지 않는다

예시:

```bat
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat ^
  --bundle-dir "C:\KORStockScanV2\downloads\h1000\offline_live_canary_exports\2026-04-28\h1000" ^
  --output-dir "C:\KORStockScanV2\downloads\h1000\offline_live_canary_exports\2026-04-28\h1000\results" ^
  --since 09:00:00 ^
  --until 10:00:00 ^
  --label h1000
```

누적 모드:

```bat
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat ^
  --bundle-dir "C:\KORStockScanV2\downloads\h1500\offline_live_canary_exports\2026-04-28\h1500" ^
  --output-dir "C:\KORStockScanV2\downloads\h1500\offline_live_canary_exports\2026-04-28\h1500\results" ^
  --cumulative-since 09:00:00 ^
  --until 15:00:00 ^
  --label h1500_cumulative
```

## 산출물

로컬 실행 후 기본값은 `bundle-dir\results\`에 생성된다. `--output-dir`를 주면 summary-only 폴더로 분리해서 쓸 수 있다. `--bundle-dir`는 반드시 실제 export bundle 루트여야 하며, summary만 모아둔 별도 폴더를 `bundle-dir`로 넘기면 stale 결과를 다시 보게 된다.

즉, 아래처럼 쓰면 된다.

- 올바른 `--bundle-dir`: `C:\KORStockScanV2\downloads\h1200\offline_live_canary_exports\2026-04-28\h1200`
- 잘못된 `--bundle-dir`: `C:\KORStockScanV2\downloads\h1200\offline_live_canary_exports\2026-04-28\h1200\results`

- `entry_quote_fresh_composite_summary_<label>.json`
- `entry_quote_fresh_composite_summary_<label>.md`
- `soft_stop_micro_grace_summary_<label>.json`
- `soft_stop_micro_grace_summary_<label>.md`
- `gatekeeper_fast_reuse_summary_<label>.json`
- `gatekeeper_fast_reuse_summary_<label>.md`
- `entry_latency_offline_summary_<label>.json`
- `entry_latency_offline_summary_<label>.md`
- `live_canary_combined_summary_<label>.json`
- `live_canary_combined_summary_<label>.md`

`entry_quote_fresh_composite_summary_<label>`에는 observe-only `orderbook_stability` 섹션도 포함된다. 이 섹션은 `unstable_quote_observed_count/share`, `unstable_reason_breakdown`, `unstable_vs_submitted`, `unstable_vs_fill`, `unstable_vs_latency_danger`를 제공하지만 live gate 판정에는 쓰지 않는다.

`entry_quote_fresh_composite_summary_<label>`에는 `latency_entry_price_guard` 섹션도 포함된다. 이 섹션은 `latency_state=DANGER`가 기존 `latency_quote_fresh_composite` canary로 `ALLOW_NORMAL` override된 주문의 `latency_danger_override_defensive` cohort를 분리하고, `submitted`, `full_fill`, `partial_fill`, `realized_slippage`, `COMPLETED + valid profit_rate`를 집계한다. `latency_override_defensive_ticks=3`은 v1 임시값이며 정식 정책 고정값이 아니다.

`gatekeeper_fast_reuse_summary_<label>`와 `entry_latency_offline_summary_<label>`는 retired gatekeeper 전용 bundle의 compatibility 산출물이다. `gatekeeper_fast_reuse_ratio`, `gatekeeper_eval_ms_p95`, `latency_state_danger`, `submitted/full/partial`를 같은 창에서 보지만 live 승격 근거가 아니라 보조 진단이다.

## 시간대별 기본 실행

```bat
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h0900\offline_live_canary_exports\2026-04-28\h0900" --output-dir "C:\KORStockScanV2\downloads\h0900\offline_live_canary_exports\2026-04-28\h0900\results" --since 09:00:00 --until 10:00:00 --label h0900
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1000\offline_live_canary_exports\2026-04-28\h1000" --output-dir "C:\KORStockScanV2\downloads\h1000\offline_live_canary_exports\2026-04-28\h1000\results" --since 09:00:00 --until 10:00:00 --label h1000
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1100\offline_live_canary_exports\2026-04-28\h1100" --output-dir "C:\KORStockScanV2\downloads\h1100\offline_live_canary_exports\2026-04-28\h1100\results" --since 10:00:00 --until 11:00:00 --label h1100
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1200\offline_live_canary_exports\2026-04-28\h1200" --output-dir "C:\KORStockScanV2\downloads\h1200\offline_live_canary_exports\2026-04-28\h1200\results" --since 11:00:00 --until 12:00:00 --label h1200
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1300\offline_live_canary_exports\2026-04-28\h1300" --output-dir "C:\KORStockScanV2\downloads\h1300\offline_live_canary_exports\2026-04-28\h1300\results" --since 12:00:00 --until 13:00:00 --label h1300
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1400\offline_live_canary_exports\2026-04-28\h1400" --output-dir "C:\KORStockScanV2\downloads\h1400\offline_live_canary_exports\2026-04-28\h1400\results" --since 13:00:00 --until 14:00:00 --label h1400
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1500\offline_live_canary_exports\2026-04-28\h1500" --output-dir "C:\KORStockScanV2\downloads\h1500\offline_live_canary_exports\2026-04-28\h1500\results" --since 14:00:00 --until 15:00:00 --label h1500
```

서버 export 기준도 같은 label을 쓴다.

```bash
PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h0900 --evidence-cutoff 10:00:00
PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1000 --evidence-cutoff 10:00:00
PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1100 --evidence-cutoff 11:00:00
PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1200 --evidence-cutoff 12:00:00
PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1300 --evidence-cutoff 13:00:00
PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1400 --evidence-cutoff 14:00:00
PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1500 --evidence-cutoff 15:00:00
```

`slot_label`은 판정 시각 기준이다. 따라서 `h1000`은 `10:00 KST`에 닫는 `09:00~10:00` 구간 bundle이다.

## 판정 원칙

- `latency_quote_fresh_composite`는 `submitted_orders >= 20`, baseline `>= N_min`, `ShadowDiff0428` 해소 전에는 hard pass/fail이 아니라 direction-only로만 본다.
- `legacy_gatekeeper_fast_reuse`와 `entry_latency_offline`은 retired diagnostic compatibility 섹션이다. `submitted/full/partial` 회복 없이 `gatekeeper_fast_reuse_ratio` 또는 latency p95만으로 entry live 후보를 승격하지 않는다.
- `latency_entry_price_guard`는 신규 entry canary가 아니라 기존 active entry canary의 BUY 체결품질 보호 가드다. v1은 실주문 3틱 하향과 `counterfactual_order_price_1tick` 로그를 함께 남기며, 부분 live A/B와 fallback/scout/split-entry는 별도 승인 전까지 금지한다.
- `latency_signal_quality_quote_composite`는 예비 검증축이다. analyzer는 `signal>=90`, `latest_strength>=110`, `buy_pressure_10t>=65`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False` 후보 수를 `signal_quality_quote_composite_candidate_events`로 산출하지만, 현재 live 판정에는 합산하지 않는다.
- `orderbook_stability`는 observe-only다. `unstable_quote_observed=True`라도 현재 진입병목 해소 전에는 주문 차단, scout-only 전환, position/frequency cap을 적용하지 않는다.
- `soft_stop_micro_grace`는 `soft_stop_micro_grace_events >= 10` 또는 `COMPLETED + valid profit_rate >= 10` 전에는 hard pass/fail이 아니라 direction-only로만 본다.
- `soft_stop_micro_grace_extend`는 기본 OFF 예비 파라미터다. 20초 유예가 비악화이나 반등 포착이 부족할 때만 `extension_sec`/`extension_buffer_pct`를 별도 축으로 검토한다.
- 두 축은 stage-disjoint concurrent canary이므로 combined summary에서 합산 판정하지 않는다.

## 월간 경량 백필

장중에도 `today growing file`을 피하고 `전일자까지`의 saved snapshot/jsonl만으로 `soft_stop`/`follow-through` 후보를 선별하려면 아래 스크립트를 사용한다.

```bash
PYTHONPATH=. .venv/bin/python analysis/april_follow_through_backfill.py \
  --month-start 2026-04-01 \
  --target-date 2026-04-27 \
  --output-dir tmp/monthly_backfill \
  --label through_0427
```

산출물:

- `tmp/monthly_backfill/april_follow_through_backfill_<label>.json`
- `tmp/monthly_backfill/april_follow_through_backfill_<label>.md`

특징:

- `trade_review` snapshot과 `post_sell_candidates/evaluations`만 읽는다.
- `guard_stdin_heavy_build` 경로를 타지 않는다.
- `good_cut_candidate / whipsaw / ambiguous / follow_through_failure` 1차 선별용이며, 정책 변경용 최종 감리 리포트가 아니다.

압축 참고:

- 서버 export bundle은 `pipeline_events`, `post_sell`, `gatekeeper`의 `jsonl`을 `.jsonl.gz`로 저장한다.
- 로컬 analyzer는 `.jsonl`과 `.jsonl.gz`를 모두 읽는다.
