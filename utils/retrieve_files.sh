#!/bin/bash
# Script to retrieve git-annex files using datalad
# Requires: git-annex >= 10.20230126

echo "Checking for git-annex installation..."
if ! command -v git-annex &> /dev/null; then
    echo "ERROR: git-annex is not installed."
    echo ""
    echo "To install git-annex on macOS:"
    echo "  brew install git-annex"
    echo ""
    echo "Or download from: https://git-annex.branchable.com/install/"
    exit 1
fi

echo "git-annex version: $(git-annex version | head -1)"
echo ""

echo "Retrieving fMRI files using datalad..."
cd "$(dirname "$0")"

# Retrieve files for first 3 subjects (or all if specified)
SUBJECTS=${1:-"01 02 03"}
for sub in $SUBJECTS; do
    echo "Retrieving files for subject $sub..."
    python3 -m datalad get "sub-$sub/func/sub-$sub_task-speech_bold.nii.gz" 2>&1 | grep -v "AutomagicIO"
    python3 -m datalad get "sub-$sub/anat/sub-$sub_T1w.nii.gz" 2>&1 | grep -v "AutomagicIO"
done

echo ""
echo "Checking retrieved files..."
for sub in $SUBJECTS; do
    func_file="sub-$sub/func/sub-$sub_task-speech_bold.nii.gz"
    if [ -f "$func_file" ] && [ ! -L "$func_file" ] || [ -e "$(readlink -f "$func_file" 2>/dev/null)" ]; then
        echo "  ✓ $func_file (available)"
    else
        echo "  ✗ $func_file (still missing)"
    fi
done
