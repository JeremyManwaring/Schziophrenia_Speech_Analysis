# ds004302 - Analysis Guide

Single consolidated how-to for setup, data retrieval, and running the analysis
pipeline. Supersedes the previously separate QUICKSTART / RUN_ANALYSIS /
RUNNING_ANALYSIS / INSTALL_GIT_ANNEX / RETRIEVE_FILES / MONITOR / GLM_* guides.

---

## 1. Environment

Python is the canonical analysis stack. Use the project virtualenv `venv/`
(it has nilearn + statsmodels installed):

```bash
# from the dataset root
python3 -m venv venv          # only if venv/ does not exist
source venv/bin/activate
pip install -r requirements.txt
```

All scripts can also be invoked without activating: `venv/bin/python code/python/<script>.py`.

MATLAB/SPM is only needed to (re)run preprocessing and the original SPM GLM:

```matlab
cd code/matlab
init_spm            % sets SPM path
run_complete_analysis
```

---

## 2. Data layout (canonical)

- `results/data/` - the single source of truth for every CSV / JSON / NIfTI.
  - `first_level/` - per-subject first-level contrast maps (effect + zstat).
  - `roi_values/`, `effect_sizes/`, `correlations/`, `cluster_maps/`,
    `svm_weights/`, `connectivity*`, `laterality*`, `qc.csv`, `demographics/`.
  - `confirmatory/` - covariate-adjusted (ANCOVA) + pre-specified results.
- `results/poster/` - 300 dpi figures, rebuilt from `results/data/`.

Raw BIDS NIfTIs are git-annex pointers. If content is missing, fetch with
`datalad get <path>` or `git annex get <path>` (see the dataset's DataLad setup).

---

## 3. Running the pipeline

```bash
source venv/bin/activate

# (a) Heavy compute: first/second-level GLM, ROI extraction
python code/python/run_complete_analysis.py     # SPM-independent Nilearn path

# (b) Advanced AVH analyses: cluster perm, MVPA, connectivity, laterality
python code/python/run_advanced_analyses.py

# (c) Confirmatory rework: ANCOVA + pre-specified Bonferroni + motion sensitivity
python code/python/confirmatory_roi_analysis.py

# (d) Rebuild all poster figures (fast; reads only results/data/)
python code/python/poster_visualizations.py
```

Steps (a) and (b) are the only ones that need the first-level maps in
`results/data/first_level/`. Steps (c) and (d) run from the consolidated CSVs.

---

## 4. Statistical approach (rework)

- **Confirmatory (pre-specified):** `sentences > reversed` x {L_MTG, L_STS},
  AVH- vs AVH+, ANCOVA adjusting age + IQ + sex + mean FD, Bonferroni m = 2.
  Validated with a motion-clean sensitivity analysis (n = 67).
- **Exploratory:** all 7 contrasts x 12 ROIs, Welch ANOVA + FDR within each
  contrast. Group ROI test uses the validated Welch implementation in
  `welch_anova.py`.
- **Symptom correlation:** PSYRATS vs ROI activation in AVH+, partial
  correlation controlling age + IQ, FDR within contrast.
- **MVPA / connectivity / laterality:** exploratory only; report as such.

---

## 5. Contrasts

T-tests: Words>Baseline, Sentences>Baseline, Reversed>Baseline, Words>Reversed,
Sentences>Reversed, (Words+Sentences)>Reversed, Words>Sentences.
F-tests: all-conditions omnibus; condition-differences omnibus.
