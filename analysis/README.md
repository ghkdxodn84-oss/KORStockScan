# Analysis Codebase Status

기준: `2026-05-04 KST`

## 판정

- `offline_live_canary_bundle`: 유지. 장중/장후 fresh 로그가 없을 때 same-slot 판정을 닫는 standby diagnostic/report-only 표준 경로다.
- `offline_gatekeeper_fast_reuse_bundle`: retired/deprecated. 과거 증적 링크와 legacy wrapper만 남기고 active codebase로 보지 않는다.
- `claude_scalping_pattern_lab`, `gemini_scalping_pattern_lab`: postclose monitoring 분석랩이며, `scalping_pattern_lab_automation`이 두 lab의 EV backlog/observability를 machine-readable `code_improvement_order`와 `auto_family_candidate`로 집계한다. live routing, threshold mutation, 주문/청산 판단, repo code patch를 직접 수행하지 않는다.

## 근거

- gatekeeper 전용 offline bundle/codebase는 `2026-04-27` checklist에서 삭제 대상으로 닫혔다.
- Plan Rebase 기준으로 offline/live bundle은 heavy builder 반복을 피하는 판정 입력이며, hard pass/fail 전제와 direction-only 사유 확인에만 쓴다.
- `offline_live_canary_bundle`은 legacy `gatekeeper_fast_reuse`/`entry_latency_offline` compatibility summary까지 생성한다.

## 표준 명령

```bash
PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py \
  --target-date YYYY-MM-DD \
  --slot-label h1000 \
  --evidence-cutoff 10:00:00
```

```bash
PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/run_local_canary_bundle_analysis.py \
  --bundle-dir tmp/offline_live_canary_exports/YYYY-MM-DD/h1000 \
  --since 09:00:00 \
  --until 10:00:00 \
  --label h1000
```

## 금지선

- analysis bundle/lab 산출물만으로 live threshold/order/exit 판단이나 repo code를 직접 변경하지 않는다.
- `gatekeeper_fast_reuse_ratio`, latency p95, pattern lab 제안은 submitted/full/partial, blocker, 체결품질, `COMPLETED + valid profit_rate`와 분리해 `code_improvement_order` 또는 `auto_family_candidate(allowed_runtime_apply=false)`로만 넘긴다.
