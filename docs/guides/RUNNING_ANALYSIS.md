# Analysis Status: Processing All Subjects

## Current Status

✅ **Analysis Pipeline Started**

The complete preprocessing → GLM → visualization pipeline is running for all 71 subjects.

## What's Running

1. **File Retrieval**: Retrieving all `.nii.gz` files from git-annex
2. **Preprocessing**: For each subject:
   - Realignment (motion correction)
   - Coregistration (functional to structural)
   - Segmentation
   - Normalization (MNI space)
   - Smoothing (8mm FWHM)
3. **GLM Analysis**: For each subject:
   - First-level GLM specification
   - Model estimation
   - 7 T-test contrasts
   - 2 F-test contrasts
4. **Visualization**: Results ready for viewing

## Monitor Progress

### Check Status:
```matlab
cd matlab
matlab -batch "monitor_analysis_progress"
```

Or:
```bash
tail -f spm/complete_analysis.log
```

### View Logs:
```bash
# Main analysis log
tail -f spm/complete_analysis.log

# Check for errors
grep -i error spm/complete_analysis.log | tail -20
```

## Expected Timeline

- **Per subject**: ~20-40 minutes
  - Preprocessing: 15-30 minutes
  - GLM: 5-10 minutes
  
- **All 71 subjects**: ~24-48 hours total

## Processing Strategy

- Subjects processed in batches of 3 (to manage memory)
- Sequential processing to ensure data integrity
- Error logging for failed subjects
- Can resume from any point

## Results Location

After processing, results will be in:
```
sub-*/spm/first_level/
├── SPM.mat
├── beta_*.nii
├── con_0001.nii - Words > Baseline
├── con_0002.nii - Sentences > Baseline
├── con_0003.nii - Reversed > Baseline
├── con_0004.nii - Words > Reversed
├── con_0005.nii - Sentences > Reversed
├── con_0006.nii - (Words+Sentences) > Reversed
├── con_0007.nii - Words > Sentences
├── spmT_0001.nii through spmT_0007.nii
├── spmF_0001.nii - All Conditions
└── spmF_0002.nii - Condition Differences
```

## View Results (After Processing)

Once subjects are processed:

```matlab
% View T-test results
show_glm_results('01', 1)     % Words > Baseline
show_glm_results('01', 4)     % Words > Reversed

% View F-test results  
show_glm_results('01', 1, true)   % All Conditions

% Generate reports
report_glm_statistics('first_level', '01', 1)
```

## Notes

- Analysis runs in background - your terminal is free
- Check progress periodically with monitor script
- Failed subjects will be logged in `spm/logs/`
- Can rerun failed subjects: `process_all_subjects(3, START_FROM)`

---

**Analysis Started**: All 71 subjects
**Check Progress**: `monitor_analysis_progress` or check log files

