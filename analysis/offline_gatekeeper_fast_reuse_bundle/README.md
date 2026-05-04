# Offline Gatekeeper Fast Reuse Bundle (Deprecated)

이 디렉토리는 `2026-04-27` gatekeeper fast reuse/entry latency 진단 증적 링크 보존용이다.

## 현재 상태

- 상태: `retired/deprecated`
- active export/analyzer 경로: 사용하지 않음
- 표준 대체 경로: `analysis/offline_live_canary_bundle/`
- runtime 정책: `standby_diagnostic_report_only`

`gatekeeper_fast_reuse` 전용 offline bundle/codebase는 `2026-04-27` 장후 체크리스트에서 삭제 대상으로 닫혔다. core runtime의 `gatekeeper_fast_reuse` baseline 로직과 회귀 테스트는 별개이며, 이 retired bundle의 제거 대상이 아니다.

## Migration

서버 export는 아래 표준 명령을 사용한다.

```bash
PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py \
  --target-date 2026-04-27 \
  --slot-label smoke_1000 \
  --evidence-cutoff 10:00:00
```

로컬 분석은 아래 표준 명령을 사용한다.

```bat
analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat ^
  --bundle-dir "C:\KORStockScanV2\downloads\smoke_1000\offline_live_canary_exports\2026-04-27\smoke_1000" ^
  --since 09:00:00 ^
  --until 10:00:00 ^
  --label smoke_1000
```

## Compatibility

아래 legacy entrypoint는 한 릴리즈 동안 compatibility wrapper로 남긴다.

- `analysis/offline_gatekeeper_fast_reuse_bundle/export_server_bundle.py`
- `analysis/offline_gatekeeper_fast_reuse_bundle/run_local_bundle_analysis.py`
- `analysis/offline_gatekeeper_fast_reuse_bundle/run_local_bundle_analysis.bat`

wrapper도 내부적으로 `offline_live_canary_bundle` 표준 export/analyzer를 호출한다.

## Legacy Outputs

표준 analyzer는 compatibility 산출물을 계속 생성한다.

- `gatekeeper_fast_reuse_summary_<label>.json`
- `gatekeeper_fast_reuse_summary_<label>.md`
- `entry_latency_offline_summary_<label>.json`
- `entry_latency_offline_summary_<label>.md`

이 산출물은 제출병목 보조 진단이다. `submitted/full/partial` 회복 없이 `gatekeeper_fast_reuse_ratio`나 latency p95만으로 live entry 후보를 승격하지 않는다.
