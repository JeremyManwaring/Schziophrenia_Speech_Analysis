"""
First-Level GLM Analysis (VM Version)
"""

import numpy as np
import pandas as pd
from pathlib import Path
import nibabel as nib
from nilearn.glm.first_level import FirstLevelModel
from nilearn.image import load_img
import warnings
import json

warnings.filterwarnings('ignore')

# Define contrasts
CONTRASTS = {
    'words_vs_baseline': 'words - white_noise',
    'sentences_vs_baseline': 'sentences - white_noise',
    'reversed_vs_baseline': 'reversed - white_noise',
    'words_vs_reversed': 'words - reversed',
    'sentences_vs_reversed': 'sentences - reversed',
    'speech_vs_reversed': '0.5*words + 0.5*sentences - reversed',
    'words_vs_sentences': 'words - sentences',
}

F_CONTRASTS = {
    'all_conditions': ['words', 'sentences', 'reversed'],
    'condition_differences': ['words - reversed', 'sentences - reversed', 'words - sentences'],
}


def load_events(events_path):
    """Load task events from BIDS events file."""
    events = pd.read_csv(events_path, sep='\t')
    if 'condition' in events.columns and 'trial_type' not in events.columns:
        events = events.rename(columns={'condition': 'trial_type'})
    return events[['onset', 'duration', 'trial_type']]


def select_confounds(confounds_df, strategy='standard'):
    """Select confound regressors for GLM."""
    if strategy == 'minimal':
        cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    elif strategy == 'standard':
        cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z',
                'csf', 'white_matter']
    else:
        cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    
    available_cols = [col for col in cols if col in confounds_df.columns]
    confounds = confounds_df[available_cols].copy()
    confounds = confounds.fillna(0)
    return confounds


def run_first_level_glm(subject_id, fmriprep_dir, events_path, output_dir, 
                        t_r=2.0, confound_strategy='standard', smoothing_fwhm=6.0):
    """Run first-level GLM for a single subject."""
    fmriprep_dir = Path(fmriprep_dir)
    output_dir = Path(output_dir)
    
    subject_output = output_dir / subject_id
    subject_output.mkdir(parents=True, exist_ok=True)
    
    # Find files
    bold_file = fmriprep_dir / subject_id / 'func' / f'{subject_id}_task-speech_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz'
    confounds_file = fmriprep_dir / subject_id / 'func' / f'{subject_id}_task-speech_desc-confounds_timeseries.tsv'
    mask_file = fmriprep_dir / subject_id / 'func' / f'{subject_id}_task-speech_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz'
    
    if not bold_file.exists():
        raise FileNotFoundError(f"BOLD file not found: {bold_file}")
    
    print(f"  Loading data for {subject_id}...")
    
    bold_img = load_img(str(bold_file))
    events = load_events(events_path)
    confounds_df = pd.read_csv(confounds_file, sep='\t')
    confounds = select_confounds(confounds_df, strategy=confound_strategy)
    
    print(f"    BOLD shape: {bold_img.shape}, Confounds: {list(confounds.columns)}")
    
    # Create and fit model
    fmri_glm = FirstLevelModel(
        t_r=t_r,
        noise_model='ar1',
        standardize=False,
        hrf_model='spm',
        drift_model='cosine',
        high_pass=0.01,
        smoothing_fwhm=smoothing_fwhm,
        mask_img=str(mask_file) if mask_file.exists() else None,
        minimize_memory=True,
        n_jobs=-1
    )
    
    print(f"    Fitting GLM...")
    fmri_glm.fit(str(bold_file), events=events, confounds=confounds)
    
    results = {'subject_id': subject_id, 'contrasts': {}}
    
    print(f"    Computing contrasts...")
    
    # T-contrasts
    for contrast_name, contrast_def in CONTRASTS.items():
        try:
            z_map = fmri_glm.compute_contrast(contrast_def, output_type='z_score')
            effect_map = fmri_glm.compute_contrast(contrast_def, output_type='effect_size')
            
            nib.save(z_map, subject_output / f'{subject_id}_{contrast_name}_zstat.nii.gz')
            nib.save(effect_map, subject_output / f'{subject_id}_{contrast_name}_effect.nii.gz')
            
            results['contrasts'][contrast_name] = {
                'z_map': str(subject_output / f'{subject_id}_{contrast_name}_zstat.nii.gz'),
                'effect_map': str(subject_output / f'{subject_id}_{contrast_name}_effect.nii.gz')
            }
        except Exception as e:
            print(f"      Warning: Could not compute '{contrast_name}': {e}")
    
    # F-contrasts
    for f_name, conditions in F_CONTRASTS.items():
        try:
            f_map = fmri_glm.compute_contrast(conditions, output_type='z_score', stat_type='F')
            nib.save(f_map, subject_output / f'{subject_id}_{f_name}_fstat.nii.gz')
            results['contrasts'][f_name] = {'f_map': str(subject_output / f'{subject_id}_{f_name}_fstat.nii.gz')}
        except Exception as e:
            print(f"      Warning: Could not compute F-contrast '{f_name}': {e}")
    
    print(f"    Results saved to: {subject_output}")
    return results


def run_all_subjects(fmriprep_dir, events_path, output_dir, t_r=2.0, 
                     confound_strategy='standard', smoothing_fwhm=6.0,
                     exclude_subjects=None):
    """Run first-level GLM for all subjects."""
    fmriprep_dir = Path(fmriprep_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    exclude_subjects = exclude_subjects or []
    
    # Find all subjects
    subjects = sorted([d.name for d in fmriprep_dir.iterdir() 
                       if d.is_dir() and d.name.startswith('sub-')])
    subjects = [s for s in subjects if s not in exclude_subjects]
    
    print(f"\n{'='*70}")
    print("FIRST-LEVEL GLM ANALYSIS")
    print("="*70)
    print(f"\nSubjects to process: {len(subjects)}")
    print(f"Confound strategy: {confound_strategy}")
    print(f"Smoothing FWHM: {smoothing_fwhm} mm")
    
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
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print("="*70)
    print(f"\nSuccessfully processed: {successful}/{len(subjects)} subjects")
    
    if failed:
        print(f"\nFailed subjects ({len(failed)}):")
        for subject_id, error in failed:
            print(f"  - {subject_id}: {error}")
    
    # Save log
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
    
    with open(output_dir / 'first_level_processing.json', 'w') as f:
        json.dump(log_data, f, indent=2)
    
    print("="*70 + "\n")
    return all_results
