# Reproducibility Guide

This guide separates checks that run from the public Git checkout from stages
that require local neuroimaging inputs.

## Environment

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

MATLAB/SPM is optional and is used only by `code/matlab/`. Set `MATLAB_BIN`
if MATLAB is not on `PATH`, then run `./run_spm_analysis.sh`.

## Inputs by stage

| Stage | Required input | Public checkout |
|---|---|---|
| Tests and stored-result validation | tracked source and `results/data/` | yes |
| Manuscript/poster figures | tracked tables and inferential maps | yes |
| ROI/effect/correlation regeneration | local first-level effect maps | no; Git-ignored |
| First-level GLM | local `derivatives/fmriprep/` | no; Git-ignored |
| Raw preprocessing/SPM | OpenNeuro NIfTI payloads | no; git-annex links only |

Do not interpret an unfetched annex link as a missing participant. Cohort
membership is defined by `participants.tsv`, and the public raw payloads are
retrieved from OpenNeuro.

## Run order

Run only the stages for which the required inputs are present:

```bash
python code/python/first_level_glm.py
python code/python/roi_analysis.py
python code/python/effect_size_analysis.py
python code/python/correlation_analysis.py
python code/python/posthoc_roi_analysis.py
python code/python/advanced_cluster_analysis.py
python code/python/connectivity_analysis.py
python code/python/laterality_analysis.py
python code/python/poster_visualizations.py
python code/python/paper_visualizations.py
```

`advanced_cluster_analysis.py` is the expensive confirmatory stage. It requires
all planned first-level maps and aborts before replacing its summary if a run
fails. The MVPA outputs are historical and should not be promoted to
confirmatory evidence without redesigning the validation and permutation plan.

## Release validation

```bash
python -m pytest -q
python -m compileall -q code tests
bids-validator-deno . --ignoreNiftiHeaders --prune
bash -n run_spm_analysis.sh code/matlab/setup_spm.sh code/matlab/start_matlab.sh
python code/python/paper_visualizations.py
git diff --check
```

The tests independently check the corrected Welch ANOVA, Games-Howell
studentized-range p-values, partial-correlation degrees of freedom, ROI radii
and overlap, cohort grain, stored result metadata, and canonical figure set.

## Reporting rules

- Report ROI omnibus tests as Welch ANOVA with numerator and denominator
  degrees of freedom.
- Report Games-Howell results with `q_stat`, Welch-Satterthwaite df, and the
  studentized-range p-value.
- Treat the L MTG/L STS ANCOVA as post hoc. Use model n = 69 and n = 65;
  cohort N = 71 and N = 67 are provenance counts.
- For AVH+ age/IQ-adjusted correlations, report df = 19 and the
  within-contrast FDR value.
- Describe whole-brain results as two-sided, 10,000 permutations, voxelwise
  CFT p < .001, maximum-cluster-size FWER p < .05, n = 45 (22/23), with
  sub-28 excluded for missing IQ.
- Do not call descriptive t maps corrected results.
- State that connectivity outputs are uncorrected and that historical MVPA
  permutation p-values are based on 100 permutations.

## ROI definitions

`SPEECH_ROIS` in `code/python/roi_analysis.py` is the single coordinate and
radius source. Cortical spheres use 8 mm, bilateral Heschl spheres use 6 mm,
and the summary JSON records the three intentional overlapping pairs.
