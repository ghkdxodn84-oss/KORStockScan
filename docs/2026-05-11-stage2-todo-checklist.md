# 2026-05-11 Stage2 To-Do Checklist

## 오늘 목적

- threshold-cycle은 장전 수동 승인 없이 `auto_bounded_live`로 무인 반영한다.
- 장후에는 daily EV 성과 리포트만 제출 기준으로 보며, Gemini/Claude pattern lab 결과는 EV report 요약으로만 포함한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN cron의 runtime env 생성과 봇 기동 시 source로만 수행한다.
- 조건 미달은 rollback이 아니라 calibration trigger다. safety breach만 `safety_revert_required=true`로 분리한다.
- 장전 수동 enable/hold checklist를 만들지 않는다. postclose 제출물은 `threshold_cycle_ev_YYYY-MM-DD.{json,md}`로 통일하고, pattern lab 상세는 별도 artifact 링크로만 둔다.

## 장전 체크리스트 (08:50~09:00)

- 없음

## 장중 체크리스트 (09:00~15:20)

- 없음

## 장후 체크리스트 (16:00~17:00)

- [ ] `[ThresholdDailyEVReport0511] threshold-cycle 무인 반영 daily EV 성과 리포트 제출 확인` (`Due: 2026-05-11`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [README.md](/home/ubuntu/KORStockScan/data/threshold_cycle/README.md), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [threshold_cycle_ev_report.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_ev_report.py), [scalping_pattern_lab_automation.py](/home/ubuntu/KORStockScan/src/engine/scalping_pattern_lab_automation.py), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py)
  - 판정 기준: `data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-11.{json,md}`가 생성되고, selected family/runtime_change, completed/open, win/loss, avg profit rate, realized PnL, submitted funnel, holding/exit latency, calibration decisions, pattern lab automation freshness/consensus/order 요약이 포함되어야 한다.
  - 범위: 장전 수동 승인, 수동 enable/hold 판정, 별도 관찰축 추가는 하지 않는다. 오류가 있으면 daily EV report의 `warnings`와 cron log/status로만 후속 원인을 분리한다.
  - 다음 액션: EV report 생성 정상 시 제출 완료로 닫는다. 누락 시 wrapper/cron/status 보강만 진행하고 threshold runtime 값을 장중 수동 변경하지 않는다.
