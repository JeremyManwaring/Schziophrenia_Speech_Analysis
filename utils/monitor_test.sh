#!/bin/bash
# Monitor the fresh test progress

cd /Users/adrianecheverria/DATASET/ds004302

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Fresh Test Monitoring"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check log file
if [ -f spm/fresh_test_coreg.log ]; then
    echo "Log file exists. Recent activity:"
    tail -20 spm/fresh_test_coreg.log | grep -E "Running|Done|complete|Error|Failed" | tail -5
    echo ""
else
    echo "Log file not found yet"
    echo ""
fi

# Check files
echo "File Status:"
echo "  Realignment (mean image):"
[ -f sub-01/func/meansub-01_task-speech_bold.nii ] && echo "    ✓ Complete" || echo "    ✗ Not found"

echo "  Coregistration (KEY TEST):"
if [ -f sub-01/anat/rsub-01_T1w.nii ]; then
    echo "    ✓✓✓ SUCCESS! ✓✓✓"
    ls -lh sub-01/anat/rsub-01_T1w.nii | awk '{print "    Size:", $5}'
else
    echo "    ✗ Not found (test may still be running)"
fi

echo "  Preprocessing complete:"
[ -f sub-01/func/swrsub-01_task-speech_bold.nii ] && echo "    ✓ Complete" || echo "    - Not yet"

echo ""
echo "Monitor log: tail -f spm/fresh_test_coreg.log"

