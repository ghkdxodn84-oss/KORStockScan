# Gemini Scalping Pattern Lab Final Review

- generated_at: `2026-05-08 16:14:02`
- analysis_period: `2026-04-21 ~ 2026-05-08`

## 1. 판정

### 1-1. 코호트별 EV 요약

| 코호트 | 거래수 | 승률 | 손익 중앙값 | 손익 평균값 | 기여손익 합 | 표본충분 |
|---|---:|---:|---:|---:|---:|---|
| split-entry | 58 | 46.6% | -0.785% | -0.383% | -22.240% | ✓ |
| full_fill | 8 | 37.5% | -0.785% | -0.613% | -4.900% | ⚠️부족 |

### 1-2. Plan Rebase 관찰축 요약

- `WAIT65~79 total_candidates=511`, `recovery_check=0`, `promoted=0`, `submitted=1`
- `blocked_ai_score_share=90.2%`, `budget_pass_to_submitted_rate=1.4%`, `gatekeeper_eval_ms_p95=11428ms`

- `AI threshold dominance`: 경고 — `blocked_ai_score_share=90.2%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.

### 1-3. 손실 패턴 Top 5

**#1** — 코호트: `split-entry` / 청산규칙: `scalp_soft_stop_pct`
- 빈도: 26건 | 중앙손익: -1.745% | 평균손익: -1.843% | 기여손익: -47.910%
- 보유시간 중앙값: 530.5초
- 선행 조건: 없음

**#2** — 코호트: `full_fill` / 청산규칙: `scalp_soft_stop_pct`
- 빈도: 3건 | 중앙손익: -1.710% | 평균손익: -1.763% | 기여손익: -5.290%
- 보유시간 중앙값: 8021.0초
- 선행 조건: 없음

**#3** — 코호트: `split-entry` / 청산규칙: `protect_trailing_stop`
- 빈도: 3건 | 중앙손익: -1.170% | 평균손익: -0.813% | 기여손익: -2.440%
- 보유시간 중앙값: 1168.0초
- 선행 조건: 없음

**#4** — 코호트: `full_fill` / 청산규칙: `scalp_hard_stop_pct`
- 빈도: 1건 | 중앙손익: -2.250% | 평균손익: -2.250% | 기여손익: -2.250%
- 보유시간 중앙값: 172465.0초
- 선행 조건: 없음

**#5** — 코호트: `split-entry` / 청산규칙: `scalp_preset_hard_stop_pct`
- 빈도: 1건 | 중앙손익: -0.830% | 평균손익: -0.830% | 기여손익: -0.830%
- 보유시간 중앙값: 116.0초
- 선행 조건: 없음

### 1-4. 수익 패턴 Top 5

**#1** — 코호트: `split-entry` / 청산규칙: `scalp_trailing_take_profit` / 진입모드: `nan`
- 빈도: 22건 | 중앙손익: +0.760% | 평균손익: +1.015% | 기여손익: +22.340%

**#2** — 코호트: `split-entry` / 청산규칙: `scalp_ai_momentum_decay` / 진입모드: `nan`
- 빈도: 3건 | 중앙손익: +2.470% | 평균손익: +1.950% | 기여손익: +5.850%

**#3** — 코호트: `full_fill` / 청산규칙: `scalp_trailing_take_profit` / 진입모드: `nan`
- 빈도: 3건 | 중앙손익: +0.590% | 평균손익: +0.913% | 기여손익: +2.740%

**#4** — 코호트: `split-entry` / 청산규칙: `scalp_trailing_take_profit` / 진입모드: `normal`
- 빈도: 1건 | 중앙손익: +1.300% | 평균손익: +1.300% | 기여손익: +1.300%

**#5** — 코호트: `split-entry` / 청산규칙: `protect_trailing_stop` / 진입모드: `nan`
- 빈도: 1건 | 중앙손익: +0.190% | 평균손익: +0.190% | 기여손익: +0.190%

### 1-5. 기회비용 회수 후보 Top 5

**#1** — `AI threshold miss`
- 차단 건수 합계: 2546880건 | 차단 비율: 100.0% | 관찰 일수: 16일

**#2** — `overbought gate miss`
- 차단 건수 합계: 818347건 | 차단 비율: 100.0% | 관찰 일수: 16일

**#3** — `latency guard miss`
- 차단 건수 합계: 58907건 | 차단 비율: 99.5% | 관찰 일수: 16일

**#4** — `liquidity gate miss`
- 차단 건수 합계: 44016건 | 차단 비율: 99.3% | 관찰 일수: 16일

---

## 2. 근거

### 2-1. 코호트 분리 이유

- `full_fill`, `partial_fill`, `split-entry`는 손익 구조가 달라 합치면 EV 해석이 왜곡된다.
- Plan Rebase 관찰축은 EV 패턴의 원인을 설명하는 보조 증거로만 사용한다.
- 따라서 report의 중심은 실현 EV, 패턴 기여손익, 기회비용 순으로 유지한다.

### 2-2. sequence_fact 관찰

- rebase_integrity_flag: 6건
- partial_then_expand_flag: 0건
- same_symbol_repeat_flag: 0건
- same_ts_multi_rebase_flag: 0건

## 3. 다음 액션

### 3-1. EV 개선 우선순위

- `split-entry EV 누수 분리 점검`
  검증지표: split-entry 거래수, 손익 중앙값, 기여손익 합 재확인
- `split-entry / scalp_soft_stop_pct 손실패턴 분해`
  검증지표: 빈도=26, 중앙손익=-1.745%, 기여손익=-47.910%
- `AI threshold miss EV 회수 조건 점검`
  검증지표: 차단건수=2546880, 차단비율=100.0%
- `overbought gate miss EV 회수 조건 점검`
  검증지표: 차단건수=818347, 차단비율=100.0%

### 3-2. Plan Rebase 연계 관찰

- HOLDING 발생 이후에는 `post_sell_feedback`과 `trade_review`를 함께 묶어 EV 해석을 보강한다.
- `WAIT65~79 -> submitted`가 끊겨 있으면 threshold 완화보다 제출 병목 원인 분리가 우선이다.
- `gatekeeper latency`는 EV 회수 실패 원인인지 성능 병목인지 분해 후 축 우선순위를 정한다.
