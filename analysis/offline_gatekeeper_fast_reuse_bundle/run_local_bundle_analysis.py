"""Deprecated compatibility wrapper for offline live canary bundle analysis."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.offline_live_canary_bundle.local_canary_analysis_runtime import main


if __name__ == "__main__":
    argv = list(sys.argv[1:])
    if "--label" not in argv:
        try:
            bundle_dir = Path(argv[argv.index("--bundle-dir") + 1])
            argv.extend(["--label", bundle_dir.name or "legacy_gatekeeper"])
        except (ValueError, IndexError):
            argv.extend(["--label", "legacy_gatekeeper"])
    raise SystemExit(main(argv))
