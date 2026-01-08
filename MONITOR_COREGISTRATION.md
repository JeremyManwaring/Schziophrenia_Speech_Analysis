# Monitor Coregistration Success

## Quick Status Check

Run this command to check if coregistration succeeded:

```bash
cd /Users/adrianecheverria/DATASET/ds004302
ls sub-01/anat/rsub-01_T1w.nii
```

**If file exists:** ✓✓✓ COREGISTRATION SUCCESSFUL!

**If file missing:** Coregistration hasn't completed yet or failed

## Test Subject 01

To test the coregistration fix:

```bash
cd /Users/adrianecheverria/DATASET/ds004302/matlab

# Clean previous test files
rm -f ../sub-01/func/rsub-*.nii ../sub-01/func/meansub-*.nii 2>/dev/null
rm -f ../sub-01/anat/rsub-*.nii 2>/dev/null

# Run test
matlab -batch "test_coreg"
```

## Expected Files After Successful Preprocessing

1. **Realignment:**
   - `sub-01/func/meansub-01_task-speech_bold.nii` ✓
   - `sub-01/func/rsub-01_task-speech_bold.nii` ✓

2. **Coregistration:** ⭐ KEY TEST
   - `sub-01/anat/rsub-01_T1w.nii` ← This confirms coregistration works!

3. **Segmentation:**
   - `sub-01/anat/y_rsub-01_T1w.nii` (deformation field)

4. **Normalization:**
   - `sub-01/func/wrsub-01_task-speech_bold.nii`

5. **Smoothing:**
   - `sub-01/func/swrsub-01_task-speech_bold.nii`

## What We Fixed

The coregistration batch is now properly rebuilt after realignment completes:
- Line 327-334 in `run_complete_analysis.m`
- Creates fresh batch structure with correct file paths
- Uses mean image created by realignment

## Monitoring Commands

```bash
# Check coregistration file
ls -lh sub-01/anat/rsub-01_T1w.nii

# Watch preprocessing progress
tail -f spm/test_coreg_output.log

# Count completed subjects (when running full analysis)
find sub-*/anat -name "rsub-*T1w.nii" | wc -l
```

---

**Once coregistration file exists, the fix is verified and ready for full analysis!**

