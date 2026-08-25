# Corrected fMRI Analysis Summary

## Cohort and first-level data

- Cohort: HC=25, AVH-=23, AVH+=23 (N=71).
- All seven T-contrast map families contain 71 subjects in `results/data/first_level/`.
- The previously absent map sets for sub-02, sub-07, sub-19, sub-21, sub-32, sub-38, sub-54, sub-60, sub-61, and sub-76 were regenerated from their fMRIPrep inputs with the existing first-level design.
- Canonical analysis directories are `first_level`, `roi_values`, `correlations`, and `effect_sizes` under `results/data/`.

## ROI analysis

Each of the seven ROI value files contains 71 rows with HC=25, AVH-=23, and AVH+=23. Every omnibus table contains 12 Welch tests; every pairwise table contains 36 Games-Howell comparisons with `q_stat`, Welch-Satterthwaite `df`, and studentized-range p-values.

Welch's ANOVA is implemented as

\[
F_W = \frac{\sum_i w_i(\bar{x}_i-\bar{x}_w)^2/(k-1)}
{1 + \frac{2(k-2)}{k^2-1}\sum_i\frac{(1-w_i/W)^2}{n_i-1}},
\]

with numerator df `k-1`, Welch denominator df, and the F survival function. Benjamini-Hochberg FDR is recomputed within each contrast over 12 ROIs.

No omnibus ROI test survives within-contrast FDR. The most suggestive family is sentences > reversed:

| ROI | Welch F | df numerator | df denominator | raw p | FDR q |
|---|---:|---:|---:|---:|---:|
| L STS | 5.059 | 2 | 45.237 | .0104 | .0995 |
| L MTG | 4.501 | 2 | 44.532 | .0166 | .0995 |

## ROI radii and non-independence

Ten cortical ROIs use 8 mm spheres; bilateral Heschl's gyri use 6 mm. Values are extracted by radius-specific maskers with overlap enabled, preserving each declared sphere rather than silently dropping shared voxels. The full coordinates, radii, and overlap metadata are in `results/data/roi_values/roi_analysis_summary.json`.

| Pair | center distance | radii sum | overlap depth |
|---|---:|---:|---:|
| L posterior STG–L STS | 10.198 mm | 16 mm | 5.802 mm |
| L MTG–L STS | 8.246 mm | 16 mm | 7.754 mm |
| L IFG triangularis–L IFG opercularis | 14.967 mm | 16 mm | 1.033 mm |

Because these spheres share voxels, their ROI means are not independent.

## Post hoc targeted ANCOVA

The targeted sentences > reversed analysis of L MTG and L STS is post hoc. The model is `activation ~ group + age + iq + sex + mean_fd`, and the AVH- versus AVH+ contrast is Bonferroni-adjusted over two ROIs.

| ROI | model sample | adjusted d [95% CI] | raw p | Bonferroni p |
|---|---|---:|---:|---:|
| L MTG | full_n69 | -.90 [-1.59, -.38] | .0052 | .0105 |
| L STS | full_n69 | -.84 [-1.46, -.38] | .0090 | .0179 |
| L MTG | motion_clean_n65 | -.87 [-1.60, -.38] | .0083 | .0167 |
| L STS | motion_clean_n65 | -.82 [-1.46, -.31] | .0128 | .0255 |

The full and motion-clean source cohorts contain 71 and 67 participants, respectively; missing covariates reduce model complete cases to 69 and 65. The exploratory all-12-ROI ANCOVA FDR family has no hits.

## PSYRATS partial correlations

Partial-correlation p-values use `df=n-k-2`, where `k` is the independent covariate rank. For age and IQ in AVH+, n=23 and df=19 in every row. Within each contrast, BH-FDR covers 12 ROIs.

The primary reported association is speech > reversed in right posterior STG: partial r=.647, p=.00152, q=.0182. Right Heschl and right MTG have raw partial p values near .033 but do not survive within-contrast FDR (q=.136).

## Whole-brain permutation inference

All three planned contrasts completed using Nilearn 0.13.0 with:

- 10,000 permutations and fixed random seed 20260824;
- two-sided testing;
- voxelwise uncorrected cluster-forming p<.001;
- maximum-cluster-size FWER p<.05;
- complete covariate cases for age, IQ, and sex.

Sub-28 is excluded for missing IQ, yielding n=45 (AVH-=22, AVH+=23). No cluster survives in sentences > reversed, speech > reversed, or words > sentences. Corrected t maps are therefore empty by design; the poster panels show descriptive thresholded t maps and state the null corrected result. No smoothing is applied after inference.

## MVPA documentation

The stored MVPA computation was not changed. It uses shuffled five-fold `KFold` cross-validation with `random_state=42`. The stored n=40 results range from accuracy .425 to .500 and none is significant by permutation testing.

## Output map

```text
results/data/
├── first_level/
├── roi_values/
├── effect_sizes/
├── correlations/
├── posthoc/
├── cluster_maps/
└── svm_weights/
```

Paper/poster figures are in `results/poster/`. No `main.tex` exists in the workspace or Git history, so no TeX synchronization artifact is part of this repository.
