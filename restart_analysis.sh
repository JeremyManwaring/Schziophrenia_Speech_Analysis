#!/bin/bash
# Restart complete analysis for all 71 subjects

cd /Users/adrianecheverria/DATASET/ds004302/matlab

echo "═══════════════════════════════════════════════════════════"
echo "Starting complete analysis for all 71 subjects"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "This will process:"
echo "  - Preprocessing (realignment, coregistration, normalization, smoothing)"
echo "  - GLM Analysis (7 T-tests, 2 F-tests)"
echo "  - Visualization preparation"
echo ""
echo "Expected time: 24-48 hours"
echo ""
echo "Log file: ../spm/complete_analysis_FINAL_$(date +%Y%m%d_%H%M%S).log"
echo ""

/Applications/MATLAB_R2025b.app/bin/matlab -nodesktop -nosplash -batch \
  "cd('$(pwd)'); init_spm; fprintf('Starting complete analysis...\n'); process_all_subjects(5, 1);" \
  > ../spm/complete_analysis_FINAL_$(date +%Y%m%d_%H%M%S).log 2>&1 &

echo "Analysis started in background!"
echo "Monitor with: tail -f spm/complete_analysis_FINAL_*.log"
echo "Or: cd matlab && matlab -batch 'monitor_analysis_progress'"

