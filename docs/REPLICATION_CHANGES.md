# Statistical Correction and Regeneration Record

This record identifies the material corrections applied in August 2026. All values below are read from regenerated artifacts under `results/data/`.

## Corrections

1. Welch's omnibus formula now divides the weighted between-group term by `k-1`, uses the Welch denominator and denominator degrees of freedom, and evaluates the F survival function. The previous implementation doubled F for three groups.
2. Pairwise outputs are genuine Games-Howell tests using a studentized-range statistic and Welch-Satterthwaite degrees of freedom. Every contrast now has 36 rows with `q_stat`, `df`, and adjusted p-values.
3. All seven ROI value/descriptive/ANOVA/pairwise/FDR families were regenerated at N=71 (HC=25, AVH-=23, AVH+=23). No omnibus ROI test survives within-contrast FDR. The earlier claims of corrected L MTG/L STS findings were artifacts of the incorrect Welch numerator.
4. Partial-correlation p-values now use `df=n-k-2`. With n=23 and two independent covariates, df=19. The primary right posterior STG result is partial r=.647, p=.00152, q=.0182.
5. The targeted ANCOVA was renamed and relabeled post hoc throughout. Complete-case labels are `full_n69` and `motion_clean_n65`; 71 and 67 are retained only as cohort counts.
6. ROI extraction now honors 8 mm cortical and 6 mm bilateral Heschl radii. Non-Heschl values match their earlier 8 mm values exactly; Heschl values were regenerated at 6 mm.
7. Overlapping spheres are retained and disclosed: L posterior STG–L STS (10.198 mm), L MTG–L STS (8.246 mm), and L IFG triangularis–L IFG opercularis (14.967 mm). Their values are not independent.
8. MVPA documentation now matches the unchanged code: shuffled five-fold KFold CV with `random_state=42`.
9. Whole-brain inference was rerun successfully with 10,000 two-sided permutations, voxel p<.001 cluster formation, maximum-cluster-size FWER p<.05, and seed 20260824. The complete-case sample is n=45 (22 AVH-, 23 AVH+), excluding sub-28 for missing IQ. No cluster survives in any of the three contrasts.
10. Ten absent first-level map sets were regenerated from available fMRIPrep inputs: sub-02, sub-07, sub-19, sub-21, sub-32, sub-38, sub-54, sub-60, sub-61, and sub-76.

## Corrected key numbers

### ROI omnibus tests

| Contrast | ROI | Welch F(df1, df2) | raw p | within-contrast q |
|---|---|---:|---:|---:|
| sentences > reversed | L STS | 5.059 (2, 45.237) | .0104 | .0995 |
| sentences > reversed | L MTG | 4.501 (2, 44.532) | .0166 | .0995 |
| words > sentences | L STS | 4.268 (2, 44.723) | .0201 | .1491 |
| words > sentences | L MTG | 4.014 (2, 45.164) | .0249 | .1491 |

There are zero within-contrast omnibus FDR hits across all seven contrasts.

### Post hoc targeted ANCOVA

| ROI | sample label | n | adjusted d | raw p | Bonferroni p |
|---|---|---:|---:|---:|---:|
| L MTG | full_n69 | 69 | -.90 | .0052 | .0105 |
| L STS | full_n69 | 69 | -.84 | .0090 | .0179 |
| L MTG | motion_clean_n65 | 65 | -.87 | .0083 | .0167 |
| L STS | motion_clean_n65 | 65 | -.82 | .0128 | .0255 |

These are post hoc results selected after review of the omnibus ROI results. They must not be used as evidence of an a priori family.

### Symptom correlation

For speech > reversed in right posterior STG, AVH+ n=23: raw r=.586, p=.00333, q=.0400; partial r=.647 controlling age and IQ, df=19, p=.00152, q=.0182.

### Whole-brain inference

Sentences > reversed, speech > reversed, and words > sentences each yielded zero clusters at cluster-size FWER p<.05. Figures state the exact 10,000 permutations and show a descriptive voxel-p<.001 t map only when the corrected map is empty.

## Validation performed

- Welch results match Statsmodels `anova_oneway(use_var="unequal")`.
- Games-Howell p-values match independent studentized-range calculations.
- Partial-correlation p-values match the `n-k-2` t test.
- Every stored BH-FDR family was independently recomputed.
- Every ROI table has the expected dimensions and group counts.
- ANCOVA cohort versus model-complete-case counts are distinct.
- All corrected whole-brain maps, cluster tables, metadata, and zero-valued corrected masks were checked after the 10,000-permutation runs.
- Affected paper and poster figures were regenerated and visually inspected.

No `main.tex` exists in the workspace, Git history, or repository file set; the approved plan therefore creates no TeX file.
