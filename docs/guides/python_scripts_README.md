# Analysis Scripts

This directory contains Python scripts for analyzing the ds004302 dataset.

## Setup

1. Create and activate the virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

2. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r ../requirements.txt
   ```

   Or use the setup script:
   ```bash
   bash ../setup_env.sh
   ```

## Usage

Example analysis script:
```bash
python scripts/example_analysis.py
```

This script demonstrates:
- Loading BIDS dataset layout
- Accessing participant information
- Loading BOLD functional images

## Dataset Structure

This is a BIDS 1.7.0 dataset containing:
- T1-weighted anatomical images (`anat/`)
- Functional BOLD images for speech task (`func/`)
- Participant metadata (`participants.tsv`)
- Task event files (`task-speech_events.tsv`)

