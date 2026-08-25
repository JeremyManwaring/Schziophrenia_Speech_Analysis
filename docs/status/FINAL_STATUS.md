# Final Analysis Status

## Pipeline status: complete

| Stage | Status | Output |
|---|---|---|
| First-level T-map recovery | 71/71 subjects for all seven families | `results/data/first_level/` |
| ROI extraction | 8 mm cortical, 6 mm Heschl, overlap retained | `results/data/roi_values/` |
| Welch/Games-Howell/FDR | corrected and regenerated | `results/data/roi_values/` |
| Effect sizes | regenerated | `results/data/effect_sizes/` |
| Partial correlations | n/df/p/FDR corrected | `results/data/correlations/` |
| Targeted ANCOVA | post hoc; model n=69/65 | `results/data/posthoc/` |
| Whole-brain permutation inference | 3/3 contrasts, 10,000 permutations, no surviving clusters | `results/data/cluster_maps/` |
| MVPA | computation unchanged; five-fold KFold documentation reconciled | `results/data/svm_weights/` |
| Poster and paper figures | regenerated and visually checked | `results/poster/` |

## Samples

- ROI cohort: HC=25, AVH-=23, AVH+=23 (N=71).
- Post hoc ANCOVA full cohort/model: 71/69.
- Post hoc ANCOVA motion-clean cohort/model: 67/65.
- Whole-brain complete-case patient sample: AVH-=22, AVH+=23 (n=45); sub-28 excluded for missing IQ.

## Corrected inference status

- Zero ROI omnibus tests survive within-contrast BH-FDR.
- The right posterior STG partial PSYRATS association survives within-contrast BH-FDR (partial r=.647, p=.00152, q=.0182, df=19).
- The post hoc targeted L MTG/L STS ANCOVA survives its two-test Bonferroni correction in both complete-case models.
- Zero clusters survive maximum-cluster-size FWER p<.05 in each of the three 10,000-permutation whole-brain analyses.

## Reproduce and validate

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

`results/data/` is the canonical statistical source; `results/poster/` is derived from it. No `main.tex` exists in this repository.
