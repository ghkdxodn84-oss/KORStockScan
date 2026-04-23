# Gemini Scalping Pattern Lab Final Review

- generated_at: `2026-04-22 19:14:50`
- analysis_period: `2026-04-22 ~ 2026-04-22`

## 1. 판정

- 종합 판정: `buy_recovery_canary 유지`, `신규 live 축 추가 보류`, `gatekeeper latency 경로 분해 지속`.
- why: today 기준으로 BUY 후보 회복 조짐은 있으나 제출/체결 연결 증거가 아직 없다.

## 2. 근거

### 2-1. Entry Funnel

- `gatekeeper_decisions=37`
- `gatekeeper_eval_ms_p95=16637ms`
- `gatekeeper_lock_wait_ms_p95=0ms`
- `gatekeeper_model_call_ms_p95=0ms`
- `budget_pass_events=1188`
- `submitted_events=1`
- `latency_block_events=1187`
- `quote_fresh_latency_blocks=947`

### 2-2. Buy Recovery Canary

- `WAIT65~79 total_candidates=246`
- `recovery_check=40`
- `promoted=6`
- `submitted=0`
- `blocked_ai_score_share=84.6%`

### 2-3. Priority Findings

- `AI threshold dominance`: 경고 | why: `blocked_ai_score_share=84.6%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.
- `Prompt improved but submit disconnected`: 경고 | why: `promoted=6`인데 `submitted=0`라 프롬프트 개선과 주문 회복을 동일시할 수 없다.
- `Gatekeeper latency high`: 경고 | why: `gatekeeper_eval_ms_p95=16637ms`로 지연 경고 구간에 들어가 있다.

### 2-4. Pattern Stats

- loss_patterns_top5=0
- profit_patterns_top5=0

## 3. 다음 액션

- `gatekeeper latency` 경로별 p95를 내일 장전 스냅샷에서 우선 확인한다.
- `WAIT65~79 -> submitted` 단절이 유지되면 threshold 추가 완화보다 제출 병목 수정/판정이 우선이다.
- `HOLDING` 축은 유효 표본 확보 전까지 확대하지 않는다.
