# Analysis In Progress: Preprocessing + GLM + Visualization

## ✅ Analysis Started

The complete analysis pipeline has been initiated for **subject 01**. This includes:

1. ✅ **Data Preparation**: Unzipping NIfTI files
2. 🔄 **Preprocessing**: Realignment, coregistration, normalization, smoothing (15-30 min)
3. ⏳ **GLM Analysis**: First-level GLM with t-tests and F-tests (5-10 min)
4. ⏳ **Visualization**: Results viewing and reporting

## Current Status

The analysis is running in the background. To check progress:

```matlab
cd matlab
check_analysis_status
```

Or check the log file:
```bash
tail -f /tmp/analysis_progress.log
```

## What's Being Created

### Preprocessing Output:
- Realigned functional images (`r*.nii`)
- Coregistered structural image
- Normalized images (`w*.nii`)
- Smoothed images (`swr*.nii`)

### GLM Analysis Output:
- **7 T-test contrasts**:
  1. Words > Baseline
  2. Sentences > Baseline
  3. Reversed > Baseline
  4. Words > Reversed
  5. Sentences > Reversed
  6. (Words+Sentences) > Reversed
  7. Words > Sentences

- **2 F-test contrasts**:
  1. All Conditions (omnibus test)
  2. Condition Differences

### Visualization Output:
- SPM Results Viewer ready
- Statistical reports
- Summary documents

## Expected Timeline

- **Subject 01**: ~20-40 minutes total
  - Preprocessing: 15-30 minutes
  - GLM: 5-10 minutes

## Next Steps After Completion

Once analysis completes, you can:

### 1. View Results
```matlab
% Open SPM Results Viewer
show_glm_results('01', 1)     % Words > Baseline
show_glm_results('01', 4)     % Words > Reversed
show_glm_results('01', 1, true)  % F-test: All Conditions
```

### 2. Generate Reports
```matlab
report_glm_statistics('first_level', '01', 1, 0.001, 10)
```

### 3. Run More Subjects
```matlab
run_complete_analysis({'02', '03'}, false)  % Process 2 more
```

### 4. Run All Subjects
```matlab
run_complete_analysis([], true)  % All 71 subjects (takes hours)
```

## Files Created

Results will be saved in:
```
sub-01/spm/first_level/
├── SPM.mat
├── beta_*.nii (parameter estimates)
├── con_0001.nii through con_0007.nii (contrast images)
├── spmT_0001.nii through spmT_0007.nii (T-statistics)
├── spmF_0001.nii (F-test: All Conditions)
└── spmF_0002.nii (F-test: Condition Differences)
```

## Monitoring

To monitor the analysis:

```bash
# Watch log file in real-time
tail -f /tmp/analysis_progress.log

# Check MATLAB workspace status
cd matlab
matlab -batch "check_analysis_status"
```

## Troubleshooting

If analysis seems stuck:
1. Check log file for error messages
2. Verify disk space (need ~1GB per subject)
3. Check MATLAB is still running: `ps aux | grep matlab`
4. Restart if needed: `run_complete_analysis({'01'}, false)`

---

**Analysis started**: Subject 01
**Expected completion**: ~20-40 minutes
**Check status**: `check_analysis_status` or `tail -f /tmp/analysis_progress.log`

