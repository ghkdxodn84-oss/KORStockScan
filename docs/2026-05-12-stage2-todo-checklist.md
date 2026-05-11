# 2026-05-12 Stage2 To-Do Checklist

## 오늘 목적

- 2026-05-11 postclose 자동화가 만든 threshold apply 후보와 OpenAI WS 유지 상태를 장전 산출물 기준으로 확인한다.
- 스윙 실주문, 스윙 숫자 floor, 스윙 scale-in real canary는 approval request가 없으므로 사용자 artifact 없이 열지 않는다.
- 2026-05-11 code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- OpenAI WS 확인은 transport/provenance 검증이며 threshold 값, 주문가/수량 guard, 스윙 dry-run guard를 변경하지 않는다.
- `actual_order_submitted=false`인 sim/probe 표본은 실주문 전환 근거가 아니라 EV/source-quality 입력이다. 실주문 전환은 별도 approval artifact와 checklist가 필요하다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 장전 체크리스트 (08:50~09:00)

- Runbook 운영 확인은 [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md) `장전 확인 절차`와 `build_codex_daily_workorder --slot PREOPEN`의 `PreopenAutomationHealthCheckYYYYMMDD` 블록을 기준으로 본다.

- [ ] `[ThresholdEnvAutoApplyPreopen0512] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-12`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: RuntimeStability`)
  - Source: [README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_threshold_cycle_preopen.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_preopen.sh), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 트리거: `2026-05-12 07:35` PREOPEN apply wrapper가 종료됐거나 `08:50 KST`까지 runtime env/apply plan source 여부를 확인해야 할 때 실행한다.
  - 판단 입력: 전일 `threshold_cycle_ev_2026-05-11.{json,md}`, `data/threshold_cycle/apply_plans/threshold_apply_2026-05-12.json`, `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-12.{env,json}`, `src/run_bot.sh`의 runtime env source 로그.
  - 필수 요건: apply mode `auto_bounded_live`, AI correction guard result, deterministic guard result, selected/blocked family, max step/bounds/sample window/safety/same-stage owner guard, generated env keys, `run_bot.sh` source log가 확인되어야 한다.
  - 판정 기준: `auto_bounded_live` guard를 통과한 family만 장전 runtime env로 반영됐는지 확인한다. blocked family는 `blocked_reason`, AI guard, same-stage owner conflict를 남기고 수동 env override를 하지 않는다.
  - 허용 결론: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나다. `partial_apply_with_blocked_families`는 selected env와 blocked reason이 모두 manifest에 있어야 한다.
  - 유지 가드: 장중 runtime threshold mutation은 계속 금지한다. 스윙 approval artifact가 없는 `approval_required` 요청은 env apply 대상이 아니다.

- [ ] `[OpenAIWSPreopenConfirm0512] OpenAI WS 유지 설정 및 entry_price provenance 다음 장전 확인` (`Due: 2026-05-12`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-11.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-11.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 실행 기준: `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`가 startup env에 유지되는지 확인한다.
  - entry_price 확인: 2026-05-11 canary 적용 3건은 있었지만 transport provenance가 누락됐으므로, 다음 영업일에는 `entry_ai_price_canary_*`의 `openai_endpoint_name=entry_price`, `openai_transport_mode=responses_ws`, fallback/fail-closed/latency provenance를 별도 확인한다.
  - 유지 가드: OpenAI WS 유지 확인은 provider transport 검증이며 threshold 값, 주문가/수량 guard, 스윙 dry-run guard를 변경하지 않는다.

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
