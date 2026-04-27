# Offline Live Canary Bundle

`offline_live_canary_bundle`은 장중 Codex 작업환경에 fresh 로그가 없을 때 사용자 로컬 PC에서 같은 서버 export 묶음을 분석하기 위한 lightweight 번들이다. 기존 `offline_gatekeeper_fast_reuse_bundle`은 호환용으로 유지하고, 이 번들은 `latency_quote_fresh_composite`와 `soft_stop_micro_grace`를 함께 판정한다.

## 서버 Export

서버에서는 heavy snapshot/report builder를 호출하지 않고 파일 copy와 `pipeline_events` cutoff filtering만 수행한다.

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

- `data/pipeline_events/pipeline_events_YYYY-MM-DD.jsonl`
- `data/post_sell/post_sell_candidates_*.jsonl`
- `data/post_sell/post_sell_evaluations_*.jsonl`
- `data/report/monitor_snapshots/performance_tuning_YYYY-MM-DD.json`
- `data/report/monitor_snapshots/trade_review_YYYY-MM-DD.json`
- `data/report/monitor_snapshots/holding_exit_observation_*.json`
- `data/report/monitor_snapshots/manifests/*YYYY-MM-DD*.json`
- `data/gatekeeper/gatekeeper_snapshots_YYYY-MM-DD.jsonl` if exists

없는 파일은 실패가 아니라 `bundle_manifest.json.missing_files`에 기록한다.

## 로컬 PC 실행

예시:

```bat
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat ^
  --bundle-dir "C:\KORStockScanV2\downloads\h1000\offline_live_canary_exports\2026-04-28\h1000" ^
  --since 09:00:00 ^
  --until 10:00:00 ^
  --label h1000
```

누적 모드:

```bat
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat ^
  --bundle-dir "C:\KORStockScanV2\downloads\h1500\offline_live_canary_exports\2026-04-28\h1500" ^
  --cumulative-since 09:00:00 ^
  --until 15:00:00 ^
  --label h1500_cumulative
```

## 산출물

로컬 실행 후 `results\`에 생성된다.

- `entry_quote_fresh_composite_summary_<label>.json`
- `entry_quote_fresh_composite_summary_<label>.md`
- `soft_stop_micro_grace_summary_<label>.json`
- `soft_stop_micro_grace_summary_<label>.md`
- `live_canary_combined_summary_<label>.json`
- `live_canary_combined_summary_<label>.md`

`entry_quote_fresh_composite_summary_<label>`에는 observe-only `orderbook_stability` 섹션도 포함된다. 이 섹션은 `unstable_quote_observed_count/share`, `unstable_reason_breakdown`, `unstable_vs_submitted`, `unstable_vs_fill`, `unstable_vs_latency_danger`를 제공하지만 live gate 판정에는 쓰지 않는다.

## 시간대별 기본 실행

```bat
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h0900\offline_live_canary_exports\2026-04-28\h0900" --since 09:00:00 --until 10:00:00 --label h0900
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1000\offline_live_canary_exports\2026-04-28\h1000" --since 09:00:00 --until 10:00:00 --label h1000
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1100\offline_live_canary_exports\2026-04-28\h1100" --since 10:00:00 --until 11:00:00 --label h1100
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1200\offline_live_canary_exports\2026-04-28\h1200" --since 11:00:00 --until 12:00:00 --label h1200
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1300\offline_live_canary_exports\2026-04-28\h1300" --since 12:00:00 --until 13:00:00 --label h1300
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1400\offline_live_canary_exports\2026-04-28\h1400" --since 13:00:00 --until 14:00:00 --label h1400
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1500\offline_live_canary_exports\2026-04-28\h1500" --since 14:00:00 --until 15:00:00 --label h1500
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
- `latency_signal_quality_quote_composite`는 예비 검증축이다. analyzer는 `signal>=90`, `latest_strength>=110`, `buy_pressure_10t>=65`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False` 후보 수를 `signal_quality_quote_composite_candidate_events`로 산출하지만, 현재 live 판정에는 합산하지 않는다.
- `orderbook_stability`는 observe-only다. `unstable_quote_observed=True`라도 현재 진입병목 해소 전에는 주문 차단, scout-only 전환, position/frequency cap을 적용하지 않는다.
- `soft_stop_micro_grace`는 `soft_stop_micro_grace_events >= 10` 또는 `COMPLETED + valid profit_rate >= 10` 전에는 hard pass/fail이 아니라 direction-only로만 본다.
- `soft_stop_micro_grace_extend`는 기본 OFF 예비 파라미터다. 20초 유예가 비악화이나 반등 포착이 부족할 때만 `extension_sec`/`extension_buffer_pct`를 별도 축으로 검토한다.
- 두 축은 stage-disjoint concurrent canary이므로 combined summary에서 합산 판정하지 않는다.
