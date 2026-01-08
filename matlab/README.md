# MATLAB/SPM Analysis Scripts for ds004302

This directory contains MATLAB scripts for analyzing the ds004302 dataset using SPM12.

## Prerequisites

1. **MATLAB** (R2014b or later recommended)
   - Download from: https://www.mathworks.com/products/matlab.html

2. **SPM12**
   - Download from: https://www.fil.ion.ucl.ac.uk/spm/software/download/
   - Extract to a directory (e.g., `/path/to/spm12`)

## Setup

1. **Install SPM12**
   ```matlab
   % Download and extract SPM12 to your preferred location
   % Example: /Applications/spm12 or /usr/local/spm12
   ```

2. **Initialize SPM**
   ```matlab
   cd matlab
   edit init_spm.m  % Modify SPM_PATH variable
   init_spm
   ```

3. **Verify setup**
   ```matlab
   spm('version')  % Should display SPM version
   ```

## Dataset Information

- **Task**: Speech perception (block design)
- **Conditions**: words, sentences, reversed, white-noise (baseline)
- **TR**: 2.0 seconds
- **Block duration**: 26 seconds
- **Note**: First 5 volumes (10 seconds) were discarded in original analysis

## Scripts Overview

### `init_spm.m`
Initializes SPM and sets up paths. **Run this first** before any analysis.

### `load_bids_data.m`
Loads BIDS dataset structure and participant information.

### `batch_preprocessing.m`
Preprocessing pipeline:
1. Realignment (motion correction)
2. Coregistration (functional to structural)
3. Segmentation (tissue segmentation)
4. Normalization (to MNI space)
5. Smoothing (8mm FWHM)

### `batch_first_level.m`
First-level (subject-level) GLM analysis:
- Models task conditions (words, sentences, reversed)
- Includes motion regressors
- Creates contrasts of interest

### `batch_second_level.m`
Second-level (group-level) analysis:
- One-sample t-tests for each condition
- Group comparisons (HC vs AVH- vs AVH+)

## Usage Workflow

### Complete Analysis Pipeline

```matlab
% 1. Initialize SPM
cd matlab
init_spm

% 2. Preprocess all subjects
batch_preprocessing

% 3. Run first-level analysis
batch_first_level

% 4. Create contrasts at first level (manual step)
% Use SPM GUI: Stats > Results > Select contrast

% 5. Run second-level analysis
batch_second_level
```

### Individual Steps

```matlab
% Load data
[subjects, participants] = load_bids_data();

% Process specific subject
% (modify batch scripts to process single subject)
```

## Important Notes

1. **File Formats**: 
   - SPM may require unzipped `.nii` files (not `.nii.gz`)
   - You may need to unzip files first:
   ```bash
   gunzip sub-*/func/*.nii.gz
   gunzip sub-*/anat/*.nii.gz
   ```

2. **Disk Space**: 
   - Preprocessing creates many intermediate files
   - Ensure sufficient disk space (~500MB-1GB per subject)

3. **Memory**: 
   - Large datasets may require substantial RAM
   - Consider processing subjects in batches if needed

4. **Computing Time**: 
   - Full preprocessing: ~10-30 minutes per subject
   - First-level analysis: ~5-10 minutes per subject
   - Second-level: ~1-5 minutes

## Customization

### Modify Preprocessing Parameters

Edit `batch_preprocessing.m`:
- `VoxelSize`: Normalization voxel size (default: [2 2 2] mm)
- `FWHM`: Smoothing kernel (default: [8 8 8] mm)

### Modify Analysis Parameters

Edit `batch_first_level.m`:
- `TR`: Repetition time (default: 2.0 seconds)
- `HPF`: High-pass filter (default: 128 seconds)
- `BASIS_DERIVS`: HRF derivatives (default: [0 0])

### Add Custom Contrasts

Modify `batch_first_level.m` to add contrast specification after model estimation.

## Troubleshooting

1. **SPM not found**
   - Check SPM_PATH in `init_spm.m`
   - Ensure SPM is properly installed

2. **File not found errors**
   - Verify BIDS structure is intact
   - Check file naming conventions
   - Ensure files are unzipped if needed

3. **Out of memory**
   - Process fewer subjects at once
   - Increase MATLAB memory: Preferences > General > Java Heap Memory

4. **Preprocessing errors**
   - Check image quality
   - Verify acquisition parameters match script settings
   - Review SPM error messages for specific issues

## Additional Resources

- SPM Manual: https://www.fil.ion.ucl.ac.uk/spm/doc/
- SPM Wiki: https://en.wikibooks.org/wiki/SPM
- BIDS Specification: https://bids-specification.readthedocs.io/

## Citation

If using these scripts, please cite:
- SPM: https://www.fil.ion.ucl.ac.uk/spm/doc/
- Original dataset: Soler-Vidal et al. (2022) PLOS ONE

