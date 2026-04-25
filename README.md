# ds004302: Speech Perception in Schizophrenia

Brain correlates of speech perception in schizophrenia patients with and without auditory hallucinations.

## Dataset Overview

- **Study**: Soler-Vidal et al. (2022) PLOS ONE
- **Task**: Speech perception (block design)
- **Conditions**: Words, Sentences, Reversed speech, White-noise (baseline)
- **Subjects**: 71 participants
  - **HC** (sub-01 to sub-25): Healthy Controls
  - **AVH-** (sub-26 to sub-54): Schizophrenia without auditory hallucinations
  - **AVH+** (sub-55 to sub-77): Schizophrenia with auditory hallucinations

---

## Directory Structure

```
ds004302-Edited/
│
├── code/                              # All analysis code
│   ├── matlab/                        # MATLAB/SPM preprocessing & GLM scripts
│   └── python/                        # Python analysis scripts
│       ├── poster_style.py            # Shared rcParams, palette, formatters
│       ├── poster_visualizations.py   # Orchestrator: builds results/poster/
│       ├── surface_brain_plots.py     # Cluster + SVM brain map utilities
│       ├── advanced_cluster_analysis.py
│       ├── mvpa_classification.py
│       ├── connectivity_analysis.py
│       ├── laterality_analysis.py
│       ├── first_level_glm.py / second_level_glm.py
│       ├── roi_analysis.py / correlation_analysis.py / effect_size_analysis.py
│       └── run_advanced_analyses.py   # One-shot pipeline driver
│
├── derivatives/                       # fMRIPrep preprocessed data (71 subjects)
│
├── results/
│   ├── data/                          # SINGLE source of truth for stats
│   │   ├── roi_values/                # one CSV per contrast
│   │   ├── effect_sizes/              # per-contrast + combined CSV
│   │   ├── correlations/              # PSYRATS Pearson + partial
│   │   ├── cluster_maps/              # FWE-corrected NIfTI
│   │   ├── svm_weights/               # SVM weight maps
│   │   ├── connectivity*.{json,csv}   # ROI-ROI connectivity
│   │   ├── laterality*.{csv,json}     # Laterality indices
│   │   ├── qc.csv                     # Per-subject motion summary
│   │   └── demographics/              # Statistical tests
│   ├── poster/                        # 300 dpi poster-ready figures
│   │   ├── 01_brain_maps/             # Glass + inflated fsaverage surfaces
│   │   ├── 02_roi_effects/            # Raincloud + grouped bar + forest
│   │   ├── 03_correlations/           # PSYRATS scatter
│   │   ├── 04_classification/         # MVPA SVM
│   │   ├── 05_connectivity/           # Connectivity matrix + sig diffs
│   │   ├── 06_laterality/             # Heatmap + bars + effect sizes
│   │   ├── 07_demographics_qc/        # Age, IQ, sex, motion
│   │   ├── summary/                   # Hero key-findings figure
│   │   └── README.md                  # Index + key findings
│   ├── demographics/                  # Demographic stats
│   └── vm_analysis/                   # First-/second-level GLM (Nilearn)
│
├── docs/                              # Documentation
│   ├── ANALYSIS_SUMMARY.md / GLM_Analysis_Plan.txt
│   ├── guides/                        # How-to & workflow docs
│   └── status/                        # FINAL_STATUS.md (single canonical)
│
├── utils/                             # Utility shell scripts
│
├── sub-*/                             # BIDS subject data (71 subjects)
│
└── [BIDS metadata files]              # participants.tsv, task JSONs, etc.
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Python environment
bash utils/setup_env.sh

# For MATLAB/SPM analysis
cd code/matlab
matlab -batch "init_spm"
```

### 2. Run Analysis

**MATLAB/SPM Pipeline:**
```matlab
cd code/matlab
init_spm
run_complete_analysis  % Full preprocessing + GLM
```

**Python Analysis:**
```bash
source venv/bin/activate
python code/python/example_analysis.py
```

### 3. View Results

```matlab
% In MATLAB
show_glm_results('01', 1)  % View subject 01, contrast 1
```

---

## 📊 Analysis Pipeline

| Stage | Scripts | Description |
|-------|---------|-------------|
| **Preprocessing** | `batch_preprocessing.m` | Realignment, coregistration, normalization, smoothing |
| **First-Level GLM** | `batch_first_level.m`, `voxelwise_glm_tests.m` | Subject-level T-tests and F-tests |
| **Second-Level** | `batch_second_level.m` | Group-level analysis |
| **Visualization** | `show_glm_results.m`, `visualize_glm_results.m` | View statistical maps |
| **Statistics** | `normality_tests.py`, `welch_anova.py` | Statistical testing |

---

## 📖 Key Documentation

| File | Description |
|------|-------------|
| `docs/guides/QUICKSTART.md` | Quick start guide |
| `docs/guides/COMPLETE_WORKFLOW_SUMMARY.md` | Full analysis workflow |
| `docs/guides/GLM_VISUAL_RESULTS.md` | T-test & F-test interpretation |
| `docs/guides/GLM_ANALYSIS_SUMMARY.md` | GLM analysis details |

---

## 🏷️ Contrasts Performed

### T-tests (7 contrasts):
1. Words > Baseline
2. Sentences > Baseline
3. Reversed > Baseline
4. Words > Reversed
5. Sentences > Reversed
6. (Words + Sentences) > Reversed
7. Words > Sentences

### F-tests (2 omnibus tests):
1. All Conditions (any task activation)
2. Condition Differences (differential responses)

---

## AVH- vs AVH+ Advanced Analyses

Advanced analyses comparing schizophrenia patients with and without auditory hallucinations.
All analyses write to `results/data/`; `poster_visualizations.py` then renders the
poster-ready figures into `results/poster/`.

| Analysis | Method | Output (data) | Output (figures) |
|----------|--------|---------------|------------------|
| **Cluster correction** | Permutation testing (1000 perm) | `results/data/cluster_maps/` | `results/poster/01_brain_maps/` |
| **ROI activation**     | Raincloud + grouped bars + forest | `results/data/roi_values/` & `effect_sizes/` | `results/poster/02_roi_effects/` |
| **PSYRATS correlations** | Pearson r in AVH+ | `results/data/correlations/` | `results/poster/03_correlations/` |
| **MVPA classification** | Linear SVM, LOO-CV, permutation | `results/data/svm_weights/` | `results/poster/04_classification/` |
| **Connectivity** | ROI-to-ROI Fisher-z | `results/data/connectivity*.{json,csv}` | `results/poster/05_connectivity/` |
| **Laterality** | LI = (L-R)/(\|L\|+\|R\|) | `results/data/laterality*.{csv,json}` | `results/poster/06_laterality/` |

### Run Advanced Analyses

```bash
source venv/bin/activate

# Heavy compute pipeline (cluster perm tests, MVPA, connectivity, laterality)
python code/python/run_advanced_analyses.py

# Re-render poster figures only (fast, reads from results/data/)
python code/python/poster_visualizations.py
```

Data sources -> `results/data/`. Figures -> `results/poster/` (300 dpi PNGs).

---

## Key Findings

1. **L_MTG and L_STS** show large effect sizes between AVH- and AVH+ during speech processing
2. **R_STG posterior** activation correlates with hallucination severity (r = 0.59, p = 0.003)
3. Classification accuracy suggests distributed rather than focal group differences

---

## Citation

```bibtex
@article{soler2022brain,
  title={Brain correlates of speech perception in schizophrenia patients 
         with and without auditory hallucinations},
  author={Soler-Vidal, Joan and Fuentes-Claramonte, Paola and ...},
  journal={PLOS ONE},
  year={2022},
  doi={10.1371/journal.pone.0276975}
}
```

---

## 📁 Original Files

- **BIDS Version**: 1.7.0
- **License**: CC0
- **DOI**: [10.18112/openneuro.ds004302.v1.0.1](https://doi.org/10.18112/openneuro.ds004302.v1.0.1)
