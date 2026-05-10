KORStockScan 작업 기본 규칙:

## 1. 우선 참조

- 작업 시작 전 `docs/plan-korStockScanPerformanceOptimization.rebase.md` §1~§8과 당일 `docs/YYYY-MM-DD-stage2-todo-checklist.md` 상단 요약(`오늘 목적`, `오늘 강제 규칙`)을 먼저 읽는다.
- 튜닝 원칙, 판정축, 일정, rollback guard는 `Plan Rebase` 문서를 기준으로 삼고, 실행 작업항목은 날짜별 checklist가 소유한다.
- 현재 active/open 상태는 `Plan Rebase` §7~§8을 기준으로 읽되, 과거 checklist의 `[x]` 완료 항목은 현재 OPEN owner로 보지 않는다. 완료 항목은 증적/근거 링크이고, 현재 owner는 같은 행에 명시된 다음 checklist 또는 현재 runtime owner다.
- `docs/plan-korStockScanPerformanceOptimization.prompt.md`는 세션 진입용 경량 포인터다. 일반 작업마다 필수로 읽지 않고, 사용자가 명시적으로 요구했거나 Plan Rebase 위치, Source of Truth 문서 맵, 현재 실행표가 불명확할 때만 확인한다.

## 1.1 현재 상태 기준 (`2026-05-09 KST`)

- 현재 단계는 `Plan Rebase`이며, 목적은 손실 억제가 아니라 기대값/순이익 극대화다.
- 현재 entry owner는 `mechanical_momentum_latency_relief` 운영 override와 `dynamic_entry_price_resolver_p1`/`dynamic_entry_ai_price_canary_p2` 가격축이다.
  - `MechanicalMomentumLatencyRelief0430-*`는 반영/판정 완료 기록이다. `2026-05-06` 장중 submitted drought 대응 spread cap 완화는 두산 손실 guard 후 `0.0085`로 rollback됐으며, 다음 원인축은 mechanical cap이 아니라 `SAFE normal submit 직전 음수 수급/strength fade`와 `holding_flow_override defer cost` observe anchor로 분리한다.
  - `AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED=True`라 score 50 fallback/neutral은 mechanical relief로 내려보내지 않고 `blocked_ai_score` 매수보류로 처리한다.
  - `AI_SCORE65_74_RECOVERY_PROBE_ENABLED=False`는 5/6 장후 구현된 기본 OFF entry canary다. 기존 `buy_recovery_canary` 재개가 아니라 score65~74, latency DANGER 제외, 수급/가속/micro-VWAP gate, `score65_74_recovery_probe` cohort log로 분리하며 5/7 장전 판정 전 live enable하지 않는다. 5/9 후속 사용자 지시로 신규 BUY의 1주 수량 cap은 기본 ON으로 복귀했다.
  - `BUY Funnel Sentinel`은 장중 BUY/submitted 병목을 5/10/30분과 전 영업일 동시간대 기준으로 자동 감지·분류하는 report-only 운영 감시축이다. `2026-05-06`부터 `09:05~15:20 KST` 5분 cron으로 실행하며, `2026-05-08`부터 Telegram 알림 기능은 삭제됐다. `UPSTREAM_AI_THRESHOLD`, `LATENCY_DROUGHT`, `PRICE_GUARD_DROUGHT`, `RUNTIME_OPS`, `NORMAL` 분류와 권고 액션만 생성하며, score threshold/spread cap/fallback/live threshold/runtime restart를 자동 변경하지 않는다.
  - `latency_quote_fresh_composite`, `latency_signal_quality_quote_composite`, legacy `other_danger/ws_jitter/spread` relief, fallback/split-entry 계열은 종료/폐기 축이다. 재개하려면 새 workorder, 새 rollback guard, 새 checklist가 필요하다.
- `scalp_ai_buy_all_live_simulator`는 스캘핑 AI/Gatekeeper BUY 확정 지점에서 종목당 1개 sim 포지션을 기본 ON으로 생성하는 runtime-support 축이다. 브로커 매수/매도/추가매수 접수는 항상 차단하고 quote-based full-fill v1로 `scalp_sim_*` stage, `actual_order_submitted=false`, `calibration_authority=equal_weight`를 남긴다. open sim state는 `data/runtime/scalp_live_simulator_state.json`에 저장/복원하며 active sim target은 Kiwoom WS prune 대상에서 제외한다. threshold-cycle/daily EV는 `real`/`sim`/`combined`를 분리 표시하되 combined를 실매매 동급 튜닝 입력으로 사용한다.
- 현재 보유/청산 owner는 `soft_stop_micro_grace`, `REVERSAL_ADD`, `holding_flow_override`이며, 추가매수 주문 직전 경로는 `scale_in_price_resolver_p1` + `scale_in_dynamic_qty` live safety가 맡는다. `SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=False`는 5/6 장후 구현된 기본 OFF 보유/청산 canary이며, 단순 micro grace 연장이 아니라 base grace 종료 후 emergency/hard/protect 우선, 1회 confirmation cap, rebound/additional-worsen 로그를 별도 stage로 남긴다. 5/7 장전 판정 전 live enable하지 않는다. `HOLD/EXIT Sentinel`은 `2026-05-06`부터 `09:05~15:30 KST` 5분 cron으로 보유/청산 이상치를 자동 감지·분류하는 report-only 운영 감시축이며, `NORMAL`은 무음이고 Telegram 알림/자동 청산/threshold mutation은 수행하지 않는다. `bad_entry_refined_canary`는 `2026-05-04` 장후 rollback guard로 OFF됐고, `same_symbol_loss_reentry_cooldown`은 유안타증권 반복손실 대응 임시 운영가드이며, 단독 hard cooldown 고정이 아니라 5/6 `DowntrendReentryComposite0506`/`CooldownPolicyInventory0506`에서 복합 threshold 전환 여부를 본다. `soft_stop_expert_defense v2`는 종료했고, naive `bad_entry_block`은 observe-only 근거로만 본다.
  - `ScaleInPriceResolverP1_0506`/`ScaleInDynamicQty0506` 이후 SCALPING `AVG_DOWN`/`PYRAMID`는 `ws_data.curr` 그대로 지정가 제출하지 않고 `best_bid` 또는 defensive tick resolver 가격을 쓴다. 5/9 후속 사용자 지시로 추가매수 1주 수량 cap은 기본 ON으로 복귀했으며, 해제는 `position_sizing_cap_release` 자동화체인 기준 충족 시 사용자 승인 요청으로만 다룬다. P2 `scale_in_price_v1`은 observe-only이며 live 주문가/주문 여부를 바꾸지 않는다.
- `holding_flow_override`는 `2026-05-04` 장전부터 보유/청산 및 오버나이트 `SELL_TODAY` 후보를 재검문하는 운영 override다. hard stop/protect hard stop/주문·잔고 안전장치는 우회하지 않는다. `2026-05-04` 장후부터 오버나이트 flow `TRIM`은 `HOLD_OVERNIGHT` 승격이 아니라 원래 `SELL_TODAY` 유지로 본다.
- 스윙은 `SwingModelSelectionFunnelRepair0509` 이후 운영 추천 floor를 상승장 `0.35`/하락장 `0.40`으로 맞추고, fallback diagnostic 후보를 실전 추천 CSV/DB 후보와 분리한다. `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`가 기본이며, 스윙 `WATCHING -> gatekeeper -> market regime -> budget -> latency/price guard -> order request -> holding/exit` 로직은 그대로 실행하되 브로커 주문 접수만 차단한다. `swing_sim_*` stage와 `actual_order_submitted=false` provenance를 실제 `order_bundle_submitted`/`sell_order_sent`와 분리해 본다.
- 스윙 ML v2 재학습은 `auto_retrain_pipeline.sh`가 장후 진단, 상승장 특화모델 적용/기간 검토, staging 학습, 평가, artifact 승격/rollback을 수행한다. `bull_specialist_mode=disabled`여도 `bx/bl`은 `hx/hl`로 중립화해 `META_FEATURES` schema를 유지하며, 자동 승격은 모델 artifact 교체만 뜻하고 스윙 실주문 전환은 금지한다.
- 스윙 자가개선은 AI만이 아니라 `selection -> db_load -> entry -> holding -> scale_in -> exit -> attribution` 전체 lifecycle을 대상으로 한다. `swing_lifecycle_audit`, proposal-only `swing_threshold_ai_review`, `swing_improvement_automation`, `swing_runtime_approval`이 매 장후 생성되며, hard floor 통과 후 `overall_ev 45% + downside_tail 20% + participation/funnel 15% + regime_robustness 10% + attribution_quality 10%` trade-off score `>=0.68`이면 `approval_required` 요청만 만든다. 사용자가 별도 approval artifact를 남긴 경우에만 다음 장전 runtime env로 `approved_live` 반영하며, 이때도 `SWING_LIVE_ORDER_DRY_RUN_ENABLED=True`와 `actual_order_submitted=false`는 유지한다. `AVG_DOWN`, `PYRAMID`, exit OFI/QI smoothing, AI contract 변경은 approval request까지만 허용하고 live env apply는 별도 family guard 전까지 차단한다.
- `swing_one_share_real_canary`는 스윙 dry-run 해제가 아니라 broker execution 품질 수집용 별도 approval-required 축이다. phase0 기준은 `qty=1`, `max_new_entries_per_day=1`, `max_open_positions=3`, `max_total_notional_krw=300000`, same-symbol active 1개, AVG_DOWN/PYRAMID/scale-in 실주문 금지, 승인된 BUY와 해당 SELL만 실제 주문 허용이다. 시작은 `swing_runtime_approval` hard floor/EV trade-off 통과와 사용자 real-canary approval artifact가 모두 있어야 하며, 통과해도 스윙 전체 실주문 전환은 별도 2차 계획/승인 없이는 금지한다.
- `stat_action_decision_snapshot`, `statistical_action_weight`, `holding_exit_decision_matrix`는 report-only/observe-only다. runtime 판단 변경이나 AI live 반영은 ADM ladder 승인 전까지 금지한다.
- `System Error Detector`는 `2026-05-09` 구현된 운영 감시축이다. 6개 detector 중 4개는 report-only (runtime threshold/spread/주문/재시작 변경 금지), 2개는 filesystem maintenance mutation 허용 (stale lock cleanup, disk-low log rotate; 각 CLEANUP_ENABLED/ROTATE_ENABLED flag gated). `*/5 * * * *` cron + bot_main daemon으로 실행하며, `src/engine/error_detectors/`에 detector plugin 등록 시 자동 편입.
- `hard_time_stop_shadow`, `same_symbol_soft_stop_cooldown_shadow`, `partial_only_timeout_shadow`는 2026-05-04 runtime 기본 OFF로 정리했다. `ai_holding_fast_reuse_band`는 shadow가 아니라 HOLDING fast-reuse telemetry다.
- threshold cycle 자동화는 장중/장후 calibration, AI correction proposal, 다음 장전 `auto_bounded_live` runtime env apply, daily EV report까지 무인 loop로 관리한다. 장중 runtime threshold mutation은 금지하며, Sentinel/스윙 lifecycle 이상치는 `incident/playbook`, `threshold-family 후보`, `instrumentation gap`, `normal drift`로 먼저 분류하고 deterministic guard가 최종 threshold state/value를 결정한다.
- Gemini/DeepSeek/OpenAI 후속은 live routing 승격이 아니라 flag-off acceptance, endpoint schema contract, transport provenance로 분리한다. OpenAI runtime tier는 `FAST=gpt-5-nano`, `REPORT=gpt-5.4-mini`, `DEEP=gpt-5.4`이며, threshold AI correction은 runtime routing과 분리된 proposal layer로 `gpt-5.5 -> gpt-5.4 -> gpt-5.4-mini` fallback과 strict JSON schema를 쓴다. Gemini live enable과 OpenAI live routing은 별도 checklist 없이 열지 않는다.

## 1.2 AGENTS.md 일일 개정 절차

- AGENTS.md는 매일 작업 현황에 맞춰 갱신할 수 있는 `작업 지시 snapshot`이다. 단, 실행 작업항목의 원본 소유자는 항상 날짜별 checklist이고, 튜닝 원칙/active-open 판정의 원본은 `Plan Rebase`다.
- 장전 또는 작업 시작 시에는 `Plan Rebase` §1~§8과 당일 checklist 상단 요약을 읽고, AGENTS.md의 `현재 상태 기준` 날짜와 active owner 요약이 맞는지 확인한다.
- 장중/장후에 owner, live/observe/off 상태, rollback guard, 다음 판정 checklist가 바뀌면 먼저 `Plan Rebase` 또는 날짜별 checklist를 수정하고, 그 다음 AGENTS.md `1.1 현재 상태 기준`만 짧게 갱신한다.
- AGENTS.md에는 자동 파싱 대상 `- [ ]` 신규 작업항목을 만들지 않는다. 미래 작업, 특정 시각 작업, 재확인 작업은 날짜별 checklist에만 `Due`, `Slot`, `TimeWindow`, `Track`이 있는 체크박스로 남긴다.
- AGENTS.md에 과거 checklist ID를 링크할 때는 `완료 기록`, `현재 owner`, `다음 확인 owner`를 구분한다. `[x]` 완료 항목을 현재 OPEN owner처럼 쓰지 않는다.
- 매일 갱신 시 최소 확인 항목은 `entry owner`, `holding/exit owner`, `operating override`, `observe/report-only 축`, `OFF/폐기 축`, `Project/Calendar 동기화 규칙`이다.
- 문서 갱신 후에는 parser 검증을 실행한다. Project/Calendar 동기화는 AI가 직접 실행하지 않고, 사용자에게 표준 동기화 명령 1개만 남긴다.

## 2. 판정 원칙

- 목표는 손실 억제가 아니라 기대값/순이익 극대화다.
- `Plan Rebase` 기간 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이다.
- 실전 변경은 동일 단계 내 1축 canary만 허용한다. 진입병목축과 보유/청산축처럼 단계, 조작점, 적용시점, cohort tag, rollback guard가 분리되면 stage-disjoint concurrent canary로 병렬 검토할 수 있다.
- 신규/보완 alpha 튜닝축은 shadow 없이 `canary-only`로 본다. 단, AI transport/schema, statistical action weight, decision matrix처럼 문서에 observe/report-only로 명시된 운영/지원축은 실전 주문·청산 판단을 바꾸지 않는다.
- 원격/server 비교값은 Plan Rebase 의사결정 입력에서 제외한다.
- 손익은 `COMPLETED + valid profit_rate`만 사용한다. `NULL`, 미완료, fallback 정규화 값은 손익 기준에서 제외한다.
- 비교는 손익 파생값보다 거래수, 퍼널, blocker 분포, 체결 품질을 우선 본다.
- BUY 후 미진입은 `latency guard miss`, `liquidity gate miss`, `AI threshold miss`, `overbought gate miss`로 분리한다.
- `full fill`과 `partial fill`은 합치지 않는다.
- 원인 귀속이 불명확하면 리포트 정합성, 이벤트 복원, 집계 품질부터 점검한다.
- 운영 자동화 증적(cron/runbook/manifest/report/parser 정상화)은 전략 효과나 live 승인 근거와 분리한다.
- 답변은 가능하면 `판정 -> 근거 -> 다음 액션` 순서로 정리한다.

## 3. 문서/자동화

- 관련 문서가 있으면 함께 업데이트한다.
- 날짜별 checklist 상단은 매번 장문의 `목적/용어 범례/운영 규칙` 반복본을 복제하지 말고, `오늘 목적`과 `오늘 강제 규칙`만 짧게 적는다. 상세 용어/정책/가드는 `Plan Rebase` 또는 관련 부속문서를 참조한다.
- 개인문서(`docs/personal-decision-flow-notes.md`)는 다른 문서의 `Source`/판정 근거 링크로 참조되지 않는다.  
  즉, 개인문서는 보조 메모 성격으로 유지하고, 실행 판정의 근거는 checklist/report/plan 기준문서에서 직접 가져온다.
- 미래 작업, 특정 시각 작업, 재확인 작업은 답변에만 남기지 말고 날짜별 checklist에 자동 파싱 가능한 `- [ ]` 항목으로 기록한다.
- checklist 작업항목을 만들거나 수정했으면 parser 검증을 수행하고, Project/Calendar 동기화는 토큰 존재 여부를 확인하지 말고 사용자에게 실행할 1개 명령을 남긴다.
- 문서 변경 후 parser 검증은 AI가 실행한다. GitHub Project / Google Calendar 동기화는 AI가 직접 실행하지 않고, 사용자가 수동 실행한다.
- 사용자에게 남길 동기화 명령은 아래 1개로 통일한다.
  - `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar`
- 자동화 규칙, cron, workflow, wrapper를 바꾸면 운영문서와 checklist를 같은 변경 세트로 맞춘다.

## 4. 실행 환경

- Python 작업은 프로젝트 `.venv`를 기본으로 사용한다.
- 패키지 설치/업그레이드/제거 전에는 사용자 의사결정을 받는다.
- 임시 스크립트보다 재현 가능한 명령과 프로젝트 표준 실행 경로를 우선한다.
