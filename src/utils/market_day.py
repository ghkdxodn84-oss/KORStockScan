from __future__ import annotations

from datetime import date


def get_krx_trading_day_status(target: date) -> tuple[bool, str]:
    if target.weekday() >= 5:
        return False, "weekend"

    try:
        import holidays  # type: ignore

        kr_holidays = holidays.KR(years=[target.year, target.year + 1])
        if target in kr_holidays:
            return False, f"holiday:{kr_holidays.get(target)}"
    except Exception:
        pass

    if target.month == 5 and target.day == 1:
        return False, "market_holiday:workers_day"
    if target.month == 12 and target.day == 31:
        return False, "market_holiday:year_end_close"

    return True, "trading_day"


def is_krx_trading_day(target: date) -> bool:
    return get_krx_trading_day_status(target)[0]
