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

## 📁 Directory Structure

```
ds004302-Edited/
│
├── code/                    # All analysis code
│   ├── matlab/              # MATLAB/SPM preprocessing & GLM scripts
│   └── python/              # Python analysis scripts (normality tests, ANOVA)
│
├── docs/                    # Documentation
│   ├── guides/              # How-to guides, workflow docs, READMEs
│   └── status/              # Analysis progress & status reports
│
├── results/                 # Analysis outputs
│   ├── spm_logs/            # SPM processing logs
│   └── GLM_Analysis_Plan.txt
│
├── utils/                   # Utility shell scripts
│   ├── setup_env.sh         # Python environment setup
│   ├── retrieve_files.sh    # Download data files
│   ├── install_git_annex.sh # Install git-annex
│   └── ...                  # Other utility scripts
│
├── sub-*/                   # BIDS subject data (71 subjects)
│   ├── anat/                # T1-weighted anatomical images
│   └── func/                # Functional BOLD images
│
└── [BIDS metadata files]    # Dataset description, participants, task info
    ├── dataset_description.json
    ├── participants.tsv
    ├── participants.json
    ├── task-speech_bold.json
    ├── task-speech_events.json
    ├── task-speech_events.tsv
    └── requirements.txt
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

## 📚 Citation

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
