# Retrieving Git-Annex Files

## Status

✅ **Confirmed**: fMRI files are git-annex symlinks  
❌ **Issue**: git-annex is not installed (required for datalad)

## Problem

The dataset files are managed by git-annex and appear as broken symlinks:
```
sub-01/func/sub-01_task-speech_bold.nii.gz -> ../../.git/annex/objects/...
```

These files need to be retrieved using `datalad get`, which requires git-annex.

## Solution: Install git-annex

### Option 1: Install via Homebrew (Recommended)
```bash
brew install git-annex
```

### Option 2: Download Binary
Visit: https://git-annex.branchable.com/install/
Download the macOS installer and follow instructions.

### Option 3: Install via conda (if using conda)
```bash
conda install -c conda-forge git-annex
```

## After Installing git-annex

### Retrieve Files for Analysis

```bash
cd /Users/adrianecheverria/DATASET/ds004302

# Retrieve files for specific subjects
python3 -m datalad get sub-01/func/sub-01_task-speech_bold.nii.gz
python3 -m datalad get sub-01/anat/sub-01_T1w.nii.gz

# Or retrieve for multiple subjects
python3 -m datalad get sub-01/func/*.nii.gz sub-01/anat/*.nii.gz
python3 -m datalad get sub-02/func/*.nii.gz sub-02/anat/*.nii.gz
python3 -m datalad get sub-03/func/*.nii.gz sub-03/anat/*.nii.gz

# Or retrieve all at once (WARNING: Large download!)
python3 -m datalad get sub-*/func/*.nii.gz sub-*/anat/*.nii.gz
```

### Or Use the Provided Script

```bash
./retrieve_files.sh 01 02 03  # Retrieve for subjects 01, 02, 03
```

## Verify Files Are Retrieved

```bash
# Check if file is accessible (not a broken symlink)
file sub-01/func/sub-01_task-speech_bold.nii.gz

# Should show: gzip compressed data (not broken symlink)
```

## Current Status

- ✅ datalad installed (version 1.2.3)
- ❌ git-annex not installed (required)
- ⏳ Files not yet retrieved

## Next Steps

1. Install git-annex: `brew install git-annex`
2. Retrieve files: Use commands above
3. Run analysis: `cd matlab && start_matlab_spm && run_complete_analysis`

## Note

The files remain as `.nii.gz` (compressed) - they do NOT need to be unzipped for SPM analysis. SPM can read `.nii.gz` files directly, or the analysis scripts will handle unzipping if needed.

