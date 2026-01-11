# Quick Start Guide - MATLAB/SPM

## Status: ✓ Initialized and Ready!

- **MATLAB**: R2025b detected at `/Applications/MATLAB_R2025b.app`
- **SPM**: Version 25.01.02 auto-detected at `/Users/adrianecheverria/Documents/MATLAB/spm`
- **Dataset**: 71 subjects loaded successfully

## Quick Start

### Option 1: Start MATLAB from Command Line
```bash
cd matlab
./start_matlab.sh
```

### Option 2: Start MATLAB Manually
```matlab
cd matlab
start_matlab_spm
```

### Option 3: Test Installation
```bash
cd matlab
matlab -batch "test_spm"
```

## Basic Usage

1. **Initialize SPM** (done automatically with start_matlab_spm):
   ```matlab
   init_spm
   ```

2. **Load Dataset**:
   ```matlab
   [subjects, participants] = load_bids_data();
   ```

3. **Run Preprocessing**:
   ```matlab
   batch_preprocessing
   ```

4. **Run First-Level Analysis**:
   ```matlab
   batch_first_level
   ```

5. **Run Second-Level Analysis**:
   ```matlab
   batch_second_level
   ```

## Key Variables in Workspace

After initialization, these variables are available:
- `SPM_PATH`: Path to SPM installation
- `DATASET_ROOT`: Path to dataset root directory
- `subjects`: Cell array of subject IDs
- `participants`: Table with participant information

## Next Steps

1. Review `batch_preprocessing.m` and adjust parameters if needed
2. Consider unzipping .nii.gz files if needed: `unzip_nifti_files`
3. Run preprocessing: `batch_preprocessing`
4. Check preprocessing results before proceeding to first-level analysis

## Help

- Full documentation: `README.md`
- Test installation: `test_spm`
- Troubleshooting: See README.md

