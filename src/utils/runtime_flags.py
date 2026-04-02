from __future__ import annotations

from pathlib import Path

from src.utils.constants import PROJECT_ROOT


def get_pause_flag_path() -> Path:
    """Return the absolute project-root path for the persistent pause flag."""
    return PROJECT_ROOT / "pause.flag"


def is_trading_paused() -> bool:
    """Return True when the persistent pause flag exists."""
    return get_pause_flag_path().exists()


def set_trading_paused() -> Path:
    """
    Create or overwrite the persistent pause flag.

    Raises:
        OSError: If the flag file cannot be created or written.
    """
    flag_path = get_pause_flag_path()
    flag_path.write_text("paused", encoding="utf-8")
    return flag_path


def clear_trading_paused() -> None:
    """
    Remove the persistent pause flag if present.

    Raises:
        OSError: If the flag file exists but cannot be removed.
    """
    flag_path = get_pause_flag_path()
    if flag_path.exists():
        flag_path.unlink()
