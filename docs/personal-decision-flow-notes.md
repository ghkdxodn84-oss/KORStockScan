# 판정항목별 개선 흐름 정리

주의: 이 문서는 개인 정리용이며 다른 문서에서 참조하지 않는다. 개인문서는 다른 문서를 참조할 수 있다.

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
    |               (scalp_soft_stop_pct / scalp_hard_stop_pct / scalp_trailing_take_profit / scalp_ai_early_exit / scalp_ai_momentum_decay)
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
- 여기서 `window`는 “직전 판단이 아직 재사용해도 될 만큼 최근인가”를 보는 시간 조건이고, `signature`는 “지금 장면이 직전 판단과 사실상 같은가”를 보는 상태 조건이다.
- 즉 `window`가 만료되면 `age_expired` 쪽으로 재사용이 깨지고, `window` 안이어도 가격/스프레드/점수/수급 같은 핵심 입력이 달라지면 `sig_changed`로 재사용이 깨진다.
- 의미는 `새 AI gatekeeper 호출을 생략하고 직전 판단을 그대로 재사용했다`는 것이다. 따라서 `gatekeeper_fast_reuse`가 찍히면 gatekeeper 구간에는 도달한 것이 맞지만, 새로운 모델 평가가 매번 다시 돈 것은 아니다.
- 왜 중요하나: BUY 회복이 안 보일 때 `gatekeeper_fast_reuse` 비중이 높으면 실제 병목이 모델 호출 지연이 아니라 `같은 장면 재사용`, `score boundary`, `ws freshness`, `signature 변화` 쪽일 수 있다.
- HOLDING 단계에서는 `is_sell_signal`이 생기기 전까지 `ai_holding_review`와 `scale_in` 후보평가가 반복된다. 즉 제출축이 살아나면 다음 병목은 보유 중 `soft stop/trailing/ai exit` 품질로 넘어간다.
- 이후 보완도 `append`가 아니라 기존 판정 섹션을 최신 스냅샷 기준으로 갱신하는 방식으로 유지한다.

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
| 현재 제약 | 기존 `SCALP_LATENCY_GUARD_CANARY_ENABLED`는 여전히 `ALLOW_FALLBACK` 경로와 결합돼 있다. 다만 장중 구현으로 `SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED`가 추가돼, 이제 fallback 비결합 downstream 축을 코드 레벨에선 직접 켤 수 있다. 남은 제약은 코드 부재가 아니라 `1축 canary` 교체 순서와 live 검증이다. |
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
| 검증 대상 지표 | `ai_confirmed`, `entry_armed`, `budget_pass`, `submitted`, `latency_block`, `quote_fresh_latency_blocks`, `quote_fresh_latency_pass_rate`, `full_fill`, `partial_fill`, `gatekeeper_fast_reuse`, `gatekeeper_eval_ms_p95` |
| 선행조건 결과 | PREOPEN에서 `gatekeeper_fast_reuse=0`, `gatekeeper_fast_reuse_bypass=0`인 표본 공백 상태를 먼저 확인했고, 장중 누적에서는 `gatekeeper_fast_reuse=18`, `gatekeeper_fast_reuse_bypass=58`까지 관측돼 `fast_reuse 코드 미도달` 가설은 해소됐다. |
| 10:00 KST 판정 | `09:00~10:00` 누적 `ai_confirmed=77`, `entry_armed=31`, `submitted=4`, `budget_pass_events=863`, `latency_block_events=859`, `quote_fresh_latency_blocks=777`, `quote_fresh_latency_pass_rate=0.5%`, `full_fill=0`, `partial_fill=0`, `gatekeeper_eval_ms_p95=12543.0ms`였다. 따라서 원인 축은 `upstream BUY 부족`이 아니라 `budget_pass -> latency_block/submitted` downstream 단절로 고정했다. |
| 10:30 KST 재판정 | `09:00~10:30` 누적 `ai_confirmed=91`, `entry_armed=39`, `submitted=8`, `budget_pass_events=1220`, `latency_block_events=1212`, `quote_fresh_latency_blocks=1092`, `quote_fresh_latency_pass_rate=0.7%`, `full_fill=0`, `partial_fill=0`, `gatekeeper_eval_ms_p95=12485.0ms`였다. `10:20~10:30` 증분에서도 `spread_only_required=82`가 차단사유 대부분이었다. |
| 오늘 판정 | `spread relief canary`는 원인 위치를 downstream으로 잠그는 데는 성공했지만, 실효성 승인에는 실패했다. 즉 `제출축 병목 위치 확인`은 됐고, `실제 제출 회복 효과`는 오전 표본에서 입증하지 못했다. |
| why 1 | `submitted_orders=8`로 Plan Rebase §6 `N_min` 최소치 `20`에 `+12`가 부족하다. 따라서 hard pass/fail을 줄 표본은 없다. |
| why 2 | 표본 미달과 별개로 `budget_pass_events=1220` 대비 `submitted=8`, `latency_block_events=1212`, `quote_fresh_latency_blocks=1092`라서 downstream 차단이 지배적이라는 방향성은 충분히 강하다. |
| why 3 | `gatekeeper_eval_ms_p95`는 `12.5s` 수준으로 높지만 rollback guard(`>15,900ms`, sample>=50)까지는 아니다. 따라서 immediate rollback 사유도 아니다. |
| 금지 유지 | 이 결과만으로 `entry_filter_quality`, `score/promote`, `HOLDING`, `EOD/NXT`를 같은 오전 창의 주병목 축으로 올리면 안 된다. 원인귀속이 다시 upstream으로 흔들리기 때문이다. |
| 후속 연결 | same-day 보조축은 `quote_fresh` downstream 1축으로 고정했고, `entry_filter_quality`는 parking 유지로 남겼다. 이후 `quote_fresh` 4요인 중 `ws_jitter`를 독립 조작점으로 고정해 same-day live replacement까지 반영했다. |

### 플로우차트 진행 위치

- 현재 플로우는 여전히 `entry_armed -> budget_pass -> latency_block -> submitted` 구간(플로우차트 단계 7~8)에 고정돼 있다.
- upstream 단계인 `감시종목/AI 판정`(`DF-ENTRY-001`, `DF-ENTRY-002`)은 `보류`가 아니라 `선결 조건 충족` 상태다. 지금 흔들면 안 되는 것은 upstream이 아니라 downstream 세부축 선택이다.
- 오늘 오전 기준 다음 단일 조작점 후보는 `quote_fresh/spread_only_required` 하위원인을 직접 겨누는 replacement였다. 이후 same-day 결정으로 `spread_relief`는 parking으로 내리고, `ws_jitter-only relief`를 독립 replacement 축으로 올려 live 교체를 마쳤다. `entry_filter_quality`는 이 흐름 밖의 후순위 parking이다.
- 같은 날 후속 재분해에서 `ws_jitter-only relief`와 `other_danger residual`도 제출 회복 근거를 만들지 못해 `quote_fresh family` 전체를 장중 잠갔다. 이 시점부터 다음 독립축은 `gatekeeper_fast_reuse`로 넘어간다.

### DF-ENTRY-005 `gatekeeper_fast_reuse` window vs signature 재판정

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-005` |
| 판정항목 | `gatekeeper_fast_reuse` 병목이 `window`인지 `signature`인지 재분해하고, 다음 승인축을 무엇으로 잠글지 결정 |
| 초기 가설 | 장중 중간까지는 `fast_reuse`가 거의 안 보이니 `reuse window`가 너무 짧아서 age 만료가 주원인일 수 있다고 봤다. 즉 `window`를 늘리면 bypass가 줄지부터 확인하려 했다. |
| same-day 재분해 결과 | `2026-04-24 14:25:15 KST` 직전 raw 분해 기준 `age_expired_only=1`, `sig_only=1`, `age_expired+sig_changed=8`이었다. `window만 늘리면 해결`되는 표본은 극히 적고, 실제 주력 blocker는 `signature_changed` 결합 경로였다. |
| 오늘 결론 | 초기 가설은 `window`였지만, 오늘 판정은 `signature` 쪽이 더 큰 원인으로 잠겼다. 따라서 다음 승인축은 `gatekeeper_fast_reuse signature-only`다. |
| 왜 signature인가 | `window-only`가 아니라 `sig_changed`가 붙는 순간 재사용이 깨지는 표본이 더 많았고, `curr_price`, `v_pw_now`, `spread_tick`, `score`, `buy_ratio_ws`, `prog_delta_qty` 같은 미세 변화가 signature를 쉽게 흔들고 있었다. `window`를 먼저 만지면 `signature_changed`와 섞여 원인귀속이 다시 흐려진다. |
| 코드 반영 상태 | same-day에 `signature-only deadband`는 이미 코드에 넣었다. `prog_net_qty`, `prog_delta_qty`는 작은 signed flow 노이즈 구간을 0 bucket으로 정규화하도록 반영했고, 관련 테스트도 통과했다. |
| 아직 안 한 것 | 아직 `live 승인`은 안 했다. 즉 코드는 적재됐지만, 다음 거래일 PREOPEN에서 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서로 실제 1축 live 승인만 남아 있다. 장전에 다시 코딩하는 게 아니라 승인/보류를 닫는 절차다. |
| 현재 해석 | `entry_armed -> budget_pass`는 병목이 아니고, `budget_pass -> latency_block -> submitted`가 여전히 주병목이다. `gatekeeper_fast_reuse signature-only`는 `quote_fresh family` 잠금 이후의 다음 독립축 후보일 뿐, 아직 주병목이 해결됐다는 뜻은 아니다. |
| 다음 액션 | PREOPEN에서는 `signature-only` 축을 live 승인할지, 아니면 보류 사유와 다음 절대시각을 남길지만 본다. 장전 작업의 의미는 코드 작성이 아니라 `1축 live 승인`이다. |

## 제출축 판정 후 다음 단계

### DF-HOLDING-001 `submitted 증가 이후 HOLDING/청산 품질 판정`

| 항목 | 내용 |
| --- | --- |
| ID | `DF-HOLDING-001` |
| 시작 조건 | `ws_jitter-only relief` replacement 또는 후속 downstream 1축에서 `submitted` 회복이 확인된 뒤에만 시작한다. |
| 현재 상태 | `13:07 KST` 선행 누적 기준 `budget_pass_events=1390`, `submitted=1`, `latency_pass_events=1`, `quote_fresh_latency_pass_rate=0.09%`, `latency_canary_applied=True=0`라서 `ws_jitter-only relief`는 공식 슬롯을 기다리지 않아도 `다음 단계 진입 불가`로 잠근다. 이제 same-day 초점은 `HOLDING/청산 품질`이 아니라 `quote_fresh` 하위원인 재분해다. raw `latency_block` 1400건에서 `latency_danger_reason_top5=[other_danger 534, ws_age_too_high 423, ws_jitter_too_high 388, spread_too_wide 379, quote_stale 245]`였고, fresh quote 하위원인 재분해는 `other_quote_fresh 534`, `ws_jitter 230`, `spread 168`, `ws_age 79`, `ws_age+spread 52`, `ws_jitter+spread 45`, `ws_jitter+ws_age 30`, `ws_jitter+ws_age+spread 17`이다. 즉 4요인 밖 residual(`other_danger`)이 explicit 단일요인보다 더 크다. |
| 다음 단계 목적 | 제출량 증가가 실제 기대값 개선으로 이어지는지 `HOLDING/청산 품질`로 검증한다. 단, 진입 조건은 `submitted` 회복이 먼저다. |
| 핵심 검증축 | `soft_stop/trailing/good_exit`, `holding_action_applied`, `holding_force_exit_triggered`, `exit_rule` 분포, `full/partial` 분리, `COMPLETED + valid profit_rate` |
| 분리 원칙 | `initial-only`와 `pyramid-activated` 표본을 섞지 않는다. `full fill`과 `partial fill`도 합치지 않는다. |
| 성공 판정 | 제출 증가와 함께 체결 품질/청산 품질 악화가 없고 `COMPLETED + valid profit_rate`가 유지 또는 개선 |
| 실패 판정 | 제출 증가 대비 `soft_stop` 급증, `full_fill` 악화, `COMPLETED + valid profit_rate` 악화 동반 |
| 다음 액션 | 이번 턴의 next live 후보 재선정은 `quote_fresh 4요인`만이 아니라 `quote_fresh residual(other_danger)`까지 포함한 5분기로 본다. 여기서 끝내지 않고 `ws_jitter` 축을 닫는 즉시 `other_danger residual` 1축을 같은 장중에 바로 연다. 이번에는 [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py)의 `other_danger-only normal override` 코드가 먼저 들어간 뒤 관찰을 시작한다. 새 관찰창은 코드 적재 시점부터 다시 시작하되, `13:40` 중간점검 없이 `14:00 KST`에 바로 최종판정을 내린다. `14:00`까지 `other_danger residual`도 `submitted <= 2`로 잠기면 `quote_fresh family` 전체를 닫고, 준비된 다음 독립축 1개를 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서로 same-day replacement 할 수 있다. 여기서 `1축 원칙`은 `동시 live 1축`만 금지한다. `submitted >= 5`가 새 축에서 다시 확보되기 전까지 `HOLDING/청산 품질`은 열지 않는다. |
| Source | [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md) |

## 항목 간 연결 관계

| 선행 ID | 결정 결과 | 후속 ID | 연결 의미 |
| --- | --- | --- | --- |
| `DF-ENTRY-001` | 독립 개선축 폐기 | `DF-ENTRY-002` | `blocked_ai_score_share`는 관찰지표로 남기고, 실제 실행은 `buy_recovery_canary prompt` 재교정으로 전환 |
| `DF-ENTRY-002` | upstream 표본 생성 유효, 유지/고정 | `DF-ENTRY-003` | `BUY 부족`보다는 `entry_armed -> submitted` 제출 병목이 다음 공식 판정축으로 넘어갔음을 의미 |
| `DF-ENTRY-003` | 제출축 live 검증 진행 후 원인 위치 고정 | `DF-ENTRY-004` | `spread relief canary`는 downstream 병목 위치 확인까지는 완료했고, 실효성 승인 실패 후 `quote_fresh` replacement 후보로 연결됐다는 의미 |
| `DF-ENTRY-004` | same-day 보조축을 `quote_fresh`로 고정 후 `ws_jitter` replacement live 교체 | `DF-ENTRY-005` | `quote_fresh family` 잠금 이후 다음 독립축을 `gatekeeper_fast_reuse`로 넘겨 `window vs signature`를 다시 분해했다는 의미 |
| `DF-ENTRY-005` | `window`보다 `signature`가 주원인으로 재판정, code-load 완료/live 승인 대기 | `DF-HOLDING-001` | HOLDING/청산 품질 판정은 여전히 제출 회복 이후 단계이며, `gatekeeper_fast_reuse signature-only` live 결과가 먼저 필요하다는 의미 |
