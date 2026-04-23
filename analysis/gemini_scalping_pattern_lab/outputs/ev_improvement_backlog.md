# EV Improvement Backlog

1. [Canary-Keep] buy_recovery_canary 유지 + 제출 병목 확인
   - 판정 근거: promoted=6 대비 submitted=0
   - why: prompt 개선 효과와 주문 회복 효과를 아직 동일시할 수 없다.
   - 다음 액션: WAIT65~79 -> submitted 단절 구간을 로그 기준으로 재확인

2. [Observability] gatekeeper latency 경로 분해 유지
   - 판정 근거: gatekeeper_eval_ms_p95=16637ms, lock_wait_p95=0ms, model_call_p95=0ms
   - why: 지연 원인을 lock/model/packet 중 어디에 귀속할지 분해해야 다음 축 우선순위가 선다.
   - 다음 액션: 내일 장전 스냅샷에서 경로별 p95를 우선 확인

3. [Hold] HOLDING 확대 보류 유지
   - 판정 근거: evaluated_candidates=0
   - why: post-sell 표본이 없어 우선순위 확대 판단 자체가 성립하지 않는다.
   - 다음 액션: 다음 유효 표본 축적 후 재판정
