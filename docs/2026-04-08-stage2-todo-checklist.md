# 2026-04-08 Stage 2 To-Do Checklist

## 목적

- 2단계 잔여 plan을 무리하게 당겨 바꾸지 않고, 내일 해야 할 관측/설계 작업을 순서대로 정리한다.
- 특히 `공통 hard time stop`처럼 크리티컬한 변경은 충분한 기준을 만든 뒤 결정한다.

## 순서 재정의

- `ai_holding_shadow_band`는 "내일 할 일"이 아니라 **내일 데이터를 받기 위한 오늘 선행 작업**이다.
- 따라서 체크리스트는 `오늘 선반영` → `내일 장중 관찰` → `내일 장후 분석` 순으로 본다.
- 봇은 사용자가 수동으로 재실행할 예정이므로, 오늘 항목은 `코드 선반영 완료`와 `운영 로그 확인 대기`를 분리해서 본다.

## 오늘(2026-04-07) 선반영 필수

- [x] `ai_holding_shadow_band` 로그 추가
  - `near_ai_exit`, `near_safe_profit` 때문에 실제 fresh review가 몇 건 발생하는지 내일부터 바로 수집 시작
- [x] 봇 수동 재실행 완료
  - `2026-04-07 16:38 KST` 기준 `python bot_main.py` 신규 프로세스 재기동 확인
- [ ] 운영 로그 확인
  - 실제 `HOLDING_PIPELINE` 로그에 `ai_holding_shadow_band`가 찍히는지 확인
  - `review|skip` action과 `distance_to_*` 값이 정상 형식으로 남는지 함께 점검
  - `2026-04-07 16:39 KST` 현재는 장마감 후 `WATCHING` 로그만 확인되어 첫 보유 AI 사이클 발생 전까지는 pending

## 내일(2026-04-08) 장중 바로 확인할 일

- [ ] `age_sec` 수정 후 운영 모니터링
  - `trade-review`와 실시간 로그에 epoch 수준 숫자가 재발하지 않는지 확인
- [ ] `ai_holding_shadow_band` 표본 정상 수집 확인
  - 전제: 오늘 반영 코드 기준으로 봇 수동 재실행은 완료됨
  - `review|skip` action이 모두 기대한 형식으로 찍히는지 확인
  - `near_ai_exit`, `near_safe_profit`, `distance_to_*` 값이 비정상 없이 기록되는지 확인
- [ ] 보유 AI 재사용 경로 모니터링
  - `holding_skip_ratio`, `holding_ai_cache_hit_ratio`, `holding_reuse_blockers` 변화 추적
- [ ] 스윙 market regime 상태 기록
  - 세션 기준 `risk_state`, `allow_swing_entry`, `swing_score`를 최소 시작/중간/마감 기준으로 확인
  - `allow_swing_entry=false`가 유지된 날은 threshold 완화 검토일과 분리
- [ ] 스윙 blocker 실시간 분류
  - `market_regime_block`, `blocked_gatekeeper_reject`, `blocked_swing_gap`, `blocked_zero_qty`, `latency_entry_block`를 구분해서 본다
  - `blocked_gatekeeper_reject`는 `action_label`, `cooldown_policy`를 함께 기록

## 내일(2026-04-08) 장후 분석할 일

- [ ] `curr`, `spread` 완화 후보 분석용 기준 정리
  - `holding_sig_deltas` 상위 필드가 시간대/종목별로 어떻게 달라지는지 집계 축 정의
- [ ] fallback 진입 거래 표본 분리
  - `entry_mode=normal/fallback` 기준으로 승률, 평균 보유시간, 평균 손익을 같은 포맷으로 비교
- [ ] shadow band 1일차 결과 요약
  - `near_ai_exit`, `near_safe_profit` 때문에 review로 간 건수를 초안 수준으로라도 집계
- [ ] 공통 hard time stop 설계용 기초 표본 정리
  - 긴 보유 손실 거래를 `entry_mode`, `position_tag`, `peak_profit`, `시간대` 기준으로 분해
- [ ] 스윙 0진입 원인 일일 분류
  - `RISK_OFF / allow_swing_entry=false` day인지 먼저 판정
  - 그 다음 `Gatekeeper reject day`인지, `swing gap day`인지, 기타 실행 차단인지 분리
- [ ] 스윙 Gatekeeper missed case 정리
  - `blocked_gatekeeper_reject` 종목 중 이후 추세가 실제로 좋았던 표본이 있었는지 확인
  - `dual_persona_shadow`가 `ALLOW` 또는 더 공격적인 결론이었던 케이스를 같이 기록
- [ ] 스윙 gap 완화 검토 전제 확인
  - 실제 `blocked_swing_gap` 샘플이 있었는지 먼저 확인
  - 샘플이 없으면 gap 완화 논의는 다음날로 미룬다

## 공통 Hard Time Stop 기준 설계 체크

- [ ] 단순 `N분 청산`으로 갈지, 조건부 hard stop으로 갈지 먼저 결정
- [ ] 최소 분류 축 확정
  - `entry_mode`
  - `position_tag`
  - `peak_profit`
  - `current profit_rate`
  - `AI score 추이`
  - `time-of-day`
- [ ] 비교 후보안 작성
  - `3분`, `5분`, `7분` 단일 cut
  - `5분 + 저점수`
  - `fallback 전용 3~5분 cut`
  - `수익 미전환 + 장시간 보유` 조건부 cut
- [ ] 오늘 포함 최근 거래일에서 각 후보안이 승률/손익에 주는 영향 추정

## 내일은 아직 바꾸지 않을 것

- [ ] `near_safe_profit` 수치 직접 하향
- [ ] `near_ai_exit` 수치 직접 완화
- [ ] 공통 hard time stop 실전 적용
- [ ] fallback 전면 차단
- [ ] Early Exit 임계값 직접 완화
- [ ] 스윙 AI threshold 직접 완화
- [ ] `RISK_OFF` 상태의 스윙 허용 기준 완화
- [ ] `dual_persona_shadow`의 스윙 실전 승급
- [ ] 스윙 gap 기준 직접 완화

## 내일 작업 완료 기준

- [ ] 오늘 반영한 `ai_holding_shadow_band` 로그가 실제 장중 로그에 찍힌다
- [ ] fallback/normal 비교표가 나온다
- [ ] hard time stop 설계 후보안 2~3개와 각각의 장단점이 문서화된다
- [ ] `2026-04-09`에 바로 이어서 판단할 수 있을 수준의 근거가 정리된다
- [ ] 스윙 day를 `market-regime 제한` / `gatekeeper 거부 중심` / `gap 차단 중심` 중 하나로 분류할 수 있다
- [ ] 스윙 missed case 요약표가 남고, threshold 완화 검토 여부를 근거 기반으로 말할 수 있다

## 참고 문서

- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [2026-04-07-performance-tuning-checklist.md](./2026-04-07-performance-tuning-checklist.md)
- [2026-04-07-stage2-task1-execution-report.md](./2026-04-07-stage2-task1-execution-report.md)
- [2026-04-07-swing-results](./2026-04-07-swing-results)
