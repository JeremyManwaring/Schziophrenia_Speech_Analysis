"""
VM Configuration for fMRI Analysis Pipeline

This file contains path configurations for running on the GCP VM.
"""

from pathlib import Path

# VM Paths
FMRIPREP_DIR = Path('/data/output')
ANALYSIS_ROOT = Path('/data/analysis')
PARTICIPANTS_PATH = ANALYSIS_ROOT / 'participants.tsv'
EVENTS_PATH = ANALYSIS_ROOT / 'task-speech_events.tsv'
TASK_JSON_PATH = ANALYSIS_ROOT / 'task-speech_bold.json'
RESULTS_DIR = ANALYSIS_ROOT / 'results'

# Analysis parameters
TR = 2.0  # Repetition time in seconds
SMOOTHING_FWHM = 6.0  # Smoothing kernel in mm
CONFOUND_STRATEGY = 'standard'  # 6 motion + CSF + WM
