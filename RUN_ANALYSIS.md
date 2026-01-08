# Running Complete Analysis: Preprocessing + GLM + Visualization

## Current Status

The complete analysis pipeline has been started. This includes:
1. **Preprocessing**: Realignment, coregistration, normalization, smoothing
2. **GLM Analysis**: First-level GLM with t-tests and F-tests
3. **Visualization**: Results viewing and reporting

## Running the Analysis

### Option 1: Run Complete Pipeline (Recommended)
```matlab
cd matlab
start_matlab_spm
run_complete_analysis({'01', '02', '03'}, false)  % Process 3 subjects
```

### Option 2: Run All Subjects (Takes Several Hours)
```matlab
run_complete_analysis([], true)  % Process all 71 subjects
```

### Option 3: Step by Step
```matlab
% Step 1: Preprocessing
batch_preprocessing

% Step 2: GLM Analysis
run_glm_tests

% Step 3: Visualize
show_glm_results('01', 1)
```

## Monitor Progress

```matlab
% Check analysis status
check_analysis_status
```

Or check log file:
```bash
tail -f /tmp/glm_run.log
```

## Expected Processing Times

- **Preprocessing per subject**: 15-30 minutes
- **GLM analysis per subject**: 5-10 minutes
- **Total per subject**: ~20-40 minutes
- **3 subjects**: ~1-2 hours
- **All 71 subjects**: ~24-48 hours

## Results Location

After completion, results will be in:
```
sub-*/spm/first_level/
├── SPM.mat
├── con_0001.nii - Words > Baseline
├── con_0002.nii - Sentences > Baseline
├── con_0003.nii - Reversed > Baseline
├── con_0004.nii - Words > Reversed
├── con_0005.nii - Sentences > Reversed
├── con_0006.nii - (Words+Sentences) > Reversed
├── con_0007.nii - Words > Sentences
├── spmT_0001.nii through spmT_0007.nii (T-statistics)
├── spmF_0001.nii - All Conditions (F-test)
└── spmF_0002.nii - Condition Differences (F-test)
```

## Visualize Results

Once analysis is complete:

```matlab
% View T-test results
show_glm_results('01', 1)     % Words > Baseline
show_glm_results('01', 4)     % Words > Reversed
show_glm_results('01', 7)     % Words > Sentences

% View F-test results
show_glm_results('01', 1, true)   % All Conditions
show_glm_results('01', 2, true)   % Condition Differences

% Generate statistics report
report_glm_statistics('first_level', '01', 1, 0.001, 10)
```

## Troubleshooting

If preprocessing fails:
1. Check that files are unzipped: `unzip_nifti_files`
2. Verify disk space (need ~1GB per subject)
3. Check MATLAB memory settings

If GLM fails:
1. Ensure preprocessing completed successfully
2. Check for motion parameter files
3. Verify events file is readable

## Next Steps After Analysis

1. **Review Results**: Use SPM Results GUI
2. **Second-Level**: Run group analysis
3. **Export**: Save thresholded images for publication
4. **Statistical Reports**: Generate detailed statistics

---

*Analysis is running in the background. Check progress with `check_analysis_status`*

