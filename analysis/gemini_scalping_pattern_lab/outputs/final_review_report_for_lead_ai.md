# Gemini Scalping Pattern Lab Final Review

- generated_at: `2026-05-05 18:00:38`
- analysis_period: `2026-04-01 ~ 2026-04-17`

## 1. 판정

### 1-1. 코호트별 EV 요약

| 코호트 | 거래수 | 승률 | 손익 중앙값 | 손익 평균값 | 기여손익 합 | 표본충분 |
|---|---:|---:|---:|---:|---:|---|
| split-entry | 46 | 54.3% | +0.250% | -0.063% | -2.890% | ✓ |
| full_fill | 6 | 50.0% | -0.200% | -0.478% | -2.870% | ⚠️부족 |

### 1-2. Plan Rebase 관찰축 요약

- `WAIT65~79 total_candidates=0`, `recovery_check=0`, `promoted=0`, `submitted=0`
- `blocked_ai_score_share=0.0%`, `budget_pass_to_submitted_rate=1.0%`, `gatekeeper_eval_ms_p95=29336ms`

- `Gatekeeper latency high`: 경고 — `gatekeeper_eval_ms_p95=29336ms`로 지연 경고 구간에 들어가 있다.

### 1-3. 손실 패턴 Top 5

**#1** — 코호트: `split-entry` / 청산규칙: `scalp_soft_stop_pct`
- 빈도: 13건 | 중앙손익: -1.550% | 평균손익: -1.625% | 기여손익: -21.120%
- 보유시간 중앙값: 158.0초
- 선행 조건: 없음

**#2** — 코호트: `full_fill` / 청산규칙: `scalp_hard_stop_pct`
- 빈도: 1건 | 중앙손익: -3.380% | 평균손익: -3.380% | 기여손익: -3.380%
- 보유시간 중앙값: 61343.0초
- 선행 조건: 없음

**#3** — 코호트: `split-entry` / 청산규칙: `scalp_ai_early_exit`
- 빈도: 3건 | 중앙손익: -1.000% | 평균손익: -1.000% | 기여손익: -3.000%
- 보유시간 중앙값: 2179.0초
- 선행 조건: 없음

**#4** — 코호트: `split-entry` / 청산규칙: `scalp_preset_hard_stop_pct`
- 빈도: 4건 | 중앙손익: -0.770% | 평균손익: -0.740% | 기여손익: -2.960%
- 보유시간 중앙값: 256.0초
- 선행 조건: 없음

**#5** — 코호트: `full_fill` / 청산규칙: `scalp_soft_stop_pct`
- 빈도: 1건 | 중앙손익: -2.040% | 평균손익: -2.040% | 기여손익: -2.040%
- 보유시간 중앙값: 65.0초
- 선행 조건: 없음

### 1-4. 수익 패턴 Top 5

**#1** — 코호트: `split-entry` / 청산규칙: `scalp_trailing_take_profit` / 진입모드: `nan`
- 빈도: 20건 | 중앙손익: +0.800% | 평균손익: +1.111% | 기여손익: +22.220%

**#2** — 코호트: `full_fill` / 청산규칙: `scalp_preset_ai_review_exit` / 진입모드: `nan`
- 빈도: 1건 | 중앙손익: +1.920% | 평균손익: +1.920% | 기여손익: +1.920%

**#3** — 코호트: `split-entry` / 청산규칙: `scalp_ai_momentum_decay` / 진입모드: `nan`
- 빈도: 3건 | 중앙손익: +0.580% | 평균손익: +0.540% | 기여손익: +1.620%

**#4** — 코호트: `full_fill` / 청산규칙: `scalp_trailing_take_profit` / 진입모드: `nan`
- 빈도: 1건 | 중앙손익: +1.030% | 평균손익: +1.030% | 기여손익: +1.030%

**#5** — 코호트: `split-entry` / 청산규칙: `scalp_preset_protect_profit` / 진입모드: `nan`
- 빈도: 2건 | 중앙손익: +0.250% | 평균손익: +0.250% | 기여손익: +0.500%

### 1-5. 기회비용 회수 후보 Top 5

**#1** — `AI threshold miss`
- 차단 건수 합계: 983997건 | 차단 비율: 100.0% | 관찰 일수: 7일

**#2** — `overbought gate miss`
- 차단 건수 합계: 411938건 | 차단 비율: 100.0% | 관찰 일수: 7일

**#3** — `latency guard miss`
- 차단 건수 합계: 18025건 | 차단 비율: 99.2% | 관찰 일수: 7일

**#4** — `liquidity gate miss`
- 차단 건수 합계: 12991건 | 차단 비율: 98.9% | 관찰 일수: 7일

---

## 2. 근거

### 2-1. 코호트 분리 이유

- `full_fill`, `partial_fill`, `split-entry`는 손익 구조가 달라 합치면 EV 해석이 왜곡된다.
- Plan Rebase 관찰축은 EV 패턴의 원인을 설명하는 보조 증거로만 사용한다.
- 따라서 report의 중심은 실현 EV, 패턴 기여손익, 기회비용 순으로 유지한다.

### 2-2. sequence_fact 관찰

- rebase_integrity_flag: 19건
- partial_then_expand_flag: 0건
- same_symbol_repeat_flag: 0건
- same_ts_multi_rebase_flag: 0건

## 3. 다음 액션

### 3-1. EV 개선 우선순위

- `split-entry EV 누수 분리 점검`
  검증지표: split-entry 거래수, 손익 중앙값, 기여손익 합 재확인
- `split-entry / scalp_soft_stop_pct 손실패턴 분해`
  검증지표: 빈도=13, 중앙손익=-1.550%, 기여손익=-21.120%
- `AI threshold miss EV 회수 조건 점검`
  검증지표: 차단건수=983997, 차단비율=100.0%
- `overbought gate miss EV 회수 조건 점검`
  검증지표: 차단건수=411938, 차단비율=100.0%

### 3-2. Plan Rebase 연계 관찰

- HOLDING 발생 이후에는 `post_sell_feedback`과 `trade_review`를 함께 묶어 EV 해석을 보강한다.
- `WAIT65~79 -> submitted`가 끊겨 있으면 threshold 완화보다 제출 병목 원인 분리가 우선이다.
- `gatekeeper latency`는 EV 회수 실패 원인인지 성능 병목인지 분해 후 축 우선순위를 정한다.
