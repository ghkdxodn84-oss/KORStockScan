# 2026-04-27 Stage 2 To-Do Checklist

## 오늘 목적

- `2026-04-24` 장중에 잠근 `quote_fresh family` 이후 다음 독립축을 `gatekeeper_fast_reuse signature/window`로 고정하고 PREOPEN 승인/보류를 닫는다.
- PREOPEN에서는 live 승인 전에 `fallback 비결합`, `단일 live 1축`, `restart.flag` 반영 순서를 먼저 점검한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 `1축 canary`만 허용하고, replacement도 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
- 관찰창이 끝나면 `즉시 판정 -> 다음 축 즉시 착수`를 기본으로 한다. 이미 수집된 데이터로 닫을 수 있는 판정은 장후/익일로 미루지 않는다.
- `장후/익일/다음 장전` 이관은 예외사유 4종(`단일 조작점 미정`, `rollback guard 미문서화`, `restart/code-load 불가`, `운영 경계상 same-day 반영 불가`) 중 하나로만 허용한다. 막힌 조건과 다음 절대시각이 없으면 이관 판정은 무효다.
- PREOPEN은 전일에 이미 `단일 조작점 + rollback guard + 코드/테스트 + restart 절차`가 준비된 carry-over 축만 받는다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- `ApplyTarget`은 문서에 명시된 값만 사용하고, parser/workorder가 `remote`를 추정하지 않도록 유지한다.
- 다축 동시 변경 금지, 승인 전 `main` 실주문 변경 금지 규칙을 유지한다.

## 장전 체크리스트 (08:20~)

- [ ] `[LatencyOps0427] gatekeeper_fast_reuse signature/window 독립축 PREOPEN 승인 판정` (`Due: 2026-04-27`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:35`, `Track: ScalpingLogic`)
  - Source: [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)
  - 판정 기준: `reuse window expired`와 `signature changed`를 분리하는 단일 조작점 1개와 rollback guard를 먼저 고정하고, `fallback 비결합`, `단일 live 1축`, `restart.flag` 반영 순서가 준비됐을 때만 live 승인/보류를 닫는다.
  - why: `2026-04-24 14:00 KST` 기준 `quote_fresh family`는 `submitted=0`, `quote_fresh_latency_pass_rate=0.0%`로 잠겼고, next independent axis는 `gatekeeper_fast_reuse signature/window`로만 남았다.
  - 다음 액션: 승인되면 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서로 PREOPEN 반영하고, 미승인이면 same-day `08:35 KST` 안에 막힌 이유 1개와 POSTCLOSE 재판정 시각 1개를 같이 고정한다.

## 장후 체크리스트 (18:05~18:20)

- [ ] `[OpsFollowup0427] pattern lab postclose 산출물/로그 보수 및 재실행 확인` (`Due: 2026-04-27`, `Slot: POSTCLOSE`, `TimeWindow: 18:05~18:20`, `Track: Plan`)
  - Source: [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)
  - 판정 기준: `deploy/run_tuning_monitoring_postclose.sh` 기준 실제 로그 경로를 `logs/tuning_monitoring_postclose_cron.log`로 통일해 확인하고, Gemini pattern lab의 `trade_id` dtype merge 오류를 해소한 뒤 `analysis/gemini_scalping_pattern_lab/outputs/*`, `analysis/claude_scalping_pattern_lab/outputs/*` 최신 산출물이 `2026-04-27 POSTCLOSE` 시각으로 갱신되어야 한다.
  - why: `2026-04-24` 점검에서 전용 cron log 두 개는 더 이상 생성되지 않았고, 통합 로그에는 Gemini 분석이 `trade_id str/float64 merge` 예외로 실패한 흔적이 남았다.
  - 다음 액션: 보수 완료 시 same-day 결과를 checklist와 execution delta에 함께 반영한다.
