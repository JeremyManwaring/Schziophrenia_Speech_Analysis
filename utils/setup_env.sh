#!/bin/bash
# Setup script for Python environment

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

echo "Python environment setup complete!"
echo "To activate the environment, run: source venv/bin/activate"

