# Coregistration Verification

## Current Status

### Files Present
- ✓ Realignment complete: `meansub-01_task-speech_bold.nii` exists
- ✓ Realigned functional: `rsub-01_task-speech_bold.nii` exists

### Files Missing (Expected if coregistration not complete)
- ✗ Coregistered anatomical: `rsub-01_T1w.nii` **NOT FOUND**

## Verification Commands

### Quick Check
```bash
cd /Users/adrianecheverria/DATASET/ds004302
ls sub-01/anat/rsub-01_T1w.nii
```

### Full Status
```bash
./CHECK_TEST_RESULTS.sh
```

### MATLAB Verification
```matlab
cd matlab
matlab -batch "init_spm; DATASET_ROOT = evalin('base', 'DATASET_ROOT'); anat_coreg = fullfile(DATASET_ROOT, 'sub-01', 'anat', 'rsub-01_T1w.nii'); if exist(anat_coreg, 'file'); fprintf('COREGISTRATION SUCCESSFUL!\n'); else; fprintf('Not found\n'); end"
```

## What to Expect

If coregistration succeeds:
1. File created: `sub-01/anat/rsub-01_T1w.nii`
2. This is the anatomical image coregistered to the mean functional image
3. File size should be similar to original anatomical (~40MB)

## Test in Progress

A verification test is running. Check results in:
- Log: `spm/verify_coreg.log`
- Files: `sub-01/anat/rsub-01_T1w.nii`

---

**Run the verification commands above to check current status.**

