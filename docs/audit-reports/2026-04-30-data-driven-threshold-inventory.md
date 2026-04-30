# 2026-04-30 Data-Driven Threshold Inventory

작성시각: `2026-04-30 14:08 KST`  
범위: main-only, `2026-04-30` 실전 DB + `data/pipeline_events/pipeline_events_2026-04-30.jsonl`  
목적: 데이터 기반 threshold 산정이 가능한 파라미터를 `데이터량`, `산정 가능성`, `운영 전환 방식`으로 분리한다.

## 판정

- 데이터 기반 threshold 산정은 지금부터 바로 열 수 있다.
- 대상은 `REVERSAL_ADD`에 한정되지 않는다. entry gate, latency relief, soft stop, bad entry, pre-submit price guard, partial fill, trailing, position sizing까지 모두 후보군이다.
- 다만 모든 파라미터가 같은 수준으로 준비된 것은 아니다. `분포 산정`이 가능한 축과 `outcome 기반 EV 산정`이 가능한 축을 분리해야 한다.
- 운영 전환은 `실시간 자동변경`이 아니라 `매일 적재 -> 장후 산정 -> 다음 장전 적용` 구조로 고정한다.

## 현재 데이터량 요약

| 데이터 | 현재 표본 |
| --- | ---: |
| DB `COMPLETED + valid profit_rate` | `63`건 |
| DB 손실 거래 | `41`건 |
| `budget_pass` | `6,232`건 / unique `109` |
| `order_bundle_submitted` | `78`건 / unique `73` |
| `exit_signal/sell_order_sent/sell_completed` | 각 `66`건 / unique `66` |
| `strength_momentum_observed` | `153,335`건 / unique `231` |
| `strength_momentum_pass` | `3,726`건 / unique `177` |
| `blocked_strength_momentum` | `153,335`건 / unique `231` |
| `blocked_liquidity` | `2,339`건 / unique `81` |
| `blocked_ai_score` | `349`건 / unique `110` |
| `ai_cooldown_blocked` | `429`건 / unique `111` |
| `soft_stop_micro_grace` | `307`건 / unique `37` |
| `soft_stop_expert_shadow` | `59`건 / unique `12` |
| `soft_stop_absorption_probe` | `7`건 / unique `6` |
| `soft_stop_absorption_extend/recovered` | `1`건 / unique `1` |
| `bad_entry_block_observed` | `329`건 / unique `31` |
| `reversal_add_blocked_reason` | `1,735`건 / unique `65` |
| `reversal_add_candidate` | `22`건 / unique `8` |
| `scale_in_executed` | `7`건 / unique `7`, 전부 `PYRAMID`, `AVG_DOWN=0` |
| partial fill 관련 stage | `0`건 |
| post-sell feedback stage | `0`건 |

## IO 부하 판정 보정 (2026-04-30 POSTCLOSE)

- `data/pipeline_events/pipeline_events_2026-04-30.jsonl`은 장후 확인 시점 기준 약 `486MB`였고, `data/pipeline_events/` 전체는 약 `2.7GB`였다.
- `threshold_cycle_2026-04-30.json`은 `event_count_same_day=10,894`로 생성됐지만, 원천 raw 파일에는 blocker/관찰 이벤트가 훨씬 많아 항목별 반복 full scan은 스토리지 IO 부하를 크게 키운다.
- 오늘 장후 판정은 raw jsonl을 반복 스캔하지 않고, 가능한 한 single-pass 경량 집계와 기존 threshold cycle 산출물을 재사용했다.
- 운영 판정: threshold 수집 기능은 기대값 개선의 기반이지만, 장중/장후마다 raw full scan을 반복하면 시스템 가용성과 체결 truth 품질을 훼손한다. `2026-05-06` `[ThresholdCollectorIO0506]`에서 과부하가 초기 적재 1회성인지, 매 cycle 반복성인지 분리 판정한다.
- 후속 설계 후보: cursor 기반 증분 collector, stage 필터 사전집계, 일자/분 단위 partition, single-pass shared snapshot. 반복성 과부하로 확인되면 이 중 하나를 구현 항목으로 승격한다.

## Threshold Collector IO 구조개선 (2026-04-30 Night)

- 반복 raw full scan은 폐기한다. 운영 경로는 `1회 bootstrap -> daily incremental -> partitioned compact dataset -> 장후 threshold 산정 -> 다음 장전 적용`으로 고정한다.
- compact dataset은 `data/threshold_cycle/date=YYYY-MM-DD/family=<family>/part-000001.jsonl` 구조를 우선 사용하고, 기존 `threshold_events_YYYY-MM-DD.jsonl`은 호환 fallback으로만 남긴다.
- 파티션은 `date/family`뿐 아니라 라인수 상한을 둔다. 기본값은 input chunk `20,000` raw lines, output partition `25,000` compact lines이며, 라인 cap 도달 시 checkpoint를 남기고 다음 실행에서 이어간다.
- checkpoint는 `data/threshold_cycle/checkpoints/YYYY-MM-DD.json`에 source path/size/mtime, byte offset, raw line count, written count, partition state, completed, paused reason, system metric sample을 저장한다.
- source truncate 또는 mtime/size 불일치가 감지되면 자동 재개하지 않고 `stopped_source_changed`로 중단한다. 이 경우 overwrite 여부를 사람이 명시해야 한다.
- 시스템 가용성 측정은 기존 `src/engine/system_metric_sampler.py`를 사용한다. 각 chunk 전후 `cpu.iowait_pct`, `io.disk_read_mb_delta`, `memory.mem_available_mb`를 기록하고, 기본 guard는 `iowait_pct>=20`, `chunk read>=128MB`, `mem_available<512MB`다.
- checkpoint에는 다음 실행 권고값 `recommended_next_input_lines_per_chunk`도 남긴다. guard에 걸리면 현재 cap의 50%로 낮추고, iowait/read/memory가 안정적이면 기본 상한 안에서만 완만하게 늘린다.
- threshold report loader 우선순위는 `partitioned compact > legacy compact > small raw fallback`이다. raw fallback은 기존 `64MB` 이하에서만 허용하고, 초과 시 scan하지 않고 warning/meta만 남긴다.
- `2026-05-01` 오전 휴일 bootstrap은 실전 trading 작업이 아니라 maintenance 작업으로 분리한다. 첫 실행은 보수 line cap으로 시작해 system metric sample을 보고 다음 cap을 조정한다.

## Threshold 후보 분류

| 영역 | 파라미터/묶음 | 데이터량 | 현재 산정 가능성 | 해석 |
| --- | --- | ---: | --- | --- |
| Entry latency | `mechanical_momentum`의 `MAX_SIGNAL_SCORE`, `MIN_STRENGTH`, `MIN_BUY_PRESSURE`, `MAX_WS_AGE`, `MAX_WS_JITTER`, `MAX_SPREAD` | `budget_pass 6,232`, submitted `78` | 가능 | 제출 회복 threshold는 분포 기반 재산정 가능하다. outcome 연결은 completed `63`건이라 direction-only로 둔다. |
| Entry VPW | `SCALP_VPW_MIN_BASE`, `MIN_BUY_VALUE`, `MIN_BUY_RATIO`, `MIN_EXEC_BUY_RATIO`, `NET_BUY_QTY`, relax set | observed `153,335`, pass `3,726` | 가능 | 분포 표본은 충분하다. 다만 pass가 제출/체결/손익으로 이어졌는지 record-level join을 해야 EV 산정이 된다. |
| Entry liquidity | `MIN_SCALP_LIQUIDITY` | blocked `2,339` / unique `81` | 분포 가능, EV 제한 | 현재 blocked 표본은 많지만 미진입 outcome이 없으므로 완화 시 기대값은 submitted 후보와 결합해야 한다. |
| Entry AI score | `BUY_SCORE_THRESHOLD`, `entry_score_threshold`, cooldown threshold | blocked AI `349`, cooldown `429` | 가능 | AI threshold/cooldown 분포는 충분하다. 단, AI 완화는 entry live 축이므로 기존 canary와 분리해야 한다. |
| Pre-submit price guard | `SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS=80` | submitted `78`, `price_below_bid_bps` `234`, block `0` | 분포 가능, block outcome 부족 | 현재 p90이 약 `74.7bps`라 80bps anchor 검증은 가능하지만 실제 block 표본이 없어 하향/상향 효과는 장후 보수 판정이다. |
| Soft stop v1 | `SCALP_STOP=-1.5`, `MICRO_GRACE_SEC=20`, `EMERGENCY=-2.0` | micro grace `307` / unique `37`, soft stop exit unique `36` | 가능 | 오늘 손실 핵심축이라 threshold 산정 우선순위가 높다. `profit_rate`, `elapsed_sec`, `peak_profit`, 후행 exit가 연결된다. |
| Soft stop expert v2 | `ABSORPTION_MIN_SCORE`, `EXTENSION_SEC`, `MIN_BUY_PRESSURE`, `MIN_TICK_ACCEL`, `MIN_MICRO_VWAP_BP`, `MAX_TOP3_DEPTH_RATIO` | shadow `59` / unique `12`, probe `7` / unique `6`, extend `1` | 부분 가능 | shadow feature 분포는 가능하지만 live 유예 결과는 표본 부족이다. 장마감까지 유지 후 재집계한다. |
| Bad entry | `MIN_HOLD_SEC=60`, `MIN_LOSS=-0.70`, `MAX_PEAK=0.20`, `AI_LIMIT=45` | observed `329` / unique `31` | 가능 | 손실 flow 1순위와 직접 연결된다. live block 전 counterfactual threshold 산정이 가능하다. |
| REVERSAL_ADD | `PNL_MIN/MAX`, `MIN/MAX_HOLD`, `MIN_AI`, `AI_RECOVERY_DELTA`, supply 3/4, qty ratio | blocked `1,735` / unique `65`, candidate `22` / unique `8`, AVG_DOWN executed `0` | blocked cohort 기반 가능, realized EV 부족 | 현재 조건은 과도하게 좁다. 다만 first-fail 로그라 완화 후 다음 gate 통과 여부를 완전히 복원하려면 all-predicate logging이 필요하다. |
| PYRAMID | `PYRAMID_MIN_PROFIT`, `SIZE_RATIO`, `post_add_trailing_grace` | executed `7` | 부족 | 실제 체결은 있으나 표본이 작다. 오늘은 로직 오류 방지와 would_qty counterfactual만 가능하다. |
| Trailing | `SCALP_TRAILING_START_PCT`, drawdown/continuation 후보 | trailing exit unique `23` | 제한 가능 | 표본은 작지만 post-sell/continuation과 결합하면 장후 direction-only 가능하다. |
| Preset hard stop | `SCALP_PRESET_HARD_STOP_PCT`, grace/emergency | exit unique `3` | 부족 | 오늘 표본으로 threshold 재산정 금지. 안전가드로 유지한다. |
| Partial fill guard | `SCALP_PARTIAL_FILL_MIN_RATIO_*` | `0` | 불가 | 오늘 실전 표본 없음. historical 또는 다음 체결 발생 전까지 현행 유지. |
| Post-sell feedback | `MISSED_UPSIDE_MFE`, `GOOD_EXIT_MAE/CLOSE` | pipeline stage `0` | 오늘 데이터 불가 | 별도 post-sell 리포트/월간 표본으로만 가능하다. 오늘 pipeline 기준으로는 산정 불가. |

## 즉시 산정 우선순위

1. `bad_entry_block` threshold
   - 이유: 오늘 손실 flow 1순위가 `bad_entry/never-green`이고 observe 표본 `329`건/unique `31`이 있다.
   - 산정축: `MIN_HOLD_SEC`, `MIN_LOSS_PCT`, `MAX_PEAK_PROFIT_PCT`, `AI_SCORE_LIMIT`.

2. `REVERSAL_ADD` threshold
   - 이유: blocked 표본 `1,735`건/unique `65`가 있고 `AVG_DOWN=0`이라 현행 조건이 실제 체결을 거의 열지 못했다.
   - 산정축: `PNL_MIN`, `MAX_HOLD_SEC`, `MIN_AI_SCORE`, `AI_RECOVERY_DELTA`.
   - 주의: 현재 로그가 first-fail 방식이라 all-predicate counterfactual은 보강 필요.

3. `soft_stop_micro_grace` threshold
   - 이유: micro grace `307`건/unique `37`, soft stop exit unique `36`으로 당일 산정 가능한 최소 표본이 있다.
   - 산정축: `GRACE_SEC`, `EMERGENCY_PCT`, `soft stop touch 후 rebound/recovery`.

4. `entry mechanical/VPW/liquidity` threshold
   - 이유: 분포 표본은 가장 많다. 다만 같은 날 holding/exit canary와 섞이지 않게 entry stage 단독으로 산정한다.
   - 산정축: `ws_age`, `spread`, `latest_strength`, `buy_pressure`, VPW buy ratio/exec ratio, liquidity.

## 일일 Threshold 운영 사이클

실시간 자동변경 아이디어는 폐기한다. threshold는 장중에 흔들지 않고, 아래 일일 사이클로만 움직인다.

1. `장중 적재`
   - 실전 런타임은 고정 threshold만 사용한다.
   - 대신 모든 후보 축에 대해 `would_pass`, `would_block`, `would_add`, `would_exit`, 후행 `COMPLETED + valid profit_rate`, soft/hard/trailing 전환을 계속 적재한다.

2. `장후 산정`
   - `same-day`, `rolling 3d`, `rolling 7d`를 같이 본다.
   - 추천 threshold는 family별 최소 표본을 넘길 때만 산출한다.
   - 기본 최소 표본 anchor:
     - entry gate: submitted `>=50` 또는 budget_pass `>=500`
     - holding/exit: completed `>=30`
     - `REVERSAL_ADD`: candidate `>=20`
     - `bad_entry_block`: observed `>=30`

3. `bounded recommendation`
   - 추천값은 문서화된 상하한 안에서만 움직인다.
   - 예: `REVERSAL_ADD_MAX_HOLD_SEC=180~900`, `REVERSAL_ADD_PNL_MIN=-0.70~-1.30`, `SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS=60~120`, `SCALP_SOFT_STOP_MICRO_GRACE_SEC=10~60`.

4. `change governor`
   - 하루 변경폭 cap을 둔다.
   - 예: 시간 threshold는 일일 `+-60초`, 손익률 threshold는 일일 `+-0.15%p`, ratio/bps threshold는 일일 `+-10~15%` 또는 `+-10bps` 이내로 제한한다.

5. `다음 장전 적용`
   - 장후 추천값을 바로 live에 넣지 않는다.
   - 다음 장전 `PREOPEN`에서 `단일 owner`, `rollback guard`, `cohort tag`를 잠근 뒤 적용한다.
   - 같은 단계에서는 하루에 1축만 live owner가 된다.

6. `장중 고정`
   - 장중에는 추천값이 다시 계산돼도 적용하지 않는다.
   - 재계산 결과는 `shadow recommendation`으로만 남기고 다음 장후 판정 입력으로 넘긴다.

## 운영전환 필수 구현 조건

최종 안정화가 완료되어 threshold cycle을 운영 전환할 때는 아래 4개 조건을 모두 구현해야 한다. 하나라도 빠지면 수동 리포트/수동 적용 단계로 유지한다.

1. `매일 자동 실행`
   - 장중에는 compact threshold event 적재가 자동으로 계속되어야 한다.
   - 장후에는 partitioned compact dataset 기준 threshold 산정 배치가 자동 실행되어야 한다.
   - raw full scan은 bootstrap/복구성 작업으로만 허용하고, daily path에는 넣지 않는다.

2. `다음 장전 자동 적용 + 봇 기동`
   - 장후 산정 결과 중 승인된 `apply_candidate_list`만 다음 장전 `PREOPEN`에 적용한다.
   - 적용 전에는 `threshold_snapshot`, `change governor`, `rollback_guard_pack`, `single owner` 조건을 검사한다.
   - 적용 후 봇이 기동될 때 runtime config/env provenance에 `threshold_version`, `source_report`, `applied_family`, `current -> applied` diff가 남아야 한다.

3. `장후 매매실적 결과 분석 제출`
   - 매일 장후에는 당일 적용 threshold version별 매매실적 결과를 제출해야 한다.
   - 최소 분석 단위는 `COMPLETED + valid profit_rate`, 거래수, blocker 분포, submitted/full/partial, sell_completed, soft/hard/trailing exit, GOOD_EXIT/MISSED_UPSIDE, owner contamination 여부다.
   - threshold 변경이 없던 날도 baseline 유지 결과로 제출한다.

4. `실적 기반 다음 가중치 미세조정`
   - 장후 실적 결과는 다음 threshold 산정의 weight 입력으로 들어가야 한다.
   - weight는 실시간으로 바꾸지 않고 장후 배치에서만 갱신한다.
   - 같은 family 안에서도 손익만 보지 않고 opportunity cost, blocker 감소, 체결 품질, post-exit MFE/MAE를 같이 반영한다.
   - 단일축 canary 원칙을 깨지 않도록 최종 live 적용은 다음 장전 1축 owner로 제한한다.

## 일일 산정 산출물

장후 배치가 남겨야 할 산출물은 아래 4종으로 고정한다.

1. `threshold_snapshot`
   - family별 현행값, 추천값, 상하한, sample count, 적용 가능 여부

2. `threshold_diff_report`
   - `current -> recommended` 변화량, 변화 이유, 예상 blocker 감소/증가, 후행 손익 변화

3. `apply_candidate_list`
   - 다음 장전 live 후보 1축과 observe/shadow 유지축 분리

4. `rollback_guard_pack`
   - 신규 추천값 적용 시 감시할 `loss_cap`, `quality regression`, `cross-contamination`, `sample insufficiency` 조건

## Threshold Family별 적용 원칙

1. `entry`
   - `mechanical_momentum`, VPW, liquidity, AI threshold, pre-submit price guard는 같은 family로 묶지 않고 개별 owner로 본다.
   - 다음 장전에는 이 중 하나만 live 완화/강화 후보가 된다.

2. `holding/exit`
   - `soft_stop_micro_grace`, `soft_stop_expert_defense`, `bad_entry_block`, `REVERSAL_ADD`, trailing은 서로 outcome contamination이 크므로 동시 live 변경을 금지한다.

3. `position sizing`
   - `PYRAMID`, `AVG_DOWN`, `partial de-risk`는 수량/평단/후행 손익 계산을 바꾸므로 threshold family보다 한 단계 보수적으로 다룬다.
   - 표본이 충분해도 먼저 `would_qty`와 shadow PnL로만 본다.

## 로깅 보강 필요

- `REVERSAL_ADD`는 현재 first-fail reason만 남는다. 데이터 기반 완화값을 정확히 산정하려면 `pnl_ok`, `hold_ok`, `low_floor_ok`, `ai_ok`, `supply_ok`, 각 원시값을 한 이벤트에 모두 남겨야 한다.
- entry gate도 threshold별 `would_pass_at_candidate_threshold`를 남기면 장후 grid search가 빨라진다.
- soft stop 계열은 `touch_price`, `would_exit_price`, `max_rebound_10m`, `min_adverse_10m`가 연결되어야 grace/absorption threshold를 안정적으로 산정할 수 있다.
