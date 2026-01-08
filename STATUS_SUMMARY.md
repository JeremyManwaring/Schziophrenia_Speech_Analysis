# Analysis Status Summary

## ✅ Analysis Running

**Status**: Complete preprocessing + GLM pipeline running for all 71 subjects

**Log File**: `spm/complete_analysis_FIXED.log`

### Fix Applied ✓
- Coregistration batch now properly rebuilt after realignment
- Sequential processing verified
- File dependencies fixed

### Current Progress

The analysis is processing subjects sequentially. Check the log file for current status:

```bash
tail -f spm/complete_analysis_FIXED.log
```

### What Each Subject Will Have

Once complete, each subject will have:

**Preprocessing:**
- `sub-XX/func/swrsub-XX_task-speech_bold.nii` (smoothed, normalized)
- `sub-XX/anat/rsub-XX_T1w.nii` (coregistered)

**GLM Results:**
- `sub-XX/spm/first_level/SPM.mat` (GLM results)
- `sub-XX/spm/first_level/spmT_0001.nii` through `spmT_0007.nii` (7 T-tests)
- `sub-XX/spm/first_level/spmF_0001.nii`, `spmF_0002.nii` (2 F-tests)

### Monitor Commands

```bash
# Real-time log
tail -f spm/complete_analysis_FIXED.log

# Progress monitor
cd matlab && matlab -batch "monitor_analysis_progress"

# Count completed subjects
find sub-*/func -name "swrsub-*.nii" | wc -l
find sub-*/spm/first_level -name "SPM.mat" | wc -l
```

### Expected Time
- Per subject: ~30-40 minutes  
- All 71 subjects: ~24-48 hours

---

**Analysis started successfully. Monitor progress using the commands above.**

