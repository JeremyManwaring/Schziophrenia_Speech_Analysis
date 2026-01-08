# Voxel-wise GLM Analysis Summary

## ✅ Setup Complete

All scripts for voxel-wise GLM analysis with t-tests and F-tests have been created and validated.

## Created Scripts

### Main Analysis Scripts

1. **`voxelwise_glm_tests.m`**
   - Core function for voxel-wise GLM analysis
   - Handles first-level specification, estimation, contrasts, F-tests, and second-level analysis
   - Usage: `voxelwise_glm_tests(run_first, run_contrasts, run_ftests, run_second)`

2. **`run_glm_tests.m`**
   - Main entry point for complete GLM pipeline
   - Automatically initializes SPM and runs all analysis steps
   - Usage: `run_glm_tests`

3. **`visualize_glm_results.m`**
   - Interactive visualization of GLM results
   - Opens SPM Results GUI with proper settings
   - Usage: `visualize_glm_results('first_level', '01', 1)`

4. **`report_glm_statistics.m`**
   - Generates detailed statistical reports
   - Includes cluster analysis and thresholding
   - Usage: `report_glm_statistics('first_level', '01', 1, 0.001, 10)`

## Analysis Pipeline

### Step 1: First-Level GLM
- Specifies GLM model for each subject
- Models 3 conditions: Words, Sentences, Reversed
- Includes motion regressors
- Estimates parameters (beta values)

### Step 2: T-Test Contrasts
Creates 7 t-test contrasts:
1. Words > Baseline
2. Sentences > Baseline
3. Reversed > Baseline
4. Words > Reversed
5. Sentences > Reversed
6. (Words + Sentences) > Reversed
7. Words > Sentences

### Step 3: F-Tests
Creates 2 F-tests:
1. All Conditions (omnibus test)
2. Condition Differences

### Step 4: Second-Level Group Analysis
- One-sample t-tests across all subjects
- Creates group-level statistical maps
- For each condition > baseline contrast

## Quick Start Commands

```matlab
% Initialize and run complete pipeline
start_matlab_spm
run_glm_tests

% Or run step by step
voxelwise_glm_tests(true, true, true, true)

% View results
visualize_glm_results('first_level', '01', 1)
visualize_glm_results('second_level', 'Words_Baseline', 1)

% Generate reports
report_glm_statistics('first_level', '01', 1)
report_glm_statistics('second_level', 'Words_Baseline', 1)
```

## Output Files

### First-Level (per subject)
- `SPM.mat`: GLM specification and results
- `beta_*.nii`: Parameter estimates
- `con_*.nii`: Contrast images
- `spmT_*.nii`: T-statistic images
- `spmF_*.nii`: F-statistic images

### Second-Level (group)
- `spm/second_level/Words_Baseline/SPM.mat`
- `spm/second_level/Words_Baseline/spmT_*.nii`
- Similar for Sentences and Reversed

## Statistical Testing

### T-Tests
- Test specific contrasts (e.g., Words > Baseline)
- One-tailed tests (positive or negative)
- Voxel-wise significance testing

### F-Tests
- Omnibus tests for multiple conditions
- Tests for ANY significant effect
- Useful for initial screening

### Multiple Comparisons
- Uncorrected (default: p < 0.001)
- FWE correction (family-wise error)
- FDR correction (false discovery rate)
- Cluster-level inference

## Next Steps

1. **Run preprocessing** (if not done):
   ```matlab
   batch_preprocessing
   ```

2. **Run GLM analysis**:
   ```matlab
   run_glm_tests
   ```

3. **View and interpret results**:
   ```matlab
   visualize_glm_results('second_level', 'Words_Baseline', 1)
   ```

4. **Generate publication-ready figures**:
   - Use SPM Results GUI
   - Export thresholded images
   - Create overlays on anatomical images

## Documentation

- **Full documentation**: `GLM_TESTS_README.md`
- **Quick start**: `QUICKSTART.md`
- **General SPM guide**: `README.md`

## Status

✅ All scripts created
✅ Syntax validated
✅ SPM initialized
✅ Ready to run analysis

---

*Created for ds004302: Speech perception in schizophrenia dataset*

