# 2026-05-07 Stage2 To-Do Checklist

## 오늘 목적

- `statistical_action_weight` 2차 고급축 중 `SAW-3 eligible_but_not_chosen` 후행 성과 연결을 설계한다.
- 선택된 행동만 보는 selection bias를 줄이고, 물타기/불타기/청산 후보의 기회비용을 후행 MFE/MAE로 복원할 수 있는지 판정한다.
- AI 보유/청산 판단에 `holding_exit_decision_matrix`를 shadow prompt context로 주입할 수 있는지 확인한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- `statistical_action_weight`는 report-only/decision-support 축이며 직접 runtime threshold나 주문 행동을 바꾸지 않는다.
- `holding_exit_decision_matrix`는 장중 self-updating 금지다. 전일 장후 산정 matrix를 다음 장전 로드하고 장중에는 immutable context로만 쓴다.
- `AI decision matrix`는 `ADM-1 report-only -> ADM-2 shadow prompt -> ADM-3 advisory nudge -> ADM-4 weighted live -> ADM-5 policy gate` 순서로만 전환한다. 5/7의 허용 범위는 ADM-2 설계이며 live AI 응답 변경은 금지한다.
- 후행 성과 연결은 `COMPLETED + valid profit_rate`와 분리해 보고, full/partial fill은 합치지 않는다.
- raw full scan 반복은 금지하고 compact partition/checkpoint 경로만 사용한다.

## 장전 체크리스트 (08:50~09:00)

- 없음

## 장중 체크리스트 (09:00~15:20)

- 없음

## 장후 체크리스트 (16:00~17:00)

- [ ] `[StatActionEligibleOutcome0507] SAW-3 eligible-but-not-chosen 후행 MFE/MAE 연결 설계` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:30`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: `stat_action_decision_snapshot`의 `eligible_actions/rejected_actions/chosen_action`을 후행 quote/position outcome과 연결해 `post_decision_mfe`, `post_decision_mae`, `missed_upside`, `avoided_loss`를 계산할 수 있는지 확인한다. join key, time horizon, quote source, compact partition read cap, selection-bias caveat를 같이 잠근다.
  - why: 선택된 행동의 realized PnL만 보면 “하지 않은 물타기/불타기/청산”의 기대값을 복원할 수 없다. 이 축이 열려야 행동가중치가 단순 사후 평균이 아니라 기회비용까지 반영한다.
  - 다음 액션: 연결 가능하면 Markdown 리포트에 `eligible_but_not_chosen` 섹션을 추가하고, 불가능하면 누락 필드와 추가 snapshot 필드를 명시한다.

- [ ] `[AIDecisionMatrixShadow0507] ADM-2 holding/exit shadow prompt matrix 주입 설계` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~17:00`, `Track: AIPrompt`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py)
  - 판정 기준: `holding_exit_decision_matrix`를 `prompt_profile=holding/exit` 경로에 shadow-only context로 넣는 설계를 확정한다. 확인 항목은 token budget, cache key 영향, matrix_version provenance, Gemini/OpenAI/DeepSeek parity, `action_label/confidence/reason` drift 로그다. live AI 응답 변경은 금지한다.
  - ON/OFF 기준: `ADM-1 report-only`는 ON, `ADM-2 shadow prompt`는 이 항목에서 ON 후보로 설계, `ADM-3 advisory nudge`, `ADM-4 weighted live`, `ADM-5 policy gate`는 OFF 유지다. ADM-3 이상은 별도 checklist에서 `COMPLETED + valid profit_rate`, `GOOD_EXIT/MISSED_UPSIDE`, soft stop tail, 추가매수 기회비용의 비악화가 확인될 때만 연다.
  - why: threshold 산정 결과가 AI 보유/청산 판단에 쓰이려면 사람이 보는 리포트만으로는 부족하다. 다만 첫 단계는 AI 판단 변경이 아니라 동일 장면에서 matrix context가 응답을 어떻게 바꾸는지 shadow diff로 봐야 한다.
  - 다음 액션: shadow diff가 안정적이면 `ADM-3 observe-only nudge`로 넘어가고, 불안정하면 prompt_hint 표현/토큰 범위부터 줄인다.
