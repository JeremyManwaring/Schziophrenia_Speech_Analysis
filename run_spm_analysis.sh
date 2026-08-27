#!/usr/bin/env bash
set -euo pipefail

DATASET_DIR="$(cd "$(dirname "$0")" && pwd)"
MATLAB_BIN="${MATLAB_BIN:-matlab}"
NUM_WORKERS="${1:-4}"
START_FROM="${2:-1}"
LOG_DIR="${DATASET_DIR}/results/spm_logs"
LOG_FILE="${LOG_DIR}/analysis_$(date +%Y%m%d_%H%M%S).log"

if ! command -v "$MATLAB_BIN" >/dev/null 2>&1; then
    echo "MATLAB was not found. Add it to PATH or set MATLAB_BIN." >&2
    exit 1
fi

case "$NUM_WORKERS:$START_FROM" in
    *[!0-9:]*|0:*|*:0)
        echo "NUM_WORKERS and START_FROM must be positive integers." >&2
        exit 2
        ;;
esac

mkdir -p "$LOG_DIR"
echo "Running the SPM pipeline with ${NUM_WORKERS} workers; log: ${LOG_FILE}"

"$MATLAB_BIN" -nodisplay -nosplash -r "\
    cd('${DATASET_DIR}/code/matlab'); \
    init_spm; \
    process_all_subjects(${NUM_WORKERS}, ${START_FROM}, true); \
    exit;" 2>&1 | tee "$LOG_FILE"
