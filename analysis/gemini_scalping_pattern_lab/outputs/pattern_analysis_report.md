# Gemini EV Pattern Analysis Report

## 1. EV 관점 핵심 판정

- 목적: EV 성과를 극대화하기 위한 튜닝 포인트를 코호트/패턴/기회비용 기준으로 점검한다.
- 보조 관찰축: Plan Rebase 이후 `WAIT65~79`, `blocked_ai_score`, `gatekeeper latency`, `submitted` 단절을 함께 본다.

## 2. Plan Rebase 관찰축 요약

- `WAIT65~79 total_candidates=0`
- `recovery_check=0`, `promoted=0`, `submitted=0`
- `blocked_ai_score_share=0.0%`, `gatekeeper_eval_ms_p95=29336ms`

## 3. 손실 패턴 (Top 5)

### 1. split-entry / scalp_soft_stop_pct
- 판정: 음수 EV 기여 패턴
- 근거: 발생 13건, 중앙손익 -1.550%, 평균손익 -1.625%, 기여손익 -21.120%
- 다음 액션: 전역 조정이 아니라 해당 코호트/패턴을 분리해 shadow 점검

### 2. full_fill / scalp_hard_stop_pct
- 판정: 음수 EV 기여 패턴
- 근거: 발생 1건, 중앙손익 -3.380%, 평균손익 -3.380%, 기여손익 -3.380%
- 다음 액션: 전역 조정이 아니라 해당 코호트/패턴을 분리해 shadow 점검

### 3. split-entry / scalp_ai_early_exit
- 판정: 음수 EV 기여 패턴
- 근거: 발생 3건, 중앙손익 -1.000%, 평균손익 -1.000%, 기여손익 -3.000%
- 다음 액션: 전역 조정이 아니라 해당 코호트/패턴을 분리해 shadow 점검

### 4. split-entry / scalp_preset_hard_stop_pct
- 판정: 음수 EV 기여 패턴
- 근거: 발생 4건, 중앙손익 -0.770%, 평균손익 -0.740%, 기여손익 -2.960%
- 다음 액션: 전역 조정이 아니라 해당 코호트/패턴을 분리해 shadow 점검

### 5. full_fill / scalp_soft_stop_pct
- 판정: 음수 EV 기여 패턴
- 근거: 발생 1건, 중앙손익 -2.040%, 평균손익 -2.040%, 기여손익 -2.040%
- 다음 액션: 전역 조정이 아니라 해당 코호트/패턴을 분리해 shadow 점검

## 4. 수익 패턴 (Top 5)

### 1. split-entry / scalp_trailing_take_profit / nan
- 판정: 양수 EV 기여 패턴
- 근거: 발생 20건, 중앙손익 +0.800%, 평균손익 +1.111%, 기여손익 +22.220%
- 다음 액션: 해당 패턴을 훼손하지 않는 범위에서 병목 해소 우선

### 2. full_fill / scalp_preset_ai_review_exit / nan
- 판정: 양수 EV 기여 패턴
- 근거: 발생 1건, 중앙손익 +1.920%, 평균손익 +1.920%, 기여손익 +1.920%
- 다음 액션: 해당 패턴을 훼손하지 않는 범위에서 병목 해소 우선

### 3. split-entry / scalp_ai_momentum_decay / nan
- 판정: 양수 EV 기여 패턴
- 근거: 발생 3건, 중앙손익 +0.580%, 평균손익 +0.540%, 기여손익 +1.620%
- 다음 액션: 해당 패턴을 훼손하지 않는 범위에서 병목 해소 우선

### 4. full_fill / scalp_trailing_take_profit / nan
- 판정: 양수 EV 기여 패턴
- 근거: 발생 1건, 중앙손익 +1.030%, 평균손익 +1.030%, 기여손익 +1.030%
- 다음 액션: 해당 패턴을 훼손하지 않는 범위에서 병목 해소 우선

### 5. split-entry / scalp_preset_protect_profit / nan
- 판정: 양수 EV 기여 패턴
- 근거: 발생 2건, 중앙손익 +0.250%, 평균손익 +0.250%, 기여손익 +0.500%
- 다음 액션: 해당 패턴을 훼손하지 않는 범위에서 병목 해소 우선

## 5. 기회비용 분해

### 1. AI threshold miss
- 판정: EV 회수 우선 후보
- 근거: 차단건수 983997건, 차단비율 100.0%, 관찰일수 7일
- 다음 액션: blocker 성격을 관찰축과 연결해 원인 귀속

### 2. overbought gate miss
- 판정: EV 회수 우선 후보
- 근거: 차단건수 411938건, 차단비율 100.0%, 관찰일수 7일
- 다음 액션: blocker 성격을 관찰축과 연결해 원인 귀속

### 3. latency guard miss
- 판정: EV 회수 우선 후보
- 근거: 차단건수 18025건, 차단비율 99.2%, 관찰일수 7일
- 다음 액션: blocker 성격을 관찰축과 연결해 원인 귀속

### 4. liquidity gate miss
- 판정: EV 회수 우선 후보
- 근거: 차단건수 12991건, 차단비율 98.9%, 관찰일수 7일
- 다음 액션: blocker 성격을 관찰축과 연결해 원인 귀속
