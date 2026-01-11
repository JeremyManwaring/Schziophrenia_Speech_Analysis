# Test Status: Subject 01 Coregistration

## Current Test Status

### Files Being Checked

**Realignment:**
- `sub-01/func/meansub-01_task-speech_bold.nii` - Mean image (indicates realignment)
- `sub-01/func/rsub-01_task-speech_bold.nii` - Realigned functional images

**Coregistration (KEY TEST):**
- `sub-01/anat/rsub-01_T1w.nii` - **Coregistered anatomical image** ← This is what we're testing!

**Preprocessing Complete:**
- `sub-01/func/swrsub-01_task-speech_bold.nii` - Smoothed, normalized functional images

## How to Verify Coregistration Success

Run this command to check:
```bash
cd /Users/adrianecheverria/DATASET/ds004302
ls -lh sub-01/anat/rsub-01_T1w.nii
```

If the file exists, coregistration was successful! ✓✓✓

## Test Script

A test script has been created at:
`matlab/test_coreg.m`

Run it with:
```bash
cd matlab
matlab -batch "test_coreg"
```

## Expected Timeline

- Realignment: ~30 seconds - 1 minute
- Coregistration: ~10-30 seconds  
- Segmentation: ~2-5 minutes
- Normalization: ~1-2 minutes
- Smoothing: ~1-2 minutes

**Total: ~5-10 minutes per subject**

---

*Check the file status above to verify coregistration success.*

