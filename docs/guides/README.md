# ds004302 Analysis Guide

## Environment

Python is the canonical analysis stack. From the dataset root:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Canonical layout

- `results/data/first_level/`: per-subject maps.
- `results/data/roi_values/`: ROI values, descriptives, corrected Welch ANOVAs, genuine Games-Howell tables, and ROI definition metadata.
- `results/data/correlations/`: raw and corrected partial correlations.
- `results/data/effect_sizes/`: regenerated effect-size families.
- `results/data/posthoc/`: post hoc targeted ANCOVA outputs.
- `results/data/cluster_maps/`: 10,000-permutation maps, cluster tables, and result metadata.
- `results/data/svm_weights/`: unchanged MVPA outputs.
- `results/poster/`: figures rebuilt from the canonical data outputs.

## Run order

```bash
source venv/bin/activate
python code/python/first_level_glm.py
python code/python/roi_analysis.py
python code/python/effect_size_analysis.py
python code/python/correlation_analysis.py
python code/python/posthoc_roi_analysis.py
python code/python/advanced_cluster_analysis.py
python code/python/poster_visualizations.py
python code/python/paper_visualizations.py
python -m pytest -q tests/test_statistics.py
```

The permutation script requires every planned first-level map and aborts rather than writing a corrected-inference summary if a run fails.

## Statistical reporting rules

- Report ROI omnibus tests as Welch's ANOVA with numerator and denominator degrees of freedom.
- Report pairwise comparisons as Games-Howell with `q_stat`, Welch-Satterthwaite df, and studentized-range p.
- Treat the L MTG/L STS targeted ANCOVA as post hoc. Use model n=69 and n=65; use cohort N=71 and N=67 only for provenance.
- Report partial-correlation p-values with df=19 for the current AVH+ age/IQ-adjusted tests and quote their within-contrast FDR values.
- Describe MVPA as shuffled five-fold KFold CV with `random_state=42`.
- Describe whole-brain results as two-sided, 10,000 permutations, voxelwise CFT p<.001, maximum-cluster-size FWER p<.05, n=45 (22/23), with sub-28 excluded for missing IQ. State that no cluster survives all three tested contrasts.
- Do not call descriptive t maps corrected results.

## ROI definitions

`SPEECH_ROIS` in `code/python/roi_analysis.py` is the single coordinate/radius source used by extraction and figures. Cortical radii are 8 mm and Heschl radii are 6 mm. The summary JSON records the three intentional overlapping sphere pairs and the resulting non-independence caveat.
