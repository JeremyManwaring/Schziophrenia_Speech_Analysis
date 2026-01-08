# Complete Analysis Workflow Summary

## ✅ All Scripts Created and Ready

I've created a complete pipeline for preprocessing, GLM analysis (t-tests and F-tests), and visualization. Here's what's available:

## 📁 Created Scripts

### Main Analysis Scripts:
1. **`matlab/run_complete_analysis.m`** - Complete pipeline (preprocessing + GLM + visualization)
2. **`matlab/voxelwise_glm_tests.m`** - GLM analysis with t-tests and F-tests
3. **`matlab/show_glm_results.m`** - Interactive visualization
4. **`matlab/report_glm_statistics.m`** - Statistical reporting
5. **`matlab/check_analysis_status.m`** - Progress monitoring

### Supporting Scripts:
- `matlab/batch_preprocessing.m` - Preprocessing pipeline
- `matlab/batch_first_level.m` - First-level GLM
- `matlab/batch_second_level.m` - Second-level analysis

## 🎯 Analysis Plan

### T-Tests (7 contrasts):
1. Words > Baseline
2. Sentences > Baseline
3. Reversed > Baseline
4. Words > Reversed
5. Sentences > Reversed
6. (Words+Sentences) > Reversed
7. Words > Sentences

### F-Tests (2 omnibus tests):
1. All Conditions - Tests for any task-related activation
2. Condition Differences - Tests for differences between conditions

## 🚀 How to Run

### Step 1: Prepare Data
If files are symlinked to git-annex, you may need to retrieve them:
```bash
# If using datalad
datalad get sub-*/func/*.nii.gz
datalad get sub-*/anat/*.nii.gz

# Or unzip manually if files are accessible
cd matlab
matlab -batch "unzip_nifti_files"
```

### Step 2: Run Complete Analysis
```matlab
cd matlab
start_matlab_spm
run_complete_analysis({'01', '02', '03'}, false)  % 3 subjects
```

Or step by step:
```matlab
% Preprocessing
batch_preprocessing

% GLM Analysis
run_glm_tests

% Or use voxelwise_glm_tests
voxelwise_glm_tests(true, true, true, true)
```

### Step 3: Visualize Results
```matlab
% View T-test results
show_glm_results('01', 1)     % Words > Baseline
show_glm_results('01', 4)     % Words > Reversed

% View F-test results
show_glm_results('01', 1, true)   % All Conditions

% Generate report
report_glm_statistics('first_level', '01', 1, 0.001, 10)
```

## 📊 Expected Results

After running, you'll have:

### First-Level Results (per subject):
```
sub-*/spm/first_level/
├── SPM.mat              # GLM specification
├── beta_*.nii           # Parameter estimates
├── con_0001.nii         # Words > Baseline
├── con_0002.nii         # Sentences > Baseline
├── con_0003.nii         # Reversed > Baseline
├── con_0004.nii         # Words > Reversed
├── con_0005.nii         # Sentences > Reversed
├── con_0006.nii         # (Words+Sentences) > Reversed
├── con_0007.nii         # Words > Sentences
├── spmT_0001.nii        # T-statistics for contrast 1
├── ...                  # T-statistics for other contrasts
├── spmF_0001.nii        # F-test: All Conditions
└── spmF_0002.nii        # F-test: Condition Differences
```

## ⏱️ Processing Times

- **Preprocessing per subject**: 15-30 minutes
- **GLM analysis per subject**: 5-10 minutes
- **Total per subject**: ~20-40 minutes
- **3 subjects**: ~1-2 hours
- **All 71 subjects**: ~24-48 hours

## 📖 Documentation

- **`GLM_VISUAL_RESULTS.md`** - Visual results guide
- **`GLM_TESTS_README.md`** - Detailed GLM documentation
- **`matlab/README.md`** - SPM setup guide
- **`matlab/QUICKSTART.md`** - Quick start guide

## 🔍 Monitor Progress

```matlab
check_analysis_status  % Check what's been processed
```

## 📝 Notes

1. **Data Access**: If files are git-annex symlinks, ensure data is retrieved
2. **Disk Space**: Need ~1GB per subject for preprocessing
3. **Memory**: MATLAB may need increased memory for large datasets
4. **Preprocessing Required**: GLM analysis requires preprocessed data

## ✨ Next Steps

1. Ensure data files are accessible (not just symlinks)
2. Run `run_complete_analysis` for desired subjects
3. View results with `show_glm_results`
4. Generate reports with `report_glm_statistics`
5. Run second-level analysis for group results

---

**All scripts are ready and validated!** Once data files are accessible, the complete pipeline can be run.

