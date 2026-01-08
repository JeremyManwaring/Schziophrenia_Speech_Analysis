#!/bin/bash
# Script to download changes CSV from analytics endpoint

# Configuration
OUTPUT_FILE="changes.csv"
BASE_URL="${1:-http://localhost:8080}"  # Default or first argument
ENDPOINT="/analytics/ai-code/changes.csv"
FULL_URL="${BASE_URL}${ENDPOINT}"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Download Changes CSV"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Attempting to download from: ${FULL_URL}"
echo "Output file: ${OUTPUT_FILE}"
echo ""

# Method 1: Using curl (recommended on macOS)
if command -v curl &> /dev/null; then
    echo "Using curl..."
    
    # Try without authentication first
    curl -L -o "${OUTPUT_FILE}" "${FULL_URL}" 2>&1
    
    if [ $? -eq 0 ] && [ -f "${OUTPUT_FILE}" ]; then
        FILE_SIZE=$(wc -l < "${OUTPUT_FILE}" 2>/dev/null || echo "0")
        if [ "$FILE_SIZE" -gt 0 ]; then
            echo ""
            echo "✓✓✓ Download successful! ✓✓✓"
            echo "   File: ${OUTPUT_FILE}"
            echo "   Lines: ${FILE_SIZE}"
            head -5 "${OUTPUT_FILE}"
            exit 0
        fi
    fi
    
    echo "Download may have failed or returned empty file"
    echo ""
    echo "If authentication is required, try:"
    echo "  curl -H 'Authorization: Bearer YOUR_TOKEN' -o ${OUTPUT_FILE} ${FULL_URL}"
    exit 1
else
    echo "curl not found. Please install curl or use wget."
    exit 1
fi

