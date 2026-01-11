"""
Quality Control Summary Script for fMRIprep Outputs (VM Version)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')


def load_confounds(confounds_path):
    """Load confounds TSV file from fMRIprep."""
    return pd.read_csv(confounds_path, sep='\t')


def calculate_motion_metrics(confounds_df):
    """Calculate motion metrics from confounds."""
    metrics = {}
    
    # Framewise displacement
    if 'framewise_displacement' in confounds_df.columns:
        fd = confounds_df['framewise_displacement'].dropna()
        metrics['mean_fd'] = fd.mean()
        metrics['max_fd'] = fd.max()
        metrics['std_fd'] = fd.std()
        metrics['n_high_motion_volumes'] = (fd > 0.5).sum()
        metrics['pct_high_motion'] = (fd > 0.5).mean() * 100
    
    # DVARS
    if 'dvars' in confounds_df.columns:
        dvars = confounds_df['dvars'].dropna()
        metrics['mean_dvars'] = dvars.mean()
        metrics['max_dvars'] = dvars.max()
    
    # Translation parameters
    trans_cols = ['trans_x', 'trans_y', 'trans_z']
    if all(col in confounds_df.columns for col in trans_cols):
        for col in trans_cols:
            metrics[f'max_{col}'] = confounds_df[col].abs().max()
        metrics['max_translation'] = max(metrics[f'max_{col}'] for col in trans_cols)
    
    # Rotation parameters
    rot_cols = ['rot_x', 'rot_y', 'rot_z']
    if all(col in confounds_df.columns for col in rot_cols):
        for col in rot_cols:
            metrics[f'max_{col}_deg'] = np.degrees(confounds_df[col].abs().max())
        metrics['max_rotation_deg'] = max(metrics[f'max_{col}_deg'] for col in rot_cols)
    
    return metrics


def generate_qc_summary(fmriprep_dir, output_dir):
    """Generate QC summary for all subjects."""
    fmriprep_dir = Path(fmriprep_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all confounds files
    confounds_files = sorted(fmriprep_dir.glob('sub-*/func/*_desc-confounds_timeseries.tsv'))
    
    if len(confounds_files) == 0:
        print("No confounds files found!")
        print(f"Looking in: {fmriprep_dir}")
        return None
    
    print(f"Found {len(confounds_files)} subjects with confounds files")
    
    qc_data = []
    
    for confounds_path in confounds_files:
        subject_id = confounds_path.name.split('_')[0]
        
        try:
            confounds_df = load_confounds(confounds_path)
            metrics = calculate_motion_metrics(confounds_df)
            metrics['subject_id'] = subject_id
            metrics['n_volumes'] = len(confounds_df)
            qc_data.append(metrics)
        except Exception as e:
            print(f"Error processing {subject_id}: {e}")
            qc_data.append({'subject_id': subject_id, 'error': str(e)})
    
    qc_df = pd.DataFrame(qc_data)
    
    # Reorder columns
    cols = ['subject_id', 'n_volumes', 'mean_fd', 'max_fd', 'std_fd', 
            'n_high_motion_volumes', 'pct_high_motion', 'mean_dvars', 'max_dvars',
            'max_translation', 'max_rotation_deg']
    cols = [c for c in cols if c in qc_df.columns]
    qc_df = qc_df[cols + [c for c in qc_df.columns if c not in cols]]
    
    # Save to CSV
    qc_df.to_csv(output_dir / 'qc_summary.csv', index=False)
    print(f"\nQC summary saved to: {output_dir / 'qc_summary.csv'}")
    
    return qc_df


def flag_motion_outliers(qc_df, fd_threshold=0.5, pct_threshold=20):
    """Flag subjects with excessive motion."""
    if qc_df is None or len(qc_df) == 0:
        return [], []
    
    exclusions = []
    reasons = []
    
    for _, row in qc_df.iterrows():
        subject_id = row['subject_id']
        exclude = False
        reason = []
        
        if 'mean_fd' in row and pd.notna(row['mean_fd']):
            if row['mean_fd'] > fd_threshold:
                exclude = True
                reason.append(f"mean_fd={row['mean_fd']:.3f}")
        
        if 'pct_high_motion' in row and pd.notna(row['pct_high_motion']):
            if row['pct_high_motion'] > pct_threshold:
                exclude = True
                reason.append(f"pct_high_motion={row['pct_high_motion']:.1f}%")
        
        if exclude:
            exclusions.append(subject_id)
            reasons.append(f"{subject_id}: {', '.join(reason)}")
    
    return exclusions, reasons


def print_qc_report(qc_df, exclusions, reasons, output_dir):
    """Print and save QC report."""
    output_dir = Path(output_dir)
    
    print("\n" + "="*70)
    print("QUALITY CONTROL SUMMARY")
    print("="*70)
    
    if qc_df is None or len(qc_df) == 0:
        print("No QC data available")
        return
    
    print(f"\nTotal subjects: {len(qc_df)}")
    
    if 'mean_fd' in qc_df.columns:
        print(f"\nFramewise Displacement Statistics:")
        print(f"  Mean FD across subjects: {qc_df['mean_fd'].mean():.3f} mm")
        print(f"  Range: {qc_df['mean_fd'].min():.3f} - {qc_df['mean_fd'].max():.3f} mm")
    
    print(f"\n{'='*70}")
    print("MOTION EXCLUSIONS")
    print("="*70)
    
    if len(exclusions) == 0:
        print("\nNo subjects flagged for exclusion.")
    else:
        print(f"\n{len(exclusions)} subjects flagged:")
        for reason in reasons:
            print(f"  - {reason}")
    
    # Save exclusions
    with open(output_dir / 'motion_exclusions.txt', 'w') as f:
        f.write("Motion-based exclusion recommendations\n")
        f.write("="*50 + "\n\n")
        if len(exclusions) == 0:
            f.write("No subjects flagged for exclusion.\n")
        else:
            f.write(f"Flagged subjects ({len(exclusions)}):\n")
            for reason in reasons:
                f.write(f"  {reason}\n")
    
    print(f"\nExclusion list saved to: {output_dir / 'motion_exclusions.txt'}")
    print("="*70 + "\n")
