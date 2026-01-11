#!/bin/bash
# Run Complete SPM Analysis for ds004302 dataset
# This script runs preprocessing and GLM analysis for all 71 subjects
# Uses PARALLEL PROCESSING for faster execution (~4x speedup)

# Configuration
MATLAB_APP="/Applications/MATLAB_R2024b.app/bin/matlab"
DATASET_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="${DATASET_DIR}/results/spm_logs"
LOG_FILE="${LOG_DIR}/analysis_$(date +%Y%m%d_%H%M%S).log"

# Parallel processing settings
NUM_WORKERS=${1:-4}  # Default: 4 parallel workers (adjust based on your CPU cores)
START_FROM=${2:-1}   # Default: start from subject 1

# Create log directory if needed
mkdir -p "$LOG_DIR"

echo "=============================================="
echo "SPM Analysis Pipeline for ds004302"
echo "=============================================="
echo "Dataset: $DATASET_DIR"
echo "Parallel workers: $NUM_WORKERS"
echo "Starting from subject: $START_FROM"
echo "Log file: $LOG_FILE"
echo ""
echo "Estimated time: ~9-12 hours with 4 workers"
echo "              (vs 35+ hours sequential)"
echo ""
echo "Starting MATLAB..."
echo ""

# Run MATLAB with parallel processing
"$MATLAB_APP" -nodisplay -nosplash -r "\
    cd('${DATASET_DIR}/code/matlab'); \
    init_spm; \
    process_all_subjects(${NUM_WORKERS}, ${START_FROM}, true); \
    exit;" 2>&1 | tee "$LOG_FILE"

echo ""
echo "=============================================="
echo "Analysis complete. Check log file for details:"
echo "$LOG_FILE"
echo "=============================================="
