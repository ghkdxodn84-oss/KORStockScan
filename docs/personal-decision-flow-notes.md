# 판정항목별 개선 흐름 정리

주의: 이 문서는 개인 정리용이며 다른 문서에서 참조하지 않는다. 개인문서는 다른 문서를 참조할 수 있다.

## 현재 기준 스냅샷

| 항목 | 현재 기준 |
| --- | --- |
| 기준일 | `2026-04-29 KST` 장후 반영 기준 |
| entry live owner | `mechanical_momentum_latency_relief`. `latency_quote_fresh_composite`는 `2026-04-29 08:29 KST` OFF + restart 완료, `latency_signal_quality_quote_composite`는 `2026-04-29 12:50 KST` 효과 미약으로 OFF |
| submitted 상태 | 운영상 급한 drought는 완화됐다. `12:57 restart -> 14:00` 고유 기준 `budget_pass=38`, `submitted=20`, `filled=7`; `13:15 hotfix -> 14:00` 기준 `budget_pass=32`, `submitted=17`, `filled=7`이다. 단, baseline-lock 전까지는 관찰 대상이다. |
| entry 수량축 | 스캘핑 신규 BUY는 임시 `2주 cap` 유지. `3주 cap`은 기술적으로 가능하지만 `mechanical_momentum_latency_relief`와 같은 entry 단계 live 변경이므로, `2026-04-30` 장후 승인조건 판정 전에는 적용하지 않는다. |
| 보유/청산 live owner | `soft_stop_micro_grace` active. 1순위 관찰축은 `soft_stop_rebound_split`, 2순위 후보는 `trailing_continuation_micro_canary`다. |
| soft stop 해석 | 4월 soft stop post-sell 61건 중 10분 내 매도가 재상회 57건, +0.5% 이상 반등 43건, +1.0% 이상 반등 23건, 매수가 회복 16건이다. 즉 휩쏘 가능성은 높지만 무조건 더 오래 버티는 결론은 아니다. |
| 2026-04-29 soft stop 표본 | `올릭스`는 `GOOD_EXIT`, `덕산하이메탈`은 `NEUTRAL`, `지앤비에스 에코`는 `MISSED_UPSIDE + 고가 재진입 체결 + 익절 완료`, `코오롱`은 `GOOD_EXIT`지만 고가 재진입 제출 흔적이 있다. |
| runtime truth 이슈 | `SK이노베이션(096770)`은 BUY/SELL 모두 WS 실제체결이 들어왔으나 `EXEC_IGNORED`가 발생했고, 정기 계좌동기화가 HOLDING/COMPLETED를 복구했다. 수동 HTS 매도 기준 실손익은 비용 반영 약 `+4.2%`다. 핵심 후속은 order-binding 품질이다. |
| 휴장 보정 | `2026-05-01`은 근로자의 날 KRX 휴장, 다음 운영일은 `2026-05-04`. `2026-05-05`는 어린이날 휴장, 이월 작업은 `2026-05-06` checklist가 소유한다. |

## 감시종목 -> 보유/청산 완료 흐름

### 단계 요약표

| 단계 | 관문 | 통과 의미 | 대표 차단/결과 |
| --- | --- | --- | --- |
| 1 | 감시종목 유입 | 조건검색/스캐너로 WATCHING 대상에 들어옴 | 감시망 미유입 |
| 2 | 선행 차단 통과 | 과열, 유동성, AI 점수, 스윙 갭 차단을 넘김 | `blocked_overbought`, `blocked_liquidity`, `blocked_ai_score`, `blocked_swing_gap` |
| 3 | 진입 후보 자격 충족 | `(score >= buy_threshold or is_shooting) and vpw_condition` 충족 | score/vpw 미달 |
| 4 | gatekeeper 진입 | WATCHING 최종 진입 검증 구간에 도달. 먼저 `fast_reuse` 재사용 가능성(`window`, `signature`)을 확인 | `gatekeeper_fast_reuse_bypass` 후 실평가 또는 `gatekeeper_fast_reuse` |
| 5 | gatekeeper 통과 | AI가 `allow_entry=true`, `action_label=즉시 매수`로 판단 | `blocked_gatekeeper_reject`, `blocked_gatekeeper_error`, `blocked_gatekeeper_missing` |
| 6 | BUY 신호 | 텔레그램/런타임 기준 BUY 신호로 해석 가능한 상태. 주문 직전 후보 | 이후 `entry_armed`, 예산/수량, `submitted_orders`는 다음 단계 |
| 7 | 주문 자격 확보 | `entry_armed`, `budget_pass`까지 도달해 실제 주문 제출을 재시도할 수 있는 상태 | `latency_block`, `entry_armed_expired`, `entry_armed_expired_after_wait` |
| 8 | 주문 제출/체결 | `submitted` 이후 `full/partial` 체결로 넘어가는 상태 | `submitted` 미도달, `partial fill`, `full fill` |
| 9 | HOLDING 시작 | 체결 수량 기준 보유 상태로 진입, 보호주문/상태동기화 시작 | `holding_started`, `preset_exit_setup`, `preset_exit_sync_*` |
| 10 | HOLDING AI 리뷰 루프 | 가격/시간 변화에 따라 보유 AI 재평가 또는 스킵 수행 | `ai_holding_review`, `ai_holding_skip_unchanged`, `ai_holding_reuse_bypass` |
| 11 | 보유 중 분기 판단 | 추가매수 후보 또는 청산 신호로 분기 | `reversal_add_candidate`, `scale_in_executed`, `exit_signal` |
| 12 | 매도 주문/복구 | 청산 주문 전송 성공 또는 실패 후 HOLDING 복구 재시도 | `sell_order_sent`, `sell_order_failed` |
| 13 | 청산 완료 | 매도 체결 완료 후 포지션 종료 | `sell_completed`, `completed` |

### 플로우차트

```text
[감시종목 유입]
    |
    v
[선행 차단 통과]
    |- 실패 -> blocked_overbought
    |- 실패 -> blocked_liquidity
    |- 실패 -> blocked_ai_score
    |- 실패 -> blocked_swing_gap
    v
[(score >= buy_threshold or is_shooting) and vpw_condition]
    |- 실패 -> BUY 후보 미형성
    v
[gatekeeper 진입]
    |- 직전 판단이 재사용 window 안이고 signature도 동일 -> gatekeeper_fast_reuse
    |- 재사용 window 만료(age_expired) -> gatekeeper_fast_reuse_bypass -> 실 gatekeeper 평가
    |- 재사용 window 안이지만 signature 변경(sig_changed) -> gatekeeper_fast_reuse_bypass -> 실 gatekeeper 평가
    v
[gatekeeper 통과 여부]
    |- 실패 -> blocked_gatekeeper_reject / blocked_gatekeeper_error / blocked_gatekeeper_missing
    v
[BUY 신호]
    |- AI WAIT/보류 + Score 50 fallback -> mechanical fallback
    |
    v
[entry_armed]
    |- 예산 통과 -> budget_pass
    |- TTL 만료 -> entry_armed_expired / entry_armed_expired_after_wait
    v
[제출 전 검증]
    |- 실패 -> latency_block
    |- 재시도 성공 -> submitted
    v
[주문 제출]
    |- 일부 체결 -> partial fill
    |- 전량 체결 -> full fill
    v
[HOLDING 시작]
    |- holding_started / preset_exit_setup
    v
[HOLDING AI 리뷰 루프]
    |- 변화 미미 -> ai_holding_skip_unchanged
    |- 변화 감지 -> ai_holding_review
    v
[보유 중 의사결정]
    |- 추가매수 후보 -> reversal_add_candidate -> scale_in_executed -> HOLDING AI 리뷰 루프
    |- 청산 신호 -> exit_signal
    |               (scalp_soft_stop_pct / scalp_hard_stop_pct / scalp_trailing_take_profit / scalp_ai_momentum_decay)
    v
[매도 주문]
    |- 성공 -> sell_order_sent -> sell_completed -> completed
    |- 실패 -> sell_order_failed -> HOLDING 복구 후 재시도
```

### 해석 메모

- 텔레그램 BUY 신호는 대체로 `gatekeeper 통과`까지는 온 상태로 본다.
- 다만 `BUY 신호 = 주문접수 완료`는 아니다. `entry_armed`, 예산/수량, 주문 제출, 체결은 다음 단계다.
- `AI 판단 보류(Score 50)`는 항상 종료 상태가 아니다. 실제 주문 흐름에서는 `mechanical fallback -> entry_armed -> budget_pass`로 이어질 수 있다.
- `entry_armed`에 들어간 뒤에는 `latency_block`, `quote_stale`, `ws_age/ws_jitter` 같은 제출 전 병목 때문에 곧바로 `submitted`로 가지 못할 수 있다.
- 오늘 `2026-04-23 KST` 덕산하이메탈(`077360`)은 `Score 50 fallback -> entry_armed -> budget_pass -> latency_block 반복 -> 주문접수/체결` 사례로, 플로우차트의 주문 전 구간 예시로 본다.
- `gatekeeper_fast_reuse`는 같은 종목의 직전 gatekeeper 판단을 매우 짧은 시간창에서 재사용한 경우다. fast signature, 재사용 가능 시간, websocket freshness, score 경계값, 직전 action/allow_entry 기록이 모두 맞아야 성립한다.
- `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`는 현재 기준으로 재개 후보가 아니다. live 주문 경로와 runtime guard는 제거됐고, 남아 있는 fallback 표기는 과거 로그/리포트 해석용 historical trace로만 읽는다.
- 여기서 `window`는 “직전 판단이 아직 재사용해도 될 만큼 최근인가”를 보는 시간 조건이고, `signature`는 “지금 장면이 직전 판단과 사실상 같은가”를 보는 상태 조건이다.
- 즉 `window`가 만료되면 `age_expired` 쪽으로 재사용이 깨지고, `window` 안이어도 가격/스프레드/점수/수급 같은 핵심 입력이 달라지면 `sig_changed`로 재사용이 깨진다.
- 의미는 `새 AI gatekeeper 호출을 생략하고 직전 판단을 그대로 재사용했다`는 것이다. 따라서 `gatekeeper_fast_reuse`가 찍히면 gatekeeper 구간에는 도달한 것이 맞지만, 새로운 모델 평가가 매번 다시 돈 것은 아니다.
- 왜 중요하나: BUY 회복이 안 보일 때 `gatekeeper_fast_reuse` 비중이 높으면 실제 병목이 모델 호출 지연이 아니라 `같은 장면 재사용`, `score boundary`, `ws freshness`, `signature 변화` 쪽일 수 있다.
- HOLDING 단계에서는 `is_sell_signal`이 생기기 전까지 `ai_holding_review`와 `scale_in` 후보평가가 반복된다. 즉 제출축이 살아나면 다음 병목은 보유 중 `soft stop/trailing/ai exit` 품질로 넘어간다.
- 이후 보완도 `append`가 아니라 기존 판정 섹션을 최신 스냅샷 기준으로 갱신하는 방식으로 유지한다.

### 보유/청산 보조 관찰 메모

| 항목 | 내용 |
| --- | --- |
| soft_stop 휩쏘 가설 | 소프트손절 후 `1m/3m/5m/10m/20m` 반등을 `rebound_above_sell`, `rebound_above_buy`, `mfe_ge_0_5`, `mfe_ge_1_0`로 분리한다. 매도가만 재상회하면 micro grace/확인유예 후보이고, 매수가까지 회복하면 cooldown live가 아니라 threshold/AI 재판정 후보로 본다. |
| 하드스탑 위치 | `scalp_preset_hard_stop_pct`, `scalp_hard_stop_pct`, `protect_hard_stop`은 soft_stop보다 완화 우선순위를 낮춘다. 하드스탑은 극단 손실 방어선이므로 반등 사례가 있어도 `hard_stop_whipsaw_aux` 보조 관찰로만 두고, 바로 완화 canary로 올리지 않는다. |
| 하방카운트 위치 | `ai_low_score_hits`/`scalp_ai_early_exit`는 2026-04-27 기준 live 경로에서 제거했다. 기존 하방카운트는 가격 휩쏘 필터가 아니라 후행 AI 조기손절이라 soft_stop 보호장치로서 실효성이 낮았다. |
| 4월 로그 해석 | 4월 하방카운트 `0/3` 또는 `0/4` 편중과 `3/3` 희소성은 제거 판단 근거로만 보존한다. 현재 soft_stop 해석은 `rebound_above_sell/buy`, `mfe_ge_*`, `same_symbol_reentry`, `hard_stop_auxiliary` 중심으로 고정한다. |

## ID 명명 규칙

| 항목 | 규칙 |
| --- | --- |
| 기본 형식 | `DF-영역-번호` |
| 접두어 `DF` | `Decision Flow`의 약자다. 이 문서의 모든 판정 흐름 항목에 공통으로 붙인다. |
| `영역` | 판정이 속한 개선 영역을 적는다. 예: `ENTRY`, `HOLDING`, `EXIT`, `DATA`, `OPS` |
| `번호` | 같은 영역 안에서 `001`부터 순차 증가시킨다. 번호는 의미를 담기보다 순서를 고정하는 용도다. |
| 작성 원칙 1 | 한 ID는 하나의 판정항목만 가진다. 여러 액션을 묶어 하나의 ID로 합치지 않는다. |
| 작성 원칙 2 | 이미 결정이 끝난 항목도 ID를 유지하고, `결정 결과`와 `후속 액션`으로 다음 항목과 연결한다. |
| 작성 원칙 3 | 후속 액션이 새 판정항목으로 분리되면 새 ID를 발급하고, 선행 항목 표 안에 후속 ID를 명시한다. |
| 예시 | `DF-ENTRY-001`, `DF-ENTRY-002`, `DF-HOLDING-001`, `DF-DATA-001` |

## 진입 병목 판정 흐름

### DF-ENTRY-001 `blocked_ai_score_share` 개선 검토

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-001` |
| 판정항목 | `blocked_ai_score_share` 개선 검토 |
| 문제 인식 | Gemini가 BUY 대신 WAIT/DROP으로 과도하게 막는 비중이 높으면, 실제로는 진입 가치가 있는 후보도 초기에 탈락해 `미진입 기회비용`이 커진다. |
| 해석 방향 | 단순 손실 억제보다 `기대값/순이익 극대화` 기준으로 본다. 즉, 잘못된 진입을 조금 더 줄이는 것보다 “들어가야 할 종목을 너무 많이 놓치고 있지 않은가”를 먼저 본다. |
| 확인하려는 지표 의미 | `blocked_ai_score_share`는 AI가 BUY로 보내지 않고 점수 단계에서 막아버린 비중이다. 이 값이 높고 BUY/제출 표본이 같이 마르면 AI 해석이 과보수적일 가능성이 높다. |
| 기대효과 | `blocked_ai_score_share`가 내려가면 `WAIT/DROP 과밀`이 완화되고, `ai_confirmed -> submitted`로 이어질 수 있는 후보 풀이 늘어난다. 결국 목표는 BUY 남발이 아니라 “막히지 말아야 할 후보의 복구”다. |
| 주의점 | 이 지표만 보고 threshold를 바로 풀면 원인귀속이 흐려질 수 있다. 제출 병목, latency, budget blocker와 분리해서 봐야 한다. |
| 결정 결과 | 독립 개선축으로는 채택하지 않았다. `blocked_ai_score_share` 자체는 핵심 관찰지표로 유지하되, 이 지표만을 직접 완화 목표로 삼는 별도 액션은 폐기했다. |
| 폐기 사유 | 장중 판정 시점에 필요한 것은 지표 자체의 개선 선언이 아니라 `WAIT65~79 -> BUY 회복`을 실제로 만드는 구체 액션이었다. 독립 `blocked_ai_score_share` 개선축은 실행 단위가 모호하고, `score`, `prompt`, `latency`, `budget` 중 무엇을 건드리는지 흐릴 수 있다. |
| 후속 액션 | `DF-ENTRY-002 buy_recovery_canary prompt 재교정`으로 연결한다. 즉, 관찰지표는 유지하되 실행은 recovery prompt 1축으로 옮긴다. |

### DF-ENTRY-002 `buy_recovery_canary prompt` 재교정

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-002` |
| 판정항목 | `buy_recovery_canary prompt` 재교정 |
| 적용 배경 | 12시 기준 `recovery_check=21`인데 `promoted=0`, `submitted=0`이었다. 회복 재평가를 걸었는데도 BUY 복구가 전혀 안 나와, 점수 숫자보다 `recovery prompt` 해석 문맥이 더 보수적일 가능성이 높다고 봤다. |
| 작업 방향성 | `WAIT 65~79` 구간을 단순 보류대가 아니라 “조건이 살아나면 BUY로 복구될 수 있는 회복 구간”으로 읽게 만든다. 재돌파, 매도벽 흡수, 거래 재가속, 고점 재안착 같은 회복 신호를 더 적극적으로 해석하게 하는 쪽이다. |
| 무엇을 안 건드렸는가 | 전역적인 `score/promote` 완화는 하지 않았다. `AI_MAIN_BUY_RECOVERY_CANARY_PROMOTE_SCORE` 값은 유지했고, `scalping_buy_recovery_canary` 전용 프롬프트만 바꿨다. |
| 기대효과 1 | `promoted=0` 상태를 깨서 `WAIT65~79 -> BUY 회복` 표본을 만든다. |
| 기대효과 2 | 회복된 BUY가 실제 `submitted`까지 이어지는지 확인해, 병목이 프롬프트인지 아니면 latency/budget인지 더 분명히 분리한다. |
| 기대효과 3 | 단순 BUY 수 증가가 아니라 `미진입 기회비용`을 줄이면서도 `main-only`, `1축 canary`, 원인귀속 보존 원칙을 유지한다. |
| 결정 결과 | 채택. `score/promote`가 아니라 `buy_recovery_canary prompt` 재교정 1축을 적용했다. |
| 선정 이유 | `recovery_check=21`, `promoted=0`, `submitted=0` 조합은 score 임계치 전역 완화보다 recovery 전용 해석 문맥 보정이 더 직접적인 수단이라고 판단했다. |
| 장후 재판정 요약 | 오후 스냅샷 기준 `total_candidates=246`, `recovery_check=40`, `promoted=6`, `submitted=0`, `blocked_ai_score=208건(84.6%)`, `gatekeeper_eval_ms_p95=16637ms`, `gatekeeper_decisions=37`, `full_fill=0`, `partial_fill=0`, `completed_trades=0`이다. |
| 현재 해석 1 | `promoted=0 -> 6`으로 바뀐 것은 분명히 좋은 신호다. 즉, 프롬프트 재교정이 `WAIT65~79` 구간을 전부 묶어두던 상태는 일부 풀었다. |
| 현재 해석 2 | 하지만 `submitted=0`, `completed_trades=0`이라 아직 `BUY 회복 성공`으로 부를 수는 없다. 회복 BUY 후보가 생긴 것과 실제 주문/체결 회복은 아직 분리되어 있다. |
| 현재 해석 3 | `blocked_ai_score=208건(84.6%)`가 여전히 절대다수라서, BUY 신호 자체가 충분히 살아났다고 보기도 어렵다. 현재는 `0 -> 소폭 회복`에 가깝고, 여전히 AI threshold 병목이 크다. |
| 현재 해석 4 | 동시에 제출 병목도 남아 있다. `budget_pass_candidates=10`, `latency_block_candidates=10`, `submitted_candidates=0`이라 `BUY 후보 생성` 다음 단계에서 또 막힌다. 즉 병목은 `BUY 부족`과 `BUY -> submitted 단절`이 함께 존재한다. |
| 장중 후속 판정 업데이트 | `2026-04-23 11:03 KST` snapshot 기준 `candidates=124`, `ai_confirmed=66`, `entry_armed=36`, `submitted=1`, `budget_pass_events=1893`, `order_bundle_submitted_events=2`, `latency_block_events=1891`, `quote_fresh_latency_blocks=1693`, `gatekeeper_eval_ms_p95=16869ms`다. `wait6579`도 `recovery_check=20`, `promoted=13`, `budget_pass=15`, `latency_block=15`, `submitted=0`이라 오전 방향성은 `BUY 부족`이 아니라 `BUY는 충분하나 entry_armed 이후 병목`으로 바뀌었다. |
| 현재 해석 5 | 따라서 `DF-ENTRY-002`는 이제 “BUY 후보를 못 만든다” 문제를 보는 축이 아니라, upstream 표본 생성은 유효했고 다음 live 주연은 downstream 제출축으로 넘어갔다는 기준점 역할을 한다. `buy_recovery_canary`는 종료가 아니라 유지/고정이다. |
| 현재 해석 6 | `blocked_ai_score_share`와 `score/promote` 해석은 보조가설로 남지만, 당장 다음 canary 우선순위는 아니다. 다시 말해 `DF-ENTRY-002`의 성공 기준은 `BUY 부족 해소 여부`까지이고, `submitted/full/partial` 회복은 후속 제출축에서 본다. |
| 가드 해석 | `latency_p95=16637ms`는 임계치(`15900ms`)를 넘지만 `gatekeeper_decisions=37`이라 가드 발동 조건인 `sample >= 50`을 아직 못 채웠다. 따라서 hard OFF 근거는 아니고 방향성 경고로만 본다. |
| 오늘 결론 | `현 축 유지 + upstream 고정`이 맞다. 지금 OFF하면 BUY drought 완화 입력이 사라지고, 지금 다른 upstream 축으로 넘어가면 `prompt 개선`, `AI threshold`, `제출 병목`의 원인귀속이 다시 흐려진다. |
| 실패 시 해석 | 이후 관측에서 `ai_confirmed/entry_armed`가 다시 줄거나 `blocked_ai_score_share`가 재악화되면 upstream 문제 재개로 본다. 반대로 `promoted/entry_armed`가 유지되는데 `submitted`만 낮으면 핵심 병목은 계속 제출 경로(latency/quote)다. |
| 다음 확인 포인트 | `ai_confirmed`, `entry_armed`, `promoted`, `submitted`, `submission_blocker_breakdown`, `quote_fresh_latency_blocks`, `full/partial`, `COMPLETED + valid profit_rate`, `latency_p95`를 같은 기준으로 다시 본다. |

### DF-ENTRY-003 `entry_armed -> submitted` latency/quote 제출축 분해

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-003` |
| 판정항목 | `entry_armed -> submitted` 구간의 `latency/quote freshness` 병목을 다음 공식 live/판정축으로 올릴지 여부 |
| 문제 인식 | 현재는 BUY 후보가 부족해서가 아니라, `entry_armed`와 `budget_pass`를 거친 뒤에도 대부분이 `submitted`로 가지 못한다. 같은 날 `budget_pass_events=1893`, `order_bundle_submitted_events=2`, `latency_block_events=1891`, `quote_fresh_latency_blocks=1693`이면 병목의 중심은 제출 직전이다. |
| 왜 다음 축인가 | upstream인 `DF-ENTRY-002`가 `recovery_check/promoted/entry_armed` 표본을 이미 만들고 있기 때문이다. 이제 기대값을 더 올리려면 `BUY를 더 만들까`보다 `만들어진 후보가 왜 주문 직전에서 잘리는가`를 먼저 분해해야 한다. |
| 분해 대상 1 | `quote_fresh latency block` 자체의 비중이 높은지 확인한다. 즉 stale quote가 아닌데도 내부 지연/guard 조건 때문에 잘리는 표본을 따로 본다. |
| 분해 대상 2 | `gatekeeper_eval_ms_p95`, `gatekeeper_lock_wait_ms`, `gatekeeper_model_call_ms`, `gatekeeper_total_internal_ms`, `gatekeeper_fast_reuse_ratio`, `gatekeeper_ai_cache_hit_ratio`를 함께 봐서 병목이 모델응답인지, lock 직렬화인지, cache miss인지 분리한다. |
| 분해 대상 3 | `ws_age`, `ws_jitter`, `spread_ratio`, `quote_stale`가 어떤 조합에서 `latency_block`을 만드는지 구간화한다. 핵심은 `fresh quote인데도 막힌 표본`과 `실제 stale quote 차단`을 섞지 않는 것이다. |
| 현재 제약 | 기존 `SCALP_LATENCY_GUARD_CANARY_ENABLED`는 더 이상 fallback 주문으로 이어지지 않고 `latency_fallback_deprecated` reject trace만 남긴다. 따라서 남은 제약은 fallback 재개가 아니라 `1축 canary` 교체 순서, 복합축 묶음 판정, same-day live 검증이다. |
| 정의 가능 시점 | 장후가 되어서가 아니라, 아래 사전조건 3개가 채워지는 시점부터 정의 가능하다. 현재는 1, 2번은 충족됐고, 3번도 `spread relief canary` 구현으로 코드 레벨에선 충족됐다. 남은 것은 live ON/OFF와 장중 검증 기록이다. |
| 사전조건 1 | 문제 구간이 `BUY 부족`이 아니라 `entry_armed/budget_pass 이후 submitted 단절`로 잠겨 있어야 한다. 오늘은 `candidates=124`, `ai_confirmed=66`, `entry_armed=36`, `submitted=1`, `budget_pass_events=1893`, `latency_block_events=1891`이라 이 조건은 충족으로 본다. |
| 사전조건 2 | 분해용 관측값이 live 로그/스냅샷에 존재해야 한다. 즉 `quote_fresh_latency_blocks`, `gatekeeper lock_wait/model_call/total_internal`, `ws_age/ws_jitter/spread/quote_stale` 중 최소 핵심 필드가 이미 기록돼 있어야 한다. 오늘은 PREOPEN/INTRADAY에서 이 계측 경로가 확인돼 있어 충족으로 본다. |
| 사전조건 3 | 실전에서 ON/OFF 가능한 조작점이 `fallback`과 분리된 단일 행동으로 정의돼야 한다. 예를 들면 `reason allowlist만 조정`, `quote_stale=False cohort만 별도 처리`, `ws_jitter 한도만 조정`처럼 효과와 리스크를 한 문장으로 설명할 수 있어야 한다. 현재는 이 조작점이 아직 문서/코드로 고정되지 않아 미충족이다. |
| 정의 기준 1 | 축 설명이 `무엇을 완화/조정하는가` 한 문장으로 닫혀야 한다. `latency를 개선한다`처럼 넓은 표현은 불가하고, `fresh quote + ws_jitter 상한 재조정`처럼 단일 행동이어야 한다. |
| 정의 기준 2 | 기대효과가 `budget_pass_to_submitted_rate` 또는 `quote_fresh_latency_pass_rate` 개선처럼 제출축 지표로 직접 연결돼야 한다. `BUY 수 증가` 같은 upstream 효과를 주 KPI로 삼으면 안 된다. |
| 정의 기준 3 | rollback guard가 최소 3개는 같이 붙어야 한다. 기본형은 `loss_cap`, `submitted/full/partial 품질 악화`, `fallback_regression=0 유지`다. 필요하면 `latency_p95` 또는 `reject_rate`를 추가한다. |
| 정의 기준 4 | 금지 조건이 명시돼야 한다. `fallback_scout/main`, `fallback_single`, `ALLOW_FALLBACK` 재유입, 전역 threshold 하향, 다축 동시 변경은 정의 단계에서 제외한다. |
| 지금 바로 할 수 있는 일 | blocker 분해뿐 아니라 `spread-only + quote fresh` 케이스 전용 `fallback 비결합 canary`를 코드에 넣고, 테스트까지 통과시킨 뒤 남은 장에서 live 검증할 수 있다. |
| 지금 바로 못 하는 일 | 다축 동시 ON 상태에서 downstream 효과를 검증할 수는 없다. same-day live는 `기존 축 OFF -> restart.flag -> 새 축 ON` 교체 규칙을 지켜야 하고, fallback 관련 플래그는 재사용하면 안 된다. |
| 결정 결과 | 다음 공식 판정축으로 등록했고, 장중에 `fallback 비결합 spread relief canary` 구현까지 완료했다. 남은 단계도 `장중 정량 checkpoint -> same-day 유지/확대/롤백` 판정이어야 하며, `POSTCLOSE에서 첫 제출/체결 품질만 보고 닫는 방식`은 허용하지 않는다. |
| 장중 1차 분해 결과 | `2026-04-23 11:21:13 KST` snapshot 기준 `budget_pass_events=2091`, `order_bundle_submitted_events=2`, `latency_block_events=2089`, `quote_fresh_latency_blocks=1882`, `quote_fresh_latency_pass_rate=0.1%`다. raw log 228건 집계에서는 `quote_stale=False 203건`, `quote_stale=True 25건`으로 fresh quote 차단이 우세했고, danger reason overlap은 `spread_too_wide 177`, `ws_age_too_high 42`, `ws_jitter_too_high 36`, `quote_stale 25`, `other_danger 22`였다. |
| gatekeeper 해석 보정 | gatekeeper reject 실표본은 오늘 `2건`뿐이며 `gatekeeper_lock_wait_ms=0`, `gatekeeper_model_call_ms≈total_internal_ms`, `gatekeeper_cache=miss`였다. 즉 느린 것은 맞지만, 현재 `entry_armed -> submitted` 대량 단절의 1차 설명력은 `fresh quote spread 지배`보다 약하다. |
| 단일 조작점 후보 1 | 첫 `fallback 비결합 downstream 1축` 후보는 `quote_stale=False + spread_too_wide 지배 구간 분리`다. 핵심은 전역 latency 완화가 아니라 fresh quote spread 구간을 별도 cohort로 떼어 `budget_pass_to_submitted_rate` 개선 가능성을 보는 것이다. |
| 장중 구현 반영 | [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py)에 `_should_apply_latency_spread_relief_canary()`를 추가해 `REJECT_DANGER -> ALLOW_NORMAL` 직접 override 경로를 넣었다. 설정축은 [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py)의 `SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED`, `..._TAGS`, `..._MIN_SIGNAL_SCORE`, `..._MAX_SPREAD_RATIO`다. 혼합 danger(`ws_age/ws_jitter/quote_stale` 동반)는 계속 차단한다. |
| 테스트 상태 | [test_sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_entry_latency.py) 기준 `spread-only danger -> ALLOW_NORMAL`, `mixed danger -> 차단 유지`를 포함해 `10 passed`다. |
| 후속 액션 | 남은 장에서는 기존 live 축을 끈 뒤 `spread relief canary`만 켜서 `budget_pass_to_submitted_rate`, `quote_fresh_latency_pass_rate`, `submitted/full/partial fill quality`, `fallback_regression=0`를 본다. 장후 checklist의 `LatencyOps0423 gatekeeper latency 경로 분해(lock/cache/quote_fresh)`는 새 구현의 live 결과까지 포함해 `유지/확대/롤백`을 닫는 단계로 쓴다. |

### DF-ENTRY-004 `spread relief canary` 오전 판정 결과

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-004` |
| 판정항목 | `2026-04-24 09:00~10:30 KST` `spread relief canary` 실효성 판정 |
| 검증축 이름 | `spread relief canary` 오전 판정 |
| 왜 이 축인가 | `DF-ENTRY-002`가 upstream 표본 생성은 이미 확보했기 때문에, 오늘 오전의 핵심은 `BUY를 더 만들까`가 아니라 `entry_armed -> submitted` 제출축에서 `spread relief canary`가 실제 blocker를 줄였는지 확인하는 것이었다. |
| 검증 목적 | `spread-only + quote fresh` 완화가 `budget_pass_to_submitted_rate`, `quote_fresh_latency_pass_rate`, `submitted/full/partial fill quality`를 개선하는지 same-day로 닫는다. |
| 검증 대상 지표 | `ai_confirmed`, `entry_armed`, `budget_pass`, `submitted`, `latency_block`, `latency_state_danger`, `latency_danger_reasons`, `latency_canary_reason`, `quote_fresh_latency_blocks`, `quote_fresh_latency_pass_rate`, `full_fill`, `partial_fill` |
| 보조 진단 지표 | `gatekeeper_fast_reuse`, `gatekeeper_eval_ms_p95`는 AI 평가 지연/재사용 경로 진단용으로만 본다. `budget_pass -> latency_block -> submitted` 직접 blocker보다 우선하는 live 축으로 올리지 않는다. |
| 10:00 KST 판정 | `09:00~10:00` 누적 `ai_confirmed=77`, `entry_armed=31`, `submitted=4`, `budget_pass_events=863`, `latency_block_events=859`, `quote_fresh_latency_blocks=777`, `quote_fresh_latency_pass_rate=0.5%`, `full_fill=0`, `partial_fill=0`, `gatekeeper_eval_ms_p95=12543.0ms`였다. 따라서 원인 축은 `upstream BUY 부족`이 아니라 `budget_pass -> latency_block/submitted` downstream 단절로 고정했다. |
| 10:30 KST 재판정 | `09:00~10:30` 누적 `ai_confirmed=91`, `entry_armed=39`, `submitted=8`, `budget_pass_events=1220`, `latency_block_events=1212`, `quote_fresh_latency_blocks=1092`, `quote_fresh_latency_pass_rate=0.7%`, `full_fill=0`, `partial_fill=0`, `gatekeeper_eval_ms_p95=12485.0ms`였다. `10:20~10:30` 증분에서도 `spread_only_required=82`가 차단사유 대부분이었다. |
| 오늘 판정 | `spread relief canary`는 원인 위치를 downstream으로 잠그는 데는 성공했지만, 실효성 승인에는 실패했다. 즉 `제출축 병목 위치 확인`은 됐고, `실제 제출 회복 효과`는 오전 표본에서 입증하지 못했다. |
| why 1 | `submitted_orders=8`로 Plan Rebase §6 `N_min` 최소치 `20`에 `+12`가 부족하다. 따라서 hard pass/fail을 줄 표본은 없다. |
| why 2 | 표본 미달과 별개로 `budget_pass_events=1220` 대비 `submitted=8`, `latency_block_events=1212`, `quote_fresh_latency_blocks=1092`라서 downstream 차단이 지배적이라는 방향성은 충분히 강하다. |
| why 3 | `gatekeeper_eval_ms_p95`는 `12.5s` 수준으로 높지만 rollback guard(`>15,900ms`, sample>=50)까지는 아니다. 따라서 immediate rollback 사유도 아니다. |
| 금지 유지 | 이 결과만으로 `entry_filter_quality`, `score/promote`, `HOLDING`, `EOD/NXT`를 같은 오전 창의 주병목 축으로 올리면 안 된다. 원인귀속이 다시 upstream으로 흔들리기 때문이다. |
| 후속 연결 | same-day 보조축은 `quote_fresh` downstream 1축으로 고정했고, `entry_filter_quality`는 parking 유지로 남겼다. 이후 `spread/ws_jitter/other_danger residual`을 차례로 봤지만, direct 제출 회복은 만들지 못했다. 따라서 다음 연결은 `gatekeeper_fast_reuse`가 아니라 `latency_state_danger` 하위원인 재분해로 넘어간다. |

### DF-ENTRY-005 `latency_state_danger` 직접 병목 pivot

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-005` |
| 판정항목 | `budget_pass -> latency_block -> submitted` 단절의 직접 blocker를 `latency_state_danger` 하위 이유로 재고정하고, live 축을 `other_danger relief`로 넘길지 결정 |
| 매몰 지점 | `quote_fresh family`가 효과 미약으로 잠긴 뒤 `gatekeeper_fast_reuse`를 다음 독립축 후보로 올린 것이 흐름을 옆길로 틀었다. `gatekeeper_eval_ms_p95`와 `fast_reuse_ratio=0.0%`는 지연 진단에는 유효하지만, `latency_block` 직접 원인보다 우선하는 제출 회복축은 아니었다. |
| 피벗 잠금 | `SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=True` 상태에서 `13:00` 즉시 재점검이 최우선이다. 이 창에서는 `submitted/full/partial`, `latency_block`, `latency_state_danger`를 먼저 보고 `gatekeeper_fast_reuse_ratio`는 보지 않는다. `SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False` 또는 미동작이면 판정은 미루고 `LatencyCarry0427`의 offload 대상로 넘긴다. |
| 폐기된 보조가설 | `2026-04-24`에는 `window`보다 `signature_changed`가 더 많다는 이유로 `signature-only` deadband를 시도했다. 하지만 `2026-04-27 10:00~11:00`에도 `gatekeeper_fast_reuse_ratio=0.0%`, `budget_pass_to_submitted_rate=0.2%`가 유지돼 live 제출 회복축으로는 닫았다. |
| 11:31 same-day 종료 판정 | raw 재집계 기준 `latency_block=3196`, `latency_state_danger=3000`이었고 내부 분해는 `other_danger=1218`, `ws_jitter-only=869`, `spread-only=257` 순이었다. `other_danger` 단일 케이스 1427건 중 `latency_canary_reason=low_signal`가 `1079건`이라, 남은 기대값 개선 여지는 `latency_state_danger -> other_danger relief` 쪽이 가장 직접적이었다. |
| 현재 해석 | `entry_armed -> budget_pass`는 계속 병목이 아니고, `budget_pass -> latency_block -> submitted`가 주병목이다. 이 구간의 우선 KPI는 `submitted/full/partial`, `latency_state_danger`, `latency_danger_reasons`, `latency_canary_reason`, `other_danger relief applied`다. |
| 코드 반영 상태 | `SCALP_LATENCY_OTHER_DANGER_RELIEF_MIN_SIGNAL_SCORE`를 `90.0 -> 85.0`으로 낮춰 `other_danger relief`의 `low_signal` 병목을 바로 완화했다. `85.0 통과 / 84.9 차단` 회귀 테스트도 추가했다. |
| 13:00 장중 판정 | offline bundle `latency_1300` 기준 `budget_pass=5628`, `submitted=9`, `budget_pass_to_submitted_rate=0.2%`, `latency_block=5619`, `latency_state_danger=5290`, `full_fill=4`, `partial_fill=0`이었다. `11:00` 대비 absolute `submitted/full_fill`는 늘었지만 비율 개선이 없고 `latency_state_danger` 비중도 유지 또는 악화돼, `other_danger-only normal override` 효과를 유의미한 제출 회복으로 보지는 않는다. |
| 15:00 장중 판정 | offline bundle `ws_jitter_1500` 기준 `budget_pass=7568`, `submitted=11`, `budget_pass_to_submitted_rate=0.1%`, `latency_block=7557`, `latency_state_danger=7178`, `full_fill=7`, `partial_fill=0`이었다. `13:00` 대비 absolute `submitted/full_fill`는 늘었지만 효율 비율은 악화됐고 danger 분해도 `other_danger=3256`, `ws_age_too_high=2224`, `ws_jitter_too_high=2203` 순으로 유지돼 `ws_jitter-only relief`도 제출 회복축으로는 닫았다. |
| 금지 조건 | `gatekeeper_fast_reuse_ratio` 개선, `gatekeeper_eval_ms_p95` 하락, signature/window blocker 감소만으로 live 승격/유지 판정을 하지 않는다. 이 값들은 `submitted/full/partial` 또는 `latency_state_danger` 감소와 함께 움직일 때만 보조 근거로 쓴다. `other_danger-only normal override` 적용 후에도 `submitted` 개선이 없다면 `gatekeeper_fast_reuse`로 판정을 되돌리지 않는다. |
| 복합축 적용 | 단일 `gatekeeper_fast_reuse`, `other_danger-only normal override`, `ws_jitter-only relief replacement`는 모두 same-day latency residual 평가축으로 종료됐다. 이후 `latency_quote_fresh_composite`를 live로 열었지만 `2026-04-29 08:29 KST` OFF + restart로 닫혔고, `latency_signal_quality_quote_composite`도 `2026-04-29 12:21~12:50 KST` replacement 후 후보 0건으로 종료됐다. 현재 entry live 축은 `mechanical_momentum_latency_relief`다. 조건은 `signal_score<=75`, `latest_strength>=110`, `buy_pressure_10t>=50`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False`, fallback/split-entry 금지, normal override만 허용이다. |
| fallback/split-entry 정합화 | `CAUTION -> ALLOW_FALLBACK`은 더 이상 실전 주문 경로를 만들지 않도록 `latency_fallback_deprecated` reject로만 남긴다. split-entry follow-up shadow도 기본 OFF로 두고, runtime에서 재개 후보처럼 읽히는 문구를 제거한다. 남는 것은 과거 로그/감리용 helper와 폐기 경로 감지뿐이다. |
| 다음 액션 | 이후 판정은 `quote_fresh_composite_canary_applied`, `submitted/full/partial`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `normal_slippage_exceeded`, `COMPLETED + valid profit_rate`로 닫는다. `gatekeeper_fast_reuse_ratio`는 계속 보조 진단값이고, `other_danger/ws_jitter/spread` 단일축으로 되돌아가지 않는다. |

### DF-ENTRY-006 `latency_quote_fresh_composite` 복합축 live canary

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-006` |
| 판정항목 | `latency_quote_fresh_composite`를 entry live canary로 독립 관리하고, 개별 파라미터가 아니라 묶음 ON/OFF 효과로만 판정할지 결정 |
| 문제 인식 | `other_danger-only`, `ws_jitter-only`, `spread-only`, `gatekeeper_fast_reuse` 단일/보조축은 모두 same-day 제출 회복 실패로 종료됐다. 남은 blocker는 `ws_age/ws_jitter/spread/quote_stale/low_signal`이 quote freshness family로 겹치는 복합 구간일 가능성이 가장 높다. |
| 왜 별도 ID인가 | 이 축은 단일 threshold 완화가 아니라 `signal`, `ws_age`, `ws_jitter`, `spread`, `quote_stale`를 한 묶음 가설로 잠그는 active entry canary다. 따라서 `DF-ENTRY-005`의 pivot 설명 안에 문장으로만 두면, `pivot`과 `실제 live canary`가 같은 항목으로 섞여 판정 추적이 끊긴다. |
| live 정의 | `signal>=88`, `ws_age<=950ms`, `ws_jitter<=450ms`, `spread<=0.0075`, `quote_stale=False`, `fallback/split-entry 금지`, `normal override만 허용`을 1개 묶음으로 적용한다. |
| 판정 원칙 | `signal/ws_age/ws_jitter/spread/quote_stale`를 개별 독립축으로 재해석하지 않는다. 오직 `latency_quote_fresh_composite` 전체 ON/OFF 효과만 본다. |
| 기준선 | primary baseline은 같은 bundle 내 `quote_fresh_composite_canary_applied=False`, `normal_only`, `post_fallback_deprecation` 표본이다. `ShadowDiff0428`이 닫히기 전까지는 이 기준선을 hard baseline으로 승격하지 않고, `2026-04-27 15:00 offline bundle`(`budget_pass=7568`, `submitted=11`, `budget_pass_to_submitted_rate=0.1%`, `latency_state_danger=7178`, `full_fill=7`, `partial_fill=0`)은 방향성 참고선으로만 쓴다. baseline 표본이 `N_min` 미달이면 hard pass/fail이 아니라 방향성 판정으로만 둔다. |
| 핵심 KPI | `submitted/full/partial`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `normal_slippage_exceeded`, `COMPLETED + valid profit_rate` |
| 도달목표 | primary: `budget_pass_to_submitted_rate >= baseline +1.0%p` and `submitted_orders >= 20`. secondary: `latency_state_danger / budget_pass` 비율 `-5.0%p` 이상 개선 and `full_fill + partial_fill`의 `submitted` 대비 전환율 비악화. |
| 보조 진단 | `quote_fresh_composite_canary_applied`, `latency_canary_reason`, `other_danger/ws_age/ws_jitter/spread` 분해는 보조 설명용이다. 이 값들만으로 유지/종료를 판정하지 않는다. |
| rollback guard | `budget_pass_to_submitted_rate`가 baseline 대비 `+1.0%p` 이상 개선하지 못하면 `composite_no_recovery`로 OFF한다. `full/partial` 품질 악화, `normal_slippage_exceeded` 증가, `fallback_regression` 재유입도 즉시 OFF 사유다. |
| 감리 검토 포인트 | baseline이 `same bundle + canary_applied=False`로 잠겼는지, `04-27 15:00 offline bundle`이 참고선으로만 분리됐는지, 성공 기준과 rollback guard가 뒤섞이지 않았는지, baseline 부족 또는 shadow diff 미해소 시 `direction-only`로 격하한다는 규칙이 문서에 남아 있는지를 같이 본다. |
| 금지 조건 | 같은 entry 단계에서 다른 canary를 동시에 두지 않는다. `other_danger/ws_jitter/spread` 단일축으로 되돌아가 개별 attribution을 시도하지 않는다. `gatekeeper_fast_reuse_ratio` 개선만으로 유지 판정을 하지 않는다. |
| 현재 상태 | historical/reference 축으로 전환됐다. `2026-04-29 08:29 KST` 기준 OFF + restart가 반영됐고, 현재는 active entry live canary가 아니다. |
| 후속 연결 | 제출 회복이 확인되지 않아 `latency_signal_quality_quote_composite` same-day replacement를 거쳤고, 다시 효과 미약으로 닫힌 뒤 `DF-ENTRY-007 mechanical_momentum_latency_relief`로 넘어갔다. |

### DF-ENTRY-007 `mechanical_momentum_latency_relief` 운영 override

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-007` |
| 판정항목 | `latency_quote_fresh_composite`와 `latency_signal_quality_quote_composite` 종료 후, AI 50/70 mechanical fallback 상태까지 포함해 제출 drought를 직접 완화하는 replacement 축을 same-day 운영 override로 관리 |
| 문제 인식 | `2026-04-29 12:21:28~12:45:59 KST` `latency_signal_quality_quote_composite` post-restart cohort는 `budget_pass=972`, `submitted=0`, 후보 통과 0건이었다. `signal>=90` 전제는 AI 50/70 fallback 상태를 열지 못해, submitted 회복 직접성이 낮았다. |
| live 정의 | `signal_score<=75`, `latest_strength>=110`, `buy_pressure_10t>=50`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False`, fallback/split-entry 금지, normal override만 허용 |
| 왜 이 축인가 | 같은 post-restart 창 counterfactual 기준으로는 약 `91`건 후보가 보여, 기존 복합축이 버리던 `mechanical fallback` 표본을 제한적으로 열 수 있다. 즉 지금 필요한 것은 `high score only`가 아니라 `기계 fallback이라도 microstructure가 충분한 후보`를 살리는 것이다. |
| 판정 원칙 | hard baseline 승격이 아니라 same-day 운영 override다. 따라서 새 restart 이후 cohort만 분리해 보고, 기존 `h1200`이나 `QuoteFresh` historical cohort와 직접 합산하지 않는다. |
| 현재 상태 | `2026-04-29 12:50 KST` ON, `12:57 KST` restart 반영 완료. main PID는 `30566 -> 35539`로 교체됐다. 현재 entry live 1축은 이 축이다. |
| 핵심 KPI | `mechanical_momentum_relief_canary_applied`, `latency_mechanical_momentum_relief_normal_override`, `submitted`, `full fill`, `partial fill`, `COMPLETED + valid profit_rate`, `fallback_regression=0` |
| 14시 관찰 결과 | `12:57 restart -> 14:00` 고유 기준 `budget_pass=38`, `mechanical_unique=22`, `submitted=20`, `guard_block=2`, `order_failed=2`, `filled=7`이었다. `13:15 hotfix -> 14:00` 기준으로도 `budget_pass=32`, `submitted=17`, `filled=7`이라 제출 drought는 완화됐지만, fill quality와 청산 품질까지 baseline-lock 할 단계는 아니다. |
| rollback guard | post-restart cohort에서 `budget_pass >= 150`인데 `submitted <= 2`, `pre_submit_price_guard_block_rate > 2.0%`, `normal_slippage_exceeded` 반복, 또는 canary cohort 일간 손익이 NAV 대비 `<= -0.35%`이면 OFF 후보로 본다. |
| 다음 액션 | 먼저 same-day post-restart cohort에서 제출 회복 여부를 본다. 회복이 확인되면 `DF-HOLDING-001`의 HOLDING/청산 품질 판정으로 넘어가고, 실패하면 다음 replacement 축 또는 entry price/P0 guard 축과 연결해 다시 닫는다. |

### 플로우차트 진행 위치

- 현재 플로우는 여전히 `entry_armed -> budget_pass -> latency_block -> submitted` 구간(플로우차트 단계 7~8)에 고정돼 있다.
- upstream 단계인 `감시종목/AI 판정`(`DF-ENTRY-001`, `DF-ENTRY-002`)은 `보류`가 아니라 `선결 조건 충족` 상태다. 지금 흔들면 안 되는 것은 upstream이 아니라 downstream 세부축 선택이다.
- `spread_relief`, `ws_jitter-only relief`, `other_danger residual`까지 `quote_fresh family`는 한 차례 장중 잠금됐다. 그 뒤 `gatekeeper_fast_reuse`로 넘어간 것이 매몰 지점이었고, DF-ENTRY-005는 이를 철회해 `latency_state_danger -> other_danger relief` 직접 병목으로 되돌리는 항목이다.
- 따라서 현재 위치는 `gatekeeper_fast_reuse` 재관찰 대기가 아니라, `latency_quote_fresh_composite` historical/reference 종료와 `latency_signal_quality_quote_composite` same-day 종료를 거친 뒤 `DF-ENTRY-007 mechanical_momentum_latency_relief` live 관찰 흐름이다. 지금은 `mechanical fallback` 표본을 포함한 post-restart cohort에서 `submitted/full/partial`과 `COMPLETED + valid profit_rate`를 본다.

## 제출축 판정 후 다음 단계

### DF-HOLDING-001 `submitted 증가 이후 HOLDING/청산 품질 판정`

| 항목 | 내용 |
| --- | --- |
| ID | `DF-HOLDING-001` |
| 시작 조건 | `mechanical_momentum_latency_relief` 또는 후속 downstream 1축에서 `submitted` 회복이 확인된 뒤 hard pass/fail을 시작한다. |
| 현재 상태 | `latency_quote_fresh_composite`는 OFF, `latency_signal_quality_quote_composite`는 후보 0건으로 종료됐고 현재 entry live는 `mechanical_momentum_latency_relief`다. 따라서 HOLDING/청산 hard pass/fail의 선결조건은 과거 `quote_fresh`가 아니라 현 live replacement 축의 `submitted/full/partial` 회복 여부다. 다만 동일 단계 원칙상 entry live 1축과 보유/청산 `soft_stop_micro_grace`는 여전히 분리 병렬 canary로 운용할 수 있다. |
| 다음 단계 목적 | 제출량 증가가 실제 기대값 개선으로 이어지는지 `HOLDING/청산 품질`로 검증한다. 단, 진입 조건은 `submitted` 회복이 먼저다. |
| 핵심 검증축 | `soft_stop/trailing/good_exit`, `holding_action_applied`, `holding_force_exit_triggered`, `exit_rule` 분포, `full/partial` 분리, `COMPLETED + valid profit_rate` |
| 분리 원칙 | `initial-only`와 `pyramid-activated` 표본을 섞지 않는다. `full fill`과 `partial fill`도 합치지 않는다. |
| 수량정책 메모 | `2026-04-28` 기준 스캘핑 초기 진입 `initial_entry_qty_cap`은 임시 `2주`로 완화한다. 이유는 `1주 cap`이 `buy_qty=1 -> template_qty=int(1*0.5)=0`을 만들어 `PYRAMID zero_qty`를 구조적으로 만들 수 있기 때문이다. 다음 판정도 `2주` 자체의 손익보다 `zero_qty 감소`, `pyramid-activated 표본 회복`, `initial-only vs pyramid-activated` 분리 유지 여부를 먼저 본다. |
| 2주 cap 최신 메모 | `2026-04-29` full-day 기준 `initial_entry_qty_cap_applied=38`, `ADD_BLOCKED reason=zero_qty=0`, `completed_valid_count=17`, `completed_valid_avg_profit_rate=+0.0535%`, `pyramid_activated=3`이다. `2주 cap`은 유지 방향성은 확인됐지만 `3주 cap` 확대는 별도 entry live 축이므로 `2026-04-30` 장후 승인조건 전에는 열지 않는다. |
| VM 기준선 메모 | `m7g.xlarge` 상향 직후 첫 거래일은 `runtime basis shift day`로 본다. 이 날의 `gatekeeper_eval_ms_p95`, `latency_state_danger share`, `ws_age/ws_jitter`, `budget_pass_to_submitted_rate` 변화는 전략 개선과 infra 처리속도 개선이 섞일 수 있으므로, 기존 baseline과 바로 hard 비교하지 않고 `VM 이후 provisional baseline` 후보로만 둔다. |
| 관찰축 흔들림 메모 | VM 상향 직후에는 `QuoteFresh`, `latency_state_danger`, `gatekeeper_eval_ms_p95`가 동시에 흔들릴 수 있다. 이때 `latency_state_danger` 감소나 `p95` 하락만으로 entry 축 회복으로 판정하지 않는다. 최소 `submitted/full/partial` 회복이 같이 붙어야 하고, 그렇지 않으면 `infra-only improvement` 또는 `observation wobble`로 분리한다. |
| 성공 판정 | 제출 증가와 함께 체결 품질/청산 품질 악화가 없고 `COMPLETED + valid profit_rate`가 유지 또는 개선 |
| 실패 판정 | 제출 증가 대비 `soft_stop` 급증, `full_fill` 악화, `COMPLETED + valid profit_rate` 악화 동반 |
| 다음 액션 | `HoldingExitPlan0427`에서는 `soft_stop qualifying cohort`의 단일 조작점을 `micro grace`로 승인한다. 근거 묶음은 `rebound_above_sell_10m=93.4%`, `rebound_above_buy_10m=26.2%`, `same_symbol_reentry_loss_count=5`, `hard_stop_auxiliary`다. `whipsaw confirmation`은 AI/호가 확인을 추가해 지연과 미체결을 다시 만들 수 있어 1차 live 조작점에서 제외한다. |
| Source | [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md) |

### VM 성능변경에 따른 기준선 해석 메모

| 항목 | 내용 |
| --- | --- |
| 변경 사실 | `2026-04-28` 사용자 확인 기준 EC2 인스턴스는 `m7g.xlarge`로 상향 완료됐다. |
| 해석 원칙 | VM 변경 직후 표본은 전략 canary 효과와 infra 효과를 분리해서 본다. 즉 `QuoteFresh/latency` 계열 지표는 같은 날 바로 `기존 main-only baseline`의 승패 근거로 쓰지 않고, `reference/provisional baseline`으로만 둔다. |
| 먼저 볼 것 | `instance type`, `uname -m`, `nproc`, `MemAvailable`, `SwapUsed`, bot PID `/proc/<pid>/environ` 같은 provenance와 함께 `gatekeeper_eval_ms_p95`, `latency_state_danger / budget_pass`, `ws_age`, `ws_jitter`, `submitted/full/partial`를 같은 창에서 묶어 본다. |
| 흔들림 해석 | `gatekeeper_eval_ms_p95`만 내려가거나 `latency_state_danger`만 줄어드는 경우는 전략 회복이 아니라 `infra-only improvement` 가능성이 높다. 반대로 quote freshness 지표가 출렁여도 `submitted/full/partial`이 그대로면 관찰축 민감도 변화일 수 있다. |
| 기준선 reset 조건 | `ShadowDiff0428`이 닫히고 same-day에 `submitted/full/partial`까지 같이 움직인 뒤에만 `VM 이후 baseline reset` 후보로 승격한다. 그 전에는 `04-27 15:00 offline bundle`과 기존 `canary_applied=False` 기준선은 계속 참고선으로만 쓴다. |
| 오판 금지 | VM 변경일의 `QuoteFresh` 개선을 새 진입축 성공으로 바로 읽지 않는다. 반대로 악화도 즉시 새 축 실패로 단정하지 않는다. 먼저 `관찰축 흔들림`, `infra-only shift`, `strategy effect` 중 어디에 가까운지 분리해야 한다. |

### DF-HOLDING-002 `soft_stop 1차 live canary` 판정 흐름

| 항목 | 내용 |
| --- | --- |
| ID | `DF-HOLDING-002` |
| 판정항목 | `2026-04-27` 보유/청산 1차 live canary를 `soft_stop_rebound_split` 중심으로 볼지 여부 |
| 문제 인식 | 4월 누적 기준 손익 훼손은 trailing 조기익절보다 soft stop 손실축이 더 직접적이다. `2026-04-24` 생성 리포트 기준 `scalp_soft_stop_pct completed_valid=53`, 평균 `-1.669%`, 실현손익 `-651,680원`이고, `scalp_trailing_take_profit completed_valid=54`, 평균 `+1.041%`, 실현손익 `+280,742원`이다. |
| 추가 가설 | soft stop이 정상 손절이 아니라 휩쏘에 걸리는 케이스가 많을 수 있다. 즉 soft stop 시점에는 손절가를 찍었지만, 이후 1~10분 안에 매도가를 재상회하거나 +0.5~1.0% 이상 되돌리는 표본이 많으면 soft stop을 단순 유지하기보다 confirmation/micro grace 후보로 봐야 한다. |
| 기존 로그 재집계 | 4월 post-sell 평가의 `scalp_soft_stop_pct` 61건 기준, 10분 내 매도가 재상회는 57건(`93.4%`), 10분 내 +0.5% 이상 반등은 43건(`70.5%`), +1.0% 이상 반등은 23건(`37.7%`), 매수가 회복은 16건(`26.2%`)이다. 이는 `soft_stop whipsaw` 가설을 별도 검증축으로 둘 근거가 된다. |
| 왜 1순위인가 | trailing은 놓친 추가상승을 줄이는 upside capture 축이고, soft stop은 이미 실현된 손실을 줄이는 downside leakage 축이다. 기대값 관점에서는 우선 손실 기대값이 큰 soft stop을 먼저 좁혀야 한다. |
| 동시 canary 해석 | 현재 진입병목 축은 `latency_state_danger -> other_danger relief`이고 soft stop은 보유/청산 축이다. 조작점, 적용 시점, cohort tag, rollback guard가 완전히 분리되면 stage-disjoint concurrent canary로 병렬 검토할 수 있다. 단, 두 축이 같은 주문 흐름을 공유하므로 성과판정은 hard pass/fail이 아니라 provisional로 둔다. |
| 1차 canary에서 얻고 싶은 것 | soft stop 자체를 무조건 늦추는 것이 아니라, “진짜 손절해야 할 하락”과 “짧은 V-shape/휩쏘 반등을 잘라버리는 손절”을 분리할 수 있는지 확인한다. |
| 기대효과 1 | soft stop 손실 평균과 실현손익 하방 tail을 줄인다. 즉 제출이 회복될 때 손실 표본이 같이 늘어나는 것을 조기에 막는다. |
| 기대효과 2 | `rebound_above_buy_10m`가 높은 경우에는 cooldown live를 금지하고 threshold/AI 재판정 후보로 넘겨, 반등을 놓치는 역효과를 피한다. |
| 기대효과 3 | `same_symbol_reentry_loss_count`가 높은 경우에는 같은 종목 저품질 재진입을 줄이는 후보를 만들 수 있다. 이 경우 기대효과는 손실 회피와 재진입 비용 절감이다. |
| 기대효과 4 | 10시 중간점검과 11시 1차 판정으로 오염을 조기에 잡는다. cohort tag 혼선, fallback 회귀, soft stop 전환율 급증, 매도 실패가 보이면 장후까지 끌지 않고 OFF 후보로 올린다. |
| 기대효과 5 | 휩쏘 표본이 live에서도 유지되면 `soft_stop confirmation/micro grace`라는 더 직접적인 조작점으로 좁힐 수 있다. 반대로 반등 없이 계속 하락하는 표본이 우세하면 soft stop 완화가 아니라 진입 품질/손절 threshold 재판정으로 넘긴다. |
| 금지 조건 | `partial fill`, `pyramid-activated`, `EOD/NXT`, `fallback` 경로와 합산하지 않는다. soft stop cooldown을 전역 적용하지 않고 qualifying cohort 1개로만 제한한다. |
| 10시 중간점검 | `2026-04-27 10:00~10:10 KST`에는 pass/fail이 아니라 조기 오염을 본다. `soft_stop qualifying cohort`, `submitted/full/partial/completed_valid`, `fallback_regression=0`, 진입 canary와 cohort tag 분리 여부, `rebound_above_sell_1m/3m`, `mfe_ge_0_5`를 먼저 잠근다. |
| 11시 1차 판정 | `2026-04-27 11:00~11:15 KST`에는 `유지/축소/OFF/판정유예` 중 하나로 잠근다. `COMPLETED + valid profit_rate >= 10` 전에는 hard pass/fail이 아니라 방향성 판정으로만 두며, `rebound_above_sell_10m`, `rebound_above_buy_10m`, `mfe_ge_0_5`, `mfe_ge_1_0`로 휩쏘 여부를 같이 본다. |
| 15시 최종 선택 | `soft_stop qualifying cohort`는 `micro grace`로 승인한다. 기본값은 `enabled=True`, `grace_sec=20`, `emergency_pct=-2.0`이며, hard stop `-2.5%`는 그대로 둔다. soft stop 최초 터치 후 20초 안에 emergency를 넘지 않으면 `soft_stop_micro_grace`로 지연하고, 회복 시 grace state를 제거한다. |
| 2026-04-29 표본 보정 | `올릭스(226950)`은 `GOOD_EXIT`, `덕산하이메탈(077360)`은 `NEUTRAL`, `지앤비에스 에코(382800)`는 `MISSED_UPSIDE`이며 soft stop 후 고가 재진입 체결과 익절이 확인됐다. `코오롱(002020)`은 `GOOD_EXIT`지만 soft stop 후 고가 재진입 제출이 있었다. 따라서 지금 결론은 `micro grace 유지 + recovery recapture 라벨/로그 필요성 관찰`이지, 즉시 `soft_stop_micro_grace_extend` ON이 아니다. |
| trailing과의 관계 | `trailing_continuation_micro_canary`는 2순위다. `MISSED_UPSIDE rate >= 60%`, `GOOD_EXIT rate <= 30%`를 충족하고 soft stop 축이 오염되지 않을 때만 다음 후보로 다시 연다. |
| Source | [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-27-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md) |

## 항목 간 연결 관계

| 선행 ID | 결정 결과 | 후속 ID | 연결 의미 |
| --- | --- | --- | --- |
| `DF-ENTRY-001` | 독립 개선축 폐기 | `DF-ENTRY-002` | `blocked_ai_score_share`는 관찰지표로 남기고, 실제 실행은 `buy_recovery_canary prompt` 재교정으로 전환 |
| `DF-ENTRY-002` | upstream 표본 생성 유효, 유지/고정 | `DF-ENTRY-003` | `BUY 부족`보다는 `entry_armed -> submitted` 제출 병목이 다음 공식 판정축으로 넘어갔음을 의미 |
| `DF-ENTRY-003` | 제출축 live 검증 진행 후 원인 위치 고정 | `DF-ENTRY-004` | `spread relief canary`는 downstream 병목 위치 확인까지는 완료했고, 실효성 승인 실패 후 `quote_fresh` replacement 후보로 연결됐다는 의미 |
| `DF-ENTRY-004` | same-day 보조축을 `quote_fresh`로 고정 후 `spread/ws_jitter/other_danger residual`을 순차 검증 | `DF-ENTRY-005` | `quote_fresh family`가 제출 회복을 만들지 못한 뒤, `gatekeeper_fast_reuse` 후보로 새지 않고 `latency_state_danger` 직접 blocker로 복귀해야 한다는 의미 |
| `DF-ENTRY-005` | `gatekeeper_fast_reuse` 매몰을 철회하고 `latency_state_danger -> other_danger relief`로 pivot | `DF-ENTRY-006` | pivot 설명과 `latency_quote_fresh_composite` 복합축을 분리해 historical/reference 근거까지 추적한다는 의미 |
| `DF-ENTRY-006` | `latency_quote_fresh_composite`를 묶음 ON/OFF 기준의 entry 복합축으로 관리했지만 현재는 OFF historical/reference 상태 | `DF-ENTRY-007` | same-day replacement(`latency_signal_quality_quote_composite`) 실패 후 `mechanical_momentum_latency_relief`로 현재 live owner가 이동했다는 의미 |
| `DF-ENTRY-007` | `mechanical_momentum_latency_relief`를 현재 entry live replacement 축으로 관리 | `DF-HOLDING-001` | 제출 회복이 확인되면 HOLDING/청산 품질 판정으로 넘어가고, 회복 실패면 다음 entry replacement 축 또는 entry price/P0 guard 계열로 닫는다는 의미 |
| `DF-HOLDING-001` | 제출 회복 이후 HOLDING/청산 품질 판정 축 유지 | `DF-HOLDING-002` | 4월 손익 훼손 기준으로 soft stop을 1순위 live 후보로 분리하고, 10시 중간점검/11시 1차 판정으로 조기 오염을 잡는다는 의미 |
