"""Deprecated compatibility wrapper for offline live canary bundle export."""

from __future__ import annotations

import sys

from src.engine.offline_live_canary_bundle import main


if __name__ == "__main__":
    raise SystemExit(main(["export", *sys.argv[1:]]))
