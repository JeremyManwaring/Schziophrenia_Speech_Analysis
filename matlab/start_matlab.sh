#!/bin/bash
# Start MATLAB with SPM initialized for ds004302 analysis
# Usage: ./start_matlab.sh

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DATASET_ROOT="$(dirname "$SCRIPT_DIR")"

# Find MATLAB
MATLAB_PATH="/Applications/MATLAB_R2025b.app/bin/matlab"

if [ ! -f "$MATLAB_PATH" ]; then
    # Try alternative locations
    MATLAB_PATH=$(find /Applications -name "matlab" -type f 2>/dev/null | head -1)
fi

if [ -z "$MATLAB_PATH" ] || [ ! -f "$MATLAB_PATH" ]; then
    echo "ERROR: MATLAB not found!"
    echo "Please install MATLAB or modify MATLAB_PATH in this script"
    exit 1
fi

echo "Starting MATLAB with SPM initialization..."
echo "Dataset root: $DATASET_ROOT"
echo ""

# Start MATLAB and run initialization script
cd "$SCRIPT_DIR"
"$MATLAB_PATH" -nosplash -nodesktop -r "start_matlab_spm"

