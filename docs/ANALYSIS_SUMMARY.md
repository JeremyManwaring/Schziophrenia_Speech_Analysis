# Complete fMRI Analysis Summary

## Study Overview
- **Dataset**: ds004302 - Speech Perception in Schizophrenia
- **N = 71 subjects**: HC (25), AVH- (24), AVH+ (23)
- **Task**: Speech perception (words, sentences, reversed, white-noise baseline)
- **Analysis Date**: January 11, 2026

---

## Quality Control

| Metric | Value |
|--------|-------|
| Total subjects | 71 |
| Mean framewise displacement | 0.189 mm |
| Range | 0.069 - 0.455 mm |
| Flagged for motion (>20% high-motion volumes) | 4 subjects |

**Flagged subjects**: sub-02 (28.5%), sub-22 (20.6%), sub-34 (35.0%), sub-45 (35.3%)

---

## First-Level GLM

- **Subjects processed**: 71/71
- **Contrasts computed**: 9 (7 T-contrasts + 2 F-contrasts)
- **Smoothing**: 6mm FWHM
- **Confounds**: 6 motion parameters + CSF + WM

### Contrasts:
1. Words > Baseline (white_noise)
2. Sentences > Baseline
3. Reversed > Baseline
4. Words > Reversed (speech intelligibility)
5. Sentences > Reversed
6. Speech > Reversed (combined intelligibility)
7. Words > Sentences

---

## Second-Level Group Analysis

- **Groups compared**: HC vs AVH- vs AVH+
- **Covariates**: Age (demeaned), IQ (demeaned), Sex
- **Pairwise comparisons**: HC>AVH-, HC>AVH+, AVH->AVH+

---

## ROI-Based Analysis

### 12 Speech/Language ROIs:
- Left: STG posterior, STG anterior, MTG, IFG triangularis, IFG opercularis, STS, Heschl
- Right: STG posterior, STG anterior, MTG, IFG, Heschl

### Key Findings - Large Effect Sizes (|d| ≥ 0.8):

| Contrast | ROI | Comparison | Cohen's d | 95% CI |
|----------|-----|------------|-----------|--------|
| Sentences > Reversed | L_MTG | AVH- vs AVH+ | **-0.89** | [-1.49, -0.36] |
| Sentences > Reversed | L_STS | AVH- vs AVH+ | **-0.92** | [-1.46, -0.42] |
| Words > Sentences | L_MTG | AVH- vs AVH+ | **0.83** | [0.27, 1.46] |
| Words > Sentences | L_STS | AVH- vs AVH+ | **0.86** | [0.36, 1.40] |

**Interpretation**: AVH- patients (schizophrenia without hallucinations) show different activation patterns in left temporal regions compared to AVH+ patients (with hallucinations) during speech processing, particularly in:
- Left Middle Temporal Gyrus (L_MTG)
- Left Superior Temporal Sulcus (L_STS)

---

## PSYRATS Correlation Analysis (AVH+ Group Only)

### Significant Correlations with Hallucination Severity:

| Contrast | ROI | Pearson r | p-value |
|----------|-----|-----------|---------|
| Speech > Reversed | **R_STG_posterior** | **0.59** | **0.003** |
| Speech > Reversed | R_MTG | 0.39 | 0.064 |
| Speech > Reversed | R_Heschl | 0.40 | 0.056 |

**Key Finding**: Higher auditory hallucination severity (PSYRATS scores) significantly correlates with increased RIGHT posterior STG activation during speech intelligibility processing (r = 0.59, p = 0.003).

This suggests that patients with more severe auditory hallucinations show greater right hemisphere auditory cortex engagement during speech perception.

---

## Demographic Analysis

### Welch's ANOVA Results:

| Variable | F-statistic | p-value | Significant |
|----------|-------------|---------|-------------|
| Age | 4.00 | 0.026 | Yes |
| IQ | 1.36 | 0.267 | No |

- Age shows significant group differences (AVH- older on average)
- IQ is matched across groups

---

## Files Generated

```
results/vm_analysis/results/
├── qc/
│   ├── qc_summary.csv
│   └── motion_exclusions.txt
├── first_level/
│   └── [71 subject directories with contrast maps]
├── second_level/
│   └── [7 contrast directories with group maps]
├── roi_analysis/
│   ├── *_roi_values.csv (ROI activation values)
│   ├── *_roi_anova.csv (ANOVA results)
│   ├── *_roi_pairwise.csv (pairwise comparisons)
│   ├── *_roi_descriptive.csv (group means/SDs)
│   └── figures/*.png (bar plots)
├── correlations/
│   ├── *_psyrats_correlations.csv
│   ├── *_psyrats_partial.csv
│   └── figures/*.png (scatter plots)
├── effect_sizes/
│   ├── effect_sizes_summary.csv
│   └── figures/*.png (forest plots, heatmaps)
└── analysis_report.txt
```

---

## Conclusions

1. **Group differences**: Large effect sizes found between AVH- and AVH+ groups in left temporal regions (L_MTG, L_STS) during speech processing

2. **Brain-behavior correlation**: Significant correlation between hallucination severity and right posterior STG activation in AVH+ patients

3. **Motion**: 4 subjects flagged for excessive motion but not excluded from current analysis

4. **Next steps**: Consider excluding high-motion subjects for sensitivity analysis

---

## Advanced Analyses (January 2026)

Five additional analyses were conducted to further characterize AVH- vs AVH+ differences:

### 1. Cluster-Corrected Whole-Brain Analysis
- Permutation-based testing (1000 permutations)
- Cluster-forming threshold: z > 2.3
- Results: `results/visualizations/01_cluster_corrected/`

### 2. Raincloud Plot Visualizations
- Publication-quality distribution plots
- Individual data points with group summaries
- Results: `results/visualizations/02_raincloud_plots/`

### 3. MVPA Classification
- SVM classification (leave-one-out CV)
- Best accuracy: 60% (words_vs_reversed)
- Not significantly above chance (p > 0.05)
- Results: `results/visualizations/03_mvpa_classification/`

### 4. Functional Connectivity
- ROI-to-ROI correlation analysis
- 12 speech/language ROIs
- 2 significant connection differences (p < 0.05 uncorrected)
- Results: `results/visualizations/04_connectivity/`

### 5. Laterality Analysis
- Hemisphere dominance comparison
- LI = (L - R) / (|L| + |R|)
- No significant laterality differences between groups
- Results: `results/visualizations/05_laterality/`

---

## Files Generated

See `results/visualizations/README.md` for complete documentation of visualization outputs.
