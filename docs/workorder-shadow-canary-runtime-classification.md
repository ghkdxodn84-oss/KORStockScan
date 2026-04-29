# 작업지시서: Shadow/Canary 런타임 경로와 Live Cohort 분류 기준

작성일: `2026-04-25 KST`  
대상: KORStockScan 메인 코드베이스 운영/튜닝 문서 소유자  
ApplyTarget: `main` 문서/후속 코드정리 기준  

이 문서는 체크리스트/Project/Calendar 자동관리 대상이 아닌 독립 workorder다. 목적은 `shadow/canary` 경로를 일괄 삭제하는 것이 아니라, `지속 모니터링 가치`와 `운영/코드 부채`를 함께 평가해 각 경로를 `remove / observe-only / baseline-promote / active-canary` 중 하나로 고정하고, live 전환/병렬 관찰 시 섞이면 안 되는 `cohort`도 함께 분류 기준으로 잠그는 것이다.

현재 스냅샷:

1. entry live owner는 `mechanical_momentum_latency_relief`다. `latency_quote_fresh_composite`와 `latency_signal_quality_quote_composite`는 `observe-only/historical-reference`로 내린다.
2. 보유/청산 live owner는 `soft_stop_micro_grace`다. `soft_stop_rebound_split`은 1순위 관찰축이고, `trailing_continuation`은 2순위 후보로 유지한다.
3. `Gemini response schema registry`와 `DeepSeek retry acceptance snapshot`은 flag-off observability 묶음이다. live enable 또는 active canary가 아니다.
4. `AI cache hit/miss`는 영향도가 중간 이상일 수 있으나, 현재 structured join 필드가 부족해 `observe-only schema gap`으로 분류한다.
5. `Execution receipt binding`은 BUY/SELL 체결 truth 품질 이슈다. EV 판정 전제 품질축으로 보되, alpha canary로 분류하지 않는다.
6. `2026-05-01` 근로자의 날과 `2026-05-05` 어린이날은 KRX 휴장으로, 휴장일 Due 작업은 다음 운영일 체크리스트로 이관한다.

---

## 1. 배경

기준 문서:

1. [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md)
2. [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
3. [2026-04-24-stage2-todo-checklist.md](./2026-04-24-stage2-todo-checklist.md)

현재 기준은 아래로 고정한다.

1. `Plan Rebase`의 신규/보완축 운영 원칙은 `shadow 금지`, `canary-only`, `하루 1축 live`, `baseline 승격은 근거가 닫힌 뒤 별도 정리`다.
2. 그러나 코드베이스에는 여전히 `legacy shadow`, `observe-only shadow`, `이름은 canary지만 사실상 운영 기본값으로 굳은 축`, `여전히 실험 축인 canary`가 섞여 있다.
3. 따라서 다음 액션은 무조건 삭제가 아니라, 각 경로를 동일한 평가 축으로 분류하고 후속 코드 액션까지 닫는 것이다.
4. 이 문서는 실행 checklist가 아니라 `분류 기준`, `가치 평가 규칙`, `판정표`, `후속 코드정리 기준`을 소유한다.
5. 이미 적용된 `dual_persona/watch75 shadow` 런타임 가드는 현 상태의 일부로 간주한다. 이 문서는 그 상태를 포함해 해당 축을 `remove`로 닫을지, `observe-only`로 남길지를 공식 판정하는 기준 문서다.
6. 새 `shadow/canary` 경로를 추가하거나, 기존 항목의 분류를 `remove / observe-only / baseline-promote / active-canary` 중 다른 상태로 바꾸면 같은 change set에서 이 문서의 판정표도 함께 갱신해야 한다.
7. 장후 `POSTCLOSE` 분류/정리 항목은 same-day 변경 누락을 보정하는 daily review 용도이며, 생성/상태변경 시점의 문서 갱신 의무를 대체하지 않는다.
8. 조사 범위는 `src/utils/constants.py`의 운영 토글/상수와 `src/engine/`의 실런타임 분기, 이벤트 stage, shadow 기록, canary 적용 경로로 고정한다.
9. `src/web/`, `src/template/`의 CSS `box-shadow`, 공용 `analyze_target_shadow_prompt` capability, `S15 shadow record` 같은 execution bookkeeping은 `튜닝 shadow/canary 축`에서 제외한다.
10. `cohort tag`가 live 전환, stage-disjoint 예외, rollback 판정의 단위가 된 이상 `canary flag`만 정리하고 cohort를 방치하는 상태는 허용하지 않는다. live/observe/제외 코호트는 문서 기준으로 같이 잠가야 한다.

---

## 2. 평가 축

모든 항목은 아래 공통 축으로 평가한다.

| 평가축 | 설명 | 판정 기준 |
| --- | --- | --- |
| `live 영향도` | 현재 실주문/실판단 경로에 실제 영향이 있는지 | `none`, `guarded-off`, `limited-live`, `baseline-live` |
| `튜닝 모니터링 가치` | 이후 튜닝/rollback/후속 축 선택에 남길 가치 | `High`, `Medium`, `Low` |
| `EV 판정 기여도` | 기대값/순이익 판단에 직접 기여하는 정도 | `High`, `Medium`, `Low` |
| `대체 가능성` | 동일 정보가 다른 리포트/이벤트로 충분히 대체되는지 | `Low`, `Medium`, `High` |
| `운영 부하/지연 비용` | 런타임 비용, 추가 API, 지연, 관측 오염 가능성 | `Low`, `Medium`, `High` |
| `코드 유지비` | 상수, 분기, 리포트, 테스트를 유지하는 비용 | `Low`, `Medium`, `High` |
| `향후 재개 가능성` | 이후 재사용/재개할 현실적인 가능성 | `Low`, `Medium`, `High` |

`튜닝 모니터링 가치`는 아래 등급으로만 쓴다.

### `High`

1. 다른 지표로 대체되지 않고
2. 다음 canary 선택, rollback 판정, baseline 승격 판단에 직접 쓰이며
3. 운영 비용 대비 정보가치가 높다.

### `Medium`

1. 직접 판정에는 약하지만
2. 특정 failure mode 재현, 오염 탐지, 후보 검증에는 유효하다.

### `Low`

1. 이미 다른 리포트/이벤트로 충분히 대체 가능하거나
2. 현재 운영 원칙상 다시 사용할 가능성이 낮다.

각 판정은 반드시 아래 4개를 함께 남긴다.

1. `가치 등급`
2. `왜 그렇게 보는지`
3. `등급이 올라가는 조건`
4. `등급이 내려가는 조건`

최소 공통 해석 규칙은 아래로 고정한다.

1. `EV 판정 기여도`가 낮아도 `운영 오염 탐지` 가치가 높으면 `observe-only`는 가능하다.
2. `운영 부하/지연 비용`이 높고 `대체 가능성`도 높으면 `remove` 우선이다.
3. 현재 `True`인 canary라도 이미 baseline live로 해석 중이면 `baseline-promote` 후보로 본다.
4. `baseline-promote`는 즉시 rename이 아니라, `현재는 baseline처럼 쓰지만 이름/문서/로그가 canary인 상태`를 뜻한다.

---

## 3. 분류 체계

| 분류 | 의미 | 후속 코드 액션 기준 |
| --- | --- | --- |
| `remove` | live도 아니고 모니터링 가치도 낮고, 다른 지표로 대체 가능 | 호출 제거, 상수 제거, 리포트/테스트/문서 정리 여부까지 함께 닫는다 |
| `observe-only` | live 판단에는 안 쓰지만 튜닝 모니터링 가치가 남아 있음 | 실주문/실판단 비사용을 명시하고, 어느 리포트/리뷰에서만 유지할지 고정한다 |
| `baseline-promote` | 사실상 운영 기본 경로인데 이름/분기가 아직 canary | 상수명, 로그명, 문서 용어, rollback 표현 정리 범위를 함께 닫는다 |
| `active-canary` | 아직 실험 축으로 유지해야 함 | 성공 기준, 종료 조건, OFF 조건, baseline 승격 판단 시점을 같이 둔다 |

후속 코드 액션 연결 규칙은 아래로 고정한다.

1. `remove`
   - 호출 제거 여부
   - 상수 제거 여부
   - 리포트/대시보드 정리 여부
   - 테스트 삭제/수정 여부
   - same change set으로 판정표/관련 기준문서 동시 갱신 여부
2. `observe-only`
   - live 판단 비사용 명시
   - 유지 리포트/로그 범위 명시
   - baseline 승격 금지 명시
3. `baseline-promote`
   - rename 대상 상수
   - rename 대상 로그 stage/reason
   - 문서 용어 정리 범위
   - rollback guard는 유지하되 `canary` 표현 제거 범위
4. `active-canary`
   - 현재 live/guard 상태
   - 성공 기준
   - 종료 또는 승격 조건
   - 실패 시 OFF 또는 parking 조건

### 3.1 Live Cohort 분류

`shadow/canary` 축 정리와 별도로, live 전환에 쓰이는 cohort는 아래 5개 상태로만 분류한다.

| cohort 상태 | 의미 | live 판정 사용 방식 |
| --- | --- | --- |
| `baseline-decision` | 기준선 EV/품질 판정의 주 비교모집단 | 기준선 유지 여부 판단에 직접 사용 |
| `active-canary-decision` | 현재 live canary가 실제로 바꾼 모집단 | baseline과 분리 비교, rollback 직접 연결 |
| `provisional-stage-disjoint` | 병렬 canary 예외에서 다른 조작점과 분리된 임시 cohort | hard pass/fail 금지, provisional 판정만 허용 |
| `observe-only` | 리포트/모니터링에는 남기지만 live go/no-go에는 직접 쓰지 않는 cohort | 오염 탐지/후속 설계 참고용 |
| `excluded` | fallback, stale snapshot, partial/full 혼합, initial/pyramid 혼합 등 현재 판정에서 제외할 모집단 | 손익/승인 판단 입력 금지 |

live 전환 시 cohort는 최소 아래 필드를 같이 잠근다.

1. `cohort_name`
2. `cohort_status`
3. `entry_or_exit_stage`
4. `apply_target`
5. `cohort_tag`
6. `inclusion_rule`
7. `exclusion_rule`
8. `rollback_owner`
9. `allowed_metrics`
10. `forbidden_aggregations`

cohort 분류 공통 규칙은 아래로 고정한다.

1. `baseline-decision` cohort는 `main-only`, `normal_only`, `post_fallback_deprecation`, `COMPLETED + valid profit_rate`, `full/partial 분리` 원칙을 깨면 안 된다.
2. `active-canary-decision` cohort는 반드시 ON/OFF 가능한 단일 조작점과 1:1로 연결돼야 하며, `applied/not-applied`를 raw event에서 복원할 수 있어야 한다.
3. `provisional-stage-disjoint` cohort는 별도 `cohort tag`, 별도 rollback guard, 별도 적용시점이 동시에 없으면 만들 수 없다.
4. `observe-only` cohort는 future candidate 탐색에는 쓸 수 있지만, 실현손익 pass/fail 근거로 승격하면 안 된다.
5. `excluded` cohort는 손익 왜곡 방지용이므로, 제외 사유가 줄어들었다고 즉시 baseline으로 되돌리지 않고 별도 재승인 절차를 거친다.

### 3.2 Live 전환 시 Cohort 잠금 템플릿

새 live 축 승인 또는 기존 축 replacement 시 아래 형식을 checklist/report에 같이 남긴다.

1. `baseline cohort`: 예) `main-only + normal_only + post_fallback_deprecation`
2. `candidate live cohort`: 예) `other_danger relief applied cohort`, `soft_stop qualifying cohort`
3. `observe-only cohort`: 예) `wait6579_ev_cohort`, `hard_stop_whipsaw_aux`, `same_symbol cooldown shadow`
4. `excluded cohort`: 예) `fallback`, `partial/full mixed`, `initial/pyramid mixed`, `NULL or incomplete profit`
5. `rollback trigger owner`: 진입/보유/청산 중 어느 축이 이 cohort를 끄는지
6. `cross-contamination check`: 다른 canary가 유입 모집단을 바꿨는지 여부

판정 메모에서 위 6개 중 하나라도 비어 있으면 `cohort 미정리`로 보고 live 승인/유지 판정을 잠그지 않는다.

### 3.3 현행 Decision Cohort Inventory

아래 inventory는 `Plan Rebase`와 현행 active checklist에서 실제 판정/관찰에 쓰이면서, 최소 하나 이상에 해당하는 코호트만 잠근다.

1. `src/` 코드/리포트 빌더/스냅샷 경로가 남아 있다.
2. active checklist의 live 승인/관찰/rollback 판정에 직접 들어간다.
3. 현재 기준 문서(`Plan Rebase`, performance report, active workorder)에서 현행 영향도가 있다.

과거 문서에만 남고 현재 `src/` 흔적도 없고 active 판정에도 쓰이지 않는 historical-only cohort는 이 inventory에 올리지 않는다. 아직 상태가 비어 있는 코호트가 있으면 `전체 코호트 분류 완료`로 보지 않는다.

| cohort | cohort 상태 | 주 용도 | 유지 종료 시점/달성요건 | 기본 문서 |
| --- | --- | --- | --- | --- |
| `main-only + normal_only + post_fallback_deprecation` | `baseline-decision` | live 기준선 손익/퍼널/체결 품질 비교 | Plan Rebase 종료 전까지 유지. 새 기준선이 문서 승인되어 replacement되고 동일 메트릭/제외규칙이 승계될 때만 교체 가능 | `Plan Rebase`, 날짜별 checklist |
| `wait6579_ev_cohort` | `observe-only` | BUY recovery 후보 EV/blocked_ai_score/제출 전환 관찰 | `buy_recovery_canary` 축이 remove 또는 baseline 승격으로 닫히고, `recovery_check -> promoted -> submitted` 설명력이 다른 live/report 축으로 완전히 대체될 때 제거 가능 | `2026-04-21~22 checklist` |
| `buy_recovery_canary applied cohort` | `guarded-off` | `WAIT65~79` live canary 효과/rollback 판정 | 코드 경로는 회귀/재개 가능성 때문에 유지하되, Plan Rebase 단일 live canary 기간에는 OFF로 유지. 재개 시 새 승인 항목과 rollback guard 필요 | `2026-04-21~23 checklist` |
| `wait6579_probe_canary_applied` | `guarded-off` | 소량 probe 적용 표본 분리 | `soft_stop_micro_grace` live 관찰 중에는 OFF. 재개하려면 단일 live canary slot을 다시 확보하고 `submitted/full/partial` 회복 기준을 새로 문서화 | `wait6579_ev_cohort`, `2026-04-21 checklist` |
| `latency_quote_fresh_composite` | `observe-only` | 2026-04-29 이전 live였던 quote freshness 복합 residual 축의 historical/reference cohort | `2026-04-29 08:29 KST` OFF + restart 이후에는 historical/reference 및 감리 비교용으로만 유지. 재개 시 새 승인 항목과 rollback guard 필요 | `Plan Rebase`, `2026-04-29 checklist` |
| `latency_signal_quality_quote_composite` | `observe-only` | `latency_quote_fresh_composite` replacement로 same-day 시험한 예비 복합축의 post-restart cohort | `2026-04-29 12:21~12:50 KST` replacement cohort 분리와 효과 미약 판정 보존이 끝나면 historical-only로 유지. baseline/live 승격 금지 | `Plan Rebase`, `2026-04-29 checklist` |
| `mechanical_momentum_latency_relief` | `active-canary-decision` | AI 50/70 mechanical fallback 상태를 포함하는 현재 entry replacement live cohort | `mechanical_momentum_relief_canary_applied`, `submitted/full/partial`, `COMPLETED + valid profit_rate`, `fallback_regression=0`로 post-restart 분리 판정 후 유지/종료/승격을 결정 | `Plan Rebase`, `2026-04-29 checklist` |
| `post-restart cohort` | `active-canary-decision` | replacement 이후 same-day 제출 회복 관찰 | replacement 당일 판정이 닫히고 후속 축이 새 `post-change` cohort로 넘어가면 종료. 익일 이후 지속 baseline으로 쓰지 않음 | `2026-04-29 checklist` |
| `soft_stop qualifying cohort` | `provisional-stage-disjoint` | 보유/청산 live 예외 canary 후보 | `soft_stop_rebound_split` 승인 또는 보류+재시각이 닫히고, qualifying rule이 live 조작점으로 승격되거나 폐기될 때 종료 | `2026-04-27 checklist` |
| `soft_stop_micro_grace` | `active-canary-decision` | soft_stop 최초 터치 후 짧은 휩쏘 확인유예 | `scalp_soft_stop_pct` 손실/반등 개선이 확인되어 baseline 승격되거나, emergency/hard_stop 악화 또는 soft_stop 지연 부작용으로 OFF 확정될 때 종료 | `2026-04-27 checklist` |
| `reversal_add` | `active-canary-decision` | 유효 진입 초반 눌림을 1주 소형 추가매수로 회수하는 보유/청산 canary | `reversal_add_candidate`, `scale_in_executed add_type=AVG_DOWN`, `reversal_add_used`, 후속 `soft_stop/trailing/COMPLETED`로 손익/soft stop tail 개선 여부가 닫히면 유지/종료/승격 결정 | `Plan Rebase`, `2026-04-30 checklist` |
| `bad_entry_block` | `observe-only` | never-green/AI fade 불량 진입 후보를 실전 차단 전 관찰 | `bad_entry_block_observed`와 후속 `soft_stop/hard_stop/GOOD_EXIT/MISSED_UPSIDE`가 최소 10건 이상 연결되고 missed winner 위험이 낮다고 확인되기 전까지 live block 금지 | `Plan Rebase`, `2026-04-30 checklist` |
| `hard_stop_whipsaw_aux` | `observe-only` | severe-loss guard 보조 관찰 | 하드스탑을 보조 관찰로만 둔다는 원칙이 유지되는 동안 유지. `MISSED_UPSIDE/GOOD_EXIT/NEUTRAL`과 반등 지표가 독립 판단가치를 잃거나 hard stop 완화 의제가 공식 폐기되면 제거 | `Plan Rebase`, `2026-04-27 checklist` |
| `same_symbol_reentry` | `observe-only` | 동일종목 재진입 손실/guard 필요성 관찰 | `same_symbol_reentry_loss_count`가 독립 guard 후보성을 잃거나, soft stop/position context 축에 완전히 흡수되어 별도 재진입 cohort가 필요 없을 때 제거 | `holding_exit_observation`, `2026-04-27 checklist` |
| `trailing_continuation` | `observe-only` | upside capture 개선 후보 관찰 | `MISSED_UPSIDE rate >= 60%`, `GOOD_EXIT rate <= 30%`로 2순위 live 후보 요건을 충족해 canary로 승격되거나, 반대로 upside 개선 후보성이 약해져 후순위 폐기가 확정되면 제거/재분류 | `holding_exit_observation`, `2026-04-27 checklist` |
| `initial-only` | `observe-only` | 신규 진입만의 체결/손익/청산 품질 분리 | 임시 `2주 cap` 유지/해제와 `3주 cap` 승인조건 판정이 닫히고 initial/pyramid가 더 이상 다른 EV를 보이지 않아 분리 해석 가치가 사라질 때만 제거 | `2026-04-29`, `2026-04-30 checklist` |
| `pyramid-activated` | `observe-only` | 추가매수 활성 표본 분리 | `2주 cap` 이후 `zero_qty=0` 유지와 pyramid 손익/청산 품질이 충분히 닫히고 별도 특성이 없다고 확인될 때만 제거 | `2026-04-29`, `2026-04-30 checklist` |
| `full_fill` | `observe-only` | 체결 품질 우수 표본 분리 | `partial_fill`과 EV/청산 품질 차이가 더 이상 의사결정 의미를 잃지 않는 한 유지. full/partial 합산 허용 정책으로 바뀌기 전에는 제거 금지 | `Plan Rebase`, performance/report/checklist |
| `partial_fill` | `observe-only` | partial 전용 손익/재베이스/soft-stop 악화 관찰 | partial 악화 여부가 더 이상 독립 리스크가 아니라고 확인되기 전까지 유지. full/partial 합산 정책 변경 전에는 제거 금지 | `Plan Rebase`, performance/report/checklist |
| `initial_entry_qty_cap_2share` | `active-canary-decision` | 신규 BUY 초기 수량 tail 제한과 pyramid zero_qty 왜곡 완화 | `initial_entry_qty_cap_applied`, `zero_qty`, `pyramid_activated`, `soft_stop`, `COMPLETED + valid profit_rate`로 2주 cap 유지/해제를 닫을 때까지 유지 | `2026-04-29`, `2026-04-30 checklist` |
| `initial_entry_qty_cap_3share_candidate` | `observe-only` | 3주 cap 전환 승인조건 관찰 | `2주 cap` cohort가 제출/체결/soft_stop tail 비악화를 보이고, 동일 entry 단계 live 축 충돌 없이 canary slot을 확보할 때만 active 후보로 승격 | `2026-04-30 checklist` |
| `ai_cache_hit_miss` | `observe-only` | gatekeeper/holding AI cache hit vs miss 영향도 관찰 | structured join 필드가 `submitted/full/partial/COMPLETED`와 안정적으로 연결될 때까지 live go/no-go 입력 금지 | `2026-04-29 checklist` |
| `execution_receipt_binding_quality` | `observe-only` | WS 실제체결과 active order binding 정합성 관찰 | BUY/SELL `EXEC_IGNORED` 원인이 order number race인지 visibility 문제인지 닫힐 때까지 EV 판정 전제 품질축으로 유지 | `2026-04-29`, `2026-04-30 checklist` |
| `gemini_schema_registry_flag_off` | `observe-only` | Gemini 6 endpoint response schema registry의 flag-off contract 관찰 | `holding_exit_v1/eod_top5_v1` contract gap이 닫히고 live enable 항목이 별도 승인되기 전까지 flag-off 유지 | `2026-04-29`, `2026-04-30 checklist` |
| `deepseek_retry_acceptance_flag_off` | `observe-only` | DeepSeek retry/backoff acceptance snapshot 관찰 | `api_call_lock`, retry log visibility, live-sensitive sleep guard가 문서/테스트로 닫히기 전까지 live enable 금지 | `2026-04-29`, `2026-04-30 checklist` |
| `openai_responses_ws_shadow_flag_off` | `observe-only` | OpenAI Responses WS transport parity/load/timeout/http-fallback 관찰 | `request_id mismatch=0`, `late_discard=0`, `http fallback<=2%`, `parse_fail<=0.5%`가 shadow 기준으로 닫히고 별도 entry transport canary가 승인되기 전까지 flag-off 유지 | `2026-05-04 checklist` |

inventory 운영 규칙은 아래로 고정한다.

1. 위 표에 없는 cohort가 신규 문서/코드/리포트에 등장하면, 같은 change set에서 이 표에 추가하고 상태를 먼저 잠근다.
2. 표에 있는 cohort라도 성격이 바뀌면 `상태 변경 + why + 허용 메트릭 + 금지 집계`를 같은 턴에 같이 갱신한다.
3. `baseline-decision`, `active-canary-decision`, `provisional-stage-disjoint`는 빈 이름으로 운영하지 않는다. 임시 표현(`post-change`, `new cohort`)만 적고 상태를 안 잠그는 것은 무효다.
4. `historical-only` 문서에만 남고 `src/`/active checklist/현재 기준 리포트 어디에도 연결되지 않는 cohort는 inventory에서 제거한다. 필요하면 archive나 과거 report에서만 유지한다.
5. `observe-only` cohort는 `유지 종료 시점/달성요건` 없이 무기한 두지 않는다. 제거, 승격, 상위 축 흡수 중 하나의 종료 조건이 반드시 있어야 한다.

---

## 4. 판정표

아래 판정은 `src/` 기준 실제 런타임/리포트 경로를 기준으로 잠근다.

### 4.0 `src/engine + constants` 전수 inventory

| 축 | 분류 | live 영향도 | 비고 |
| --- | --- | --- | --- |
| `dual_persona` | `observe-only` | `guarded-off` | gatekeeper/overnight dual-persona shadow |
| `watching_shared_prompt_shadow` | `observe-only` | `guarded-off` | WATCHING shared prompt 비교 shadow |
| `watching_prompt_75_shadow` | `remove` | `guarded-off` | 제거 완료, historical 판정만 유지 |
| `hard_time_stop_shadow` | `observe-only` | `none` | 공통 hard time stop 관찰 |
| `ai_holding_shadow_band` | `observe-only` | `none` | HOLDING review/skip 경계 관찰 |
| `same_symbol_soft_stop_cooldown_shadow` | `observe-only` | `none` | same-symbol cooldown 가설 관찰 |
| `partial_only_timeout_shadow` | `observe-only` | `none` | partial-only timeout 가설 관찰 |
| `split_entry_rebase_integrity_shadow` | `remove` | `guarded-off` | split-entry 폐기 정합화로 runtime shadow 기본 OFF |
| `split_entry_immediate_recheck_shadow` | `remove` | `guarded-off` | split-entry 폐기 정합화로 runtime shadow 기본 OFF |
| `strength_shadow_feedback` | `observe-only` | `none` | dynamic strength 후보 장후 평가 |
| `buy_recovery_canary` | `active-canary` | `guarded-off` | `WAIT65~79` BUY 회복축 |
| `wait6579_probe_canary` | `active-canary` | `guarded-off` | soft_stop live canary 관찰 중 entry probe OFF |
| `fallback_qty_canary` | `remove` | `guarded-off` | historical label only, live fallback 경로와 함께 종료 |
| `latency_guard_canary` | `active-canary` | `guarded-off` | broad fallback override legacy 축 |
| `latency_quote_fresh_composite` | `observe-only` | `guarded-off` | 2026-04-29 08:29 KST OFF + restart 완료. historical/reference 축 |
| `latency_signal_quality_quote_composite` | `observe-only` | `guarded-off` | 2026-04-29 12:21~12:50 KST same-day replacement 후 효과 미약 종료 |
| `mechanical_momentum_latency_relief` | `active-canary` | `limited-live` | current entry live replacement canary |
| `initial_entry_qty_cap_2share` | `active-canary` | `limited-live` | current initial entry size guard. 3주 확대는 별도 승인 전 observe-only |
| `reversal_add` | `active-canary` | `limited-live` | valid-entry early pullback recovery. 2주 cap에서도 1주 floor로 소형 canary |
| `bad_entry_block` | `observe-only` | `none` | never-green/AI fade 후보 분류. live entry block 아님 |
| `ai_cache_hit_miss` | `observe-only` | `none` | structured join gap으로 보조지표 유지 |
| `execution_receipt_binding_quality` | `observe-only` | `none` | SK이노베이션 BUY/SELL `EXEC_IGNORED` 사례로 runtime truth 품질축 유지 |
| `gemini_schema_registry_flag_off` | `observe-only` | `guarded-off` | flag-off contract/load observability. live enable 아님 |
| `deepseek_retry_acceptance_flag_off` | `observe-only` | `guarded-off` | flag-off retry acceptance observability. live enable 아님 |
| `openai_responses_ws_shadow_flag_off` | `observe-only` | `guarded-off` | OpenAI Responses WS parity/timeout/fallback observability. live enable 아님 |
| `orderbook_stability_observation` | `observe-only` | `none` | FR/quote-age/print-alignment 관찰. live gate 아님 |
| `spread_relief_canary` | `active-canary` | `guarded-off` | parking 상태 |
| `ws_jitter_relief_canary` | `active-canary` | `guarded-off` | same-day 종료된 replacement 축 |
| `other_danger_relief_canary` | `active-canary` | `guarded-off` | 2026-04-27 13:00 미개선 종료 |
| `dynamic_strength_canary` | `baseline-promote` | `baseline-live` | current runtime/log는 `dynamic_strength_relief` |
| `partial_fill_ratio_canary` | `baseline-promote` | `baseline-live` | current config는 `partial_fill_ratio_guard` |

### 4.1 `dual_persona`

- 판정: `observe-only`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: 현재 실주문 경로에서는 꺼져 있지만, historical `dual_persona_shadow_samples/conflict/veto/extra_ms`는 향후 AI 엔진 A/B 재개 여부를 판단하는 데 직접 쓸 수 있다.
  - 상향 조건: `entry_filter_quality` 이후 AI 라우팅 A/B를 다시 열거나, Gemini 대비 보수 veto/conflict를 본격 비교할 때
  - 하향 조건: AI 엔진 A/B 재개를 공식 폐기하고 historical 비교도 더 이상 쓰지 않을 때
- EV 판정 기여도: `Low`
- 대체 가능성: `Medium`
  - historical 비교 지표는 일부 대체가 어렵지만, 현재 daily tuning의 주병목 판정에는 직접 입력이 아니다.
- 운영 부하/지연 비용: `High`
  - shadow 호출이 살아 있으면 추가 API/지연 비용이 크다.
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `performance_tuning`과 대시보드에 `dual_persona_*` 메트릭과 breakdown이 이미 존재한다.
  2. 현재 `OPENAI_DUAL_PERSONA_ENABLED=False`이며 runtime guard로 신규 shadow 호출은 차단된 상태다.
  3. 현재 Plan Rebase 주병목/실주문 판정에는 직접 쓰지 않는다.
- 다음 액션:
  1. runtime submit 경로는 계속 OFF로 둔다.
  2. historical metrics/report/UI는 당장 삭제하지 않는다.
  3. AI A/B 재개가 공식 폐기되면 그때 `runtime engine wiring + report cards + tests`를 한 세트로 `remove` 후보 재판정한다.

### 4.2 `watching_prompt_75_shadow`

- 판정: `remove`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Low`
  - 이유: `WAIT 75~79` shadow는 이미 `WAIT 65~79 buy_recovery_canary`, `wait6579_ev_cohort`, `buy_recovery prompt` 계열로 대체됐다.
  - 상향 조건: 별도 `75~79` 경계구간만 독립적으로 재검증해야 하는 새로운 질문이 생길 때
  - 하향 조건: 현재처럼 `65~79` 실전 canary와 cohort report가 운영 기준을 완전히 대체할 때
- EV 판정 기여도: `Low`
- 대체 가능성: `High`
- 운영 부하/지연 비용: `Medium`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Low`
- 근거:
  1. 상수 주석도 이미 `remote 전용` legacy shadow 성격으로 남아 있다.
  2. rare score band라 표본 희소성이 강하고, 현재는 `wait6579_ev_cohort`와 `buy_recovery_canary`가 더 직접적인 판단축이다.
  3. runtime guard로 기본 운영에서 더 이상 타지 않는다.
- 다음 액션:
  1. `src/` runtime hook, 상수, 전용 report/check script, 전용 테스트를 같은 change set에서 제거 완료
  2. 현재 문서에서는 historical 제거 판정만 유지하고, `75 shadow`를 현행 축/재개 후보로 다루지 않는다
  3. 이후 재개가 필요하면 기존 축을 복구하지 않고 새 canary로 재정의한 뒤 본 판정표에 새 항목으로 추가한다

### 4.3 `hard_time_stop_shadow`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: 실주문 개입 없이 `시간기반 강제정리` 가설의 false positive와 ghost event를 관찰하는 용도로는 아직 가치가 있다.
  - 상향 조건: `soft_stop_rebound_split`과 별도로 `time-based exit` 후보를 다시 검토할 때
  - 하향 조건: `post_sell`/`trade_review`만으로 동일 판단이 충분하고, ghost event 점검도 더 이상 필요 없을 때
- EV 판정 기여도: `Low`
- 대체 가능성: `Medium`
  - 청산 후 결과는 대체되지만, 장중 `would-have-fired` 관측은 완전 대체가 어렵다.
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Medium`
- 근거:
  1. 실주문에 연결되지 않고 `hard_time_stop_shadow` 이벤트만 남긴다.
  2. trade review/performance tuning UI에서 이미 관찰 지표로 쓰인다.
  3. 과거 ghost event 점검 이력이 있어 완전 삭제 전 관측 가치가 남아 있다.
- 다음 액션:
  1. 유지 범위를 `trade_review + performance_tuning 관찰`로만 명시
  2. 실주문 승격 후보로는 두지 않는다
  3. 동일 정보가 `post_sell/trade_review`로 충분히 대체되는 시점이 오면 `remove` 재판정한다

### 4.3A `watching_shared_prompt_shadow`

- 판정: `observe-only`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: WATCHING 단계에서 shared prompt와 split prompt 차이를 다시 봐야 할 때 사용할 비교 shadow다.
  - 상향 조건: AI A/B 또는 prompt split 비교를 재개할 때
  - 하향 조건: shared 경로 비교를 다시 보지 않기로 확정할 때
- EV 판정 기여도: `Low`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `High`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. OpenAI dual-persona engine submit 함수와 stage 기록 경로가 남아 있다.
  2. 현재는 `OPENAI_DUAL_PERSONA_ENABLED=False` 가드 아래에서 실런타임 제출이 막혀 있다.
- 다음 액션:
  1. `dual_persona`와 같이 OFF 유지
  2. prompt split 비교 의제가 사라지면 `remove` 재판정

### 4.4 `ai_holding_shadow_band`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: HOLDING AI fast reuse에서 `skip/review` 경계가 얼마나 자주 흔들리는지 보는 관측 신호로는 아직 유효하다.
  - 상향 조건: `holding reuse blocker`나 `holding AI review 지연`을 직접 튜닝 후보로 다시 올릴 때
  - 하향 조건: `holding_reuse_blockers`, `holding_sig_deltas`, `holding_reviews/skips`만으로 충분히 대체될 때
- EV 판정 기여도: `Medium`
  - 직접 손익은 아니지만 holding review 품질과 재평가 빈도를 해석하는 데 기여한다.
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. `ai_holding_reuse_bypass`와 짝을 이루는 관측축으로 남아 있다.
  2. holding fast reuse를 다시 건드릴 때 band 관측이 있으면 원인귀속이 더 쉬워진다.
  3. 현재는 live 판단이 아니라 observability 성격이다.
- 다음 액션:
  1. live 판단 비사용을 문서 기준으로 고정
  2. 유지 리포트 범위는 `trade_review`와 raw holding pipeline 해석으로 제한
  3. 향후 `holding reuse` 축을 재개하지 않으면 `hard_time_stop_shadow`와 묶어 `observe-only 축 축소`를 재판정한다

### 4.4A `same_symbol_soft_stop_cooldown_shadow`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: soft stop 직후 동일 종목 재진입 cooldown이 필요한지 확인하는 관찰축이다.
  - 상향 조건: soft stop 휩쏘와 same-symbol 재진입 손실을 같이 튜닝할 때
  - 하향 조건: same-symbol cooldown live 후보를 접을 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `shadow_only=True`로 entry pipeline에만 기록하고 실주문 차단에는 연결하지 않는다.
  2. 보유/청산 cooldown 가설과 직접 연결된다.
- 다음 액션:
  1. 보유/청산 관찰축으로만 유지
  2. 재개 가능성이 사라지면 `remove` 재판정

### 4.4A-1 `soft_stop_micro_grace`

- 판정: `active-canary-decision`
- live 영향도: `limited`
- 튜닝 모니터링 가치: `High`
  - 이유: 4월 `scalp_soft_stop_pct` 61건 중 10분 내 매도가 재상회 `57건(93.4%)`, +0.5% 이상 반등 `43건(70.5%)`라 soft stop 직후 휩쏘 완화의 직접 조작점이다.
  - 상향 조건: `soft_stop_micro_grace` 적용 표본에서 `scalp_soft_stop_pct` 손실 tail이 줄고, hard stop 전환/미체결/동일종목 재진입 손실이 증가하지 않을 때
  - 하향 조건: `scalp_hard_stop_pct` 또는 emergency break가 늘거나, grace 후 더 나쁜 가격 청산이 반복될 때
- EV 판정 기여도: `High`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `High`
- 근거:
  1. `whipsaw confirmation`은 AI/호가 재확인을 추가해 entry latency와 유사한 지연/누락을 다시 만들 수 있어 1차 live 조작점에서 제외했다.
  2. `SCALP_SOFT_STOP_MICRO_GRACE_SEC=20`, `SCALP_SOFT_STOP_MICRO_GRACE_EMERGENCY_PCT=-2.0`, hard stop `-2.5%`로 유예 폭을 제한했다.
- 다음 액션:
  1. `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill/partial_fill`을 분리 관찰
  2. hard stop 전환이나 grace 후 악화가 확인되면 canary OFF

### 4.4A-2 `reversal_add`

- 판정: `active-canary-decision`
- live 영향도: `limited-live`
- 튜닝 모니터링 가치: `High`
  - 이유: `micro grace 20초`는 손절 시점 지연에 그친다. `reversal_add`는 진입 판단이 틀리지 않았고 초반 눌림만 과도한 케이스를 1주 추가매수로 회수하는 별도 전략 가설이다.
  - 상향 조건: `reversal_add_used` cohort에서 `COMPLETED + valid profit_rate`가 baseline 대비 비악화이고, `scalp_soft_stop_pct` 전환율과 hard stop 전환이 늘지 않을 때
  - 하향 조건: `reversal_add_used` 후 soft stop/hard stop으로 이어지거나, cohort 평균 손익이 `<= -0.30%`일 때
- EV 판정 기여도: `High`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. 기존 `evaluate_scalping_reversal_add()`는 AI 회복, 저점 미갱신, 매수압/틱가속/micro VWAP 조건을 이미 갖고 있어 새 진입축이 아니라 보유 중 회수축으로 제한할 수 있다.
  2. 2주 cap 환경에서는 `REVERSAL_ADD_SIZE_RATIO=0.33`이 0주가 될 수 있으므로 `REVERSAL_ADD_MIN_QTY_FLOOR_ENABLED=True`로 1주 소형 canary를 허용한다.
  3. 추가매수 체결 후에는 `soft_stop_micro_grace` 상태를 초기화해 기존 손절 유예 상태가 새 평단 판단을 오염시키지 않게 한다.
- 다음 액션:
  1. `reversal_add_candidate`, `reversal_add_blocked_reason`, `scale_in_executed add_type=AVG_DOWN`, `reversal_add_used`, 후속 `soft_stop/trailing/COMPLETED`를 분리한다.
  2. 내일 오전 1건이라도 체결되면 anchor case로 고정하고, 체결이 없으면 `zero_qty/position_at_cap/supply_conditions_not_met/ai_not_recovering` 중 병목을 닫는다.

### 4.4A-3 `bad_entry_block`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `High`
  - 이유: soft stop이 많은 종목을 무조건 더 버티거나 물타기할 수는 없다. never-green, 낮은 peak, 낮은 AI 상태로 60초 이상 손실이 지속되는 표본은 애초에 막아야 할 불량 진입 후보일 수 있다.
  - 상향 조건: `bad_entry_block_observed` 표본이 10건 이상이고 후속 `soft_stop/hard_stop` 전환이 높으며 `GOOD_EXIT/MISSED_UPSIDE` 놓침 위험이 낮을 때
  - 하향 조건: observe 후보가 이후 자주 회복하거나 `MISSED_UPSIDE`로 끝나 live block이 기회비용을 키울 가능성이 확인될 때
- EV 판정 기여도: `High`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `High`
- 근거:
  1. 초기 조건은 `held_sec>=60`, `profit_rate<=-0.70%`, `peak_profit<=+0.20%`, `current_ai_score<=45`로 제한한다.
  2. 내일은 `bad_entry_block_observed`만 남기고 주문 차단/청산 변경은 하지 않는다.
  3. feature는 `buy_pressure_10t`, `tick_acceleration_ratio`, `large_sell_print_detected`, `curr_vs_micro_vwap_bp`를 같이 남겨 `불량 진입`과 `일시 눌림`을 분리한다.
- 다음 액션:
  1. 후속 `soft_stop/hard_stop/GOOD_EXIT/MISSED_UPSIDE`와 연결 가능한 형태로만 해석한다.
  2. live block 승격은 별도 날짜 checklist에서 단일축 canary로만 연다.

### 4.4B `partial_only_timeout_shadow`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: partial fill만 남은 장기 체류를 timeout 후보로 봐야 하는지 확인하는 관찰축이다.
  - 상향 조건: partial-only 장기보유가 손익 훼손으로 반복 확인될 때
  - 하향 조건: `partial_fill_ratio`와 post-sell 평가만으로 충분할 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `shadow_only=True`로 holding pipeline에만 기록한다.
  2. 체결품질 가드와는 다른 `체결 후 timeout` 축이다.
- 다음 액션:
  1. partial fill 품질과 timeout 품질을 분리해 유지
  2. 표본 희소/대체 가능 시 `remove` 재판정

### 4.4C `split_entry_rebase_integrity_shadow`

- 판정: `remove`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Low`
  - 이유: split-entry 재개 의제가 현재 기준문서에서 닫혔고, same-day 판정축에서도 복귀 후보가 아니다.
  - 상향 조건: 없음. 재개가 필요하면 새 workorder와 새 cohort로 다시 정의해야 한다.
  - 하향 조건: historical runtime shadow까지 완전히 삭제할 때
- EV 판정 기여도: `Low`
- 대체 가능성: `High`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Low`
- 근거:
  1. `latency fallback split-entry`는 `Plan Rebase`에서 영구 폐기 축으로 잠겼다.
  2. runtime shadow는 재개 없는 상태에서 현재 판정에 기여하지 않아 기본 OFF가 맞다.
- 다음 액션:
  1. runtime emit은 기본 OFF로 두고 historical audit helper만 남긴다
  2. 재개 검토가 다시 생기면 새 판정축으로 다시 등록한다

### 4.4D `split_entry_immediate_recheck_shadow`

- 판정: `remove`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Low`
  - 이유: parent split-entry 축 자체가 폐기됐으므로 후속 recheck shadow도 운영 가치가 없다.
  - 상향 조건: 없음. split-entry 재개 정의가 새로 생길 때만 별도 재등록한다.
  - 하향 조건: historical helper까지 삭제할 때
- EV 판정 기여도: `Low`
- 대체 가능성: `High`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Low`
- 근거:
  1. `split_entry_rebase_integrity_shadow`의 하위 후속 관찰축이라 독립 유지 이유가 없다.
  2. 현재는 historical test fixture 외 live 판정 연결점이 없다.
- 다음 액션:
  1. integrity shadow와 같이 기본 OFF/remove로 묶는다

### 4.5 `dynamic_strength_canary` / current runtime `dynamic_strength_relief`

- 판정: `baseline-promote`
- live 영향도: `baseline-live`
- 튜닝 모니터링 가치: `Medium`
  - 이유: 이미 baseline live 경로로 쓰이고 있어 실험 표본보다 운영 경로 설명 가치가 더 크다.
  - 상향 조건: 이후 rollback 또는 threshold 재조정이 반복되면 baseline guard로서의 모니터링 가치가 올라간다
  - 하향 조건: 더 이상 별도 guard로 보지 않고 기본 threshold 구조에 완전히 흡수될 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. `2026-04-24` 기준 문서에서 이미 `baseline live 107건`으로 해석했다.
  2. 현재는 `canary` 이름과 달리 baseline 경로처럼 설명된다.
- 다음 액션:
  1. 현재 runtime/log는 `dynamic_strength_relief`, 상수/env는 `SCALP_DYNAMIC_STRENGTH_RELIEF_*` 기준으로 유지한다
  2. historical `dynamic_strength_canary` 명칭은 inventory/과거 추적 문서에서만 병기한다
  3. rollback guard는 유지하되 문서/코드 용어에서는 `baseline guard` 해석으로 통일한다

### 4.6 `other_danger_relief_canary`

- 판정: `active-canary`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: `2026-04-27 11:31 KST` raw 분해에서는 가장 직접적인 same-day pivot이었지만, `13:00` offline 판정에서 제출 회복 비율 개선을 만들지 못해 현재는 OFF 상태다.
  - 상향 조건: `submitted`, `quote_fresh_latency_pass_rate`, `latency_state_danger` 감소, `canary_applied`가 실제 회복을 만들 때
  - 하향 조건: 반복 관찰에도 효과가 없고 `entry_filter_quality` 또는 다른 명시적 latency 하위원인 축으로 완전히 대체될 때
- EV 판정 기여도: `Low`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Medium`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `2026-04-27 11:31 KST` raw 재집계 기준 `latency_block=3196`, `latency_state_danger=3000`, `other_danger=1218`, `low_signal=1079/1427`라 병목 직접성이 높다.
  2. `SCALP_LATENCY_OTHER_DANGER_RELIEF_MIN_SIGNAL_SCORE`를 `90.0 -> 85.0`으로 낮춰 same-day pivot 했지만, `13:00` 기준 `budget_pass_to_submitted_rate=0.2%`가 그대로여서 축을 종료했다.
  3. 현재는 `latency_block` 직접 사유를 건드린 이력이 남아 있어 inventory에는 유지하지만, live owner는 아니다.
- 다음 액션:
  1. 현재 상태는 `13:00 미개선 종료 후 OFF`로 잠근다.
  2. 재개는 `other_danger`가 다시 1순위 direct residual로 올라오고 새 rollback guard가 문서화될 때만 허용한다.

### 4.7 `partial_fill_ratio_canary` / current config `partial_fill_ratio_guard`

- 판정: `baseline-promote`
- live 영향도: `baseline-live`
- 튜닝 모니터링 가치: `High`
  - 이유: full/partial 체결 품질은 Plan Rebase의 핵심 guard이고, 이 축은 실험이라기보다 운영 품질 가드로 굳어졌다.
  - 상향 조건: `partial_fill_ratio` rollback guard를 실제 운영 판정에서 계속 쓰는 동안
  - 하향 조건: 최소 체결비율이 기본 주문 정책에 완전히 흡수되어 독립 guard로 안 볼 때
- EV 판정 기여도: `High`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `High`
- 근거:
  1. 상수 기본값이 `True`이며 immediate fix 이후 운영 품질 가드 성격으로 남아 있다.
  2. Plan Rebase guard 표에도 `partial_fill_ratio`는 핵심 판정 축이다.
  3. `full fill`/`partial fill` 분리는 손익보다 우선 보는 기본 기준이다.
- 다음 액션:
  1. 상수/env는 `SCALP_PARTIAL_FILL_RATIO_GUARD_ENABLED` 기준으로 정리했고, 문서 분류명만 historical `partial_fill_ratio_canary`로 유지한다
  2. 문서에서 `실험 축`보다 `운영 품질 가드`로 해석을 통일
  3. 예외 override(`PRESET_TP`, `strong_absolute_override`)는 유지한다

### 4.8 `buy_recovery_canary`

- 판정: `active-canary`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `High`
  - 이유: `WAIT 65~79` 과밀, `recovery_check/promoted/submitted`, `blocked_ai_score_share`는 BUY drought와 미진입 기회비용을 직접 해석하는 핵심 축이다.
  - 상향 조건: `main-only` 1축 live로 재승인되거나 `WAIT65~79` 과밀이 다시 1순위 병목으로 잠길 때
  - 하향 조건: `entry_filter_quality` 또는 다른 상위 필터 축이 동일 문제를 더 직접적으로 설명하고, `wait6579_ev_cohort`만으로 재판정이 충분해질 때
- EV 판정 기여도: `High`
- 대체 가능성: `Medium`
  - `wait6579_ev_cohort`와 `performance_tuning`이 많은 부분을 대체하지만, 실제 `recovery_check -> promoted -> submitted` 실전 변환은 코드축이 있어야 닫힌다.
- 운영 부하/지연 비용: `Medium`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. `Plan Rebase`는 여전히 `buy_recovery_canary`를 메인 진입 canary 축으로 명시한다.
  2. 코드에는 `AI_MAIN_BUY_RECOVERY_CANARY_*`, `watching_buy_recovery_canary`, `wait6579_probe_canary` 경로가 살아 있다.
  3. 다만 현재 기본 설정값은 `AI_MAIN_BUY_RECOVERY_CANARY_ENABLED=False`라 항상 live-on 상태로 볼 수는 없다.
- 다음 액션:
  1. 재승인 시에는 `main live 여부`, `WAIT65~79 cohort 표본`, `blocked_ai_score_share`, `submitted/full/partial` 기준을 같은 change set의 판정 메모와 함께 잠근다.
  2. 장기간 OFF로 유지되고 `wait6579_ev_cohort`만으로도 충분해지면 `remove`가 아니라 먼저 `parking active-canary` 재판정 후 정리 범위를 닫는다.
  3. `watching_prompt_75_shadow`와 달리 이 축은 historical legacy가 아니라 재개 가능성이 높은 실전 축으로 유지한다.

### 4.8A `wait6579_probe_canary`

- 판정: `active-canary`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `High`
  - 이유: BUY recovery가 실제 주문 품질로 이어지는지 소량 실전 표본으로 닫는 하위 probe 축이다.
  - 상향 조건: `buy_recovery_canary`가 다시 live 승인되고 promoted 표본이 누적될 때
  - 하향 조건: recovery 축 자체가 장기간 OFF거나, 다른 live canary 관찰 중 단일축 원칙을 깨는 경우
- EV 판정 기여도: `Medium`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. 2026-04-27 `soft_stop_micro_grace` live 관찰 중에는 단일축 원칙 때문에 `AI_WAIT6579_PROBE_CANARY_ENABLED=False`로 잠근다.
  2. `wait6579_ev_cohort`가 `wait6579_probe_canary_applied`를 직접 집계한다.
- 다음 액션:
  1. `buy_recovery_canary`의 하위 probe 축으로 묶되 현재 live에서는 OFF 유지
  2. 장기간 promoted 표본이 없으면 parking 또는 제거 재판정

### 4.8B `fallback_qty_canary` / current runtime `fallback_qty_guard`

- 판정: `remove`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Low`
  - 이유: fallback entry 자체가 폐기돼 multiplier guard는 더 이상 실전 조작점이 아니다.
  - 상향 조건: 없음. fallback entry 재개가 새 문서/가드와 함께 승인될 때만 재정의한다.
  - 하향 조건: historical 상수/로그 흔적까지 삭제할 때
- EV 판정 기여도: `Low`
- 대체 가능성: `High`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Low`
- 근거:
  1. `entry_mode == fallback` 실전 경로가 hard-off면 `fallback_qty_guard`도 실행되지 않는다.
  2. 남는 의미는 과거 로그 해석용 historical label뿐이다.
- 다음 액션:
  1. 문서 분류는 remove로 고정하고, 잔존 로그는 historical-only로만 설명한다
  2. live runtime에서는 `fallback_qty_guard` 분기 자체를 유지하지 않는다

### 4.9 `spread_relief_canary`

- 판정: `active-canary`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: `spread_only_required` 병목을 직접 겨냥한 첫 downstream relief 축이라 same-day replacement 흐름과 실패 이유를 복기할 때는 가치가 있다.
  - 상향 조건: `quote_fresh` 하위원인에서 다시 `spread_only_required`가 단일 우세 원인으로 잠기고, `ws_jitter/other_danger`보다 우선순위가 높아질 때
  - 하향 조건: residual 분해에서 `spread`가 후순위로 밀리고 `other_danger/ws_jitter`가 주병목으로 고정될 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
  - `performance_tuning`의 `spread_relief_canary_detail`, raw `latency_canary_reason`, `quote_fresh` residual 분해로 상당 부분 대체 가능하다.
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. 코드에는 `SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED`와 `sniper_entry_latency.py`의 `spread_relief` 경로가 남아 있다.
  2. `2026-04-24` same-day 판정에서 `spread_only_required`가 컸지만, 이후 replacement 흐름은 `ws_jitter-only relief -> other_danger residual`로 이동했다.
  3. 현재 상수 주석도 `replacement 완료: spread-only relief는 parking 유지`로 잠겨 있다.
- 다음 액션:
  1. 현재 상태는 `parking된 active-canary`로 문서 기준을 고정하고, baseline/observe-only로 오해하지 않게 한다.
  2. 재개 시에는 `spread_only_required` 비중, `submitted 회복`, `quote_fresh_latency_pass_rate`, `fallback_regression=0`를 같은 판정 묶음으로 본다.
  3. 장기적으로 `quote_fresh` 하위원인에서 `spread`가 재부상하지 않으면 `remove` 또는 `historical note only`로 낮출지 재판정한다.

### 4.9A `ws_jitter_relief_canary`

- 판정: `active-canary`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: `2026-04-27 13:00` 기준 `ws_jitter_too_high=1852`가 `other_danger` 다음 직접 잔여 원인이라, 오늘 `15:00` 전 관찰 가능한 다음 독립축으로 가장 빠르게 교체 가능하다.
  - 상향 조건: `submitted`, `quote_fresh_latency_pass_rate`, `latency_state_danger` 감소, `ws_jitter_relief_canary_applied`가 실제 회복을 만들 때
  - 하향 조건: residual 분해상 `ws_jitter`가 후순위로 밀릴 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. 상수와 runtime branch가 이미 존재하고 회귀 테스트도 있어, same-day `기존 축 OFF -> restart.flag -> 새 축 ON` 교체가 가능하다.
  2. `2026-04-24`에는 활성화 표본 0으로 종료됐지만, `2026-04-27 13:00`에는 raw danger breakdown에서 `ws_jitter_too_high`가 다시 큰 잔여 원인으로 남았다.
- 다음 액션:
  1. `2026-04-27 15:00` 미개선으로 OFF 상태를 유지한다.
  2. 재개는 `ws_jitter`가 다시 단일 우세 원인으로 올라오고 복합축보다 직접성이 높을 때만 허용한다.

### 4.9A-1 `latency_quote_fresh_composite`

- 판정: `observe-only`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: `2026-04-29 08:29 KST` OFF + restart가 확정됐고 현재는 live owner가 아니지만, `quote_fresh_composite_canary_applied` historical cohort와 `composite_no_recovery` 근거는 replacement 축 선택의 reference로 남는다.
  - 상향 조건: 동일 단계 live 축이 비워지고, 새 승인 항목에서 `signal/ws_age/ws_jitter/spread/quote_stale` 묶음 전체를 다시 1축으로 재승인할 때
  - 하향 조건: historical/reference 비교도 더 이상 쓰지 않고 완전히 archive로 내릴 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `Plan Rebase`와 `2026-04-29 checklist`에서 현재 entry live 축은 `mechanical_momentum_latency_relief`로 고정됐다.
  2. `latency_quote_fresh_composite`는 제출 회복 hard baseline을 만들지 못했고, OFF 값과 restart provenance까지 확보됐다.
- 다음 액션:
  1. 장중/번들 판정에서는 historical/reference 축으로만 집계한다.
  2. 재개 없이는 baseline/live 승격 후보로 취급하지 않는다.

### 4.9A-2 `latency_signal_quality_quote_composite`

- 판정: `observe-only`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: same-day replacement로 실제 켰던 축이라 `post-restart cohort` 분리는 남길 가치가 있지만, `budget_pass=972`, `submitted=0`, 후보 통과 0건으로 현재 live owner는 아니다.
  - 상향 조건: future replacement 후보가 다시 `high AI score + quote freshness` 쪽으로 좁혀지고, 새 승인 항목에서 same-day 재승인될 때
  - 하향 조건: `signal>=90` 계열 예비 복합축을 완전히 폐기하고 historical cohort도 더 이상 쓰지 않을 때
- EV 판정 기여도: `Low`
- 대체 가능성: `High`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Low`
- 근거:
  1. `2026-04-29 12:21~12:50 KST` replacement 이후 `low_signal=770`, `quote_stale=76`, 통과 후보 0건으로 효과 미약 종료가 문서화됐다.
  2. AI score 50/70 mechanical fallback 상태를 열지 못해 제출 drought 완화 직접성이 낮았다.
- 다음 액션:
  1. `post-restart cohort`의 historical comparison과 실패 근거만 유지한다.
  2. 새 문서 승인 없이 live 재개 후보로 읽지 않게 `observe-only`로 고정한다.

### 4.9A-3 `mechanical_momentum_latency_relief`

- 판정: `active-canary-decision`
- live 영향도: `limited-live`
- 튜닝 모니터링 가치: `High`
  - 이유: `latency_quote_fresh_composite`와 `latency_signal_quality_quote_composite`를 닫은 뒤, AI 50/70 mechanical fallback 상태까지 포함해 제출 drought를 직접 완화하는 현재 entry live replacement 축이다.
  - 상향 조건: `mechanical_momentum_relief_canary_applied` cohort에서 `submitted/full/partial` 회복, `budget_pass_to_submitted_rate` 개선, `fallback_regression=0`, `COMPLETED + valid profit_rate` 비악화가 확인될 때
  - 하향 조건: post-restart cohort에서 `budget_pass >= 150`인데 `submitted <= 2`, `pre_submit_price_guard_block_rate > 2.0%`, `normal_slippage_exceeded` 반복, 또는 일간 canary 손익이 NAV 대비 `<= -0.35%`일 때
- EV 판정 기여도: `High`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. `2026-04-29 12:50 KST` 운영 override로 `latency_signal_quality_quote_composite=False`, `mechanical_momentum_latency_relief=True` replacement가 반영됐다.
  2. same-day counterfactual 기준 약 `91`건 후보가 확인돼, AI score 50/70 기계 fallback 표본을 완전히 버리지 않는 현재 가장 직접적인 제출 회복 축이다.
  3. `2026-04-29 12:57 KST` restart 후 main PID `30566 -> 35539` 교체 provenance가 확보됐다.
- 다음 액션:
  1. `mechanical_momentum_relief_canary_applied`, `latency_mechanical_momentum_relief_normal_override`, `submitted/full/partial`, `COMPLETED + valid profit_rate`, `fallback_regression=0`를 post-restart cohort로 분리한다.
  2. baseline 승격 전까지는 same-day 운영 override 1축으로만 유지한다.

### 4.9A-4 `orderbook_stability_observation`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: `FR_10s`, `quote_age_p50/p90`, `print_quote_alignment`는 quote freshness 복합축의 세부 품질을 설명할 수 있지만, 현재 entry 병목 해소 전에는 추가 차단으로 쓰면 submitted 회복을 더 늦출 수 있다.
  - 상향 조건: entry 병목이 해소되고, `unstable_quote_observed=True` 표본이 submitted/fill/COMPLETED + valid profit_rate에서 명확히 악화될 때
  - 하향 조건: unstable 표본과 체결품질/손익 간 차이가 없거나 기존 `ws_age/ws_jitter/spread_ratio`로 충분히 대체될 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `orderbook_stability_observed`는 `ENTRY_PIPELINE` 관찰 이벤트로만 남기며 주문 판단, canary flag, threshold, fallback/scout 경로를 변경하지 않는다.
  2. canary 승격은 현재 entry canary가 submitted 회복과 baseline `N_min`을 충족한 뒤 별도 checklist에서만 검토한다.
  3. 1차 canary 후보는 `BYPASS`가 아니라 `unstable_quote_position_cap` 또는 `unstable_quote_frequency_cap`이며, `scout-only`는 폐기된 fallback/scout 원칙과 충돌하므로 제외한다.
- 다음 액션:
  1. offline bundle summary에서 `unstable_quote_observed_count/share`, `unstable_reason_breakdown`, `unstable_vs_submitted/fill/latency_danger`를 본다.
  2. live gate 승격 전까지는 분석 지표로만 유지한다.

### 4.9A-5 `initial_entry_qty_cap_2share` / `initial_entry_qty_cap_3share_candidate`

- 판정: `2share=active-canary-decision`, `3share=observe-only`
- live 영향도: `2share=limited-live`, `3share=none`
- 튜닝 모니터링 가치: `High`
  - 이유: `2주 cap`은 `buy_qty=1 -> pyramid template_qty=0` 왜곡을 줄이는 현재 수량 가드이고, `3주 cap`은 exposure와 soft stop tail을 직접 키우는 다음 후보라 별도 cohort로 분리해야 한다.
  - 상향 조건: `2주 cap` cohort에서 `zero_qty=0` 유지, `pyramid_activated` 표본 증가, `soft_stop` tail 비악화, `COMPLETED + valid profit_rate` 비악화가 확인될 때
  - 하향 조건: `3주 cap` 후보가 entry live 축과 충돌하거나, 2주 cap 상태에서 soft stop/partial/order_failed가 악화될 때
- EV 판정 기여도: `High`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Low`
- 향후 재개 가능성: `High`
- 근거:
  1. `2026-04-29` full-day 기준 `initial_entry_qty_cap_applied=38`, `ADD_BLOCKED reason=zero_qty=0`, `completed_valid_count=17`, `completed_valid_avg_profit_rate=+0.0535%`, `pyramid_activated=3`이 확인됐다.
  2. `3주 cap`은 `KORSTOCKSCAN_SCALPING_INITIAL_ENTRY_MAX_QTY=3` 또는 상수 변경으로 가능하지만, 현재 `mechanical_momentum_latency_relief`와 같은 entry 단계 변경이므로 같은 날 병행 live 승인 대상이 아니다.
- 다음 액션:
  1. `initial-only`, `pyramid-activated`, `full_fill`, `partial_fill`, `soft_stop`, `order_failed`를 계속 분리한다.
  2. `3주 cap`은 별도 승인조건이 닫히기 전까지 observe-only 후보로만 유지한다.

### 4.9A-6 `ai_cache_hit_miss`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: holding cache hit/miss는 호출량과 decision freshness에 영향을 줄 수 있지만, 현재 structured field가 `submitted/full/partial/COMPLETED`와 안정적으로 조인되지 않는다.
  - 상향 조건: gatekeeper/holding cache hit/miss가 raw event에 canonical field로 남고, `submitted`, `soft_stop`, `COMPLETED + valid profit_rate`와 조인 가능한 schema가 생길 때
  - 하향 조건: cache miss/hit 차이가 호출비용 외 EV/청산 품질과 무관하다고 확인될 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `2026-04-29` 기준 `AI 보유감시` 로그는 `MISS=2260`, `HIT=67`로 관측량은 충분했다.
  2. 그러나 pipeline event에는 `gatekeeper_cache`/`ai_cache`가 제출/체결/손익과 직접 조인되는 structured field로 남아 있지 않아 live go/no-go 근거로 쓸 수 없다.
- 다음 액션:
  1. cache 축은 영향도 0이 아니라 `schema gap`으로 둔다.
  2. canary가 아니라 structured logging 보강 후보로만 유지한다.

### 4.9A-7 `execution_receipt_binding_quality`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `High`
  - 이유: WS 실제체결이 들어왔는데 active order binding이 실패하면 보유/청산 판단보다 먼저 runtime truth가 흔들린다.
  - 상향 조건: BUY/SELL `EXEC_IGNORED`가 반복되고, 계좌동기화가 HOLDING/COMPLETED 복구를 대신하는 빈도가 늘 때
  - 하향 조건: order number binding race가 해결되고 정기 계좌동기화 의존도가 낮아졌을 때
- EV 판정 기여도: `High`
- 대체 가능성: `Low`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `High`
- 근거:
  1. `SK이노베이션(096770)`은 `2026-04-29 13:28:19 BUY`, `15:06:28 SELL` 모두 WS 실제체결이 있었지만 `[EXEC_IGNORED] no matching active order`로 빠졌다.
  2. 정기 계좌동기화가 `BROKER_RECOVER -> HOLDING`, 이후 `잔고 없음 -> COMPLETED`를 대신 수행했다.
  3. 사용자는 단절 리스크 때문에 HTS에서 수동 매도했고, 실제 체결 기준 수익률은 비용 반영 약 `+4.2%`였다.
- 다음 액션:
  1. 이 축은 alpha canary가 아니라 `EV 판정 전제 품질축`으로 유지한다.
  2. `ORDER_NOTICE_BOUND -> WS 실제체결 -> active order binding` 경로를 BUY/SELL로 분리해 추적한다.

### 4.9A-8 `gemini_schema_registry_flag_off` / `deepseek_retry_acceptance_flag_off`

- 판정: `observe-only`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Medium`
  - 이유: 둘 다 live enable이 아니라 flag-off load/contract/log visibility 묶음이다. 기본 live 동작을 바꾸지 않지만, 이후 AI engine enable acceptance의 전제다.
  - 상향 조건: Gemini schema registry가 endpoint별 response_schema ingress와 fallback/test matrix를 갖추고, DeepSeek retry acceptance가 `api_call_lock`/rate-limit/server-error 경로에서 충분히 관찰될 때
  - 하향 조건: live enable 계획이 폐기되거나 기존 text fallback만으로 충분하다고 확정될 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. Gemini `holding_exit_v1` enum/normalization contract와 `eod_top5_v1` required field gap은 live enable 전 필수 정합성 항목으로 남아 있다.
  2. DeepSeek context-aware backoff guard는 준비됐지만, retry acceptance 문서화와 로그 확인 전에는 enable 불가다.
- 다음 액션:
  1. flag 기본값 OFF를 유지한다.
  2. `GeminiSchemaContractCarry0430`, `DeepSeekAcceptanceCarry0430`, `DeepSeekInterfaceGap0430`에서 contract/test/log visibility만 닫는다.

### 4.9B `latency_guard_canary`

- 판정: `active-canary`
- live 영향도: `guarded-off`
- 튜닝 모니터링 가치: `Low`
  - 이유: broad `REJECT_DANGER -> fallback override` 경로라 현재 원인귀속 원칙과 잘 맞지 않는다.
  - 상향 조건: 세부 relief 축이 모두 실패하고 broad override를 다시 비교해야 할 때
  - 하향 조건: `spread/ws_jitter/other_danger` 세부축 체계가 굳을 때
- EV 판정 기여도: `Low`
- 대체 가능성: `High`
- 운영 부하/지연 비용: `Medium`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Low`
- 근거:
  1. 기본값이 `False`이고 broad fallback canary 성격이다.
  2. same-day 운영은 세부 relief 축 분해 쪽으로 이동했다.
- 다음 액션:
  1. 장기간 재개 근거가 없으면 `remove` 후보로 낮추는 재판정 필요
  2. 유지하더라도 broad legacy 축으로 취급

### 4.9C `strength_shadow_feedback`

- 판정: `observe-only`
- live 영향도: `none`
- 튜닝 모니터링 가치: `Medium`
  - 이유: dynamic strength 경계 표본을 장후에 후행평가하는 전용 shadow 피드백이다.
  - 상향 조건: `dynamic_strength_relief` 경계값을 재튜닝하거나 운영 해석을 다시 조정할 때
  - 하향 조건: dynamic strength가 완전 baseline이 되고 경계 표본을 더 이상 안 볼 때
- EV 판정 기여도: `Medium`
- 대체 가능성: `Medium`
- 운영 부하/지연 비용: `Low`
- 코드 유지비: `Medium`
- 향후 재개 가능성: `Medium`
- 근거:
  1. `shadow_candidate_recorded`와 별도 JSONL 평가 경로를 유지한다.
  2. 실주문 개입 없이 post-close evaluation만 수행한다.
- 다음 액션:
  1. `dynamic_strength_relief` 운영 해석 변경 시 유지 여부를 함께 재판정
  2. 경계 표본 가치가 낮아지면 `remove` 후보로 내린다

---

## 부록: 최소 후속 코드세트 연결

이 문서 기준의 다음 코드세트 우선순위는 아래로 고정한다.

1. `remove`
   - `watching_prompt_75_shadow`
2. `observe-only 유지 문서화`
   - `dual_persona`
   - `watching_shared_prompt_shadow`
   - `hard_time_stop_shadow`
   - `ai_holding_shadow_band`
   - `same_symbol_soft_stop_cooldown_shadow`
   - `partial_only_timeout_shadow`
   - `strength_shadow_feedback`
3. `baseline-promote historical/current 표기 유지`
   - `dynamic_strength_canary` (`dynamic_strength_relief`)
   - `partial_fill_ratio_canary` (`partial_fill_ratio_guard`)
4. `active-canary 운영/parking 판정`
  - `buy_recovery_canary`
  - `wait6579_probe_canary`
  - `latency_guard_canary`
  - `mechanical_momentum_latency_relief`
  - `spread_relief_canary`
  - `ws_jitter_relief_canary`
  - `other_danger_relief_canary`

이 순서를 지켜 `remove`, `observe-only`, `baseline-promote`, `active-canary`를 섞어 동시에 건드리지 않는다.
