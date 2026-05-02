# KORStockScan Plan Rebase 중심 문서

기준일: `2026-05-01 KST`  
역할: 현재 튜닝 원칙, 판정축, 정량 목표, active/open 상태만 고정하는 중심축 문서다.  
주의: 이 문서는 자동 파싱용 체크리스트를 소유하지 않는다. Project/Calendar 동기화 대상 작업항목은 날짜별 `stage2 todo checklist`가 소유한다.

---

## 1. 현재 판정

1. 현재 단계는 손실 억제형 미세조정이 아니라 `기대값/순이익 극대화`를 위한 `Plan Rebase`다.
2. 현재 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이다.
3. 현재 폐기/종료 확정 축은 [closed observation archive](./archive/closed-observation-axes-2026-05-01.md)로 내린다. rebase 본문은 active/open 축과 재개 금지 원칙만 유지한다.
4. 현재 live 운용 원칙은 `동일 단계 내 1축 canary`다. 진입병목축과 보유/청산축은 서로 다른 단계이므로 양쪽 canary 동시 존재가 가능하지만, 같은 단계 안에서 canary 중복은 금지한다.
5. 현재 entry owner는 `mechanical_momentum_latency_relief` 운영 override와 `dynamic_entry_price_resolver_p1`/`dynamic_entry_ai_price_canary_p2` 가격축이다. 종료된 latency composite 세부 경과는 archive에서만 본다.
6. 현재 보유/청산 owner는 `soft_stop_micro_grace`, `REVERSAL_ADD`, `bad_entry_refined_canary`다. `soft_stop_expert_defense v2`는 종료했고, naive `bad_entry_block`은 observe-only에서 refined canary의 근거로만 남긴다.
7. `2026-05-04 KST` 장전부터 `holding_flow_override`를 기존 튜닝 관찰축과 별개인 운영 override로 둔다. 적용 대상은 `AI/soft stop/trailing/bad-entry refined` 청산 후보와 오버나이트 `SELL_TODAY` 후보이며, hard stop/protect hard stop/주문·잔고 안전장치는 즉시 실행을 유지한다. 단일 점수구간 컷 대신 최근 tick 30개, 분봉 60개, 최근 flow review history를 넣어 `flow_state/evidence/action` 흐름으로 최종 판단하고, 최초 후보 대비 추가악화 `0.80%p` 또는 최대 보류 `90초` 도달 시 기존 청산을 허용한다.
8. AI 엔진 개선은 live routing 승격이 아니라 `Gemini/DeepSeek/OpenAI`별 flag-off acceptance, endpoint schema contract, transport provenance로 분리한다. Gemini live enable과 OpenAI live routing은 별도 checklist 없이 임의로 열지 않는다.
9. `2026-05-02 KST` 기준 AI provider routing은 유지하되, live prompt별 model tier와 호출 interval 기본값은 기대값 우선으로 즉시 보정한다. `watching/holding/shared` hot path는 Tier1, `entry_price/holding_flow/overnight/scalping_exit/gatekeeper report`는 Tier2, EOD/장후 심층 분석은 Tier3를 기본으로 쓰며, OpenAI tier 기본값은 `FAST=gpt-5.4-nano`, `REPORT=gpt-5.4-mini`, `DEEP=gpt-5.4`로 분리한다. 이는 provider live routing 승격이 아니라 기존 endpoint 내부 model tier routing 변경이다.

## 2. 용어 범례

| 표현 | 한글 설명 | 현재 판정 |
| --- | --- | --- |
| `fallback` | 정상 진입이 막힌 상황에서 보조 주문 경로로 진입을 시도하던 예외 경로 | 신규 사용 금지, 폐기 유지 |
| `fallback_scout/main` | `fallback_scout` 탐색 주문과 `fallback_main` 본 주문이 같은 축에서 함께 나가던 2-leg fallback 분할진입 | 영구 폐기. 재개/승격/canary 대상 아님 |
| `fallback_single` | scout/main으로 나뉘지 않은 단일 fallback 진입 경로 | 영구 폐기. 재개/승격/canary 대상 아님 |
| `latency fallback split-entry` | latency 상태가 `CAUTION/DANGER`일 때 fallback 허용으로 분할진입을 시도하던 경로 | 영구 폐기. latency bugfix 대상과 분리 |
| `main-only` | `songstock`/remote 비교를 제외하고 메인서버 실전 로그만 기준으로 보는 방식 | Plan Rebase 기간의 기준선 |
| `normal_only` | fallback 태그와 예외 진입이 섞이지 않은 정상 진입 표본 | 손익/성과 비교의 우선 기준 |
| `post_fallback_deprecation` | `2026-04-21 09:45 KST` fallback 폐기 이후 새로 쌓인 표본 | 폐기 이후 효과 확인 기준 |
| `canary` | 작은 범위로 실전에 적용해 성과와 리스크를 검증하는 1축 변경 | 동일 단계 안에서는 1축만 허용 |
| `stage-disjoint concurrent canary` | 진입병목과 보유/청산처럼 단계, 조작점, 적용시점, cohort tag, rollback guard가 분리되는 병렬 canary | 단계가 다르면 동시 존재 가능. 단, 동일 단계 내 canary 중복은 금지하고, 두 축 중 하나라도 cohort 혼선이 생기면 해당 단계 단일축 원칙으로 복귀 |
| `shadow` | 실전 주문에는 반영하지 않고 병렬 계산만 하던 검증 방식 | 신규/보완축에서는 금지 |
| `buy_recovery_canary` | Gemini `WAIT 65~79` 과밀 구간을 2차 재평가해 BUY 회복 여부를 보던 진입축 | 현재 live owner 아님. `2026-04-23` 이후 downstream 제출병목 축으로 교체됐고, 재개 시 새 checklist 승인 필요 |
| `entry_filter_quality` | 불량 진입을 줄이고 제출/체결 품질을 높이는 정식 튜닝 후보 | submitted 병목 해소 전까지 parking. 재개는 현재 entry owner와 충돌하지 않는 단일축으로만 가능 |
| `latency_quote_fresh_composite` | `ws_age`, `ws_jitter`, `spread`, `other_danger`가 단일 사유가 아니라 quote freshness family로 겹쳐 제출을 막는 복합축 | `2026-04-29 08:29 KST` OFF + restart 완료. 현재 standby/off이며, `signal>=88`, `ws_age<=950ms`, `ws_jitter<=450ms`, `spread<=0.0075`, `quote_stale=False` 묶음은 historical/reference 축으로만 남긴다 |
| `latency_signal_quality_quote_composite` | `latency_quote_fresh_composite` 미회복 시 검토한 예비 복합축. quote freshness 완화폭을 넓히는 대신 `signal>=90`, `latest_strength>=110`, `buy_pressure_10t>=65`를 요구했다 | `2026-04-29 12:50 KST` 운영 override로 OFF. post-restart `budget_pass=972`, `submitted=0`, 후보 통과 0건으로 효과 미약 판정 |
| `mechanical_momentum_latency_relief` | AI score 50/70 같은 mechanical fallback 상태라도 `budget_pass` 이후 수급/강도와 quote freshness 조건이 충분하면 latency DANGER를 normal 주문으로 넘기는 entry replacement 축 | `2026-04-29 12:50 KST` 운영 override로 live ON. 조건은 `signal_score<=75`, `latest_strength>=110`, `buy_pressure_10t>=50`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False`다. 성과는 post-restart cohort에서 `submitted`까지는 병목 회복으로 보고, `full/partial`, `HOLDING/exit_rule`, `COMPLETED + valid profit_rate`는 체결 품질과 BUY 신호 적정성 관찰축으로 분리한다 |
| `dynamic_entry_price_resolver_p1` | `signal_radar.target_buy_price`를 참고 기준가로만 쓰고, strategy-aware resolver가 defensive price와 timeout profile을 결정하는 진입가 기본 경로 | `2026-05-01` 구현 완료. `SCALPING_ENTRY_PRICE_RESOLVER_ENABLED=True`, best bid 대비 `80bp` 초과 하향 기준가는 거부하고, 일반 스캘핑 `90초`, `BREAKOUT 120초`, `PULLBACK 600초`, `RESERVE 1200초` timeout을 분리한다. entry price canary의 fallback baseline으로도 사용한다 |
| `dynamic_entry_ai_price_canary_p2` | submitted 직전 Tier2 AI가 reference target, defensive price, live quote, spread/latency, 호가/체결강도와 OFI/QI orderbook micro feature를 보고 최종 주문가를 재결정하는 진입가 canary | `2026-05-01` 구현 완료, `2026-05-02` OFI/QI P2 내부 feature 확장 완료. `SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED=True`, `SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED=True`, `entry_price_v1` schema, min confidence `60`, skip min `80`. `USE_DEFENSIVE | USE_REFERENCE | IMPROVE_LIMIT | SKIP` 중 하나를 선택하며 AI 실패/parse fail/guard 위반은 P1 resolver로 fail-closed한다. OFI/QI는 standalone 신규 canary가 아니라 P2 내부 입력이며, `neutral/insufficient`이면 OFI/QI만으로 SKIP하지 않는다 |
| `holding_exit_observation` | 보유/청산 후보를 saved snapshot, post-sell, pipeline event로 분해하는 리포트 축 | live canary가 아니라 관찰/후보 고정용. `partial/full`, `initial/pyramid` 합산 결론 금지. `+0.8% preset TP AI 1회 검문`은 `SCALPING_HOLDING_SYSTEM_PROMPT`를 사용하지만 익절 후보 표본으로 별도 분리해 `scalp_preset_tp_ai_exit_action/hold_action`, `scalp_preset_ai_review_exit`를 본다 |
| `soft_stop_micro_grace_extend` | soft stop 최초 유예 20초가 너무 짧을 때 threshold 근처에서 1회 추가 유예하는 보조 파라미터 | standby/off. `soft_stop_micro_grace` 20초 축의 hard stop/동일종목 손실/미체결 비악화가 확인되고도 반등 포착이 부족할 때만 검토한다 |
| `soft_stop_expert_defense` | `soft_stop_micro_grace v2`로 `stop arbitration layer`, `thesis invalidation veto`, `orderbook absorption stop`을 live에 묶고, `MAE/MFE quantile`, `recovery probability`, `partial de-risk`, `adverse fill`은 shadow/observe로 분리한 보유/청산 방어망 | `2026-04-30 12:00~15:30 KST` same-day 수집 축으로 종료. 다음 재승인 전 기본 OFF이며 로그는 다음 방어망 설계 근거로만 유지한다 |
| `valid_entry_reversal_add` | 진입 판단은 유효했지만 초반 눌림이 발생한 표본에서 저점 미갱신, AI 회복, 수급 재개가 확인될 때 평단을 낮추는 소형 추가매수 canary | `2026-04-30` 소형 canary. 기본 조건은 `REVERSAL_ADD_ENABLED=True`, `profit_rate -0.70%~-0.10%`, `held_sec 20~180`, `AI>=60`, bottom 대비 `+15pt` 또는 연속회복, 수급 3/4 충족, 1회만 허용. `2026-04-30 10:15 KST` intraday override로 오전 blocker의 대부분을 차지한 `pnl_out_of_range`, `hold_sec_out_of_range`만 완화하고 AI/supply 조건은 유지한다 |
| `pyramid_dynamic_qty_observe` | 수익 중인 포지션의 `PYRAMID` 불타기 수량을 고정 50% 템플릿이 아니라 추세/수급/트레일링 여유 기반으로 재산정하는 후보 | standby/observe-only. 현재 `PYRAMID`는 유지하되 `initial-only`와 `pyramid-activated` 표본을 분리한다. 동적 수량화는 `REVERSAL_ADD`와 같은 날 live 변경하지 않고 `would_qty` counterfactual부터 설계한다 |
| `statistical_action_weight` | 가격대/거래량/시간대별로 `exit_only`, `avg_down_wait`, `pyramid_wait`의 후행 성과를 비교해 threshold weight와 동적 수량화 근거를 만드는 decision-support 축 | report-only. `exit_signal`, `sell_completed`, `scale_in_executed` compact 표본과 completed trade를 연결해 장후에만 본다. 단순 평균이 아니라 empirical-bayes shrinkage와 lower-confidence score를 사용하며, live runtime threshold나 주문 행동을 직접 바꾸지 않는다 |
| `stat_action_decision_snapshot` | HOLDING 판단 순간의 후보/선택/차단 행동과 포지션·수급·호가 상태를 남기는 statistical action weight용 수집 이벤트 | observe-only. 기본 30초 rate-limit로 IO를 제한하며 `chosen_action`, `eligible_actions`, `rejected_actions`를 남겨 selection bias를 줄인다. live 행동 변경 없음 |
| `bad_entry_block` | soft stop으로 이어질 가능성이 큰 never-green/AI fade 유형을 조기정리 후보로 분류하는 observe-only classifier | `2026-04-30` observe-only. 표본 수는 충분하지만 `GOOD_EXIT` 제거 위험이 남아 단순 live block은 금지한다. `bad_entry_refined_canary`는 `held_sec>=180`, `profit_rate<=-1.16`, `peak_profit<=+0.05`, `AI<=45`, recovery/thesis/adverse 확인을 붙인 active canary로 다음 장전 로드 확인 대상이다 |
| `holding_flow_override` | 보유/청산과 오버나이트 `SELL_TODAY` 후보를 단일 점수 컷이 아니라 긴 입력 윈도와 AI flow summary로 재검문하는 운영 override | `2026-05-04` 장전부터 적용. 기존 튜닝 관찰축과 별개이며 `HOLD/TRIM`은 v1에서 전량청산 보류만 뜻한다. `EXIT`, AI/parse/stale/context 실패, 보류 90초 초과, 최초 후보 대비 추가악화 `0.80%p` 도달은 기존 청산 허용이다. 오버나이트 판정은 `15:20 KST`로 앞당기고 `SELL_TODAY`는 flow 재검문 후 `HOLD_OVERNIGHT` 전환 가능, `15:20~15:30` 추가악화 `0.80%p` 시 `SELL_TODAY`로 복귀한다 |
| `nan_cast_guard_followup` | 주문·체결·DB 복원 숫자 필드에 `NaN/inf`가 유입될 때 런타임 중단과 상태전이 실패를 막기 위한 숫자 정규화/업스트림 source 재분해 계획 | live canary 아님. 런타임 안정화/집계 품질 보강용 follow-up으로만 관리하고, 기대값 해석 입력은 재발건수·영향경로·미진입/미청산 기회비용 분해를 함께 남긴다 |
| `openai_transport_parity_flag_off` | OpenAI가 Gemini와 같은 endpoint schema registry/contract 기준을 공유하되, transport는 HTTP baseline과 WS shadow를 분리 관찰하는 acceptance 축 | `2026-04-30` 기준 flag-off observe-only. `response schema registry`, `deterministic JSON config`, `Responses WS transport`는 모두 rollback owner와 cohort를 잠근 뒤에만 다음 슬롯으로 넘긴다 |

### 2.1 Shadow / Canary / Cohort 운영 정의

1. `shadow`는 실주문, 실청산, 실판단을 바꾸지 않고 병렬 계산과 로그만 남기는 관찰 경로다. 현재 운영 원칙상 신규 alpha 튜닝축에는 쓰지 않는다.
2. `canary`는 ON/OFF 가능한 단일 조작점이 실주문 또는 실판단을 실제로 바꾸는 제한적 live 변경이다. 적용 대상, rollback owner, cohort tag가 raw event에서 복원 가능해야 한다.
3. `cohort`는 live/observe/excluded 모집단을 분리해 성과와 rollback을 섞이지 않게 잠그는 판정 단위다. 최소 `baseline cohort`, `candidate live cohort`, `observe-only cohort`, `excluded cohort`를 함께 기록한다.
4. `운영 override`는 canary와 달리 튜닝 가설 검증보다 실전 보호/보정 목적이 우선인 runtime 우선순위 변경이다. `holding_flow_override`, `mechanical_momentum_latency_relief`처럼 same-day 적용이 가능하지만, 이 경우에도 cohort와 rollback guard는 동일하게 잠근다.
5. `baseline-promote`는 이름에 canary가 남아 있어도 실질적으로 기본 운영경로로 굳은 상태를 뜻한다. baseline-promote 후보는 신규 canary로 세지지 않지만, rename과 문서 정리는 별도 change set으로 닫아야 한다.

## 3. 튜닝 원칙

1. 최종 목표는 손실 억제가 아니라 기대값/순이익 극대화다.
2. 손익 판단은 `COMPLETED + valid profit_rate`만 사용한다.
3. `NULL`, 미완료, fallback 정규화 값은 손익 기준으로 사용하지 않는다.
4. 비교 우선순위는 `거래수 -> 퍼널 -> blocker -> 체결품질 -> missed_upside -> 손익`이다.
5. BUY 후 미진입은 `latency guard miss`, `liquidity gate miss`, `AI threshold miss`, `overbought gate miss`로 분리한다.
6. `full fill`과 `partial fill`은 합산하지 않는다.
7. 원인 귀속이 불명확하면 먼저 리포트 정합성, 이벤트 복원, 집계 품질을 점검한다.
8. `counterfactual` 수치는 직접 실현손익과 합산하지 않고 우선순위 판단 자료로만 쓴다.
9. 향후 A/B 테스트의 목적은 단일 모델 우열 확인이 아니라 진입/보유/청산 각 단계에서 `EV`를 높여 기준 조합 대비 `최소 +10%` 개선되는 엔진 조합을 찾는 것이다.
10. AI `fast -> deep` 재판정 트리거는 엔진별 하드코딩 점수대가 아니라 `feature conflict predicates + 최근 실거래 EV 근거`로 분리해 관리한다.
11. 재판정 구조를 공통축으로 승격할 때는 `submitted/full_fill/partial_fill/COMPLETED + valid profit_rate` 기준으로 `재판정 코호트 vs 비재판정 코호트`를 먼저 비교하고, EV 개선이 확인될 때만 live 공통구조로 올린다.
12. `gatekeeper_fast_reuse_ratio`, `gatekeeper_eval_ms_p95`, `signature/window blocker`는 제출병목의 보조 진단 지표다. `submitted/full/partial` 회복 또는 `latency_state_danger` 감소 없이 이 지표만으로 entry live 후보를 승격하지 않는다.
13. 장중 판정 시각에 fresh 로그가 작업환경에 아직 없으면 판정을 빈칸으로 남기지 않는다. 같은 시각 기준 `offline bundle 생성 -> 사용자 로컬 analyzer 실행 -> 결과값 전달`을 요청하고, 그 산출물로 same-slot 판정을 닫는다.
14. `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`는 폐기 축으로만 남긴다. 실전 경로 재개, replacement 후보, observe-only runtime shadow 재가동은 새 workorder와 새 rollback guard 없이 허용하지 않는다.
15. 복합 entry canary는 `단일축 원칙의 예외`가 아니라 `단일 가설을 구성하는 묶음 축`이다. 따라서 `latency_quote_fresh_composite`는 `signal>=88`, `ws_age<=950ms`, `ws_jitter<=450ms`, `spread<=0.0075`, `quote_stale=False` 5개 파라미터를 묶음 단위로만 ON/OFF하고, 개별 파라미터 효과는 분리 판정하지 않는다.
16. active canary 임계값은 문서에 `분포 기준`, `예상 기각률`, `효과 부족 시 다음 fallback 임계값`을 함께 남긴다. 숫자만 단독으로 승격하지 않는다.
17. active canary의 다음 판정 baseline은 가능하면 같은 bundle 내 `canary_applied=False` 표본으로 고정한다. 해당 baseline이 `N_min` 미달이면 hard pass/fail 대신 방향성 판정으로 격하한다.
18. `latency_quote_fresh_composite`의 pass/fail 기준선은 `same bundle + canary_applied=False + normal_only + post_fallback_deprecation` 표본이다. `ShadowDiff0428`이 닫히기 전까지는 이 기준선을 hard baseline으로 승격하지 않고, `2026-04-27 15:00 offline bundle`은 방향성 참고선으로만 사용한다.
19. `offline_live_canary_bundle`은 장중 과부하 방지용 판정 입력이다. fresh 로그가 Codex 작업환경에 없으면 서버에서 lightweight export만 수행하고, 사용자가 로컬 analyzer로 `latency_quote_fresh_composite`와 `soft_stop_micro_grace` summary를 생성해 같은 슬롯 판정을 닫는다. 이 번들은 heavy snapshot/report builder를 호출하지 않으며, 산출물은 hard pass/fail 전제 충족 여부와 direction-only 사유를 확인하는 입력으로만 사용한다.
20. `latency_signal_quality_quote_composite`와 `soft_stop_micro_grace_extend`는 예비축/예비 파라미터다. active 축이 실패 또는 표본부족 재판정 조건을 충족하기 전에는 live ON 하지 않으며, 활성화하려면 기존 동일 단계 canary OFF, rollback guard, restart 필요 여부, baseline cohort를 같은 checklist에 잠근다.
21. `NaN cast` 계열 오류는 손익 축이 아니라 런타임 안정화 축으로 분리한다. 판정은 `재발 건수`, `루프 중단 여부`, `BUY_ORDERED->HOLDING/청산 상태전이 실패`, `미진입/미청산 기회비용` 기준으로 남기고, 원격과 동일 패치 복제 여부보다 메인 코드베이스 기준의 최소 안전 캐스팅/업스트림 source 추적 계획을 우선한다.
22. canary는 `live`로 승격되기 전 `분포 근거`, `candidate cohort`, `rollback guard`, `OFF 조건`, `판정 시각`, `same-stage owner 충돌 여부`가 문서에 모두 닫혀 있어야 한다. 하나라도 비어 있으면 observe-only 또는 guarded-off로 둔다.
23. canary를 `live 유지`에서 `baseline 운영`으로 전환할 때는 최소 `N_min`, 핵심 metric, canary-applied vs baseline cohort 비교, cross-contamination 부재, restart/rollback 경로를 함께 닫는다. 단순히 “문제 없었다”만으로는 승격하지 않는다.

## 4. 작업 규칙

| 규칙 | 기준 | 위반 시 처리 |
| --- | --- | --- |
| 동일 단계 단일 live canary | 단일 live canary 원칙은 동일 단계 안에서만 적용한다. 진입병목축과 보유/청산축은 별개 단계이므로 양측에 canary가 동시에 존재할 수 있다. | 동일 단계 안에서 동시 2축 live 금지. 같은 단계 안에서 교체가 필요하면 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서를 강제한다. |
| stage-disjoint 병렬 canary | 진입병목 canary와 보유/청산 canary는 조작점, 적용 시점, cohort tag, rollback guard가 완전히 분리되면 병렬 live가 가능하다. 이 경우 전체 성과 합산 판정은 금지하고 단계별로 분리 판정한다. | entry canary가 유입 cohort를 크게 바꿔 보유/청산 판정이 오염되거나 rollback guard가 공유되면 병렬 판정 무효. 해당 단계의 단일축 원칙으로 복귀한다. |
| shadow 금지 | 신규/보완축은 shadow 없이 canary-only | shadow 항목은 폐기 또는 코드정리로 격하 |
| canary -> live 전환 | canary를 기본 live owner 또는 운영 기본값으로 승격할 때는 `N_min`, 주요 metric 개선, rollback guard 무위반, applied/not-applied cohort 비교, cross-contamination 부재, restart 가능 여부를 checklist와 report에 함께 잠근다. | 수치 기준 미달, applied cohort 복원 불가, same-stage owner 충돌, `COMPLETED + valid profit_rate` 또는 체결품질 악화가 있으면 live 전환 금지. 기존 canary 유지 또는 OFF로 닫는다. |
| 문서 참조 방향 | `docs/personal-decision-flow-notes.md`는 개인판단 정합성 기록용 노트다. 다른 문서에서 `Source` 또는 판정 근거 링크로 사용하지 않는다. 개인문서는 checklist/report/plan 문서나 코드 레퍼런스를 참조해도 된다. | 개인문서가 판정 근거 링크로 쓰이면 링크를 checklist에서 제거하고 기준문서/감사문서 근거로 대체한다. |
| 원격 비교 제외 | Plan Rebase 기간은 main-only 기준 | songstock/remote 비교는 의사결정 입력에서 제외 |
| 라우팅 고정 | live 스캘핑 AI는 Gemini 고정 | A/B는 `entry_filter_quality` 1차 판정 후 별도 판단. 병목 완화 중에는 원격 전체 엔진 라우팅만 GPT로 바꾸는 단순 교체를 금지하고, 진입/보유/청산 단계별 코호트 비교와 품질 가드(`submitted/full/partial/soft_stop/COMPLETED + valid profit_rate`)를 함께 고정한다. |
| 문서 기준 | 중심 문서는 기준, checklist는 실행, report는 근거 | 중복 작업항목 생성 금지 |
| 일정 날짜 고정 | 모든 작업일정은 `YYYY-MM-DD KST`와 `Slot/TimeWindow`로 고정 | `후보비교 완료시`, `관찰 후`, `다음주` 같은 상대 일정은 무효. 당일 안에 절대 날짜/시각으로 재작성 |
| checklist 상단 공통화 | 날짜별 checklist 상단은 [stage2-todo-checklist-template.md](./stage2-todo-checklist-template.md) 형식을 기본으로 사용한다. `오늘 목적`/`오늘 강제 규칙` 공통 bullet는 템플릿에서 복사하고, 날짜별 파일에는 당일 예외만 최소 추가한다. | 미래 checklist가 약한 규칙셋으로 되돌아가면 템플릿 위반으로 보고 같은 턴에 상단 규칙을 재정렬한다. |
| 관찰 반나절 제한 | live 영향 여부 관찰은 오전/오후 반나절을 넘기지 않음 | 반나절에 미관측이면 관찰축 오류, live 영향 없음, 또는 그대로 진행 가능 중 하나로 판정 |
| 관찰 후 즉시 판정/즉시 착수 | 관찰창이 끝나면 같은 거래일 안에서 `즉시 판정 -> 다음 축 즉시 착수`를 기본으로 한다. 이미 수집된 데이터만으로 볼 수 있는 판정은 장후/익일로 미루지 않고 그 자리에서 닫는다. 추가 데이터가 아니라 코드베이스 수정이 필요한 경우에도 same-day 형상/가드/재시작 가능 여부를 먼저 판단하고, 가능하면 즉시 반영 후 새 관찰창을 연다. | `장후 보자`, `다음 장전에 보자` 식 이관은 금지한다. 미룰 수 있는 예외는 `1) 단일 조작점이 아직 정의되지 않음`, `2) rollback guard가 문서화되지 않음`, `3) restart/code-load가 운영 경계상 같은 턴에 불가능함` 뿐이며, 이때도 why와 막힌 조건, 다음 절대시각을 checklist에 함께 고정한다. |
| 장후/익일 이관 무효화 | 관찰축/보조축/승격후보를 장후·익일·다음 장전으로 넘기려면 같은 턴에 `지금 닫을 수 있는가`, `추가 데이터가 필요한가 vs 코드수정이 필요한가`, `same-day 단일 조작점/rollback guard/restart 가능 여부`, `불가하면 막힌 조건과 다음 절대시각` 4가지를 문서에 모두 남겨야 한다. | 위 4개가 없으면 이관 판정은 무효로 본다. 무효 항목은 자동으로 `same-day 재분해/즉시 착수 미이행`으로 간주하고, 다음 응답에서 먼저 재개한다. |
| PREOPEN 이관 제한 | PREOPEN은 전일에 이미 `단일 조작점`, `rollback guard`, `코드/테스트`, `restart 절차`가 고정된 carry-over 축만 받는다. PREOPEN을 `다음에 생각해볼 후보 검토 슬롯`으로 쓰지 않는다. | same-day에 설계/분해 가능한 축을 PREOPEN으로 넘기면 규칙 위반이다. PREOPEN checklist에는 전일 준비완료 증적과 승인/롤백 판정만 남긴다. |
| 판정 근거 서술 | `유지/보류/미완/폐기/완료` 모두 수치 + why(기대값 영향/원인귀속/표본충분성)를 함께 남긴다. 수치만 나열하고 해석이 없으면 근거 미충족으로 본다. | checklist/report에 why를 추가 기재하고, why가 없으면 완료/보류 판정을 다시 연다 |
| 봇 재실행 | 검증/반영에 봇 재실행이 필요하고 권한/안전 조건이 맞으면 AI가 표준 wrapper로 직접 실행 | 토큰/계정/운영 승인 등 보안 경계가 있으면 실행하지 않고 필요한 1개 명령을 사용자에게 요청 |
| 장중 스냅샷 운용 | 장중 판단용 스냅샷은 `12:00~12:20 full` 1회를 기준으로 하고, 그 외 장중은 `intraday_light` 증분(지연/jitter 포함)으로만 갱신한다. `server_comparison`은 Plan Rebase 기본 입력에서 제외하며, 명시 플래그(`KORSTOCKSCAN_ENABLE_SERVER_COMPARISON`)가 있을 때만 생성한다. `performance_tuning` 거래일 이력은 고정 3일이 아니라 상황별 가변 window(`trend_max_dates` 또는 env)로 운용한다. 체크리스트에 스냅샷 생성 작업을 둘 때는 `max_date_basis`, `trend_max_dates`, `evidence_cutoff`를 함께 기재한다. 12시 full 스냅샷 완료 후에는 admin Telegram 완료 알림을 발송해 일일 작업지시서 전달 기준으로 삼는다. | full 다중 실행, 고정 기간 강제, max date/cutoff 미기재, 원격 비교값을 기준 판단에 혼입하면 규칙 위반으로 간주하고 main-only 기준으로 재집계한다. |
| 보유/청산 관찰 리포트 | `holding_exit_observation`은 saved monitor snapshots, `data/post_sell/*.jsonl`, `data/pipeline_events/*.jsonl*`만 입력으로 쓰고, fresh snapshot이 필요하면 safe wrapper/cron만 사용한다. 출력 필드는 `readiness`, `cohorts`, `exit_rule_quality`, `trailing_continuation`, `soft_stop_rebound`, `same_symbol_reentry`, `opportunity_cost`, `load_distribution_evidence`로 고정한다. `soft_stop_rebound` 하위에는 `hard_stop_auxiliary`를 포함해 휩쏘/하드스탑 보조축을 함께 잠근다. `+0.8% preset TP AI 1회 검문`은 동일 holding prompt를 쓰더라도 normal `ai_holding_review` 점수 refresh와 합치지 않고 익절 관찰축에서 별도 판정한다. | foreground direct builder 호출, `partial/full` 합산 결론, `initial/pyramid` 합산 결론, counterfactual 기회비용을 실현손익과 합산하면 판정 무효 |
| PREOPEN 판정 범위 | 장전에는 `restart.flag` 반영, 신규 계측 필드 기록 여부, 전일 carry-over snapshot/로그 존재 여부만 확인한다. 같은 거래일의 `submitted/fill/completed` 발생을 장전 통과조건으로 쓰지 않는다. | 장전 항목에 same-day `submitted/fill/completed`를 완료기준으로 넣으면 무효로 보고, `INTRADAY/POSTCLOSE` 판정으로 재배치한다. |
| canary ON/OFF 반영 | canary flag는 `TRADING_RULES` 생성 시 env/code에서 읽히므로 hot-reload 기준이 아니다. OFF/ON 변경은 env/code 반영 후 `restart.flag` 기반 우아한 봇 재시작이 표준이다 | rollback guard 발동 시 canary OFF 값을 먼저 고정하고 `restart.flag`로 재시작한다. 목표 소요시간은 5분 이내, 토큰/운영 승인 경계가 있으면 사용자 실행 명령을 남김 |
| Kiwoom REST 인증 장애 | `8005 Token이 유효하지 않습니다`처럼 런타임 토큰 무효화가 발생하면 실전 중 토큰 rebind/hot-refresh를 시도하지 않고, `restart.flag` 기반 우아한 봇 재시작만 표준 복구 경로로 쓴다. | 주문가능금액 0원 fail-closed 상태가 반복되면 인증 장애로 분리하고 즉시 우아한 재시작을 수행한다. 장중 hot-patch/re-auth 실험은 canary 판정과 원인귀속을 깨므로 금지한다. |
| runtime env 증적 | canary 판정/재교정/롤백 전후에는 main bot PID의 `/proc/<pid>/environ`에서 핵심 `KORSTOCKSCAN_*` 값을 확인하고 checklist 또는 report에 남긴다. 최소 대상은 해당 축 enable flag, threshold/prompt split, runtime route다. | `/proc/<pid>/environ` 증적 없이 "env 혼선 없음"을 가정해 판정한 항목은 조건부로 취급하고, 다음 판정 전에 provenance 점검을 보강한다. |
| 운영 자동화 증적 분리 | cron/runbook/parquet/manifest/동기화 정상화는 운영 증적이다. 이는 튜닝 효과나 전략 승인 근거와 분리한다. | 운영 정상화 항목을 중심 문서의 active/open 판정으로 승격하지 않는다. 필요 시 `execution-delta`, audit/report 또는 별도 운영문서에만 남긴다. |
| 문서/동기화 | 문서 변경 후 parser 검증은 AI가 실행한다. GitHub Project / Google Calendar 동기화는 AI가 직접 실행하지 않고, 반드시 사용자가 수동 실행한다. | AI는 토큰/캘린더 자격증명 확인과 실제 Project/Calendar 동기화를 시도하지 않는다. 변경 후 사용자에게 실행 명령 `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar` 1개를 남긴다. |
| 환경 변경 | 패키지 설치/업그레이드/제거 전 사용자 승인 | 승인 전 대안 경로 사용 |

## 5. 완료 기준

| 항목 | 완료 기준 |
| --- | --- |
| 튜닝축 선정 | pain point, 실행과제, 정량 목표, rollback guard, 판정시각, 상태가 한 줄로 연결됨 |
| live canary | `N_min`, 주요 metric, rollback guard, OFF 조건, 판정시각이 문서와 로그에 고정됨 |
| 성과판정 | `COMPLETED + valid profit_rate`, full/partial 분리, blocker 분포, 체결품질이 함께 제시됨 |
| 보류/미착수 | 보류 사유, 기대값 영향, 표본충분성 또는 관측 누락 이유, 다음 판정시각 또는 폐기/코드정리 판정이 명시됨 |
| 런타임 안정화 후속 | same-day hotfix를 장기 과제로 넘길 때는 `재발건수`, `영향 경로`, `업스트림 source 후보`, `메인 코드베이스 최소 수정범위`, `다음 절대시각`이 함께 남음 |
| 장후/익일 이관 | `same-day 불가 이유`, `추가 데이터 vs 코드수정` 구분, `단일 조작점`, `rollback guard`, `restart 가능 여부`, `다음 절대시각`이 한 묶음으로 남음 |
| 판정 근거 | 수치, 기준선 비교, why(왜 그 수치가 유지/보류/미완/폐기로 이어지는지)가 한 묶음으로 남음 |
| 폐기 | 재개 조건이 없으면 폐기 문서/부속문서로 내리고 중심 문서에는 요약만 유지 |
| 하위 참조 | 일일 체크리스트, 감사보고서, Q&A, 폐기과제가 역할별로 분리됨 |
| 실제 효과 갱신 | 일일 체크리스트 완료 시 `execution-delta`의 날짜형 효과 기록 또는 audit/report를 같은 턴에 갱신함 |

## 6. 정량 목표와 가드

`latency_quote_fresh_composite`의 기준선과 도달목표는 아래처럼 잠근다.

- 5-parameter bundle rule: `signal/ws_age/ws_jitter/spread/quote_stale` 5개는 묶음 단위로만 ON/OFF하고, 묶음 효과만 판정한다. `ws_age만 유지` 같은 부분 적용은 단일축 원칙 위반으로 금지한다.
- primary baseline: 같은 bundle 안의 `quote_fresh_composite_canary_applied=False`, `normal_only`, `post_fallback_deprecation` 표본
- fallback reference baseline: `2026-04-27 15:00` offline bundle (`budget_pass=7568`, `submitted=11`, `budget_pass_to_submitted_rate=0.1%`, `latency_state_danger=7178`, `full_fill=7`, `partial_fill=0`)
- `ShadowDiff0428`: submitted/full/partial 집계의 live runtime 경로와 offline bundle 경로 간 차이가 `1건 이내`로 좁혀진 상태를 뜻한다.
- hard pass/fail preconditions: `submitted_orders >= 20`, baseline 표본이 `N_min` 이상, `ShadowDiff0428` 해소
- direction-only gate: primary baseline 표본 부족, `submitted_orders < 20`, 또는 shadow diff 미해소 시 방향성 판정으로만 유지/종료를 닫음
- direction-only expiry: direction-only 판정은 발생일로부터 `2영업일 이내` 재판정 필수이며, 미재판정 시 canary를 자동 OFF 한다.

| 지표 | 목표/발동 조건 | 적용축 | 조치 |
| --- | --- | --- | --- |
| `N_min` | 판정 시점 `trade_count < 50`이고 `submitted_orders < 20` | 모든 canary | hard pass/fail 금지, 방향성 판정 |
| `entry_hard_pass_fail_prereq` | `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소 | `latency_quote_fresh_composite` | 전제 충족 시에만 hard pass/fail 허용 |
| `entry_composite_baseline` | 같은 bundle 내 `quote_fresh_composite_canary_applied=False`, `normal_only`, `post_fallback_deprecation` 표본 확보. `ShadowDiff0428` 미해소 시 hard baseline 승격 금지 | `latency_quote_fresh_composite` | baseline 부족/오염 시 direction-only 판정 |
| `entry_arrival_primary` | `budget_pass_to_submitted_rate >= baseline + 1.0%p` | `latency_quote_fresh_composite` | keep 또는 expand 검토 |
| `entry_arrival_secondary` | `latency_state_danger / budget_pass` 비율이 baseline 대비 `-5.0%p` 이상 개선 | `latency_quote_fresh_composite` | 기대값 개선 후보로 승격 검토 |
| `entry_fill_quality_non_worse` | `full_fill + partial_fill`의 `submitted` 대비 전환율이 baseline 대비 `-2.0%p` 이내 | `latency_quote_fresh_composite` | fill quality 비악화로 판정 |
| `loss_cap` | canary cohort 일간 합산 실현손익이 당일 스캘핑 배정 NAV 대비 `<= -0.35%` | live canary | canary OFF, 전일 설정 복귀 |
| `reject_rate` | `normal_only` baseline 대비 `+15.0%p` 이상 증가 | entry canary | canary OFF |
| `latency_p95` | `gatekeeper_eval_ms_p95 > 15,900ms`, 샘플 `>=50` | entry/latency | canary OFF, latency 경로 재점검 |
| `partial_fill_ratio` | baseline 대비 `+10.0%p` 이상 증가 | entry canary | 경고. `loss_cap` 또는 soft-stop 악화 동반 시 OFF |
| `fallback_regression` | `fallback_scout/main`(탐색/본 주문 동시 fallback) 또는 `fallback_single`(단일 fallback) 신규 1건 이상 | 전체 | 즉시 OFF, 회귀 조사 |
| `composite_no_recovery` | `latency_quote_fresh_composite` 적용 표본의 `budget_pass_to_submitted_rate`가 같은 bundle 내 `canary_applied=False` baseline 대비 `+1.0%p` 이상 개선하지 못함 | entry composite canary | canary OFF, 다음 독립축 또는 새 묶음축으로 교체 |
| `direction_only_expiry` | direction-only 판정 후 `2영업일` 내 재판정 미실시 | `latency_quote_fresh_composite` | canary 자동 OFF, 새 판정창 재개 전 재승인 필요 |
| `trailing_exit_rollback` | trailing canary cohort `avg_profit_rate <= 0`, soft_stop 전환율 baseline 대비 `+5.0%p`, 또는 GOOD_EXIT rate 추가 악화 `+15.0%p` 중 하나 충족 | 보유/청산 canary | canary OFF, 전일 설정 복귀 |
| `buy_drought_persist` | canary 후에도 BUY count가 baseline 하위 3분위수 미만이고 `blocked_ai_score_share` 개선 없음 | `buy_recovery_canary` | canary 유지 금지, score/prompt 재교정 |
| `recovery_false_positive_rate` | canary로 회복된 BUY 중 soft_stop 비율이 `normal_only` baseline 대비 `+5.0%p` 이상 증가 | `buy_recovery_canary` | canary OFF, score/prompt 재교정 |
| `initial_entry_qty_cap` | prompt 재교정 이후 신규 BUY 변동성이 커질 때 스캘핑 초기 진입 수량을 제한하는 운영가드 | entry/holding/exit 관찰 기간 | `2026-04-30` 장후 사용자 지시로 최대매수가능 주수는 `1주 cap`으로 회귀한다. 초기 진입 risk tail과 holding/exit 원인귀속 보존을 우선하고, `PYRAMID zero_qty`는 별도 관찰축으로 분리한다 |
| `reversal_add_loss_cap` | `REVERSAL_ADD` 체결 cohort의 당일 `COMPLETED + valid profit_rate` 평균이 `<= -0.30%`, 또는 `reversal_add_used` 후 soft stop 전환율이 baseline 대비 `+5.0%p` 이상 | `valid_entry_reversal_add` | canary OFF, `bad_entry_block` 관찰만 유지 |
| `soft_stop_expert_defense_loss_cap` | guarded cohort의 `COMPLETED + valid profit_rate` 평균이 `<= -0.30%`, guarded 후 hard/protect stop 전이, `sell_order_failed`, 또는 `REVERSAL_ADD` 체결 포지션 적용 cross-contamination 1건 이상 | `soft_stop_expert_defense` | canary OFF, `soft_stop_micro_grace v1`만 유지하고 shadow/observe 로그는 계속 남김 |
| `bad_entry_block_promote_gate` | observe-only 표본 `>=10`에서 classifier 후보의 soft stop/하드스탑 전환율이 비후보 대비 `+10.0%p` 이상이고 missed winner 비율이 낮음 | `bad_entry_refined_canary` | 단순 block이 아니라 refined 조기정리 canary로만 승격하고, `GOOD_EXIT/MISSED_UPSIDE` would-have-been 증가 시 OFF |

## 7. 매매단계별 Open Pain Point

| 단계 | 현재 pain point | 기대값 영향 | 현재 owner / 다음 판정 |
| --- | --- | --- | --- |
| 진입 | BUY 후 제출 전 병목과 mechanical fallback score 표본 처리 | 제출 drought가 지속되면 보유/청산 개선 표본도 고갈된다 | `mechanical_momentum_latency_relief`는 [2026-04-30 checklist](./2026-04-30-stage2-todo-checklist.md) `MechanicalMomentumLatencyRelief0430-*`에서 반영/판정 완료. 현재는 신규 OPEN 작업이 아니라 운영 override ON 상태이며, [2026-05-04 checklist](./2026-05-04-stage2-todo-checklist.md) `RuntimeFlagInventory0504-Preopen`이 로드/상태 확인만 소유한다 |
| 진입가 | reference target이 실주문가/timeout을 과도하게 왜곡하는 문제와 submitted 직전 불량 호가 흐름 진입 | 미체결 기회비용과 불리한 추격진입이 동시에 생길 수 있다 | `dynamic_entry_price_resolver_p1`, `dynamic_entry_ai_price_canary_p2`는 [2026-05-04 checklist](./2026-05-04-stage2-todo-checklist.md)가 로드/health check를 소유한다. OFI/QI P2 내부 feature는 `OrderbookMicroP2Canary0504-Postclose`가 micro-enabled P2 cohort의 SKIP/fill/soft stop/missed upside를 판정하고, 5/6에 guard 분포/ingress를 재판정 |
| AI 엔진 | Gemini/DeepSeek/OpenAI 계약 안정화와 live enable 금지선 분산 | parse/contract drift가 생기면 BUY/WAIT/DROP, HOLD/TRIM/EXIT 분포가 바뀌어 원인귀속이 깨진다 | 4/29~4/30 acceptance는 완료. [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `AIEngineFlagOffBacklog0506`이 잔여 flag-off/backlog 재분류를 소유 |
| 보유/청산 | soft stop tail, never-green/AI fade, 조급한 전량청산 | 손실 축소보다 missed upside 회복과 bad-entry tail 절단의 순EV가 핵심이다 | `soft_stop_micro_grace`, `REVERSAL_ADD`, `bad_entry_refined_canary`, `holding_flow_override`를 분리. [2026-05-04 checklist](./2026-05-04-stage2-todo-checklist.md) `BadEntryRefinedCanary0504-*`, `HoldingFlowOverride0504-*`가 live health/장후 판정을 소유 |
| 포지션 증감 | `REVERSAL_ADD`와 `PYRAMID` 수량 산식이 고정비율 중심 | 유효 진입 회수와 winner size-up 기대값이 제한된다 | live 수량 변경 금지. [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `ReversalAddDynamicQty0506`, `PyramidDynamicQty0506`에서 observe-only `would_qty` 설계 |
| 의사결정 지원 | 가격대/거래량/시간대별 행동가중치와 AI decision matrix가 runtime 판단과 분리됨 | 청산/물타기/불타기 선택의 기회비용을 놓치면 기대값 개선축 선정이 늦어진다 | `statistical_action_weight`, `stat_action_decision_snapshot`, `holding_exit_decision_matrix`는 [2026-05-04 checklist](./2026-05-04-stage2-todo-checklist.md) `StatActionDecisionSnapshot0504-Preopen`, [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `StatActionWeight0506`, `StatActionMarkdown0506`, `StatActionAdvancedAxes0506`, `AIDecisionMatrix0506`, [2026-05-07 checklist](./2026-05-07-stage2-todo-checklist.md) `StatActionEligibleOutcome0507`, `AIDecisionMatrixShadow0507`, [2026-05-08 checklist](./2026-05-08-stage2-todo-checklist.md) `StatActionAdvancedContext0508`가 report-only/ADM ladder로 소유 |
| 스캐너/구조 | candidate/enrich/promote 경계, DB/WS 경계, state handler 단일 모듈 비대 | 좋은 후보를 놓치거나 WS 부하/부분 커밋으로 미진입 기회비용이 커질 수 있다 | [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `ScalpingScanner*`, `StateHandlers*`, `CodeDebt0506`이 설계/분해 순서를 소유 |
| 운영/데이터 | NaN, receipt binding, threshold collector IO, historical aggregation 품질 | 집계/truth 품질이 흔들리면 잘못된 승격/롤백이 발생한다 | [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `NaNCastGuard*`, `ExecutionReceiptsThreadSafety*`, `Threshold*`가 소유 |

## 8. 현재 Open 상태 요약

| 영역 | 현재 상태 | 체크리스트/소유 문서 | 누락 여부 |
| --- | --- | --- | --- |
| entry operating override | `mechanical_momentum_latency_relief` ON. 종료된 `latency_quote_fresh_composite`, `latency_signal_quality_quote_composite`, 단일 `other_danger/ws_jitter/spread` relief는 archive로 내림 | [2026-04-30 checklist](./2026-04-30-stage2-todo-checklist.md) `MechanicalMomentumLatencyRelief0430-*`, [closed archive](./archive/closed-observation-axes-2026-05-01.md) | 반영 완료. 재개는 새 workorder 필요 |
| entry price baseline/live | `dynamic_entry_price_resolver_p1` baseline 경로 + `dynamic_entry_ai_price_canary_p2` active canary. P2 실패는 P1로 fail-closed. OFI/QI orderbook micro는 P2 내부 입력으로만 쓰며 신규 standalone entry canary로 세지 않는다 | [2026-05-02 checklist](./2026-05-02-stage2-todo-checklist.md) `OrderbookMicroP2Canary0502-DesignApply`, [2026-05-04 checklist](./2026-05-04-stage2-todo-checklist.md) `DynamicEntryResolverP10504-*`, `DynamicEntryAIPriceCanary0504-*`, `OrderbookMicroP2Canary0504-Postclose`; [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `LatencyEntryPriceGuard*`, `PreSubmitGuard*`, `BuyPriceSchemaSplit*`, `DynamicEntryResolverIngress*` | OFI/QI P2 내부 feature 반영 완료, 5/4 장후 판정 예정 |
| entry data-quality gate | `ShadowDiff0428`는 historical fill 집계 품질 gate로 유지. TEST synthetic row 제외는 4/30에 닫힘 | [2026-04-28 checklist](./2026-04-28-stage2-todo-checklist.md) `ShadowDiff0428`, [2026-04-30 checklist](./2026-04-30-stage2-todo-checklist.md) `ShadowDiffSyntheticExclusion0430` | 반영 완료 |
| AI engine: Gemini | P0 JSON fast-path는 반영됨. P1 `system_instruction`, P1 deterministic JSON config, P2 schema registry는 flag-off 준비/관찰 승인이고 live enable 미승인 | [workorder_gemini_engine_review](./workorder_gemini_engine_review.md), [2026-04-29 Gemini spec](./2026-04-29-gemini-enable-acceptance-spec.md), [2026-04-30 checklist](./2026-04-30-stage2-todo-checklist.md) `GeminiSchemaIngress0430`, `GeminiSchemaContractCarry0430`; [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `AIEngineFlagOffBacklog0506` | 5/6 재점검 항목으로 보강 완료 |
| AI engine: DeepSeek | context-aware backoff/retry acceptance는 flag-off 관찰성 보강. gatekeeper structured-output, holding cache bucket, Tool Calling은 backlog 유지 | [2026-04-29 DeepSeek spec](./2026-04-29-deepseek-enable-acceptance-spec.md), [2026-04-30 checklist](./2026-04-30-stage2-todo-checklist.md) `DeepSeekRemoteAcceptance0430`, `DeepSeekAcceptanceCarry0430`, `DeepSeekInterfaceGap0430`; [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `AIEngineFlagOffBacklog0506` | 5/6 재점검 항목으로 보강 완료 |
| AI engine: OpenAI | schema/deterministic config/Responses WS는 flag-off parity/transport 관찰. live routing 승격 아님. `2026-05-02`에 provider routing은 유지하고 Tier 기본값만 `FAST=nano`, `REPORT=mini`, `DEEP=full`로 분리 | [2026-04-30 OpenAI spec](./2026-04-30-openai-enable-acceptance-spec.md), [2026-05-04 checklist](./2026-05-04-stage2-todo-checklist.md) `OpenAIParity0504-Preopen`, `OpenAIResponsesWS0504-*`; [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `AIEngineFlagOffBacklog0506` | 반영 완료, 5/6 통합 재점검으로 보강 |
| holding/exit live canary | `soft_stop_micro_grace`, `REVERSAL_ADD`, `bad_entry_refined_canary`가 현재 보유/청산 live owner다. `soft_stop_expert_defense v2`는 archive | [2026-05-04 checklist](./2026-05-04-stage2-todo-checklist.md) `BadEntryRefinedCanary0504-*`, [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `ReversalAddDynamicQty0506`, `PyramidDynamicQty0506`; [closed archive](./archive/closed-observation-axes-2026-05-01.md) | 반영 완료 |
| holding/overnight operating override | `holding_flow_override`는 튜닝 관찰축이 아니라 운영 override. hard/protect/order safety는 우회하지 않는다 | [2026-05-04 checklist](./2026-05-04-stage2-todo-checklist.md) `HoldingFlowOverride0504-*`, [2026-05-01 review](./2026-05-01-holding-flow-override-code-review-report.md) | 반영 완료 |
| threshold cycle / action weight | threshold compact collector, 장후 report, 다음 장전 manifest/apply, `statistical_action_weight`는 runtime mutation 전 단계다. 현재 live threshold 자동변경은 금지하고 `manifest_only`로 둔다 | [2026-05-01 checklist](./2026-05-01-stage2-todo-checklist.md) `ThresholdBootstrap0501-AM`, `StatActionMatrixReport0501-Maintenance`; [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `ThresholdCollectorIO0506`, `ThresholdOpsTransition0506`, `StatActionWeight0506`, `StatActionMarkdown0506`, `StatActionAdvancedAxes0506`; [2026-05-07 checklist](./2026-05-07-stage2-todo-checklist.md) `StatActionEligibleOutcome0507`; [2026-05-08 checklist](./2026-05-08-stage2-todo-checklist.md) `StatActionAdvancedContext0508` | 반영 완료 |
| holding/exit decision support | `stat_action_decision_snapshot`, `holding_exit_decision_matrix`는 report-only/observe-only. AI 반영은 `ADM-1 -> ADM-2 -> ADM-3 -> ADM-4 -> ADM-5` ladder | [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `AIDecisionMatrix0506`; [2026-05-07 checklist](./2026-05-07-stage2-todo-checklist.md) `AIDecisionMatrixShadow0507` | 반영 완료 |
| scanner/residual architecture | 스캐너 3단 분해, DB/WS 경계, source/gate/composite, state handler context/split은 설계/정리 단계 | [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `ScalpingScanner*`, `StateHandlers*`, `SwingTrailingPolicy0506`, `CodeDebt0506` | 반영 완료 |
| runtime stabilization | `nan_cast_guard_followup`, execution receipt binding/thread safety는 EV 판정 전제 품질축. threshold IO/ops는 위 `threshold cycle / action weight` 행에서 별도 관리 | [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `NaNCastGuard0506HolidayCarry`, `ExecutionReceiptsThreadSafety0506` | 반영 완료 |
| closed observation axes | fallback/split-entry, latency residual single-relief, `soft_stop_expert_defense v2`, Gemini/DeepSeek 종료 관찰 항목 등 | [closed archive](./archive/closed-observation-axes-2026-05-01.md) | 반영 완료 |

## 9. 델타/Q&A 라우팅

| 문서 | 무엇을 남기나 | 이 문서에서 뺀 이유 |
| --- | --- | --- |
| [execution-delta](./plan-korStockScanPerformanceOptimization.execution-delta.md) | 날짜형 과제 레지스터, 지나간 일정, same-day pivot, 효과 기록, 폐기/종료 이력 | rebase에 남기면 현재 원칙보다 과거 경과가 더 커져 active 판정이 흐려진다 |
| [qna](./plan-korStockScanPerformanceOptimization.qna.md) | baseline 해석, direction-only 규칙, 감리 확인 포인트, 반복 질의 | 규칙은 중요하지만 매번 중심 문서 본문에 장문 설명으로 둘 필요는 없다 |
| 날짜별 checklist | 특정 시각 작업, Due/Slot/TimeWindow, 완료/미완 상태 | 자동 파싱과 Project/Calendar 소유 문서는 checklist다 |
| audit/report | 외부 반출본, 세부 수치 근거, 감리 관점 해설 | rebase는 승인 기준만 남기고 수치 근거 전문은 분리한다 |
| [closed observation archive](./archive/closed-observation-axes-2026-05-01.md) | 종료/폐기/역사참조 관찰축, 재개 금지선 | 중심 문서에는 active/open 판단만 남기기 위함 |

## 10. 핵심 참조문서

| 문서 | 역할 |
| --- | --- |
| [2026-05-04-stage2-todo-checklist.md](./2026-05-04-stage2-todo-checklist.md) | 다음 KRX 운영일 장전/장중/장후 실행 작업항목 |
| [2026-05-06-stage2-todo-checklist.md](./2026-05-06-stage2-todo-checklist.md) | 휴장 이월 후속, 스캐너/threshold/AI 엔진/보유청산 잔여작업 |
| [2026-05-07-stage2-todo-checklist.md](./2026-05-07-stage2-todo-checklist.md) | `SAW-3`, `ADM-2` 후속 설계 |
| [2026-05-08-stage2-todo-checklist.md](./2026-05-08-stage2-todo-checklist.md) | `SAW-4~SAW-6` 체결품질/시장맥락/orderbook readiness |
| [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md) | 원안 대비 변경, 날짜형 이력, 종료된 축 기록 |
| [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md) | 반복 판단 기준과 감리 Q&A |
| [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md) | 정기 성과 기준선과 반복 성과값 |
| [workorder-shadow-canary-runtime-classification.md](./workorder-shadow-canary-runtime-classification.md) | shadow/canary/historical 분류와 코드베이스 정렬 기준 |
| [archive/closed-observation-axes-2026-05-01.md](./archive/closed-observation-axes-2026-05-01.md) | 종료된 관찰축 archive |
| [archive/](./archive/) | 폐기 과제, 과거 workorder, legacy shadow/fallback 경과 |
