"""
Master script: run all advanced AVH analyses end-to-end.

Pipeline:
  1. Cluster-corrected whole-brain analysis  -> results/data/cluster_maps/
  2. MVPA SVM classification                 -> results/data/svm_weights/
  3. Functional connectivity                 -> results/data/connectivity/
  4. Laterality index                        -> results/data/laterality.csv
  5. Poster visualizations (orchestrator)    -> results/poster/
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

CODE_DIR = Path(__file__).parent
sys.path.insert(0, str(CODE_DIR))


def _run_step(name: str, fn) -> None:
    print("\n" + "-" * 80)
    print(name)
    print("-" * 80)
    try:
        fn()
        print(f"OK  {name}")
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL  {name}: {exc}")


def run_all_analyses() -> None:
    start = time.time()

    print("\n" + "=" * 80)
    print("ADVANCED AVH ANALYSIS SUITE  -  AVH- vs AVH+")
    print("=" * 80)

    from advanced_cluster_analysis import main as cluster_main
    from mvpa_classification import main as mvpa_main
    from connectivity_analysis import main as connectivity_main
    from laterality_analysis import main as laterality_main
    from poster_visualizations import main as poster_main

    _run_step("STEP 1/5: Cluster-corrected whole-brain analysis", cluster_main)
    _run_step("STEP 2/5: MVPA SVM classification", mvpa_main)
    _run_step("STEP 3/5: Functional connectivity", connectivity_main)
    _run_step("STEP 4/5: Laterality index", laterality_main)
    _run_step("STEP 5/5: Poster visualizations", poster_main)

    elapsed = time.time() - start
    BASE_DIR = Path(__file__).parent.parent.parent
    print("\n" + "=" * 80)
    print("ALL ANALYSES COMPLETE")
    print(f"Elapsed: {elapsed / 60:.1f} min")
    print("Data    -> " + str(BASE_DIR / "results" / "data"))
    print("Figures -> " + str(BASE_DIR / "results" / "poster"))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_all_analyses()
