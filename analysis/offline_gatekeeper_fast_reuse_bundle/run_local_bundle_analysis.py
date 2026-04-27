"""Run offline gatekeeper_fast_reuse bundle analysis."""

from __future__ import annotations

import sys

from local_bundle_analysis_runtime import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
