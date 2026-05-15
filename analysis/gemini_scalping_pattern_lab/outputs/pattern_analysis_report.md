# Gemini EV Pattern Analysis Report

## 1. EV 관점 핵심 판정

- 목적: EV 성과를 극대화하기 위한 튜닝 포인트를 코호트/패턴/기회비용 기준으로 점검한다.
- 보조 관찰축: Plan Rebase 이후 `WAIT65~79`, `blocked_ai_score`, `gatekeeper latency`, `submitted` 단절을 함께 본다.

## 2. Plan Rebase 관찰축 요약

- `WAIT65~79 total_candidates=19`
- `recovery_check=0`, `promoted=0`, `submitted=0`
- `blocked_ai_score_share=100.0%`, `gatekeeper_eval_ms_p95=5421ms`

## 3. 손실 패턴 (Top 5)

### 1. split-entry / scalp_soft_stop_pct
- 판정: 음수 EV 기여 패턴
- 근거: 발생 26건, 중앙손익 -1.745%, 평균손익 -1.843%, 기여손익 -47.910%
- 다음 액션: 전역 조정이 아니라 해당 코호트/패턴을 분리해 shadow 점검

### 2. full_fill / scalp_soft_stop_pct
- 판정: 음수 EV 기여 패턴
- 근거: 발생 3건, 중앙손익 -1.710%, 평균손익 -1.763%, 기여손익 -5.290%
- 다음 액션: 전역 조정이 아니라 해당 코호트/패턴을 분리해 shadow 점검

### 3. split-entry / protect_trailing_stop
- 판정: 음수 EV 기여 패턴
- 근거: 발생 3건, 중앙손익 -1.170%, 평균손익 -0.813%, 기여손익 -2.440%
- 다음 액션: 전역 조정이 아니라 해당 코호트/패턴을 분리해 shadow 점검

### 4. full_fill / scalp_hard_stop_pct
- 판정: 음수 EV 기여 패턴
- 근거: 발생 1건, 중앙손익 -2.250%, 평균손익 -2.250%, 기여손익 -2.250%
- 다음 액션: 전역 조정이 아니라 해당 코호트/패턴을 분리해 shadow 점검

### 5. full_fill / scalp_preset_hard_stop_pct
- 판정: 음수 EV 기여 패턴
- 근거: 발생 1건, 중앙손익 -1.550%, 평균손익 -1.550%, 기여손익 -1.550%
- 다음 액션: 전역 조정이 아니라 해당 코호트/패턴을 분리해 shadow 점검

## 4. 수익 패턴 (Top 5)

### 1. split-entry / scalp_trailing_take_profit / nan
- 판정: 양수 EV 기여 패턴
- 근거: 발생 23건, 중앙손익 +0.780%, 평균손익 +1.028%, 기여손익 +23.640%
- 다음 액션: 해당 패턴을 훼손하지 않는 범위에서 병목 해소 우선

### 2. split-entry / scalp_ai_momentum_decay / nan
- 판정: 양수 EV 기여 패턴
- 근거: 발생 3건, 중앙손익 +2.470%, 평균손익 +1.950%, 기여손익 +5.850%
- 다음 액션: 해당 패턴을 훼손하지 않는 범위에서 병목 해소 우선

### 3. full_fill / scalp_trailing_take_profit / nan
- 판정: 양수 EV 기여 패턴
- 근거: 발생 3건, 중앙손익 +0.590%, 평균손익 +0.913%, 기여손익 +2.740%
- 다음 액션: 해당 패턴을 훼손하지 않는 범위에서 병목 해소 우선

### 4. split-entry / protect_trailing_stop / nan
- 판정: 양수 EV 기여 패턴
- 근거: 발생 1건, 중앙손익 +0.190%, 평균손익 +0.190%, 기여손익 +0.190%
- 다음 액션: 해당 패턴을 훼손하지 않는 범위에서 병목 해소 우선

## 5. 기회비용 분해

### 1. AI threshold miss
- 판정: EV 회수 우선 후보
- 근거: 차단건수 4064789건, 차단비율 100.0%, 관찰일수 23일
- 다음 액션: blocker 성격을 관찰축과 연결해 원인 귀속

### 2. overbought gate miss
- 판정: EV 회수 우선 후보
- 근거: 차단건수 1327177건, 차단비율 100.0%, 관찰일수 23일
- 다음 액션: blocker 성격을 관찰축과 연결해 원인 귀속

### 3. liquidity gate miss
- 판정: EV 회수 우선 후보
- 근거: 차단건수 75327건, 차단비율 99.6%, 관찰일수 23일
- 다음 액션: blocker 성격을 관찰축과 연결해 원인 귀속

### 4. latency guard miss
- 판정: EV 회수 우선 후보
- 근거: 차단건수 60357건, 차단비율 99.5%, 관찰일수 23일
- 다음 액션: blocker 성격을 관찰축과 연결해 원인 귀속
