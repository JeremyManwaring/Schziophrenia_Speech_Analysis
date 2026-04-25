"""
Backwards-compatible shim.

Raincloud plotting was consolidated into `poster_visualizations.py` so every
ROI plot uses the shared poster style. Calling `main()` here just delegates to
the orchestrator's ROI-effects step.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from poster_visualizations import make_roi_effects  # noqa: E402


def main() -> None:
    print("\n  Raincloud plots are produced by poster_visualizations.make_roi_effects().")
    make_roi_effects()


if __name__ == "__main__":
    main()
