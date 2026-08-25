# ds004302: Speech Perception in Schizophrenia

Brain correlates of speech perception in schizophrenia patients with and without auditory hallucinations.

## Dataset

- Study: Soler-Vidal et al. (2022), PLOS ONE
- Task: block-design speech perception (words, sentences, reversed speech, white-noise baseline)
- Cohort: 71 participants — HC=25, AVH-=23, AVH+=23
- Canonical first-level maps: `results/data/first_level/`

## Canonical outputs

All statistical outputs used by the figures live under `results/data/`:

```text
results/data/
├── first_level/       # subject-level effect, t, z, and F maps
├── roi_values/        # ROI values, descriptives, Welch ANOVA, Games-Howell
├── effect_sizes/      # omnibus and pairwise effect sizes
├── correlations/      # raw and partial PSYRATS correlations
├── posthoc/           # post hoc targeted ANCOVA and sensitivity analysis
├── cluster_maps/      # permutation inference maps, tables, and metadata
├── svm_weights/       # unchanged MVPA results and weight maps
├── demographics/
├── connectivity*.{csv,json}
├── laterality*.{csv,json}
└── qc.csv
```

Poster-ready and paper-ready figures are regenerated from those records into `results/poster/`.

## Statistical methods

- ROI omnibus tests use Welch's one-way ANOVA with the weighted between-group term divided by `k-1`, the Welch denominator/denominator degrees of freedom, and F survival-function p-values.
- Each ROI has all three genuine Games-Howell group comparisons, calculated with Welch-Satterthwaite degrees of freedom and the studentized-range distribution.
- Benjamini-Hochberg FDR is applied within each contrast across its 12 ROI omnibus tests.
- AVH+ partial correlations control age and IQ and use `df=n-k-2`; all current rows have n=23 and df=19. Their FDR family is the 12 ROIs within a contrast.
- The targeted L_MTG/L_STS ANCOVA is post hoc. Complete-case model labels are `full_n69` and `motion_clean_n65`; the corresponding source cohorts contain 71 and 67 participants.
- Whole-brain AVH- versus AVH+ inference uses 10,000 permutations, two-sided tests, voxelwise cluster-forming p<.001, maximum-cluster-size FWER p<.05, and random seed 20260824. Complete covariates give n=45 (AVH-=22, AVH+=23); sub-28 is excluded for missing IQ.
- Existing MVPA computations are unchanged: shuffled five-fold `KFold` cross-validation with `random_state=42`.

## ROI definitions and overlap

The single definition source is `SPEECH_ROIS` in `code/python/roi_analysis.py`, serialized to `results/data/roi_values/roi_analysis_summary.json`. Ten cortical spheres use an 8 mm radius; bilateral Heschl's gyri use 6 mm.

Three sphere pairs intentionally share voxels and therefore are not independent:

- L posterior STG–L STS: center distance 10.198 mm
- L MTG–L STS: center distance 8.246 mm
- L IFG triangularis–L IFG opercularis: center distance 14.967 mm

## Corrected results

- No ROI omnibus test survives within-contrast FDR. For sentences > reversed, the smallest values are L STS (raw p=.0104, q=.0995) and L MTG (raw p=.0166, q=.0995).
- The post hoc targeted ANCOVA is significant after Bonferroni correction over L MTG and L STS in both complete-case models: full n=69 (adjusted d=-.90 and -.84) and motion-clean n=65 (adjusted d=-.87 and -.82). These results must not be presented as a priori.
- In AVH+ participants, speech > reversed activation in right posterior STG correlates with PSYRATS after controlling age and IQ: partial r=.647, p=.00152, within-contrast q=.0182, n=23, df=19.
- No cluster survives the valid 10,000-permutation cluster-size FWER analysis in any of the three tested contrasts.
- Historical MVPA results remain at/below chance (accuracy .425–.500; all permutation p>=.347), and use shuffled five-fold KFold CV.

## Reproduce

```bash
python code/python/roi_analysis.py
python code/python/effect_size_analysis.py
python code/python/correlation_analysis.py
python code/python/posthoc_roi_analysis.py
python code/python/advanced_cluster_analysis.py
python code/python/poster_visualizations.py
python code/python/paper_visualizations.py
python -m pytest -q tests/test_statistics.py
```

See `docs/ANALYSIS_SUMMARY.md`, `docs/REPLICATION_CHANGES.md`, and `docs/guides/README.md` for details.

## Citation

```bibtex
@article{soler2022brain,
  title={Brain correlates of speech perception in schizophrenia patients with and without auditory hallucinations},
  author={Soler-Vidal, Joan and Fuentes-Claramonte, Paola and others},
  journal={PLOS ONE},
  year={2022},
  doi={10.1371/journal.pone.0276975}
}
```

- BIDS version: 1.7.0
- License: CC0
- Dataset DOI: [10.18112/openneuro.ds004302.v1.0.1](https://doi.org/10.18112/openneuro.ds004302.v1.0.1)
