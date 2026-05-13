# Codex 작업지시서: 패닉바잉 시작 및 소진 탐지 로직 고도화

## 1. 작업 목표

기존의 기계적 익절 로직은 일반적인 상승 구간에서는 안정적이지만, **패닉바잉 / 급등성 매수 쏠림 구간**에서는 기대값(EV)을 낮출 수 있다.

본 작업의 목표는 다음과 같다.

1. **패닉바잉 시작 탐지**
   - 고정 익절을 전량 실행하지 않고 일부 물량을 runner로 전환할 수 있는 구간을 탐지한다.
   - 가격 상승률만 보지 않고 거래량, 공격적 매수 체결, CVD, OFI, Ask depth sweep, 종가 위치를 함께 본다.

2. **패닉바잉 잦아듦 / 소진 탐지**
   - 매수 쏠림이 약해지고 상단 흡수가 시작되는 구간을 탐지한다.
   - runner 물량을 정리하거나 trailing stop을 타이트하게 조이는 신호를 반환한다.

3. **익절 정책과 분리된 신호 모듈 구현**
   - 본 모듈은 주문을 직접 실행하지 않는다.
   - `allow_tp_override`, `allow_runner`, `tighten_trailing_stop`, `force_exit_runner` 같은 flag만 반환한다.

4. **상태머신 기반 관리**
   - 단일 캔들 조건으로 판단하지 않는다.
   - M-of-N 지속성 확인과 cooldown을 통해 상태 플립플롭을 방지한다.

---

## 2. 핵심 개념

패닉바잉은 단순 상승이 아니다.

```text
단순 상승:
    완만한 상승률
    정상 거래량
    호가 안정
    buy_ratio 중립 또는 약한 우위

패닉바잉:
    단시간 급등
    거래량 폭증
    공격적 매수 체결 집중
    CVD 급상승
    OFI 강한 양수
    Ask depth 급격한 소진
    종가가 고가 근처
```

따라서 패닉바잉 탐지는 **진입 신호**가 아니라, 주로 **보유 포지션의 익절 방식을 바꾸는 리스크/수익 관리 신호**로 사용한다.

```text
일반 구간:
    고정 TP 도달 시 전량 익절

패닉바잉 active:
    일부 익절 + runner 유지

패닉바잉 소진 후보:
    runner 유지 가능
    단, trailing stop 강화

패닉바잉 소진 확정:
    runner 청산 또는 매우 타이트한 trailing stop
```

---

## 3. 구현 대상 파일 구조

아래 구조로 구현한다.

```text
src/
  panic_buy/
    __init__.py
    config.py
    models.py
    features.py
    detector.py
    state_machine.py
    reasons.py
    exit_policy.py

tests/
  test_panic_buy_features.py
  test_panic_buy_detector_entry.py
  test_panic_buy_detector_exhaustion.py
  test_panic_buy_state_machine.py
  test_panic_buy_exit_policy.py
```

기존 프로젝트 구조가 다르면 동일한 책임 단위로 적절히 통합한다.

---

## 4. 상태 정의

`state_machine.py`에 다음 enum을 구현한다.

```python
from enum import Enum


class PanicBuyState(str, Enum):
    NORMAL = "NORMAL"
    PANIC_BUY_CANDIDATE = "PANIC_BUY_CANDIDATE"
    PANIC_BUY_ACTIVE = "PANIC_BUY_ACTIVE"
    BUYING_EXHAUSTION_CANDIDATE = "BUYING_EXHAUSTION_CANDIDATE"
    BUYING_EXHAUSTED = "BUYING_EXHAUSTED"
    COOLDOWN = "COOLDOWN"
```

상태별 의미는 다음과 같다.

```text
NORMAL:
    일반 시장 상태.
    기존 익절 로직 그대로 사용.

PANIC_BUY_CANDIDATE:
    패닉바잉 가능성이 생긴 상태.
    아직 확정은 아니지만 전량 익절을 유예할 수 있는 준비 상태.

PANIC_BUY_ACTIVE:
    패닉바잉 확정 상태.
    고정 TP 전량 청산 대신 부분 익절 + runner 전략 허용.

BUYING_EXHAUSTION_CANDIDATE:
    매수 쏠림이 잦아드는 후보 상태.
    trailing stop을 강화한다.

BUYING_EXHAUSTED:
    패닉바잉 소진 확정 상태.
    잔여 runner 청산 또는 강제 청산 flag를 반환한다.

COOLDOWN:
    소진 이후 재진입/상태 플립플롭 방지를 위한 대기 상태.
```

---

## 5. 데이터 모델

### 5.1 입력 데이터 모델

`models.py`에 다음 데이터 클래스를 구현한다.

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Sequence


class AggressorSide(str, Enum):
    BUY = "buy"
    SELL = "sell"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Candle:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Optional[float] = None


@dataclass(frozen=True)
class TradeAgg:
    ts: datetime
    buy_volume: float
    sell_volume: float
    unknown_volume: float = 0.0

    @property
    def total_volume(self) -> float:
        return self.buy_volume + self.sell_volume + self.unknown_volume


@dataclass(frozen=True)
class OrderBookSnapshot:
    ts: datetime
    bid_prices: Sequence[float]
    bid_sizes: Sequence[float]
    ask_prices: Sequence[float]
    ask_sizes: Sequence[float]


@dataclass(frozen=True)
class MarketContext:
    market_return_short: Optional[float] = None
    sector_return_short: Optional[float] = None
    symbol_beta: Optional[float] = None
```

---

### 5.2 출력 데이터 모델

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class PanicBuySignal:
    state: str

    panic_buy_score: float
    exhaustion_score: float

    panic_buy_active: bool
    panic_buy_entered: bool
    exhaustion_candidate: bool
    exhaustion_confirmed: bool

    allow_tp_override: bool
    allow_runner: bool
    tighten_trailing_stop: bool
    force_exit_runner: bool

    panic_buy_high: Optional[float] = None
    panic_buy_start_ts: Optional[str] = None

    severity: str = "LOW"
    confidence: float = 0.0

    reasons: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
```

상태별 기본 flag는 다음과 같다.

```text
NORMAL:
    allow_tp_override=False
    allow_runner=False
    tighten_trailing_stop=False
    force_exit_runner=False

PANIC_BUY_CANDIDATE:
    allow_tp_override=True
    allow_runner=True
    tighten_trailing_stop=False
    force_exit_runner=False

PANIC_BUY_ACTIVE:
    allow_tp_override=True
    allow_runner=True
    tighten_trailing_stop=False
    force_exit_runner=False

BUYING_EXHAUSTION_CANDIDATE:
    allow_tp_override=False
    allow_runner=True
    tighten_trailing_stop=True
    force_exit_runner=False

BUYING_EXHAUSTED:
    allow_tp_override=False
    allow_runner=False
    tighten_trailing_stop=True
    force_exit_runner=True

COOLDOWN:
    allow_tp_override=False
    allow_runner=False
    tighten_trailing_stop=False
    force_exit_runner=False
```

---

## 6. 설정값

`config.py`에 다음 설정 클래스를 구현한다. 모든 임계값은 하드코딩하지 말고 config로 관리한다.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class PanicBuyConfig:
    # rolling windows
    short_window_bars: int = 6
    mid_window_bars: int = 18
    long_window_bars: int = 120

    # minimum data
    min_bars_required: int = 120
    min_total_volume: float = 1.0
    min_depth_levels: int = 5

    # panic buying entry
    panic_buy_entry_score_threshold: float = 0.72
    panic_buy_confirm_bars: int = 2
    panic_buy_confirm_window: int = 3

    min_abs_rise_short_pct: float = 1.2
    min_abs_rise_mid_pct: float = 2.5
    return_z_panic_buy_threshold: float = 2.2

    volume_spike_threshold: float = 2.8
    buy_ratio_threshold: float = 0.64
    cvd_slope_buy_threshold: float = 2.0
    ofi_z_panic_buy_threshold: float = 2.0

    ask_depth_drop_threshold: float = 0.35
    bid_depth_support_threshold: float = 1.15
    spread_widen_threshold: float = 1.8
    close_near_high_threshold: float = 0.75
    range_expansion_threshold: float = 1.5

    # exhaustion
    exhaustion_score_threshold: float = 0.66
    exhaustion_confirm_bars: int = 2
    exhaustion_confirm_window: int = 4

    no_new_high_bars: int = 3
    high_break_tolerance_pct: float = 0.15

    buy_ratio_exhaustion_max: float = 0.58
    cvd_slope_exhaustion_max: float = 0.4
    ofi_z_exhaustion_max: float = 0.3

    ask_depth_refill_min: float = 0.70
    failed_ask_sweep_threshold: int = 2

    upper_wick_exhaustion_min: float = 0.45
    close_location_exhaustion_max: float = 0.45
    price_progress_exhaustion_max: float = 0.35

    vwap_extension_extreme_pct: float = 3.0
    atr_extension_extreme: float = 2.5

    # state timing
    max_panic_buy_active_bars: int = 60
    cooldown_bars: int = 12

    # exit behavior
    block_full_tp_during_panic_buy: bool = True
    allow_partial_tp_during_panic_buy: bool = True
    default_partial_tp_ratio: float = 0.4

    # data behavior
    use_orderbook_features: bool = True
    use_trade_aggressor_features: bool = True
    degrade_when_orderbook_missing: bool = True
```

---

## 7. Feature 계산

`features.py`에 아래 feature들을 계산한다.

### 7.1 가격 관련 feature

구현 항목:

```text
1. short_return_pct
2. mid_return_pct
3. long_return_pct
4. short_return_z
5. mid_return_z
6. price_up_velocity
7. price_up_acceleration
8. close_location_value
9. upper_wick_ratio
10. lower_wick_ratio
11. range_expansion_ratio
12. breakout_distance_pct
13. price_progress_ratio
```

수익률 계산:

```python
short_return_pct = (close_now / close_n_bars_ago - 1.0) * 100.0
```

종가 위치:

```python
def close_location_value(open_: float, high: float, low: float, close: float) -> float:
    if high > low:
        return (close - low) / (high - low)
    return 0.5
```

해석:

```text
clv >= 0.75:
    종가가 고가 부근.
    강한 매수 마감.

clv <= 0.45:
    고가에서 밀림.
    패닉바잉 소진 후보.
```

윗꼬리 비율:

```python
def upper_wick_ratio(open_: float, high: float, low: float, close: float) -> float:
    candle_range = high - low
    if candle_range <= 0:
        return 0.0
    upper_wick = high - max(open_, close)
    return upper_wick / candle_range
```

가격 진전 비율:

```python
price_progress_ratio = abs(close_now - close_prev) / max(high_now - low_now, epsilon)
```

해석:

```text
거래량이 큰데 price_progress_ratio가 낮으면 effort-result divergence 가능성 증가.
```

---

### 7.2 거래량 관련 feature

구현 항목:

```text
1. volume_ratio_short
2. volume_z
3. volume_peak_decay
4. abnormal_volume_flag
```

예시:

```python
volume_ratio_short = current_volume / max(ewma_volume_long, epsilon)
```

주의:

```text
저유동성 종목에서는 volume_ratio가 왜곡될 수 있다.
min_total_volume 이하에서는 panic_buy_score를 cap 처리한다.
```

---

### 7.3 체결 방향 관련 feature

`TradeAgg`가 있을 경우 계산한다.

구현 항목:

```text
1. buy_ratio
2. sell_ratio
3. cvd_delta
4. cvd
5. cvd_slope
6. cvd_slope_z
7. buy_pressure_decay
8. cvd_divergence
```

공식:

```python
buy_ratio = buy_volume / max(total_volume, epsilon)
sell_ratio = sell_volume / max(total_volume, epsilon)
cvd_delta = buy_volume - sell_volume
```

해석:

```text
buy_ratio >= 0.64:
    공격적 매수 우위.

buy_ratio <= 0.58:
    패닉바잉 소진 가능성.
```

CVD bearish divergence:

```python
cvd_bearish_divergence = (
    current_high > previous_swing_high
    and current_cvd <= previous_swing_cvd_high
)
```

의미:

```text
가격은 고점 갱신했지만 CVD는 고점 갱신 실패.
시장가 매수의 가격 상승 효율이 떨어지고 있음.
```

---

### 7.4 호가 관련 feature

`OrderBookSnapshot`이 있을 경우 계산한다.

구현 항목:

```text
1. bid_depth_l5
2. ask_depth_l5
3. depth_imbalance
4. ask_depth_drop_ratio
5. ask_depth_refill_ratio
6. bid_depth_support_ratio
7. spread
8. spread_ratio
9. ofi
10. ofi_z
11. failed_ask_sweep_count
12. ask_absorption
```

L5 depth:

```python
bid_depth_l5 = sum(snapshot.bid_sizes[:5])
ask_depth_l5 = sum(snapshot.ask_sizes[:5])
```

Ask depth drop:

```python
ask_depth_drop_ratio = 1.0 - current_ask_depth_l5 / max(ask_depth_l5_ewma, epsilon)
```

Ask depth refill:

```python
ask_depth_refill_ratio = current_ask_depth_l5 / max(pre_panic_or_long_ewma_ask_depth_l5, epsilon)
```

Bid depth support:

```python
bid_depth_support_ratio = current_bid_depth_l5 / max(bid_depth_l5_ewma, epsilon)
```

Spread ratio:

```python
spread = best_ask - best_bid
spread_ratio = spread / max(ewma_spread_long, epsilon)
```

OFI 예시:

```python
def calc_ofi(prev, curr):
    ofi = 0.0

    prev_bid_px = prev.bid_prices[0]
    prev_bid_sz = prev.bid_sizes[0]
    curr_bid_px = curr.bid_prices[0]
    curr_bid_sz = curr.bid_sizes[0]

    prev_ask_px = prev.ask_prices[0]
    prev_ask_sz = prev.ask_sizes[0]
    curr_ask_px = curr.ask_prices[0]
    curr_ask_sz = curr.ask_sizes[0]

    if curr_bid_px > prev_bid_px:
        ofi += curr_bid_sz
    elif curr_bid_px < prev_bid_px:
        ofi -= prev_bid_sz
    else:
        ofi += curr_bid_sz - prev_bid_sz

    if curr_ask_px < prev_ask_px:
        ofi -= curr_ask_sz
    elif curr_ask_px > prev_ask_px:
        ofi += prev_ask_sz
    else:
        ofi += prev_ask_sz - curr_ask_sz

    return ofi
```

해석:

```text
ofi_z >= +2.0:
    강한 매수성 주문흐름.

ofi_z <= +0.3:
    매수 압력 둔화.

ofi_z < 0:
    패닉바잉 소진 또는 반전 가능성 증가.
```

Ask absorption:

```python
ask_absorption = (
    ask_depth_refill_ratio >= 0.70
    and buy_ratio >= 0.62
    and price_progress_ratio <= 0.35
)
```

의미:

```text
시장가 매수는 계속 들어오지만 상단 매물이 이를 흡수하고 있어 가격 전진이 둔화됨.
```

---

## 8. 패닉바잉 시작 탐지 로직

`detector.py`에 `PanicBuyDetector` 클래스를 구현한다.

### 8.1 패닉바잉 시작 필수 조건

패닉바잉 시작은 다음 조건 조합으로 판단한다.

```python
price_breakout = (
    features.short_return_pct >= config.min_abs_rise_short_pct
    or features.mid_return_pct >= config.min_abs_rise_mid_pct
    or features.short_return_z >= config.return_z_panic_buy_threshold
)

flow_confirmation = (
    features.volume_ratio_short >= config.volume_spike_threshold
    and (
        features.buy_ratio >= config.buy_ratio_threshold
        or features.cvd_slope_z >= config.cvd_slope_buy_threshold
        or features.ofi_z >= config.ofi_z_panic_buy_threshold
    )
)

liquidity_confirmation = (
    features.ask_depth_drop_ratio >= config.ask_depth_drop_threshold
    or features.spread_ratio >= config.spread_widen_threshold
)

candle_confirmation = (
    features.close_location_value >= config.close_near_high_threshold
    and features.range_expansion_ratio >= config.range_expansion_threshold
)
```

호가 데이터가 안정적이면 다음처럼 판단한다.

```python
panic_buy_candidate = (
    price_breakout
    and flow_confirmation
    and liquidity_confirmation
    and panic_buy_score >= config.panic_buy_entry_score_threshold
)
```

호가 데이터가 없는 경우 degrade mode로 동작한다.

```python
panic_buy_candidate = (
    price_breakout
    and flow_confirmation
    and panic_buy_score >= config.panic_buy_entry_score_threshold
)
```

이 경우 reason에 `orderbook_missing_degraded`를 포함하고 confidence를 낮춘다.

---

## 9. 패닉바잉 score 계산

패닉바잉 score는 0.0 ~ 1.0 범위로 계산한다.

```python
panic_buy_score = (
    0.28 * price_up_score
    + 0.17 * volume_score
    + 0.22 * trade_flow_score
    + 0.18 * orderbook_sweep_score
    + 0.07 * spread_score
    + 0.08 * candle_strength_score
)
```

보조 함수:

```python
def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))
```

개별 score 예시:

```python
price_up_score = max(
    clamp01(features.short_return_pct / config.min_abs_rise_short_pct),
    clamp01(features.mid_return_pct / config.min_abs_rise_mid_pct),
    clamp01(features.short_return_z / config.return_z_panic_buy_threshold),
)

volume_score = clamp01(
    features.volume_ratio_short / config.volume_spike_threshold
)

trade_flow_score = max(
    clamp01(features.buy_ratio / config.buy_ratio_threshold),
    clamp01(features.cvd_slope_z / config.cvd_slope_buy_threshold),
    clamp01(features.ofi_z / config.ofi_z_panic_buy_threshold),
)

orderbook_sweep_score = max(
    clamp01(features.ask_depth_drop_ratio / config.ask_depth_drop_threshold),
    clamp01(features.bid_depth_support_ratio / config.bid_depth_support_threshold),
)

spread_score = clamp01(
    features.spread_ratio / config.spread_widen_threshold
)

candle_strength_score = clamp01(
    features.close_location_value / config.close_near_high_threshold
)
```

호가 데이터가 없으면 orderbook 관련 score를 임의로 재분배하지 않는다. 대신 score 상한을 둔다.

```python
if orderbook_missing:
    panic_buy_score = min(panic_buy_score, 0.82)
```

저유동성 cap:

```python
if features.total_volume < config.min_total_volume:
    panic_buy_score = min(panic_buy_score, 0.45)
    reasons.append("low_liquidity_score_capped")
```

---

## 10. 패닉바잉 소진 탐지 로직

패닉바잉 소진은 단순 음봉 하나로 판단하지 않는다.

핵심은 다음이다.

```text
매수 노력은 여전히 큰데,
가격 상승 결과가 약해지는 구간.
```

이를 `effort-result divergence`로 정의한다.

---

### 10.1 소진 후보 조건

```python
no_new_high = (
    current_high <= panic_buy_high * (1.0 + config.high_break_tolerance_pct / 100.0)
)

velocity_decay = (
    features.price_up_velocity < features.prev_price_up_velocity
    and features.price_up_acceleration <= 0
)

flow_decay = (
    features.buy_ratio <= config.buy_ratio_exhaustion_max
    or features.cvd_slope_z <= config.cvd_slope_exhaustion_max
    or features.ofi_z <= config.ofi_z_exhaustion_max
)

supply_returning = (
    features.ask_depth_refill_ratio >= config.ask_depth_refill_min
    or features.failed_ask_sweep_count >= config.failed_ask_sweep_threshold
)

candle_exhaustion = (
    features.upper_wick_ratio >= config.upper_wick_exhaustion_min
    or features.close_location_value <= config.close_location_exhaustion_max
)

effort_result_divergence = (
    features.volume_ratio_short >= config.volume_spike_threshold
    and features.price_progress_ratio <= config.price_progress_exhaustion_max
)
```

소진 후보:

```python
buying_exhaustion_candidate = (
    no_new_high
    and (
        velocity_decay
        or flow_decay
        or supply_returning
    )
    and (
        candle_exhaustion
        or effort_result_divergence
    )
    and exhaustion_score >= config.exhaustion_score_threshold
)
```

---

## 11. 소진 score 계산

소진 score는 0.0 ~ 1.0 범위로 계산한다.

```python
exhaustion_score = (
    0.22 * price_stall_score
    + 0.20 * flow_decay_score
    + 0.18 * orderbook_absorption_score
    + 0.15 * candle_exhaustion_score
    + 0.15 * effort_result_divergence_score
    + 0.10 * extension_risk_score
)
```

각 항목의 의미:

```text
price_stall_score:
    고점 갱신 실패, 상승 속도 둔화.

flow_decay_score:
    buy_ratio, CVD slope, OFI가 약화.

orderbook_absorption_score:
    Ask depth가 다시 쌓이고 시장가 매수가 더 이상 위로 밀지 못함.

candle_exhaustion_score:
    윗꼬리, 종가 위치 하락, 장대양봉 이후 도지/음봉.

effort_result_divergence_score:
    거래량은 큰데 가격 진전이 작음.

extension_risk_score:
    VWAP, 단기 EMA, ATR 대비 과도한 이격.
```

예시 구현:

```python
price_stall_score = max(
    1.0 if no_new_high_for_n_bars else 0.0,
    clamp01(1.0 - features.price_up_velocity / max(features.prev_price_up_velocity, epsilon)),
)

flow_decay_score = max(
    clamp01((config.buy_ratio_threshold - features.buy_ratio) /
            max(config.buy_ratio_threshold - config.buy_ratio_exhaustion_max, epsilon)),
    clamp01((config.ofi_z_panic_buy_threshold - features.ofi_z) /
            max(config.ofi_z_panic_buy_threshold - config.ofi_z_exhaustion_max, epsilon)),
    clamp01((config.cvd_slope_buy_threshold - features.cvd_slope_z) /
            max(config.cvd_slope_buy_threshold - config.cvd_slope_exhaustion_max, epsilon)),
)

orderbook_absorption_score = max(
    clamp01(features.ask_depth_refill_ratio / config.ask_depth_refill_min),
    1.0 if features.ask_absorption else 0.0,
)

candle_exhaustion_score = max(
    clamp01(features.upper_wick_ratio / config.upper_wick_exhaustion_min),
    clamp01((config.close_near_high_threshold - features.close_location_value) /
            max(config.close_near_high_threshold - config.close_location_exhaustion_max, epsilon)),
)

effort_result_divergence_score = (
    1.0 if effort_result_divergence else 0.0
)

extension_risk_score = max(
    clamp01(features.vwap_extension_pct / config.vwap_extension_extreme_pct),
    clamp01(features.atr_extension / config.atr_extension_extreme),
)
```

---

## 12. 상태 전환 규칙

```text
NORMAL
  -> PANIC_BUY_CANDIDATE
     조건: panic_buy_candidate True

PANIC_BUY_CANDIDATE
  -> PANIC_BUY_ACTIVE
     조건: 최근 panic_buy_confirm_window개 바 중
           panic_buy_score >= threshold인 바가 panic_buy_confirm_bars개 이상

PANIC_BUY_CANDIDATE
  -> NORMAL
     조건: breakout 실패, buy flow 약화, score 하락

PANIC_BUY_ACTIVE
  -> BUYING_EXHAUSTION_CANDIDATE
     조건: exhaustion_score >= threshold
           그리고 no_new_high 또는 flow_decay 조건 충족

PANIC_BUY_ACTIVE
  -> PANIC_BUY_ACTIVE 유지
     조건: 고점 갱신 지속, buy_ratio/OFI/CVD 강함

BUYING_EXHAUSTION_CANDIDATE
  -> PANIC_BUY_ACTIVE
     조건: 고점 재돌파, OFI 재강화, ask sweep 재개

BUYING_EXHAUSTION_CANDIDATE
  -> BUYING_EXHAUSTED
     조건: 최근 exhaustion_confirm_window개 바 중
           exhaustion_score >= threshold인 바가 exhaustion_confirm_bars개 이상

BUYING_EXHAUSTED
  -> COOLDOWN
     조건: 소진 확정 직후

COOLDOWN
  -> NORMAL
     조건: cooldown_bars 경과
```

---

## 13. PanicBuyDetector 인터페이스

`detector.py`에 다음 클래스를 구현한다.

```python
class PanicBuyDetector:
    def __init__(self, config: PanicBuyConfig):
        ...

    def update(
        self,
        candle: Candle,
        trade_agg: TradeAgg | None = None,
        orderbook: OrderBookSnapshot | None = None,
        market_context: MarketContext | None = None,
    ) -> PanicBuySignal:
        ...
```

내부적으로 다음 값을 추적한다.

```python
self.state
self.bars_in_state
self.panic_buy_start_ts
self.panic_buy_high
self.panic_buy_entry_price
self.max_panic_buy_score
self.max_exhaustion_score
self.recent_panic_buy_scores
self.recent_exhaustion_scores
self.cooldown_remaining
self.panic_buy_anchored_vwap_state
self.cvd_state
self.previous_swing_high
self.previous_swing_cvd_high
```

---

## 14. 의사코드

```python
def update(candle, trade_agg=None, orderbook=None, market_context=None):
    append_to_rolling_buffers(candle, trade_agg, orderbook)

    if not enough_data:
        return neutral_signal(reason="insufficient_data")

    features = compute_features(
        candles=rolling_candles,
        trades=rolling_trades,
        orderbooks=rolling_orderbooks,
        market_context=market_context,
        config=config,
    )

    panic_buy_score, panic_buy_reasons = compute_panic_buy_score(features, config)
    exhaustion_score, exhaustion_reasons = compute_exhaustion_score(features, config)

    update_recent_score_buffers(panic_buy_score, exhaustion_score)

    prev_state = state

    if state == NORMAL:
        if is_panic_buy_candidate(features, panic_buy_score):
            transition_to(PANIC_BUY_CANDIDATE)

    elif state == PANIC_BUY_CANDIDATE:
        if confirm_panic_buy_entry():
            transition_to(PANIC_BUY_ACTIVE)
            initialize_panic_buy_tracking(candle)
        elif panic_buy_conditions_faded(features, panic_buy_score):
            transition_to(NORMAL)

    elif state == PANIC_BUY_ACTIVE:
        update_panic_buy_high(candle.high)
        update_panic_buy_anchored_vwap(candle)
        update_cvd_state(trade_agg)

        if exhaustion_candidate_conditions_met(features, exhaustion_score):
            transition_to(BUYING_EXHAUSTION_CANDIDATE)
        elif bars_in_state > config.max_panic_buy_active_bars:
            transition_to(BUYING_EXHAUSTION_CANDIDATE)
        else:
            remain_in(PANIC_BUY_ACTIVE)

    elif state == BUYING_EXHAUSTION_CANDIDATE:
        update_panic_buy_high(candle.high)
        update_panic_buy_anchored_vwap(candle)
        update_cvd_state(trade_agg)

        if panic_buy_resumed(features, panic_buy_score):
            transition_to(PANIC_BUY_ACTIVE)
        elif confirm_exhaustion():
            transition_to(BUYING_EXHAUSTED)

    elif state == BUYING_EXHAUSTED:
        transition_to(COOLDOWN)

    elif state == COOLDOWN:
        cooldown_remaining -= 1
        if cooldown_remaining <= 0:
            reset_panic_buy_tracking()
            transition_to(NORMAL)

    return build_signal(
        state=state,
        prev_state=prev_state,
        panic_buy_score=panic_buy_score,
        exhaustion_score=exhaustion_score,
        reasons=panic_buy_reasons + exhaustion_reasons,
        features=features,
    )
```

---

## 15. Reason 코드

`reasons.py`에 reason 상수를 정의한다.

```python
SHORT_RETURN_BREAKOUT = "short_return_breakout"
MID_RETURN_BREAKOUT = "mid_return_breakout"
POSITIVE_RETURN_Z = "positive_return_z"
VOLUME_SPIKE = "volume_spike"
BUY_RATIO_HIGH = "buy_ratio_high"
CVD_SLOPE_STRONG = "cvd_slope_strong"
OFI_BUY_PRESSURE = "ofi_buy_pressure"
ASK_DEPTH_SWEEP = "ask_depth_sweep"
BID_DEPTH_SUPPORT = "bid_depth_support"
SPREAD_WIDEN = "spread_widen"
CLOSE_NEAR_HIGH = "close_near_high"
RANGE_EXPANSION = "range_expansion"
BREAKOUT_CONFIRMED = "breakout_confirmed"

NO_NEW_HIGH = "no_new_high"
UPSIDE_VELOCITY_DECAY = "upside_velocity_decay"
BUY_RATIO_DECAY = "buy_ratio_decay"
OFI_DECAY = "ofi_decay"
CVD_SLOPE_DECAY = "cvd_slope_decay"
CVD_DIVERGENCE = "cvd_divergence"
ASK_DEPTH_REFILL = "ask_depth_refill"
ASK_ABSORPTION = "ask_absorption"
FAILED_ASK_SWEEP = "failed_ask_sweep"
UPPER_WICK_EXHAUSTION = "upper_wick_exhaustion"
CLOSE_LOCATION_FAILED = "close_location_failed"
EFFORT_RESULT_DIVERGENCE = "effort_result_divergence"
EXTENSION_RISK = "extension_risk"
BUYING_EXHAUSTION_CONFIRMED = "buying_exhaustion_confirmed"

LOW_LIQUIDITY_SCORE_CAPPED = "low_liquidity_score_capped"
ORDERBOOK_MISSING_DEGRADED = "orderbook_missing_degraded"
TRADE_AGGRESSOR_MISSING_DEGRADED = "trade_aggressor_missing_degraded"
```

---

## 16. 익절 정책 연동

`exit_policy.py`에 기존 익절 신호와 패닉바잉 신호를 결합하는 별도 정책 함수를 구현한다.

### 16.1 기존 단순 로직

```python
if pnl_pct >= take_profit_pct:
    close_position()
```

이 방식은 패닉바잉 active 구간에서 EV를 낮출 수 있다.

---

### 16.2 개선된 exit decision

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class PositionState:
    has_long: bool
    pnl_pct: float
    quantity: float


@dataclass(frozen=True)
class NormalExitSignal:
    take_profit_hit: bool
    stop_loss_hit: bool = False


@dataclass(frozen=True)
class ExitDecision:
    action: str
    partial_ratio: float = 0.0
    reason: str = ""
```

```python
def decide_exit(position, normal_exit_signal, panic_buy_signal):
    if not position.has_long:
        return ExitDecision(action="HOLD")

    if normal_exit_signal.stop_loss_hit:
        return ExitDecision(
            action="CLOSE_ALL",
            reason="normal_stop_loss",
        )

    if panic_buy_signal.exhaustion_confirmed:
        return ExitDecision(
            action="CLOSE_ALL",
            reason="panic_buy_exhausted",
        )

    if normal_exit_signal.take_profit_hit:
        if panic_buy_signal.panic_buy_active:
            return ExitDecision(
                action="PARTIAL_TP_AND_RUNNER",
                partial_ratio=0.4,
                reason="tp_hit_but_panic_buy_active",
            )

        if panic_buy_signal.exhaustion_candidate:
            return ExitDecision(
                action="PARTIAL_TP_AND_TIGHT_TRAIL",
                partial_ratio=0.6,
                reason="tp_hit_and_exhaustion_candidate",
            )

        return ExitDecision(
            action="CLOSE_ALL",
            reason="normal_take_profit",
        )

    if panic_buy_signal.exhaustion_candidate:
        return ExitDecision(
            action="TIGHTEN_TRAILING_STOP",
            reason="buying_exhaustion_candidate",
        )

    return ExitDecision(action="HOLD")
```

권장 정책:

```text
TP 도달 + 패닉바잉 active:
    30~50% 부분 익절
    잔여 물량 runner 전환

패닉바잉 active 유지:
    trailing stop은 너무 타이트하게 두지 않음

소진 후보:
    trailing stop 강화

소진 확정:
    runner 청산
```

---

## 17. False Positive 방지 규칙

### 17.1 단순 급등봉 오판 방지

```text
가격 상승만 있고 volume spike, buy_ratio, CVD, OFI, ask sweep이 없으면
PANIC_BUY_ACTIVE로 전환하지 않는다.
```

---

### 17.2 저유동성 가짜 급등 방지

```python
if features.total_volume < config.min_total_volume:
    panic_buy_score = min(panic_buy_score, 0.45)
    reasons.append("low_liquidity_score_capped")
```

---

### 17.3 뉴스/호재 갭상승 후 횡보 오판 방지

```text
갭상승 이후 추가 매수 흐름이 없으면 패닉바잉으로 보지 않는다.

필수:
- 현재 bar 또는 최근 N개 bar에서 buy_ratio 우위
- CVD slope 양수
- volume spike 유지
```

---

### 17.4 소진 후보 오판 방지

```text
패닉바잉 active 중 작은 음봉 하나만으로 소진 확정하지 않는다.
반드시 M-of-N 확인을 적용한다.
```

---

### 17.5 Bid/Ask spoofing 방지

```python
if features.ask_depth_refill_ratio >= config.ask_depth_refill_min:
    if features.buy_ratio >= config.buy_ratio_threshold and features.price_progress_ratio > 0.5:
        # 매수세가 여전히 가격을 밀고 있으므로 absorption으로 보지 않는다.
        orderbook_absorption_score *= 0.5
```

---

## 18. 테스트 요구사항

반드시 pytest 기반 테스트를 작성한다.

### 18.1 Feature 테스트

`test_panic_buy_features.py`

테스트 항목:

```text
1. close_location_value 계산
2. upper_wick_ratio 계산
3. volume_ratio 계산
4. buy_ratio 계산
5. cvd_delta 계산
6. cvd_slope 계산
7. ask_depth_drop_ratio 계산
8. ask_depth_refill_ratio 계산
9. spread_ratio 계산
10. OFI 계산
11. price_progress_ratio 계산
12. effort_result_divergence 계산
```

---

### 18.2 패닉바잉 시작 테스트

`test_panic_buy_detector_entry.py`

#### Case 1: 정상 상승, 패닉바잉 아님

```text
가격 +0.5%
거래량 정상
buy_ratio 0.53
호가 정상
결과: NORMAL 유지
```

#### Case 2: 가격 급등만 있고 거래량/체결 확인 없음

```text
가격 +2.0%
거래량 낮음
buy_ratio 낮음
호가 정상
결과: PANIC_BUY_ACTIVE 금지
```

#### Case 3: 전형적 패닉바잉

```text
가격 +2.5%
거래량 4배
buy_ratio 0.74
cvd_slope_z +2.8
ofi_z +3.0
ask_depth_drop 0.48
spread_ratio 2.0
close_location_value 0.91
결과: PANIC_BUY_CANDIDATE 후 PANIC_BUY_ACTIVE
allow_tp_override=True
allow_runner=True
```

#### Case 4: 호가 데이터 없음

```text
가격 급등
거래량 폭증
buy_ratio 높음
orderbook None
결과: degrade mode
panic_buy_score cap 적용
reason에 orderbook_missing_degraded 포함
```

---

### 18.3 패닉바잉 소진 테스트

`test_panic_buy_detector_exhaustion.py`

#### Case 1: 가짜 소진

```text
PANIC_BUY_ACTIVE 이후 작은 음봉 1개 발생
하지만 buy_ratio 0.72
ofi_z +2.5
ask_depth_sweep 지속
결과: BUYING_EXHAUSTED 금지
```

#### Case 2: 소진 후보

```text
고점 갱신 실패 3개 바
buy_ratio 0.57
ofi_z +0.2
cvd_slope 둔화
ask_depth_refill 0.75
upper_wick_ratio 0.52
close_location_value 0.38
결과: BUYING_EXHAUSTION_CANDIDATE
```

#### Case 3: 소진 확정

```text
BUYING_EXHAUSTION_CANDIDATE 상태에서
최근 4개 바 중 2개 이상 exhaustion_score threshold 초과
CVD divergence 발생
ask absorption 지속
결과: BUYING_EXHAUSTED 후 COOLDOWN
```

#### Case 4: 소진 후보 후 재돌파

```text
BUYING_EXHAUSTION_CANDIDATE 상태
panic_buy_high 재돌파
OFI 재강화
ask sweep 재개
결과: PANIC_BUY_ACTIVE 복귀
```

---

### 18.4 상태머신 테스트

`test_panic_buy_state_machine.py`

테스트 항목:

```text
1. NORMAL -> PANIC_BUY_CANDIDATE
2. PANIC_BUY_CANDIDATE -> PANIC_BUY_ACTIVE
3. PANIC_BUY_CANDIDATE -> NORMAL
4. PANIC_BUY_ACTIVE -> BUYING_EXHAUSTION_CANDIDATE
5. BUYING_EXHAUSTION_CANDIDATE -> BUYING_EXHAUSTED
6. BUYING_EXHAUSTION_CANDIDATE -> PANIC_BUY_ACTIVE
7. BUYING_EXHAUSTED -> COOLDOWN
8. COOLDOWN -> NORMAL
9. 플립플롭 방지
10. cooldown 기간 동안 allow_tp_override=False
```

---

### 18.5 익절 정책 테스트

`test_panic_buy_exit_policy.py`

테스트 항목:

```text
1. TP 도달 + NORMAL -> CLOSE_ALL
2. TP 도달 + PANIC_BUY_ACTIVE -> PARTIAL_TP_AND_RUNNER
3. TP 도달 + BUYING_EXHAUSTION_CANDIDATE -> PARTIAL_TP_AND_TIGHT_TRAIL
4. BUYING_EXHAUSTED -> CLOSE_ALL
5. stop_loss_hit -> CLOSE_ALL 우선
6. 포지션 없음 -> HOLD
```

---

## 19. Acceptance Criteria

작업 완료 기준은 다음과 같다.

```text
1. PanicBuyDetector.update()가 매 바마다 안정적으로 호출 가능해야 한다.
2. 패닉바잉 감지는 가격 급등 단일 조건이 아니라 복합 score 기반이어야 한다.
3. 패닉바잉 확정에는 M-of-N 지속성 확인이 있어야 한다.
4. 소진 확정에는 단순 음봉이 아니라 체결/호가/캔들/가격 진전 둔화 조건이 포함되어야 한다.
5. 패닉바잉 active 상태에서는 allow_tp_override=True, allow_runner=True를 반환해야 한다.
6. 소진 후보 상태에서는 tighten_trailing_stop=True를 반환해야 한다.
7. 소진 확정 상태에서는 force_exit_runner=True를 반환해야 한다.
8. 호가 데이터가 없을 경우 degrade mode로 동작해야 한다.
9. 모든 signal에는 reasons와 metrics가 포함되어야 한다.
10. pytest 테스트가 모두 통과해야 한다.
11. 임계값은 config로 조정 가능해야 하며 하드코딩하지 않는다.
12. 본 모듈은 주문을 직접 실행하지 않는다.
```

---

## 20. 예시 출력

### 20.1 패닉바잉 시작 예시

입력 상황:

```text
1분 상승률 +1.8%
3분 상승률 +3.7%
거래량 4.5배
buy_ratio 0.74
CVD slope z +2.8
OFI z +3.1
Ask depth 48% 감소
Spread 2.0배 확대
종가가 고가 근처, CLV 0.91
```

기대 출력:

```python
{
    "state": "PANIC_BUY_ACTIVE",
    "panic_buy_score": 0.86,
    "exhaustion_score": 0.18,
    "panic_buy_active": True,
    "panic_buy_entered": True,
    "exhaustion_candidate": False,
    "exhaustion_confirmed": False,
    "allow_tp_override": True,
    "allow_runner": True,
    "tighten_trailing_stop": False,
    "force_exit_runner": False,
    "reasons": [
        "short_return_breakout",
        "mid_return_breakout",
        "volume_spike",
        "buy_ratio_high",
        "cvd_slope_strong",
        "ofi_buy_pressure",
        "ask_depth_sweep",
        "spread_widen",
        "close_near_high"
    ]
}
```

---

### 20.2 패닉바잉 소진 후보 예시

입력 상황:

```text
고점 갱신 실패 3개 바
거래량은 여전히 3.8배
buy_ratio 0.74 -> 0.57
OFI z +3.1 -> +0.2
CVD slope 둔화
Ask depth 75% 회복
시장가 매수가 들어오는데 가격 진전 작음
윗꼬리 52%
CLV 0.38
```

기대 출력:

```python
{
    "state": "BUYING_EXHAUSTION_CANDIDATE",
    "panic_buy_score": 0.41,
    "exhaustion_score": 0.74,
    "panic_buy_active": True,
    "exhaustion_candidate": True,
    "exhaustion_confirmed": False,
    "allow_tp_override": False,
    "allow_runner": True,
    "tighten_trailing_stop": True,
    "force_exit_runner": False,
    "reasons": [
        "no_new_high",
        "buy_ratio_decay",
        "ofi_decay",
        "cvd_slope_decay",
        "ask_depth_refill",
        "upper_wick_exhaustion",
        "effort_result_divergence"
    ]
}
```

---

### 20.3 패닉바잉 소진 확정 예시

입력 상황:

```text
최근 4개 바 중 2개 이상 exhaustion_score 0.66 초과
고점 갱신 실패
OFI 중립 또는 음수 전환
CVD 상승 멈춤
Ask absorption 지속
종가가 고가 부근 유지 실패
```

기대 출력:

```python
{
    "state": "BUYING_EXHAUSTED",
    "panic_buy_score": 0.28,
    "exhaustion_score": 0.81,
    "panic_buy_active": False,
    "exhaustion_candidate": False,
    "exhaustion_confirmed": True,
    "allow_tp_override": False,
    "allow_runner": False,
    "tighten_trailing_stop": True,
    "force_exit_runner": True,
    "reasons": [
        "buying_exhaustion_confirmed",
        "no_new_high",
        "ofi_decay",
        "cvd_divergence",
        "ask_absorption",
        "close_location_failed"
    ]
}
```

---

## 21. README 사용 예시

```python
from panic_buy.config import PanicBuyConfig
from panic_buy.detector import PanicBuyDetector
from panic_buy.models import Candle, TradeAgg, OrderBookSnapshot
from panic_buy.exit_policy import decide_exit, PositionState, NormalExitSignal


detector = PanicBuyDetector(PanicBuyConfig())

signal = detector.update(
    candle=candle,
    trade_agg=trade_agg,
    orderbook=orderbook,
)

position = PositionState(
    has_long=True,
    pnl_pct=current_pnl_pct,
    quantity=current_quantity,
)

normal_exit_signal = NormalExitSignal(
    take_profit_hit=current_pnl_pct >= take_profit_pct,
    stop_loss_hit=current_pnl_pct <= -stop_loss_pct,
)

exit_decision = decide_exit(
    position=position,
    normal_exit_signal=normal_exit_signal,
    panic_buy_signal=signal,
)

if exit_decision.action == "PARTIAL_TP_AND_RUNNER":
    # 일부 익절 후 잔여 물량 runner 전환
    pass

elif exit_decision.action == "TIGHTEN_TRAILING_STOP":
    # runner trailing stop 강화
    pass

elif exit_decision.action == "CLOSE_ALL":
    # 전량 청산
    pass
```

---

## 22. 최종 산출물

Codex는 다음을 산출해야 한다.

```text
1. PanicBuyConfig
2. 입력/출력 데이터 모델
3. feature 계산 모듈
4. panic_buy_score 계산 함수
5. exhaustion_score 계산 함수
6. 상태머신 기반 PanicBuyDetector
7. reason 코드
8. exit_policy 모듈
9. pytest 테스트
10. README 또는 간단한 사용 예시
```

---

## 23. 구현 시 주의사항

### 23.1 주문 직접 실행 금지

본 모듈은 주문을 직접 내지 않는다.

```text
금지:
- market_buy()
- market_sell()
- place_order()
- cancel_order()

허용:
- signal 반환
- exit policy decision 반환
- reason 반환
- metrics 반환
```

---

### 23.2 패닉바잉 신호를 신규 매수 신호로 사용하지 말 것

`panic_buy_active=True`는 “지금 매수하라”가 아니다.

의미는 다음에 가깝다.

```text
이미 보유 중인 롱 포지션에 대해
전량 고정 익절을 유예하고
일부 물량을 runner로 가져갈 수 있는 환경이다.
```

---

### 23.3 소진 신호는 청산 보조 신호로 사용

`exhaustion_confirmed=True`는 다음 의미다.

```text
패닉바잉의 추가 상승 기대가 줄어들었다.
runner 물량을 정리하거나 trailing stop을 매우 타이트하게 조일 필요가 있다.
```

---

### 23.4 로그 가능하게 구현

각 update 결과는 나중에 분석할 수 있어야 한다.

반환 metrics에 최소한 아래 값을 포함한다.

```text
short_return_pct
mid_return_pct
short_return_z
volume_ratio_short
buy_ratio
cvd_slope_z
ofi_z
ask_depth_drop_ratio
ask_depth_refill_ratio
bid_depth_support_ratio
spread_ratio
close_location_value
upper_wick_ratio
price_progress_ratio
panic_buy_score
exhaustion_score
state
```

---

## 24. 요약

패닉바잉 탐지는 매수 진입용 모듈이 아니라 **익절 최적화 모듈**이다.

```text
패닉바잉 시작 탐지:
    가격 상승률
    거래량 폭증
    buy_ratio
    CVD slope
    OFI 양수
    Ask depth sweep
    종가 고가 부근

패닉바잉 잦아듦 탐지:
    고점 갱신 실패
    상승 속도 둔화
    buy_ratio 감소
    CVD divergence
    OFI decay
    Ask depth refill
    윗꼬리
    effort-result divergence

익절 정책:
    일반 구간 = 기계적 TP
    패닉바잉 active = 부분 익절 + runner
    소진 후보 = trailing stop 강화
    소진 확정 = 잔여 물량 청산
```

핵심은 다음이다.

```text
패닉바잉 active:
    너무 빨리 전량 익절하지 않는다.

패닉바잉 소진:
    더 끌고 가려는 욕심을 줄이고 runner를 정리한다.
```
