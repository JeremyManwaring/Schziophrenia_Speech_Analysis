# ds004302 Speech-Perception Reanalysis

This repository contains a reproducible reanalysis of the ds004302 speech-
perception fMRI dataset: 71 participants divided among healthy controls (HC),
patients without auditory verbal hallucinations (AVH-), and patients with
auditory verbal hallucinations (AVH+).

The original BIDS dataset is Soler-Vidal et al. (2022). The analysis code,
validated result tables, inferential maps, and manuscript figures are kept
separate so researchers can distinguish source data, derived statistics, and
presentation artifacts.

## Dataset notes

The task uses six blocks each of spoken word lists, spoken sentences, reversed
speech, and white noise. The original analysis discarded the first five
volumes (10 seconds), while the distributed NIfTI files retain the full run;
event onsets begin after those discarded volumes. White-noise periods appear
in the events table but were not modeled in the original publication, so they
served as an implicit baseline.

## Start here

- [Reproducibility guide](docs/REPRODUCIBILITY.md): environment, required
  inputs, run order, and validation commands.
- [Analysis summary](docs/ANALYSIS_SUMMARY.md): methods and current findings.
- [Correction record](docs/REPLICATION_CHANGES.md): statistical changes and
  regenerated outputs.
- [Data provenance](docs/DATA_PROVENANCE.md): cohort coverage, git-annex data,
  and local-only derivatives.
- [Manuscript figures](results/paper_figures/README.md): the canonical seven-
  figure package and its rendering contract.

## Repository map

```text
code/python/             Python analysis and figure generators
code/matlab/             SPM preprocessing and GLM workflow
docs/                    Methods, provenance, and correction records
results/data/            Tracked statistical tables and inferential outputs
results/paper_figures/   Canonical manuscript figures (PNG, SVG, PDF)
results/poster/          Detailed diagnostic and poster figures
sub-*/                   BIDS paths backed by git-annex pointers
tests/                   Statistical and repository-integrity checks
```

Generated environments, fMRIPrep derivatives, work directories, first-level
maps, and other large local intermediates are intentionally excluded from Git.
They are inputs or rebuild products, not source files.

## Setup and release checks

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m compileall -q code tests
bids-validator-deno . --ignoreNiftiHeaders --prune
python code/python/paper_visualizations.py
```

The figure generator reads stored records under `results/data/`; it does not
rerun models or synthesize observations.

## Raw data access

The `sub-*` NIfTI paths in the GitHub checkout are git-annex links. Their
binary payloads are distributed by OpenNeuro, not by this analysis repository.
The simplest independent download is:

```bash
uvx openneuro-py@latest download \
  --dataset=ds004302 \
  --target-dir=../ds004302-raw
```

If `uvx` is unavailable, install `openneuro-py` in a separate environment and
run the same `openneuro-py download` command.

The [OpenNeuro CLI documentation](https://docs.openneuro.org/packages/openneuro-cli.html)
also describes DataLad/git-annex retrieval. Full first-level reconstruction
additionally requires local fMRIPrep derivatives in `derivatives/fmriprep/`.

## Canonical statistical outputs

All tracked statistics used by the manuscript figures live under
`results/data/`:

```text
results/data/
├── roi_values/       ROI values, descriptives, Welch ANOVA, Games-Howell
├── effect_sizes/     omnibus and pairwise effect sizes
├── correlations/    raw and age/IQ-adjusted PSYRATS correlations
├── posthoc/          targeted post hoc ANCOVA and sensitivity analysis
├── cluster_maps/     permutation-inference maps, tables, and metadata
├── svm_weights/      historical MVPA summaries and available artifacts
├── demographics/    cohort checks
├── connectivity/    full exploratory connectivity matrices
├── connectivity.*   exploratory connectivity metadata/tables
├── laterality.*     exploratory laterality outputs
└── qc.csv            participant-level quality-control summary
```

Local first-level effect and z maps are rebuildable intermediates and remain
Git-ignored. See the reproducibility guide before rerunning a stage that
depends on them.

## Statistical methods and interpretation

- ROI omnibus tests use Welch's one-way ANOVA and genuine Games-Howell
  pairwise comparisons. Benjamini-Hochberg FDR is applied within each contrast
  across 12 ROI omnibus tests.
- AVH+ partial correlations control age and IQ and use `df = n - k - 2`.
- The L MTG/L STS ANCOVA is post hoc; its complete-case model labels are
  `full_n69` and `motion_clean_n65`.
- Whole-brain AVH- versus AVH+ inference uses 10,000 two-sided permutations,
  voxelwise cluster-forming p < .001, and maximum-cluster-size FWER p < .05.
- Existing MVPA results are retained as historical/exploratory outputs. They
  use shuffled five-fold `KFold` cross-validation and 100 permutations, which
  is insufficient for new confirmatory claims.

No ROI omnibus test survives within-contrast FDR. The post hoc L MTG/L STS
ANCOVA survives its two-test Bonferroni correction, and the right posterior
STG PSYRATS association survives within-contrast FDR after age/IQ adjustment.
No cluster survives the 10,000-permutation whole-brain analysis.

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

- Dataset DOI: [10.18112/openneuro.ds004302.v1.0.1](https://doi.org/10.18112/openneuro.ds004302.v1.0.1)
- BIDS version: 1.7.0
- Dataset license: CC0
