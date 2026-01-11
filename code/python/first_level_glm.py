"""
First-Level GLM Analysis using Nilearn

This script performs first-level GLM analysis for each subject using:
- fMRIprep preprocessed BOLD data
- Task events from BIDS events file
- Confounds from fMRIprep (motion, CSF, WM signals)
"""

import numpy as np
import pandas as pd
from pathlib import Path
import nibabel as nib
from nilearn.glm.first_level import FirstLevelModel, make_first_level_design_matrix
from nilearn.plotting import plot_design_matrix, plot_contrast_matrix
from nilearn.image import load_img
import warnings
import json
import os

warnings.filterwarnings('ignore')

# Define contrasts
CONTRASTS = {
    # T-contrasts
    'words_vs_baseline': 'words - white-noise',
    'sentences_vs_baseline': 'sentences - white-noise',
    'reversed_vs_baseline': 'reversed - white-noise',
    'words_vs_reversed': 'words - reversed',
    'sentences_vs_reversed': 'sentences - reversed',
    'speech_vs_reversed': '0.5*words + 0.5*sentences - reversed',
    'words_vs_sentences': 'words - sentences',
}

# F-contrasts (defined as arrays after design matrix is created)
F_CONTRASTS = {
    'all_conditions': ['words', 'sentences', 'reversed'],  # Any task activation
    'condition_differences': ['words - reversed', 'sentences - reversed', 'words - sentences'],
}


def load_events(events_path):
    """
    Load task events from BIDS events file.
    
    Parameters
    ----------
    events_path : Path
        Path to events TSV file
    
    Returns
    -------
    events : pd.DataFrame
        Events DataFrame with onset, duration, trial_type columns
    """
    events = pd.read_csv(events_path, sep='\t')
    
    # Rename 'condition' to 'trial_type' if needed (BIDS standard)
    if 'condition' in events.columns and 'trial_type' not in events.columns:
        events = events.rename(columns={'condition': 'trial_type'})
    
    # Ensure required columns exist
    required_cols = ['onset', 'duration', 'trial_type']
    for col in required_cols:
        if col not in events.columns:
            raise ValueError(f"Missing required column: {col}")
    
    return events[required_cols]


def select_confounds(confounds_df, strategy='minimal'):
    """
    Select confound regressors for GLM.
    
    Parameters
    ----------
    confounds_df : pd.DataFrame
        Full confounds DataFrame from fMRIprep
    strategy : str
        Confound strategy: 'minimal', 'standard', or 'full'
    
    Returns
    -------
    confounds : pd.DataFrame
        Selected confounds
    """
    if strategy == 'minimal':
        # 6 motion parameters only
        cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    
    elif strategy == 'standard':
        # 6 motion + CSF + WM
        cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z',
                'csf', 'white_matter']
    
    elif strategy == 'full':
        # 24 motion (6 + derivatives + squares) + CSF + WM + global signal
        motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
        derivative_cols = [f'{col}_derivative1' for col in motion_cols]
        power_cols = [f'{col}_power2' for col in motion_cols]
        derivative_power_cols = [f'{col}_derivative1_power2' for col in motion_cols]
        
        cols = (motion_cols + derivative_cols + power_cols + derivative_power_cols +
                ['csf', 'white_matter', 'global_signal'])
    
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    # Select only columns that exist
    available_cols = [col for col in cols if col in confounds_df.columns]
    
    confounds = confounds_df[available_cols].copy()
    
    # Fill NaN values (first row often has NaN for derivatives)
    confounds = confounds.fillna(0)
    
    return confounds


def run_first_level_glm(subject_id, fmriprep_dir, events_path, output_dir, 
                        t_r=2.0, confound_strategy='standard', smoothing_fwhm=6.0):
    """
    Run first-level GLM for a single subject.
    
    Parameters
    ----------
    subject_id : str
        Subject ID (e.g., 'sub-01')
    fmriprep_dir : Path
        Path to fMRIprep derivatives
    events_path : Path
        Path to task events file
    output_dir : Path
        Output directory for results
    t_r : float
        Repetition time in seconds
    confound_strategy : str
        Confound regression strategy
    smoothing_fwhm : float
        Smoothing kernel FWHM in mm (0 for no smoothing)
    
    Returns
    -------
    results : dict
        Dictionary with contrast maps and statistics
    """
    fmriprep_dir = Path(fmriprep_dir)
    output_dir = Path(output_dir)
    
    # Create subject output directory
    subject_output = output_dir / subject_id
    subject_output.mkdir(parents=True, exist_ok=True)
    
    # Find preprocessed BOLD file
    bold_pattern = f'{subject_id}/func/{subject_id}_task-speech_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz'
    bold_file = fmriprep_dir / bold_pattern
    
    if not bold_file.exists():
        raise FileNotFoundError(f"BOLD file not found: {bold_file}")
    
    # Find confounds file
    confounds_pattern = f'{subject_id}/func/{subject_id}_task-speech_desc-confounds_timeseries.tsv'
    confounds_file = fmriprep_dir / confounds_pattern
    
    if not confounds_file.exists():
        raise FileNotFoundError(f"Confounds file not found: {confounds_file}")
    
    # Find brain mask
    mask_pattern = f'{subject_id}/func/{subject_id}_task-speech_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz'
    mask_file = fmriprep_dir / mask_pattern
    
    print(f"\n  Loading data for {subject_id}...")
    
    # Load data
    bold_img = load_img(str(bold_file))
    n_volumes = bold_img.shape[-1]
    
    # Load events
    events = load_events(events_path)
    
    # Load and select confounds
    confounds_df = pd.read_csv(confounds_file, sep='\t')
    confounds = select_confounds(confounds_df, strategy=confound_strategy)
    
    print(f"    BOLD shape: {bold_img.shape}")
    print(f"    N volumes: {n_volumes}")
    print(f"    Confounds: {list(confounds.columns)}")
    
    # Create first-level model
    fmri_glm = FirstLevelModel(
        t_r=t_r,
        noise_model='ar1',
        standardize=False,
        hrf_model='spm',
        drift_model='cosine',
        high_pass=0.01,  # 100s high-pass filter
        smoothing_fwhm=smoothing_fwhm,
        mask_img=str(mask_file) if mask_file.exists() else None,
        minimize_memory=True,
        n_jobs=-1
    )
    
    print(f"    Fitting GLM...")
    
    # Fit the model
    fmri_glm.fit(str(bold_file), events=events, confounds=confounds)
    
    # Compute and save contrasts
    results = {'subject_id': subject_id, 'contrasts': {}}
    
    print(f"    Computing contrasts...")
    
    for contrast_name, contrast_def in CONTRASTS.items():
        try:
            # Compute contrast
            z_map = fmri_glm.compute_contrast(contrast_def, output_type='z_score')
            stat_map = fmri_glm.compute_contrast(contrast_def, output_type='stat')
            effect_map = fmri_glm.compute_contrast(contrast_def, output_type='effect_size')
            
            # Save maps
            nib.save(z_map, subject_output / f'{subject_id}_{contrast_name}_zstat.nii.gz')
            nib.save(stat_map, subject_output / f'{subject_id}_{contrast_name}_tstat.nii.gz')
            nib.save(effect_map, subject_output / f'{subject_id}_{contrast_name}_effect.nii.gz')
            
            results['contrasts'][contrast_name] = {
                'z_map': subject_output / f'{subject_id}_{contrast_name}_zstat.nii.gz',
                't_map': subject_output / f'{subject_id}_{contrast_name}_tstat.nii.gz',
                'effect_map': subject_output / f'{subject_id}_{contrast_name}_effect.nii.gz'
            }
        except Exception as e:
            print(f"      Warning: Could not compute contrast '{contrast_name}': {e}")
    
    # Compute F-contrasts
    for f_name, conditions in F_CONTRASTS.items():
        try:
            # F-contrast requires a list of contrasts
            f_map = fmri_glm.compute_contrast(conditions, output_type='z_score', stat_type='F')
            nib.save(f_map, subject_output / f'{subject_id}_{f_name}_fstat.nii.gz')
            
            results['contrasts'][f_name] = {
                'f_map': subject_output / f'{subject_id}_{f_name}_fstat.nii.gz'
            }
        except Exception as e:
            print(f"      Warning: Could not compute F-contrast '{f_name}': {e}")
    
    # Save design matrix plot
    try:
        design_matrix = fmri_glm.design_matrices_[0]
        fig = plot_design_matrix(design_matrix)
        fig.savefig(subject_output / f'{subject_id}_design_matrix.png', dpi=150, bbox_inches='tight')
        import matplotlib.pyplot as plt
        plt.close(fig)
    except Exception as e:
        print(f"      Warning: Could not save design matrix plot: {e}")
    
    print(f"    Results saved to: {subject_output}")
    
    return results


def run_all_subjects(fmriprep_dir, events_path, output_dir, t_r=2.0, 
                     confound_strategy='standard', smoothing_fwhm=6.0,
                     exclude_subjects=None):
    """
    Run first-level GLM for all subjects.
    
    Parameters
    ----------
    fmriprep_dir : Path
        Path to fMRIprep derivatives
    events_path : Path
        Path to task events file
    output_dir : Path
        Output directory for results
    t_r : float
        Repetition time in seconds
    confound_strategy : str
        Confound regression strategy
    smoothing_fwhm : float
        Smoothing kernel FWHM in mm
    exclude_subjects : list
        List of subject IDs to exclude
    
    Returns
    -------
    all_results : dict
        Dictionary with results for all subjects
    """
    fmriprep_dir = Path(fmriprep_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    exclude_subjects = exclude_subjects or []
    
    # Find all subjects
    subjects = sorted([d.name for d in fmriprep_dir.iterdir() 
                       if d.is_dir() and d.name.startswith('sub-')])
    
    # Remove excluded subjects
    subjects = [s for s in subjects if s not in exclude_subjects]
    
    print(f"\n{'='*70}")
    print("FIRST-LEVEL GLM ANALYSIS")
    print("="*70)
    print(f"\nSubjects to process: {len(subjects)}")
    print(f"Confound strategy: {confound_strategy}")
    print(f"Smoothing FWHM: {smoothing_fwhm} mm")
    print(f"Output directory: {output_dir}")
    
    all_results = {}
    successful = 0
    failed = []
    
    for i, subject_id in enumerate(subjects, 1):
        print(f"\n[{i}/{len(subjects)}] Processing {subject_id}...")
        
        try:
            results = run_first_level_glm(
                subject_id=subject_id,
                fmriprep_dir=fmriprep_dir,
                events_path=events_path,
                output_dir=output_dir,
                t_r=t_r,
                confound_strategy=confound_strategy,
                smoothing_fwhm=smoothing_fwhm
            )
            all_results[subject_id] = results
            successful += 1
        except Exception as e:
            print(f"    ERROR: {e}")
            failed.append((subject_id, str(e)))
    
    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print("="*70)
    print(f"\nSuccessfully processed: {successful}/{len(subjects)} subjects")
    
    if failed:
        print(f"\nFailed subjects ({len(failed)}):")
        for subject_id, error in failed:
            print(f"  - {subject_id}: {error}")
    
    # Save processing log
    log_path = output_dir / 'first_level_processing.json'
    log_data = {
        'n_subjects': len(subjects),
        'n_successful': successful,
        'n_failed': len(failed),
        'confound_strategy': confound_strategy,
        'smoothing_fwhm': smoothing_fwhm,
        't_r': t_r,
        'contrasts': list(CONTRASTS.keys()) + list(F_CONTRASTS.keys()),
        'failed_subjects': failed
    }
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    print(f"\nProcessing log saved to: {log_path}")
    print("="*70 + "\n")
    
    return all_results


def main():
    """Main function to run first-level GLM."""
    # Set paths
    dataset_root = Path(__file__).parent.parent.parent
    fmriprep_dir = dataset_root / 'derivatives' / 'fmriprep'
    events_path = dataset_root / 'task-speech_events.tsv'
    output_dir = dataset_root / 'results' / 'first_level'
    
    # Load task parameters
    task_json = dataset_root / 'task-speech_bold.json'
    if task_json.exists():
        with open(task_json) as f:
            task_params = json.load(f)
        t_r = task_params.get('RepetitionTime', 2.0)
    else:
        t_r = 2.0
    
    print(f"\nTR: {t_r} seconds")
    
    # Check if fMRIprep directory exists
    if not fmriprep_dir.exists():
        print(f"\nError: fMRIprep directory not found: {fmriprep_dir}")
        print("Please ensure fMRIprep outputs have been downloaded.")
        return
    
    # Check for motion exclusions
    exclusion_file = dataset_root / 'results' / 'qc' / 'motion_exclusions.txt'
    exclude_subjects = []
    
    if exclusion_file.exists():
        print(f"\nNote: Found motion exclusions file. Review before excluding subjects.")
    
    # Run first-level GLM for all subjects
    results = run_all_subjects(
        fmriprep_dir=fmriprep_dir,
        events_path=events_path,
        output_dir=output_dir,
        t_r=t_r,
        confound_strategy='standard',
        smoothing_fwhm=6.0,
        exclude_subjects=exclude_subjects
    )
    
    return results


if __name__ == "__main__":
    main()
