# Data Provenance and Coverage

## Cohort

`participants.tsv` contains 71 unique participants: HC = 25, AVH- = 23, and
AVH+ = 23. Every listed participant has a corresponding `sub-*` directory.
The gaps in accession numbering (`sub-31`, `sub-35`, `sub-39`, `sub-41`,
`sub-51`, and `sub-52`) are also absent from the upstream ds004302 participant
table; they are not missing rows from this reanalysis.

IQ is unavailable for two participants, and PSYRATS is unavailable for the 25
healthy controls. Analyses that require those variables use explicit
complete-case samples.

## Raw BIDS payloads

The 142 raw T1w and task-BOLD paths in this Git checkout are git-annex links.
The binary objects are not stored on GitHub and were not present in the local
annex during the August 2026 release audit. Retrieve the official ds004302
snapshot from OpenNeuro before raw-data preprocessing. The repository README
provides a current command-line download example.

BIDS Validator 3.0.1 reports zero errors with NIfTI-header checks disabled.
Remaining messages are recommendations for acquisition fields absent from the
source metadata; no scanner values were inferred or filled in. The 71
`rp_*` realignment files distributed with the source checkout are retained for
the MATLAB workflow and listed in `.bidsignore` because their SPM filenames are
not raw-BIDS names.

## Local derivatives

`derivatives/fmriprep/`, `work/`, and `results/data/first_level/` are ignored
because they are large computational inputs or rebuild products. They are not
part of the public Git release.

The local first-level audit requires seven effect maps and seven z maps for
each of the 71 participants (994 maps total). One absent file,
`sub-59_words_vs_baseline_zstat.nii.gz`, was regenerated from the existing
fMRIPrep input. All 13 comparable sub-59 maps were numerically identical to a
fresh run (maximum absolute difference 0), so the missing map was restored
without changing the analysis specification.

## Public analysis records

The versioned scientific record is under `results/data/`: ROI tables,
effect-size tables, correlation outputs, post hoc models, QC summaries,
whole-brain permutation metadata/maps, and exploratory connectivity,
laterality, and MVPA summaries. Manuscript figures read these records without
rerunning statistical models.

`results/data/qc.csv` contains the per-participant motion summary, and
`results/data/motion_exclusions.txt` lists four participants exceeding the
pipeline's motion-flag rule. These are QC flags, not automatic exclusions;
exclusion decisions remain analysis-specific.

Empty cluster tables are expected because no cluster survived the corrected
whole-brain threshold. The empty `roi_ancova_fdr_hits.csv` table is also
expected; the targeted L MTG/L STS models are explicitly post hoc rather than
omnibus FDR hits.
