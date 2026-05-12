"""Market regime utilities for the sniper engine."""

import os

from src.utils.constants import TRADING_RULES
from src.utils.logger import log_error


MARKET_REGIME = None


def _format_market_regime_block_reason(snap) -> str:
    debug = getattr(snap, "debug", {}) or {}
    component_scores = debug.get("component_scores", {}) or {}
    threshold = int(debug.get("score_threshold", 70) or 70)
    deficit = max(0, threshold - int(getattr(snap, "swing_score", 0) or 0))

    missing_signals = []
    if component_scores.get("vix", 0) <= 0:
        missing_signals.append(
            f"VIX미충족(vix_extreme={snap.vix_extreme}, two_day_down={snap.vix_two_day_down}, peak_passed={snap.vix_peak_passed})"
        )
    if component_scores.get("oil", 0) <= 0:
        missing_signals.append(
            f"원유미충족(oil_reversal={snap.oil_reversal}, wti_dead_cross={snap.wti_dead_cross}, from_high={snap.wti_from_recent_high_pct:.2f}%)"
        )
    if component_scores.get("fng", 0) == 0:
        missing_signals.append(
            f"FNG중립(fng={snap.fng_value:.2f}, prev={snap.fng_prev:.2f}, recovery={snap.fng_recovery}, extreme_fear={snap.fng_extreme_fear})"
        )

    reasons = ",".join(snap.reasons) if snap.reasons else "없음"
    missing = " / ".join(missing_signals) if missing_signals else "없음"
    return (
        f"시장환경 보류 | "
        f"risk={snap.risk_state}, "
        f"score={snap.swing_score}/{threshold}, "
        f"deficit={deficit}, "
        f"components=vix:{component_scores.get('vix', 0)},oil:{component_scores.get('oil', 0)},fng:{component_scores.get('fng', 0)},local_breadth:{component_scores.get('local_breadth', 0)}, "
        f"VIX={snap.vix_close:.2f}, "
        f"WTI_RSI={snap.wti_rsi:.2f}, "
        f"oil_reversal={snap.oil_reversal}, "
        f"FNG={snap.fng_value:.2f}, "
        f"fng_recovery={snap.fng_recovery}, "
        f"reasons={reasons}, "
        f"missing={missing}"
    )


def bind_market_regime_dependencies(*, market_regime=None):
    global MARKET_REGIME
    if market_regime is not None:
        MARKET_REGIME = market_regime

def init_market_regime_service():
    global MARKET_REGIME
    try:
        snap = MARKET_REGIME.refresh_if_needed(force=True)
        print(
            f"🌍 [시장환경 초기화] "
            f"risk={snap.risk_state}, "
            f"VIX={snap.vix_close:.2f}, "
            f"WTI_RSI={snap.wti_rsi:.2f}, "
            f"allow_swing={snap.allow_swing_entry}, "
            f"vol_mode={snap.volatility_mode}"
        )
    except Exception as e:
        log_error(f"🚨 시장환경 초기화 실패: {e}")

def should_block_swing_entry_by_market_regime(strategy: str):
    """
    스윙 전략(KOSPI_ML / KOSDAQ_ML / MAIN)에만 적용되는
    시장환경 필터. 스캘핑 전략에는 적용하지 않는다.
    """
    global MARKET_REGIME

    try:
        snap = MARKET_REGIME.refresh_if_needed()
        normalized = str(strategy or "").upper()

        # 스윙 전략만 적용
        if normalized not in ["KOSPI_ML", "KOSDAQ_ML", "MAIN"]:
            return False, ""

        sensitivity = str(os.getenv("KORSTOCKSCAN_SWING_MARKET_REGIME_SENSITIVITY", "") or "").strip().lower()
        dry_run_enabled = bool(getattr(TRADING_RULES, "SWING_LIVE_ORDER_DRY_RUN_ENABLED", True))
        if not snap.allow_swing_entry and sensitivity == "relaxed_entry_observe" and dry_run_enabled:
            return False, "시장환경 dry-run approval relaxed_entry_observe"

        if not snap.allow_swing_entry:
            return True, _format_market_regime_block_reason(snap)

        return False, ""

    except Exception as e:
        # 시장환경 서비스 장애가 주문엔진 장애가 되면 안 됨
        return False, f"시장환경 조회 실패(보수적 미차단): {e}"
