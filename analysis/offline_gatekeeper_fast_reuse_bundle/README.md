# Offline Entry Latency Bundle

`gatekeeper_fast_reuse` 보조 진단과 `latency_state_danger -> other_danger relief` 주병목 판정을 서버 과부하 없이 로컬 PC에서 다시 확인하기 위한 오프라인 번들 도구다.

## 목적

- `10:00 KST` 스모크는 raw `pipeline_events`만으로 재확인한다.
- 오전 반나절 방향성 판정도 server-side heavy snapshot 재생성 대신, 서버에서 잘라낸 raw bundle을 로컬에서 다시 집계한다.
- `13:00 KST` 장중 pivot 판정도 같은 번들 경로로 처리한다. 이때 핵심 KPI는 `submitted/full/partial`, `latency_block`, `latency_state_danger`, `latency_danger_reason_breakdown`이다.
- 결과는 JSON/Markdown 파일로 남겨 다시 공유할 수 있다.

## 서버 측 번들 생성

서버 repo root에서 실행한다.

```bash
PYTHONPATH=. .venv/bin/python analysis/offline_gatekeeper_fast_reuse_bundle/export_server_bundle.py \
  --target-date 2026-04-27 \
  --slot-label smoke_1000 \
  --evidence-cutoff 10:00:00
```

오전 반나절 방향성 번들 예시:

```bash
PYTHONPATH=. .venv/bin/python analysis/offline_gatekeeper_fast_reuse_bundle/export_server_bundle.py \
  --target-date 2026-04-27 \
  --slot-label morning_1120 \
  --evidence-cutoff 11:20:00
```

기본 출력 경로:

- `tmp/offline_gatekeeper_fast_reuse_exports/<YYYY-MM-DD>/<slot_label>/`

`13:00` pivot 번들 예시:

```bash
PYTHONPATH=. .venv/bin/python analysis/offline_gatekeeper_fast_reuse_bundle/export_server_bundle.py \
  --target-date 2026-04-27 \
  --slot-label latency_1300 \
  --evidence-cutoff 13:00:00
```

## 로컬 PC 실행

전제:

- 로컬 repo root: `C:\KORStockScanV2`
- 로컬 venv: `C:\KORStockScanV2\.venv`
- 이 디렉토리를 로컬 repo의 `analysis\offline_gatekeeper_fast_reuse_bundle\` 아래에 둔다.

번들 디렉토리를 서버에서 내려받은 뒤 로컬에서 실행:

```bat
analysis\offline_gatekeeper_fast_reuse_bundle\run_local_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\smoke_1000\offline_gatekeeper_fast_reuse_exports\2026-04-27\smoke_1000"
```

필요하면 since/until을 직접 덮어쓸 수 있다.

```bat
analysis\offline_gatekeeper_fast_reuse_bundle\run_local_bundle_analysis.bat ^
  --bundle-dir "C:\KORStockScanV2\downloads\morning_1120\offline_gatekeeper_fast_reuse_exports\2026-04-27\morning_1120" ^
  --since 09:00:00 ^
  --until 11:20:00 ^
  --label morning_1120
```

## 산출물

기본 결과 경로:

- `<bundle-dir>\results\gatekeeper_fast_reuse_summary_<label>.json`
- `<bundle-dir>\results\gatekeeper_fast_reuse_summary_<label>.md`
- `<bundle-dir>\results\entry_latency_offline_summary_<label>.json`
- `<bundle-dir>\results\entry_latency_offline_summary_<label>.md`

핵심 출력:

- `budget_pass_events`
- `order_bundle_submitted_events`
- `budget_pass_to_submitted_rate`
- `latency_block_events`
- `latency_state_danger_events`
- `latency_reason_breakdown`
- `latency_danger_reason_breakdown`
- `quote_fresh_latency_pass_rate`
- `gatekeeper_decisions`
- `gatekeeper_fast_reuse_stage_events`
- `gatekeeper_fast_reuse_ratio`
- `gatekeeper_eval_ms_p95`
- `gatekeeper_reuse_blockers`
- `gatekeeper_sig_deltas`
- `full_fill_events`
- `partial_fill_events`
