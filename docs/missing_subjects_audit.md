# Missing-Subjects Audit

This file records the verification performed on the eight subject IDs that
appeared "missing" in the local working copy of `ds004302-Edited`:
`sub-01`, `sub-02`, `sub-31`, `sub-35`, `sub-39`, `sub-41`, `sub-51`, `sub-52`.

The audit checked every output produced by the pipeline to determine whether
each subject is in fact missing, partially missing, or already fully
incorporated into downstream analyses.

## Summary

| Subject  | Raw BIDS file content | fMRIPrep derivatives | qc.csv | ROI value CSVs (all 7) | Status |
|----------|-----------------------|----------------------|--------|------------------------|--------|
| sub-01   | annex symlink, content NOT fetched | present (full) | row 2 present | present in 7/7 | recoverable |
| sub-02   | annex symlink, content NOT fetched | present (full) | row 3 present | present in 7/7 | recoverable |
| sub-31   | not in dataset        | not in dataset       | absent | absent                 | unrecoverable |
| sub-35   | not in dataset        | not in dataset       | absent | absent                 | unrecoverable |
| sub-39   | not in dataset        | not in dataset       | absent | absent                 | unrecoverable |
| sub-41   | not in dataset        | not in dataset       | absent | absent                 | unrecoverable |
| sub-51   | not in dataset        | not in dataset       | absent | absent                 | unrecoverable |
| sub-52   | not in dataset        | not in dataset       | absent | absent                 | unrecoverable |

## Per-subject details

### sub-01 and sub-02

Both subjects are listed in `participants.tsv` (lines 2 and 3) and are fully
present in every analysis output:

- `derivatives/fmriprep/sub-01/` and `derivatives/fmriprep/sub-02/` contain the
  full standard fMRIPrep outputs:
  - `*_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz` (~221-222 MB each,
    real files, not annex pointers)
  - `*_desc-confounds_timeseries.tsv`
  - `*_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz`
  - HMC and coregistration boldrefs and transforms
- `sub-01.html` and `sub-02.html` reports exist (~58 KB each).
- `results/data/qc.csv` contains both subjects with valid motion / DVARS rows.
- All seven ROI value CSVs in `results/data/roi_values/*_roi_values.csv`
  contain one row each for `sub-01` and `sub-02` (verified by row count).

The only thing absent for these two subjects is the **content** of the raw
BIDS NIfTIs in `sub-01/anat/`, `sub-01/func/`, `sub-02/anat/`, `sub-02/func/`.
The folders and `rp_*.txt` motion files are there, and the NIfTIs exist as
git-annex symlinks, but the underlying annex objects have not been fetched
into the local working copy. The `-Edited` suffix on the workspace folder
suggests this was intentional disk-space management.

Implications:
- No analysis output is missing or incorrect for sub-01/sub-02.
- They cannot be reprocessed from raw without first fetching the annex content.

### sub-31, sub-35, sub-39, sub-41, sub-51, sub-52

These six IDs are absent from every layer of the dataset:

- Not present in `participants.tsv` (local or upstream).
- Not present as folders under the dataset root or under
  `derivatives/fmriprep/`.
- Not present in `results/data/qc.csv` or any ROI value CSV.

The same gaps appear in the upstream OpenNeuro source
(<https://raw.githubusercontent.com/OpenNeuroDatasets/ds004302/main/participants.tsv>),
which means these IDs were excluded by the original authors before the
ds004302 v1.0.1 release was published. There is no public source from which
to fetch raw data for them.

## Cohort

The final cohort used by every downstream analysis matches the
`participant_label` list in
`derivatives/fmriprep/sub-01/log/20260109-220239_*/fmriprep.toml` line 36:

- 71 subjects total (HC = 25, AVH- = 23, AVH+ = 23).

## Conclusion

No re-preprocessing is required. The "missing" appearance of sub-01 and
sub-02 in the working tree is purely a raw-data fetch issue and does not
affect any analysis output. The other six IDs are not recoverable from
public sources.
