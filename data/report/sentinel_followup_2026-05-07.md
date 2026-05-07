# Sentinel Follow-up 2026-05-07

## 11:34 KST 중간 판정

- BUY Sentinel: `UPSTREAM_AI_THRESHOLD` primary, `LATENCY_DROUGHT` secondary, report-only 유지.
- HOLD/EXIT Sentinel: `HOLD_DEFER_DANGER` primary, `AI_HOLDING_OPS` secondary, report-only 유지.
- HOLD/EXIT `RUNTIME_OPS`는 false-positive 보정 대상이었다. 기존 `11:25` 산출물은 latest HOLDING event가 `10:54:47`이라 stale로 분류했지만, 포지션 완료 후 무이벤트 구간과 미해결 포지션 stale을 구분하지 못했다.

## BUY 다음 액션 진행

- `wait6579_ev_cohort_2026-05-07` 기준 `total_candidates=182`, `entered_attempts=2`, `missed_attempts=180`, `entered_rate=1.1%`.
- `blocked_ai_score`는 `155건(85.2%)`이고 score bucket은 `65=135건`, `74=19건`, `72=1건`이다.
- `blocked_ai_score` bucket 평균은 score65 `expected_ev=+4.5586%`, `close_10m=+5.3429%`, `mfe_10m=+7.6395%`; score74 `expected_ev=+4.5122%`, `close_10m=+5.2322%`, `mfe_10m=+7.9836%`다.
- `latency_block`은 `4건(2.2%)`, 평균 `expected_ev=-0.8549%`라 11시대 중간값만으로 spread/latency 완화 후보가 아니다.
- `approval_gate.threshold_relaxation_approved=false`다. 이유는 `full_samples=181`이지만 `partial_samples=0`으로 sample gate가 깨진다.

## HOLD/EXIT 다음 액션 진행

- `exit_signal=6`, `sell_order_sent=6`, `sell_completed=6`이라 sell execution drought는 없다.
- `holding_flow_override_defer_exit`는 `67건`이며 주요 표본은 심텍(222800) `record_id=5370`, `scalp_trailing_take_profit`, `44건`, 최대 profit_rate `+2.32%`다.
- 추가 defer 표본은 혜인(003010) `record_id=5306`, `scalp_trailing_take_profit`, `14건`, 최대 profit_rate `+0.97%`; 와이지-원(019210) `record_id=5401`, `scalp_soft_stop_pct`, `7건`이다.
- force/confirm은 `holding_flow_override_force_exit` 심텍 `record_id=5370`, `max_defer_sec`, profit_rate `+2.08%`; confirm은 `RISE ESG사회책임투자`, `코오롱`, `와이지-원`, `혜인`, `RF머트리얼즈`에서 발생했다.
- `AI holding cache MISS=100%`는 계속 `AI_HOLDING_OPS`로 라우팅한다. tail sample도 모두 `ai_cache=miss`, `tier1`, response `997~2193ms` 범위다.

## 코드 보정

- `holding_exit_sentinel`에 `active_holding` unresolved key 계산을 추가했다.
- `sell_completed`로 끝난 포지션은 active/pending으로 보지 않는다.
- `RUNTIME_OPS` stale 판정은 `stale_sec > 900`, `ai_review > 0`, `active_holding > 0`일 때만 적용한다.
- 11:25 재생성에서도 `RUNTIME_OPS`는 사라지고 `HOLD_DEFER_DANGER + AI_HOLDING_OPS`로 분류된다.

## 금지선

- BUY: score threshold 완화, fallback 재개, spread cap 완화, live threshold mutation, bot restart 금지.
- HOLD/EXIT: 자동 매도, holding threshold mutation, holding_flow_override mutation, AI cache TTL mutation, bot restart 금지.
