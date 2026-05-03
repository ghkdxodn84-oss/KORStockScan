# Threshold Cycle Operations

작성 기준: `2026-05-03 KST`

이 디렉토리는 threshold 후보 수집, 장후 리포트, 장전 apply plan을 저장한다. 현재 원칙은 `manifest_only`이며, live runtime threshold 자동 변경은 `ThresholdOpsTransition0506` acceptance 전까지 금지한다.

## 운영 흐름

| 시점 | wrapper | 역할 | 산출물 |
|---|---|---|---|
| runtime | `src.utils.pipeline_event_logger` | threshold 후보 stage를 compact stream에 적재 | `threshold_events_YYYY-MM-DD.jsonl` |
| POSTCLOSE 16:10 | `deploy/run_threshold_cycle_postclose.sh` | raw pipeline event를 family partition으로 backfill하고 장후 report 생성 | `date=YYYY-MM-DD/family=*/part-*.jsonl`, `data/report/threshold_cycle_YYYY-MM-DD.json`, 파생 `statistical_action_weight`, `holding_exit_decision_matrix` JSON/MD |
| PREOPEN 07:35 | `deploy/run_threshold_cycle_preopen.sh` | 최신 threshold report를 읽어 apply plan 생성 | `apply_plans/threshold_apply_YYYY-MM-DD.json` |

## 현재 적용 정책

- `THRESHOLD_CYCLE_APPLY_MODE` 기본값은 `manifest_only`다.
- `threshold_cycle_preopen_apply`는 현재 `manifest_only`만 허용한다.
- apply plan은 운영자가 볼 수 있는 적용 후보/금지 사유/rollback context를 남기는 artifact이며, 봇 runtime threshold를 자동 mutate하지 않는다.
- live threshold 변경은 별도 workorder, sample floor, rollback owner, env/code 반영, restart 절차가 닫힌 경우에만 허용한다.

## 주요 경로

| 경로 | 의미 |
|---|---|
| `threshold_events_YYYY-MM-DD.jsonl` | runtime compact event stream |
| `date=YYYY-MM-DD/family=*/part-*.jsonl` | family별 report 입력 partition |
| `checkpoints/YYYY-MM-DD.json` | incremental backfill resume/checkpoint |
| `apply_plans/threshold_apply_YYYY-MM-DD.json` | 장전 apply plan artifact |
| `data/report/threshold_cycle_YYYY-MM-DD.json` | 장후 canonical threshold report |
| `data/report/statistical_action_weight/statistical_action_weight_YYYY-MM-DD.{json,md}` | action weight 파생 artifact |
| `data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_YYYY-MM-DD.{json,md}` | AI decision-support matrix 파생 artifact |

## 운영 판정 기준

1. `threshold_events`와 family partition은 canonical raw/compact data다. 사람이 읽는 판정은 `data/report/README.md`의 Markdown 생성 기준을 따른다.
2. `threshold_cycle_YYYY-MM-DD.json`은 top-level threshold 후보와 rollback guard를 담지만 현재 top-level Markdown은 없다. 운영자가 매일 직접 판정해야 하는 항목이면 `data/report/README.md`의 누락 후보로 승격하고 날짜별 checklist에 Markdown 생성 작업계획을 만든다.
3. `statistical_action_weight`와 `holding_exit_decision_matrix`는 report-only/decision-support artifact다. 자체 결과만으로 runtime 주문/청산 threshold를 변경하지 않는다.
4. IO guard 또는 availability guard로 backfill이 중단되면 같은 날 무리하게 full rebuild를 반복하지 않고 checkpoint, raw file size, paused reason을 report/checklist에 남긴다.
5. PREOPEN에는 전일 POSTCLOSE에서 생성된 report/apply plan 존재 여부와 `manifest_only` 상태만 확인한다. 같은 날 성과를 장전 통과조건으로 쓰지 않는다.

## 금지 사항

- `ThresholdOpsTransition0506` acceptance 전 live threshold auto-apply 금지.
- `manifest_only`가 아닌 apply mode를 임의 추가/사용 금지.
- family별 sample floor, rollback guard, owner 없이 threshold를 runtime에 반영 금지.
- raw JSONL을 사람이 직접 해석해 승격/롤백 판정을 닫는 것 금지. 필요한 경우 Markdown/report artifact를 먼저 만든다.
