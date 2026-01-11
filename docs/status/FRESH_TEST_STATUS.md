# Fresh Test Status

## Test Started

A fresh preprocessing test has been started on subject 01 to verify coregistration.

**Log file**: `spm/fresh_test_coreg.log`

## How to Monitor

### Quick Status Check
```bash
./monitor_test.sh
```

### Check Log File
```bash
tail -f spm/fresh_test_coreg.log
```

### Check Coregistration File
```bash
ls sub-01/anat/rsub-01_T1w.nii
```

## Expected Timeline

- **Realignment**: ~30 seconds - 1 minute
- **Coregistration**: ~10-30 seconds ⭐ KEY TEST
- **Segmentation**: ~2-5 minutes
- **Normalization**: ~1-2 minutes
- **Smoothing**: ~1-2 minutes

**Total: ~5-10 minutes**

## Success Criteria

The test is successful if:
1. ✓ `sub-01/func/meansub-01_task-speech_bold.nii` exists (realignment)
2. ✓✓✓ `sub-01/anat/rsub-01_T1w.nii` exists (coregistration) ⭐
3. ✓ `sub-01/func/swrsub-01_task-speech_bold.nii` exists (preprocessing complete)

## Current Status

Test is running. Check the monitoring script or log file for current progress.

---

**Run `./monitor_test.sh` to check current status**

