# Pattern Analysis Report

## 1. 튜닝 관찰축 요약
- 판정: `buy_recovery_canary`는 BUY 후보 회복 신호는 있으나 제출 경로로 이어지지 않아 단독 승격 근거가 부족하다.
- 근거: `WAIT65~79 total_candidates=246`, `recovery_check=40`, `promoted=6`, `submitted=0`, `blocked_ai_score_share=84.6%`, `gatekeeper_eval_ms_p95=16637ms`
- 다음 액션: `gatekeeper latency` 경로 분해와 `WAIT65~79 -> submitted` 연결 확인을 우선하고, 신규 live 축 추가는 보류한다.

## 2. 손실 패턴 (Top 5)
## 3. 수익 패턴 (Top 5)
