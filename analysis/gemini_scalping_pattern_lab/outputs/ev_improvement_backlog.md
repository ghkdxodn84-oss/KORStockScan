# EV Improvement Backlog

1. split-entry EV 누수 분리 점검
   - 적용단계: shadow-only
   - 기대효과: split-entry 코호트의 음수 EV 원인을 분리해 전역 조정 오판을 줄인다.
   - 검증지표: split-entry 거래수, 손익 중앙값, 기여손익 합 재확인
   - 필요표본: 30건 이상 또는 연속 2일 동일 패턴

2. split-entry / scalp_soft_stop_pct 손실패턴 분해
   - 적용단계: shadow-only
   - 기대효과: 가장 큰 음수 기여 패턴을 별도 축으로 분리해 EV 누수 원인을 좁힌다.
   - 검증지표: 빈도=13, 중앙손익=-1.550%, 기여손익=-21.120%
   - 필요표본: 동일 패턴 10건 이상

3. AI threshold miss EV 회수 조건 점검
   - 적용단계: canary-ready
   - 기대효과: AI threshold miss 구간에서 놓친 기대값 회수 가능성을 검증한다.
   - 검증지표: 차단건수=983997, 차단비율=100.0%
   - 필요표본: 장중/장후 snapshot 동시 확인

4. overbought gate miss EV 회수 조건 점검
   - 적용단계: observability
   - 기대효과: overbought gate miss 구간에서 놓친 기대값 회수 가능성을 검증한다.
   - 검증지표: 차단건수=411938, 차단비율=100.0%
   - 필요표본: 장중/장후 snapshot 동시 확인

5. WAIT65~79 -> submitted 단절 원인 점검
   - 적용단계: observability
   - 기대효과: EV가 남아 있는 recovery 후보가 실제 제출로 이어지지 않는 병목을 분리한다.
   - 검증지표: promoted=0, submitted=0
   - 필요표본: HOLDING 발생 이후 재관찰

6. gatekeeper latency 경로 분해(lock/model/quote_fresh)
   - 적용단계: observability
   - 기대효과: latency가 EV 회수 병목인지 성능 문제인지 구간별로 분해한다.
   - 검증지표: gatekeeper_eval_ms_p95=29336ms, quote_fresh_latency_blocks=5354
   - 필요표본: 장전/장후 snapshot 누적
