#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.offline_live_canary_bundle.local_canary_analysis_runtime import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
