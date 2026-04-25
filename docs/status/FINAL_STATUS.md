# Final Analysis Status

This document supersedes all earlier status reports
(`ANALYSIS_*.md`, `COREGISTRATION_*.md`, `CURRENT_*.md`, `FRESH_*.md`,
`PROGRESS_*.md`, `STATUS_*.md`, `TEST_*.md`).

## Pipeline Status: COMPLETE

| Stage                                | Output location                          |
|--------------------------------------|------------------------------------------|
| Preprocessing (SPM/MATLAB)           | `derivatives/`                           |
| First-level GLM (Python / Nilearn)   | `results/vm_analysis/results/first_level/`|
| Second-level GLM                     | `results/vm_analysis/results/second_level/`|
| ROI analysis                         | `results/data/roi_values/`               |
| Effect sizes                         | `results/data/effect_sizes/`             |
| PSYRATS correlations                 | `results/data/correlations/`             |
| Cluster-corrected whole brain        | `results/data/cluster_maps/`             |
| MVPA SVM classification              | `results/data/svm_weights/`              |
| Functional connectivity              | `results/data/connectivity*.{json,csv}`  |
| Laterality index                     | `results/data/laterality*.{csv,json}`    |
| QC / motion exclusions               | `results/data/qc.csv`                    |
| Poster figures (300 dpi)             | `results/poster/`                        |

## Subjects

- HC: 25
- AVH-: 23
- AVH+: 23
- Excluded for motion (mean FD > 0.5 mm): see `results/data/motion_exclusions.txt`

## Reproducing the Pipeline

```bash
# 1. Re-run all data-producing analyses (cluster, MVPA, connectivity, laterality)
python code/python/run_advanced_analyses.py

# 2. Re-render the entire poster from results/data/
python code/python/poster_visualizations.py
```

The orchestrator (`poster_visualizations.py`) is idempotent and only reads from
`results/data/`, so figures can be regenerated without re-running the heavy
permutation analyses.

## Where Things Are

```
results/
├── data/      # one canonical source for every CSV / JSON / NIfTI used in plots
└── poster/    # poster-ready PNGs (one folder per analysis section)

code/python/
├── poster_style.py          # shared rcParams, palette, label formatters
├── poster_visualizations.py # builds results/poster/ from results/data/
├── surface_brain_plots.py   # cluster + SVM brain map utilities
├── advanced_cluster_analysis.py
├── mvpa_classification.py
├── connectivity_analysis.py
├── laterality_analysis.py
├── run_advanced_analyses.py # one-shot pipeline driver
└── (first/second-level GLM, QC, ROI, correlation, effect-size scripts)
```

## Key Findings (AVH- vs AVH+)

See the auto-generated table in `results/poster/README.md` and the hero figure
`results/poster/summary/key_findings.png`.
