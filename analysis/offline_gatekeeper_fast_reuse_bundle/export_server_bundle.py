"""Create an offline gatekeeper_fast_reuse bundle from server data."""

from __future__ import annotations

import sys

from src.engine.offline_gatekeeper_fast_reuse_bundle import main


if __name__ == "__main__":
    raise SystemExit(main(["export", *sys.argv[1:]]))
