#!/bin/bash
# Quick script to check test results

cd /Users/adrianecheverria/DATASET/ds004302

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Coregistration Test Results                            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "1. Realignment Status:"
if [ -f sub-01/func/meansub-01_task-speech_bold.nii ]; then
    echo "   ✓ Realignment complete (mean image exists)"
else
    echo "   ✗ Realignment not complete"
fi

echo ""
echo "2. Coregistration Status (KEY TEST):"
if [ -f sub-01/anat/rsub-01_T1w.nii ]; then
    echo "   ✓✓✓ COREGISTRATION SUCCESSFUL! ✓✓✓"
    ls -lh sub-01/anat/rsub-01_T1w.nii
else
    echo "   ✗ Coregistered anatomical not found"
    echo "   Test may still be running or failed"
fi

echo ""
echo "3. Preprocessing Complete:"
if [ -f sub-01/func/swrsub-01_task-speech_bold.nii ]; then
    echo "   ✓ Full preprocessing complete (smoothed files exist)"
else
    echo "   - Not yet at smoothing stage"
fi

echo ""
echo "4. Log File:"
if [ -f spm/test_coreg.log ]; then
    echo "   Log exists. Last 10 lines:"
    tail -10 spm/test_coreg.log
else
    echo "   Log file not found yet"
fi

