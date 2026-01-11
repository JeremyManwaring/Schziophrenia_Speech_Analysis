#!/bin/bash
# Setup script for SPM12 installation
# This script helps download and set up SPM12

echo "SPM12 Setup Script"
echo "=================="
echo ""

# Check if MATLAB is available
if ! command -v matlab &> /dev/null; then
    echo "WARNING: MATLAB not found in PATH"
    echo "Please install MATLAB first or add it to your PATH"
    echo ""
fi

# SPM download URL (check for latest version)
SPM_URL="https://www.fil.ion.ucl.ac.uk/spm/download/restricted/eldorado/spm12.zip"
SPM_DIR="${HOME}/spm12"

echo "This script will:"
echo "1. Download SPM12"
echo "2. Extract it to: ${SPM_DIR}"
echo "3. Provide instructions for MATLAB setup"
echo ""

read -p "Do you want to proceed? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Create directory
mkdir -p "${SPM_DIR}"
cd "${SPM_DIR}/.."

# Download SPM (if wget is available)
if command -v wget &> /dev/null; then
    echo "Downloading SPM12..."
    wget "${SPM_URL}" -O spm12.zip
elif command -v curl &> /dev/null; then
    echo "Downloading SPM12..."
    curl -L "${SPM_URL}" -o spm12.zip
else
    echo "ERROR: Neither wget nor curl found. Please download SPM12 manually:"
    echo "  ${SPM_URL}"
    echo "  Extract to: ${SPM_DIR}"
    exit 1
fi

# Extract
if [ -f spm12.zip ]; then
    echo "Extracting SPM12..."
    unzip -q spm12.zip
    rm spm12.zip
    echo "SPM12 extracted to: ${SPM_DIR}"
else
    echo "ERROR: Download failed. Please download manually."
    exit 1
fi

# Instructions
echo ""
echo "========================================="
echo "Setup Instructions"
echo "========================================="
echo ""
echo "1. Edit matlab/init_spm.m and set:"
echo "   SPM_PATH = '${SPM_DIR}';"
echo ""
echo "2. Start MATLAB and run:"
echo "   cd $(pwd)/matlab"
echo "   init_spm"
echo ""
echo "3. Verify installation:"
echo "   spm('version')"
echo ""

