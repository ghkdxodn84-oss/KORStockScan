# KORStockScan Plan Rebase 중심 문서

기준일: `2026-04-22 KST`  
역할: 현재 튜닝 원칙, 판정축, 정량 목표, active/open 상태만 고정하는 중심축 문서다.  
주의: 이 문서는 자동 파싱용 체크리스트를 소유하지 않는다. Project/Calendar 동기화 대상 작업항목은 날짜별 `stage2 todo checklist`가 소유한다.

---

## 1. 현재 판정

1. 현재 단계는 손실 억제형 미세조정이 아니라 `기대값/순이익 극대화`를 위한 `Plan Rebase`다.
2. 현재 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이다.
3. 현재 폐기 확정 축은 `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`다.
4. 현재 live 운용 원칙은 `동일 단계 내 1축 canary`다. 진입병목축과 보유/청산축은 서로 다른 단계이므로 양쪽 canary 동시 존재가 가능하지만, 같은 단계 안에서 canary 중복은 금지한다.
5. 현재 entry live 축은 `mechanical_momentum_latency_relief`다. `latency_quote_fresh_composite`는 `2026-04-29 08:29 KST` 기준 OFF + restart 반영까지 완료됐고, `latency_signal_quality_quote_composite`는 `2026-04-29 12:50 KST` 운영 override로 효과 미약 판정 후 OFF 했다. 같은 시각 제출 drought를 방치하지 않기 위해 `mechanical_momentum_latency_relief`를 same-day 1축 replacement로 ON 했다. 이 판정은 hard baseline 승격이 아니라 EV/거래수 회복 우선의 운영 override이며, 이후 성과판정은 새 restart 이후 cohort로 분리한다.
6. 현재 보유/청산 live 축은 `soft_stop_micro_grace`다. `gatekeeper_fast_reuse signature/window`는 same-day `종료된 보조 진단축`이며 active 후보가 아니다.
7. `2026-04-30`부터 soft stop 감소 접근은 단순 유예가 아니라 `valid_entry_reversal_add`와 `bad_entry_block` 가설로 분리한다. `REVERSAL_ADD`는 손실 초기 구간에서 저점 미갱신, AI 회복, 수급 재개가 같이 확인될 때 1주 floor까지 허용하는 소형 포지션 증감 canary이고, `bad_entry_block`은 never-green/AI fade 유형을 관찰만 하는 classifier다.

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
| `buy_recovery_canary` | Gemini `WAIT 65~79` 과밀 구간을 2차 재평가해 BUY 회복 여부를 보는 실전 1축 | 현재 유지축 |
| `entry_filter_quality` | 불량 진입을 줄이고 제출/체결 품질을 높이는 다음 정식 튜닝 후보 | `buy_recovery_canary` 1차 판정 후 재판정 |
| `latency_quote_fresh_composite` | `ws_age`, `ws_jitter`, `spread`, `other_danger`가 단일 사유가 아니라 quote freshness family로 겹쳐 제출을 막는 복합축 | `2026-04-29 08:29 KST` OFF + restart 완료. 현재 standby/off이며, `signal>=88`, `ws_age<=950ms`, `ws_jitter<=450ms`, `spread<=0.0075`, `quote_stale=False` 묶음은 historical/reference 축으로만 남긴다 |
| `latency_signal_quality_quote_composite` | `latency_quote_fresh_composite` 미회복 시 검토한 예비 복합축. quote freshness 완화폭을 넓히는 대신 `signal>=90`, `latest_strength>=110`, `buy_pressure_10t>=65`를 요구했다 | `2026-04-29 12:50 KST` 운영 override로 OFF. post-restart `budget_pass=972`, `submitted=0`, 후보 통과 0건으로 효과 미약 판정 |
| `mechanical_momentum_latency_relief` | AI score 50/70 같은 mechanical fallback 상태라도 `budget_pass` 이후 수급/강도와 quote freshness 조건이 충분하면 latency DANGER를 normal 주문으로 넘기는 entry replacement 축 | `2026-04-29 12:50 KST` 운영 override로 live ON. 조건은 `signal_score<=75`, `latest_strength>=110`, `buy_pressure_10t>=50`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False`이며, 성과는 post-restart cohort에서 `mechanical_momentum_relief_canary_applied`, `submitted/full/partial`, `COMPLETED + valid profit_rate`, `fallback_regression=0`로 분리한다 |
| `holding_exit_observation` | 보유/청산 후보를 saved snapshot, post-sell, pipeline event로 분해하는 리포트 축 | live canary가 아니라 관찰/후보 고정용. `partial/full`, `initial/pyramid` 합산 결론 금지 |
| `soft_stop_micro_grace_extend` | soft stop 최초 유예 20초가 너무 짧을 때 threshold 근처에서 1회 추가 유예하는 보조 파라미터 | standby/off. `soft_stop_micro_grace` 20초 축의 hard stop/동일종목 손실/미체결 비악화가 확인되고도 반등 포착이 부족할 때만 검토한다 |
| `valid_entry_reversal_add` | 진입 판단은 유효했지만 초반 눌림이 발생한 표본에서 저점 미갱신, AI 회복, 수급 재개가 확인될 때 평단을 낮추는 소형 추가매수 canary | `2026-04-30` 소형 canary. 기본 조건은 `REVERSAL_ADD_ENABLED=True`, `profit_rate -0.45%~-0.10%`, `held_sec 20~120`, `AI>=60`, bottom 대비 `+15pt` 또는 연속회복, 수급 3/4 충족, 1회만 허용 |
| `pyramid_dynamic_qty_observe` | 수익 중인 포지션의 `PYRAMID` 불타기 수량을 고정 50% 템플릿이 아니라 추세/수급/트레일링 여유 기반으로 재산정하는 후보 | standby/observe-only. 현재 `PYRAMID`는 유지하되 `initial-only`와 `pyramid-activated` 표본을 분리한다. 동적 수량화는 `REVERSAL_ADD`와 같은 날 live 변경하지 않고 `would_qty` counterfactual부터 설계한다 |
| `bad_entry_block` | soft stop으로 이어질 가능성이 큰 never-green/AI fade 유형을 진입 차단 후보로 분류하는 observe-only classifier | `2026-04-30` observe-only. `held_sec>=60`, `profit_rate<=-0.70%`, `peak_profit<=+0.20%`, `AI<=45`를 기본 anchor로 로깅하며 실전 차단은 하지 않는다 |
| `nan_cast_guard_followup` | 주문·체결·DB 복원 숫자 필드에 `NaN/inf`가 유입될 때 런타임 중단과 상태전이 실패를 막기 위한 숫자 정규화/업스트림 source 재분해 계획 | live canary 아님. 런타임 안정화/집계 품질 보강용 follow-up으로만 관리하고, 기대값 해석 입력은 재발건수·영향경로·미진입/미청산 기회비용 분해를 함께 남긴다 |
| `openai_transport_parity_flag_off` | OpenAI가 Gemini와 같은 endpoint schema registry/contract 기준을 공유하되, transport는 HTTP baseline과 WS shadow를 분리 관찰하는 acceptance 축 | `2026-04-30` 기준 flag-off observe-only. `response schema registry`, `deterministic JSON config`, `Responses WS transport`는 모두 rollback owner와 cohort를 잠근 뒤에만 다음 슬롯으로 넘긴다 |

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

## 4. 작업 규칙

| 규칙 | 기준 | 위반 시 처리 |
| --- | --- | --- |
| 동일 단계 단일 live canary | 단일 live canary 원칙은 동일 단계 안에서만 적용한다. 진입병목축과 보유/청산축은 별개 단계이므로 양측에 canary가 동시에 존재할 수 있다. | 동일 단계 안에서 동시 2축 live 금지. 같은 단계 안에서 교체가 필요하면 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서를 강제한다. |
| stage-disjoint 병렬 canary | 진입병목 canary와 보유/청산 canary는 조작점, 적용 시점, cohort tag, rollback guard가 완전히 분리되면 병렬 live가 가능하다. 이 경우 전체 성과 합산 판정은 금지하고 단계별로 분리 판정한다. | entry canary가 유입 cohort를 크게 바꿔 보유/청산 판정이 오염되거나 rollback guard가 공유되면 병렬 판정 무효. 해당 단계의 단일축 원칙으로 복귀한다. |
| shadow 금지 | 신규/보완축은 shadow 없이 canary-only | shadow 항목은 폐기 또는 코드정리로 격하 |
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
| 보유/청산 관찰 리포트 | `holding_exit_observation`은 saved monitor snapshots, `data/post_sell/*.jsonl`, `data/pipeline_events/*.jsonl*`만 입력으로 쓰고, fresh snapshot이 필요하면 safe wrapper/cron만 사용한다. 출력 필드는 `readiness`, `cohorts`, `exit_rule_quality`, `trailing_continuation`, `soft_stop_rebound`, `same_symbol_reentry`, `opportunity_cost`, `load_distribution_evidence`로 고정한다. `soft_stop_rebound` 하위에는 `hard_stop_auxiliary`를 포함해 휩쏘/하드스탑 보조축을 함께 잠근다. | foreground direct builder 호출, `partial/full` 합산 결론, `initial/pyramid` 합산 결론, counterfactual 기회비용을 실현손익과 합산하면 판정 무효 |
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
| `initial_entry_qty_cap` | prompt 재교정 이후 신규 BUY 변동성이 커질 때 스캘핑 초기 진입은 임시로 `2주` cap 적용 | entry/holding/exit 관찰 기간 | 초기 진입 risk tail은 제한하되 `buy_qty=1 -> pyramid zero_qty`로 추가매수가 사실상 막히는 왜곡은 줄이고, `PYRAMID`는 여전히 별도 축으로 분리 관찰 |
| `reversal_add_loss_cap` | `REVERSAL_ADD` 체결 cohort의 당일 `COMPLETED + valid profit_rate` 평균이 `<= -0.30%`, 또는 `reversal_add_used` 후 soft stop 전환율이 baseline 대비 `+5.0%p` 이상 | `valid_entry_reversal_add` | canary OFF, `bad_entry_block` 관찰만 유지 |
| `bad_entry_block_promote_gate` | observe-only 표본 `>=10`에서 classifier 후보의 soft stop/하드스탑 전환율이 비후보 대비 `+10.0%p` 이상이고 missed winner 비율이 낮음 | `bad_entry_block` | 다음 운영일에 live entry block 후보로만 승격 검토 |

## 7. 매매단계별 Pain Point

| 단계 | Pain point | 현재 증거 | 기대값 영향 | 우선 판정 |
| --- | --- | --- | --- | --- |
| 진입 | Gemini 전환 후 BUY drought, WAIT65~79 과밀 | 04-22 12시 기준 `WAIT65~79 total_candidates=121`, `recovery_check=21`, `promoted=0`, `submitted=0`, `blocked_ai_score=97건(80.2%)` | 미진입 기회비용 증가, 표본 고갈 | 현재 확정: `buy_recovery_canary` 유지, `prompt` 재교정 1축 적용 |
| 진입 | BUY 신호 자체 부재 시 전체 일정 지연 | `04-22` 종합 기준 `recovery_check=40`, `promoted=6`, `submitted=0`, `completed_trades=0`; BUY 후보가 없거나 너무 적으면 `entry_filter_quality`, `threshold`, HOLDING/EOD까지 모두 표본 부족으로 밀린다 | 후속 축 판정과 보유/청산 개선 일정이 기약 없이 밀림 | 대기 판정: `2026-04-23 INTRADAY BUY sufficiency checkpoint`, 부족 지속 시 same-day next-axis live 교체 |
| 진입 | BUY 후 제출 전 latency/budget 병목 | 04-27 `15:00` offline bundle 기준 `budget_pass=7568`, `submitted=11`, `budget_pass_to_submitted_rate=0.1%`, `latency_state_danger=7178`. 단일 `other_danger`, `ws_jitter`, `gatekeeper_fast_reuse`는 제출 회복 실패. | threshold 단일 완화만으로 거래 회복 불가. `ws_age/ws_jitter/spread/other_danger`가 quote freshness family로 겹치는 복합 병목 가능성이 가장 높다. | 현재 확정: `latency_quote_fresh_composite` active entry canary. primary baseline은 같은 bundle 내 `canary_applied=False` 표본, fallback reference는 `04-27 15:00 offline bundle`, hard pass/fail 전제는 `submitted_orders >= 20` + baseline `N_min` + `ShadowDiff0428` 해소다. 성공 목표는 `budget_pass_to_submitted_rate +1.0%p`, `latency_state_danger share -5.0%p`, fill quality `-2.0%p` 이내 비악화다 |
| 진입 | prompt 재교정 후 신규 BUY 급증 리스크 | prompt 보정 직후 제출/체결은 늘 수 있으나, soft stop tail이 함께 커질 수 있다 | holding/exit 튜닝 판정 전에 초기 진입 손실 tail이 퍼지면 원인귀속이 흐려진다 | 현재 확정: 스캘핑 신규 BUY는 임시 `2주 cap`, `PYRAMID`는 유지하되 분석/판정은 분리한다. `buy_qty=1`로 `template_qty=0`이 되는 zero_qty 왜곡은 줄이되, `initial-only`와 `pyramid-activated`는 계속 분리 해석한다 |
| 진입 | `shared` 호출 혼입 가능성 | 04-22 오전 실전 로그 `PROMPT_COUNTS={"scalping_shared":39,"scalping_buy_recovery_canary":19,"scalping_entry":357,"-":47}`, `SHARED_STAGE_COUNTS={"ai_cooldown_blocked":39}` | shared를 신규 행동 canary로 볼 근거는 없고, 원인귀속 보존을 위해 코드정리 대상으로만 유지 | 현재 확정: 종료, live canary 아님 |
| 보유 | 포지션 맥락 부족 | 보유 AI가 수익률/고점/보유시간을 직접 입력으로 받는지 미완. `2026-04-23` 덕산하이메탈(`077360`)은 `ID 3331`이 `10:11:09 KST` `scalp_trailing_take_profit`으로 `+0.67%` 완료된 뒤, `ID 3404`가 `10:39:13 KST` 더 높은 가격대에서 `entry_armed -> budget_pass`, `10:39:15 KST` `+매수` 접수로 다시 열렸다. 이어 `ID 3419`는 `12:00:24 KST` `17,520원` 3차 진입 후 `12:02:42 KST` `LOSS soft stop`으로 `-1.6%` 종료됐고, 사용자 관찰 기준으론 그 직후 가격이 다시 `17,520원` 위로 반등했다. | 트레일링 익절 직후 동일종목 고가 재진입과 soft stop 직후 V-shape 반등을 분리하지 못하면, upside를 너무 일찍 끊고 더 나쁜 가격으로 재진입한 뒤 저점 청산하는 이중 기대값 훼손이 반복될 수 있다. | 현재 확정: `position_context` 스키마 설계 유지 + trailing 익절 후 동일종목 재진입 사례와 `soft stop 직후 rebound` 사례를 HOLDING 재판정 입력에 포함 |
| 보유/청산 | 4월 trailing/soft_stop 관찰축 공백 | 4월 `COMPLETED + valid profit_rate` 225건, 실현손익 `-429,425원`, `partial_trade` 평균 `-0.347%`, `full_trade` 평균 `-0.013%`. post-fallback normal 표본은 11건, 전부 full fill, 평균 `-0.069%`. post-sell 4월 191건 중 `MISSED_UPSIDE 54`, `GOOD_EXIT 72`; `2026-04-24` 생성 리포트 기준 `scalp_soft_stop_pct completed_valid=53`, 평균 `-1.669%`, 실현손익 `-651,680원`, `scalp_trailing_take_profit completed_valid=54`, 평균 `+1.041%`, 실현손익 `+280,742원`. 4월 soft_stop post-sell 61건은 10분 내 매도가 재상회 57건(`93.4%`), +0.5% 이상 반등 43건(`70.5%`), +1.0% 이상 반등 23건(`37.7%`), 매수가 회복 16건(`26.2%`)이다. hard stop 계열은 `scalp_preset_hard_stop_pct` post-sell 28건(`MISSED_UPSIDE 4`, `GOOD_EXIT 8`, `NEUTRAL 16`)으로 보조 관찰에 둔다. 하방카운트/`scalp_ai_early_exit`는 2026-04-27 기준 폐기 완료된 historical-only 축이다. | soft_stop은 직접 손익 훼손 1순위이고, 휩쏘 가능성이 높다. trailing은 upside capture 개선 후보지만 월간 기준 live 우선순위가 낮다. 하드스탑은 severe-loss guard라 완화 우선순위를 낮춘다. submitted가 회복되면 `soft_stop_rebound/whipsaw_windows`, `hard_stop_auxiliary`, `same_symbol_reentry`, `trailing_continuation`, `EOD/NXT`를 독립 후보로 고정해야 한다. | 현재 확정: `soft_stop_rebound_split` 1순위, 단일 조작점은 `soft_stop micro grace`로 승인. `SCALP_SOFT_STOP_MICRO_GRACE_ENABLED=True`, `SEC=20`, `EMERGENCY_PCT=-2.0`을 적용하고 hard stop `-2.5%`는 유지한다. `trailing_continuation_micro_canary`는 2순위. `hard_stop_whipsaw_aux`는 parking. `gatekeeper_fast_reuse`, `other_danger`, `ws_jitter`는 same-day latency residual 평가축으로 종료했지만, 진입병목 자체는 미해소 상태로 둔다 |
| 청산 | EOD/NXT 및 exit_rule 혼선 | NXT 가능/불가능 종목의 EOD 판단 분리 필요 | 청산 원인별 기대값 개선 지점 불명확 | 현재 확정: 후순위 설계 |
| 포지션 증감 | 물타기/불타기/분할진입 축 혼재 | 불타기 수익 확대 관찰, fallback 오염 존재. `pyramid-activated`는 11건 평균 `+1.084%`로 힌트가 있고, soft stop은 10분 내 매도가 재상회가 높지만 매수가 회복은 일부에 그친다. 현재 스캘핑 `PYRAMID` 수량은 `buy_qty * 0.50` + 포지션 cap 구조라 추세 지속성/AI/수급/trailing 여유를 직접 반영하지 않는다. | 추가진입 기대값 판단 오염. 단순 soft stop 유예보다 유효 진입의 초반 눌림을 회수하는 쪽이 EV 개선 가설로 더 명확하지만, winner size-up인 `PYRAMID`도 EV 개선 여지가 커서 별도 observe-only 수량 산식이 필요하다. | 현재 확정: `2026-04-30` `valid_entry_reversal_add` 소형 canary + `bad_entry_block` observe-only classifier를 병행한다. `REVERSAL_ADD`는 1회, 소형 수량, 별도 rollback guard로 제한하고, `bad_entry_block`은 실전 차단 없이 유형 표본만 수집한다. `PYRAMID` 동적 수량화는 같은 단계 live 변경으로 보지 않고 다음 체크리스트에서 `would_qty` counterfactual 설계로만 연다 |
| 운영/데이터 | 리포트 basis 혼선 | 문서 파생값과 DB 실필드 혼용 위험 | 잘못된 승격/롤백 위험 | 현재 확정: DB 우선, 체크리스트 동기화 |

## 8. 현재 Open 상태 요약

| 영역 | 현재 상태 | 다음 판정/소유 문서 | 메모 |
| --- | --- | --- | --- |
| entry live canary | `mechanical_momentum_latency_relief` ON (`latency_quote_fresh_composite`, `latency_signal_quality_quote_composite` OFF 후 same-day replacement) | [2026-04-29 checklist](./2026-04-29-stage2-todo-checklist.md) `MechanicalMomentumLatencyRelief0429-Now` | 사용자 운영 override로 제출 drought 지속 방치 불허. hard baseline 승격은 보류하고 post-restart cohort를 별도 판정한다 |
| entry data-quality gate | `ShadowDiff0428` open | [2026-04-28 checklist](./2026-04-28-stage2-todo-checklist.md) `ShadowDiff0428` | submitted/full/partial mismatch가 닫혀야 hard pass/fail 가능 |
| holding/exit live canary | `soft_stop_micro_grace` active | 날짜별 checklist + holding audit/report | stage-disjoint 예외로 entry 축과 병렬 존재 가능 |
| holding/exit observation | `holding_exit_observation` 유지 | checklist + observation report | `soft_stop/trailing/same_symbol/EOD-NXT` 분해 입력 소유 |
| runtime stabilization follow-up | `nan_cast_guard_followup` open | [2026-05-06 checklist](./2026-05-06-stage2-todo-checklist.md) `NaNCastGuard0506HolidayCarry` | canary 아님. `2026-05-05` 어린이날 휴장 이월 후 메인 기준 최소 safe cast 범위와 upstream source 추적 계획만 잠금 |
| engine parity / transport observation | `openai_transport_parity_flag_off` observe-only | [2026-04-30-openai-enable-acceptance-spec.md](./2026-04-30-openai-enable-acceptance-spec.md), [2026-05-04-stage2-todo-checklist.md](./2026-05-04-stage2-todo-checklist.md) | Gemini/DeepSeek acceptance와 같은 문서 구조로 유지. live 라우팅 승격이 아니라 schema/transport provenance 잠금이 목적 |
| retired entry axes | `gatekeeper_fast_reuse`, `other_danger`, `ws_jitter`, `fallback/split-entry` closed | `execution-delta` + audit/report | historical-only. 재개는 새 workorder + rollback guard 필요 |

## 9. 델타/Q&A 라우팅

| 문서 | 무엇을 남기나 | 이 문서에서 뺀 이유 |
| --- | --- | --- |
| [execution-delta](./plan-korStockScanPerformanceOptimization.execution-delta.md) | 날짜형 과제 레지스터, 지나간 일정, same-day pivot, 효과 기록, 폐기/종료 이력 | rebase에 남기면 현재 원칙보다 과거 경과가 더 커져 active 판정이 흐려진다 |
| [qna](./plan-korStockScanPerformanceOptimization.qna.md) | baseline 해석, direction-only 규칙, 감리 확인 포인트, 반복 질의 | 규칙은 중요하지만 매번 중심 문서 본문에 장문 설명으로 둘 필요는 없다 |
| 날짜별 checklist | 특정 시각 작업, Due/Slot/TimeWindow, 완료/미완 상태 | 자동 파싱과 Project/Calendar 소유 문서는 checklist다 |
| audit/report | 외부 반출본, 세부 수치 근거, 감리 관점 해설 | rebase는 승인 기준만 남기고 수치 근거 전문은 분리한다 |

## 10. 핵심 참조문서

| 문서 | 역할 |
| --- | --- |
| [2026-04-28-stage2-todo-checklist.md](./2026-04-28-stage2-todo-checklist.md) | 현재 실행 작업항목, Due/Slot/TimeWindow, 자동 파싱 기준 |
| [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md) | 원안 대비 변경, 날짜형 이력, 종료된 축 기록 |
| [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md) | 반복 판단 기준과 감리 Q&A |
| [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md) | 정기 성과 기준선과 반복 성과값 |
| [workorder-shadow-canary-runtime-classification.md](./workorder-shadow-canary-runtime-classification.md) | shadow/canary/historical 분류와 코드베이스 정렬 기준 |
| [audit-reports/2026-04-28-entry-composite-auditor-export-brief.md](./audit-reports/2026-04-28-entry-composite-auditor-export-brief.md) | 외부 반출용 감리 핵심 4개 요약 |
| [archive/](./archive/) | 폐기 과제, 과거 workorder, legacy shadow/fallback 경과 |
