#!/bin/bash
# Start Complete Analysis for All Subjects
# This script starts the preprocessing → GLM → visualization pipeline

export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"

cd "$(dirname "$0")"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║    Starting Complete Analysis for All Subjects          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if git-annex is available
if ! command -v git-annex &> /dev/null; then
    echo "ERROR: git-annex not found in PATH"
    echo "Add to PATH: export PATH=\"/opt/homebrew/bin:\$PATH\""
    exit 1
fi

echo "Step 1: Retrieving all data files..."
echo "This may take a while depending on download speed..."
echo ""

# Retrieve all files (run in background)
cd matlab
/Applications/MATLAB_R2025b.app/bin/matlab -nodesktop -nosplash -batch "
cd('$(pwd)');
init_spm;
fprintf('Starting complete analysis for all subjects...\n');
process_all_subjects(3, 1);
" > ../spm/analysis_log.txt 2>&1 &

MATLAB_PID=$!

echo "Analysis started!"
echo "MATLAB PID: $MATLAB_PID"
echo ""
echo "Monitor progress:"
echo "  tail -f spm/analysis_log.txt"
echo ""
echo "Or check status in MATLAB:"
echo "  cd matlab"
echo "  matlab"
echo "  check_analysis_status"
echo ""
echo "Analysis is running in the background..."

