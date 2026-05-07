# Postclose Decision Support Follow-up 2026-05-07

## 판정

- `StatActionEligibleOutcome0507`: report-only 구현 완료로 판정한다. `statistical_action_weight` JSON/Markdown에 `eligible_but_not_chosen` 섹션을 추가했고, `post_sell_evaluation` 10분 MFE/MAE proxy를 record_id로 붙였다. live 주문/청산 판단 변경은 없다.
- `AIDecisionMatrixShadow0507`: shadow naming은 stale다. 5/7 장후 `holding_exit_matrix_runtime.py`와 provider 3종 parity patch로 loader/runtime flag/cache-key 분리/provenance logging은 구현했다. baseline/candidate/excluded cohort도 정의했지만 `HOLDING_EXIT_MATRIX_ADVISORY_ENABLED`는 기본 OFF다. 5/7 matrix는 `holding_exit_decision_matrix_v1_2026-05-07`, `entries=14`, `runtime_change=false`, `valid_for_date=next_preopen`이며 entry 대부분이 `no_clear_edge`라 same-day live AI 응답 변경 근거는 여전히 약하다.
- `PrecloseSellTargetAITelegram0507`: AI 재수행은 성공했고 실제 Telegram 전송도 실행했다. key1은 Gemini 503 `UNAVAILABLE`이었고 key2 fallback으로 JSON schema parse와 canonical artifact 생성이 통과했다.
- `PrecloseSellTargetCron0507`: wrapper 안전장치 보강 후 `15:00` cron 등록까지 반영했다. lock, log path, status manifest, venv guard, weekend/holiday guard를 유지한 채 report-only 생성/전송만 자동화한다.
- `PrecloseSellTargetConsumer0507`: consumer 범위는 `operator_preclose_review`까지만 승인한다. JSON의 future consumers는 후보로 유지하되 threshold/ADM/swing trailing 자동 소비는 별도 owner 전까지 금지한다.

## 근거

- `data/report/statistical_action_weight/statistical_action_weight_2026-05-07.json`: `completed_valid=47`, `compact_decision_snapshot=459`, `exit_only=40`, `avg_down_wait=1`, `pyramid_wait=6`, `weight_source_ready=false`, `runtime_change=false`. `eligible_but_not_chosen`은 `sample_snapshots=459`, `sample_candidates=465`, `post_sell_joined_candidates=465`다.
- `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_2026-05-07.json`: `application_mode=shadow_prompt_or_observe_only_until_owner_approval`, `runtime_change=false`, hard veto는 `emergency_or_hard_stop`, `active_sell_order_pending`, `invalid_feature`, `post_add_eval_exclusion`.
- `data/report/preclose_sell_target/preclose_sell_target_2026-05-07.json`: `automation_stage=R1_daily_report`, `policy_status=report_only`, `live_runtime_effect=false`, `track_a_holding_count=0`, `track_b_swing_count=10`, `ai_requested=true`, `ai_provider_status.status=success`, `key_name=GEMINI_API_KEY_2`, `sell_target_count=5`.
- `data/report/preclose_sell_target/status/preclose_sell_target_2026-05-07.status.json`: `status=succeeded`, `exit_code=0`, `runtime_change=false`, log/artifact path 기록.
- `crontab -l`: `0 15 * * 1-5 /home/ubuntu/KORStockScan/deploy/run_preclose_sell_target_report.sh $(TZ=Asia/Seoul date +\%F) --no-legacy-markdown ... # PRECLOSE_SELL_TARGET_1500` 등록.

## 다음 액션

- `SAW3EligibleOutcomeImplementation0508`: 5/7 선반영 완료. 다음 보강은 true 후행 quote join과 snapshot 중복 downsample 품질 개선으로 분리한다.
- `ADMCanaryLivePivot0508`: shadow가 아니라 advisory/live canary pivot readiness를 별도 owner로 판정한다. 현재 matrix는 `no_clear_edge` 비중이 높아 plumbing 구현과 live enable 판정을 분리한다.
- `ADMCanaryLivePivot0508`: readiness plumbing은 5/7 장후 선반영 완료로 닫혔다. 다음 유효 액션은 새 matrix에서 directional edge가 생기기 전까지 flag OFF baseline을 유지하고, `GOOD_EXIT/MISSED_UPSIDE/holding defer cost`가 닫힐 때만 별도 enable checklist를 여는 것이다.
- `PrecloseSellTargetAIRecovery0508`: key fallback 구현/재수행과 Telegram 실제 전송은 5/7 완료. 남은 open 범위는 consumer 연결뿐이다.
- `PrecloseSellTargetCronWrapper0508`: wrapper 보강과 cron 등록은 5/7 완료. cron은 report-only 생성/전송용으로만 유지한다.

## 금지선

- `statistical_action_weight`, `holding_exit_decision_matrix`, `preclose_sell_target` 산출물만으로 live threshold mutation, 자동 주문/매도, bot restart, AI live response 변경을 실행하지 않는다.
