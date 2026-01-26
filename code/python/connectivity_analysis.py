"""
Functional Connectivity Analysis: AVH- vs AVH+

Computes ROI-to-ROI connectivity matrices and seed-based connectivity
to examine network differences between patient groups.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import nibabel as nib
from nilearn.maskers import NiftiSpheresMasker, NiftiLabelsMasker
from nilearn.connectome import ConnectivityMeasure
from nilearn.plotting import plot_connectome, plot_matrix
from nilearn.image import load_img
from scipy import stats
from statsmodels.stats.multitest import multipletests
import matplotlib.pyplot as plt
import seaborn as sns
import json
import warnings

warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
FMRIPREP_DIR = BASE_DIR / 'derivatives' / 'fmriprep'
PARTICIPANTS_PATH = BASE_DIR / 'participants.tsv'
OUTPUT_DIR = BASE_DIR / 'results' / 'visualizations' / '04_connectivity'

# ROI definitions (MNI coordinates from literature)
ROIS = {
    'L_STG_posterior': (-58, -32, 8),
    'L_STG_anterior': (-54, 4, -8),
    'L_MTG': (-58, -22, -10),
    'L_IFG_triangularis': (-48, 30, 8),
    'L_IFG_opercularis': (-52, 14, 16),
    'L_STS': (-54, -40, 4),
    'L_Heschl': (-42, -22, 8),
    'R_STG_posterior': (58, -32, 8),
    'R_STG_anterior': (54, 4, -8),
    'R_MTG': (58, -22, -10),
    'R_IFG': (48, 30, 8),
    'R_Heschl': (42, -22, 8),
}

SEED_RADIUS = 6  # mm


def load_participants():
    """Load participant data."""
    df = pd.read_csv(PARTICIPANTS_PATH, sep='\t')
    return df


def get_preprocessed_bold(subject_id):
    """Get path to preprocessed BOLD file."""
    bold_path = FMRIPREP_DIR / subject_id / 'func' / \
                f'{subject_id}_task-speech_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz'
    
    if bold_path.exists():
        return str(bold_path)
    return None


def get_confounds(subject_id):
    """Get confound file path."""
    confound_path = FMRIPREP_DIR / subject_id / 'func' / \
                    f'{subject_id}_task-speech_desc-confounds_timeseries.tsv'
    
    if confound_path.exists():
        return str(confound_path)
    return None


def extract_roi_timeseries(bold_path, confound_path):
    """Extract timeseries from all ROIs."""
    coords = list(ROIS.values())
    roi_names = list(ROIS.keys())
    
    # Load confounds
    confounds_df = pd.read_csv(confound_path, sep='\t')
    
    # Select key confounds
    confound_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    if 'csf' in confounds_df.columns:
        confound_cols.append('csf')
    if 'white_matter' in confounds_df.columns:
        confound_cols.append('white_matter')
    
    confounds = confounds_df[confound_cols].fillna(0).values
    
    # Extract ROI timeseries
    masker = NiftiSpheresMasker(
        seeds=coords,
        radius=SEED_RADIUS,
        allow_overlap=True,  # Allow overlapping spheres
        standardize=True,
        detrend=True,
        high_pass=0.01,
        low_pass=0.1,
        t_r=2.0,  # TR in seconds
        memory='nilearn_cache'
    )
    
    try:
        timeseries = masker.fit_transform(bold_path, confounds=confounds)
        return timeseries, roi_names
    except Exception as e:
        print(f"    Error extracting timeseries: {e}")
        return None, None


def compute_connectivity_matrix(timeseries):
    """Compute correlation-based connectivity matrix."""
    conn_measure = ConnectivityMeasure(kind='correlation', vectorize=False)
    connectivity = conn_measure.fit_transform([timeseries])[0]
    return connectivity


def compute_group_connectivity(participants_df, group_name):
    """Compute average connectivity matrix for a group."""
    group_df = participants_df[participants_df['group'] == group_name]
    
    all_matrices = []
    processed_subjects = []
    
    for _, row in group_df.iterrows():
        sub_id = row['participant_id']
        bold_path = get_preprocessed_bold(sub_id)
        confound_path = get_confounds(sub_id)
        
        if bold_path is None or confound_path is None:
            continue
        
        timeseries, roi_names = extract_roi_timeseries(bold_path, confound_path)
        
        if timeseries is not None:
            conn_matrix = compute_connectivity_matrix(timeseries)
            all_matrices.append(conn_matrix)
            processed_subjects.append(sub_id)
    
    if len(all_matrices) == 0:
        return None, None, []
    
    # Average connectivity
    mean_matrix = np.mean(all_matrices, axis=0)
    
    return mean_matrix, all_matrices, processed_subjects


def fisher_z_transform(r):
    """Apply Fisher z-transformation to correlation values."""
    r = np.clip(r, -0.999, 0.999)
    return np.arctanh(r)


def compare_connectivity(matrices_group1, matrices_group2, roi_names):
    """
    Statistical comparison of connectivity between groups.
    Returns t-statistics and p-values for each connection.
    """
    n_rois = len(roi_names)
    t_stats = np.zeros((n_rois, n_rois))
    p_values = np.ones((n_rois, n_rois))
    
    # Fisher z-transform all matrices
    z_group1 = [fisher_z_transform(m) for m in matrices_group1]
    z_group2 = [fisher_z_transform(m) for m in matrices_group2]
    
    for i in range(n_rois):
        for j in range(i + 1, n_rois):
            values1 = [m[i, j] for m in z_group1]
            values2 = [m[i, j] for m in z_group2]
            
            if len(values1) > 2 and len(values2) > 2:
                t, p = stats.ttest_ind(values1, values2)
                t_stats[i, j] = t
                t_stats[j, i] = t
                p_values[i, j] = p
                p_values[j, i] = p
    
    return t_stats, p_values


def create_connectivity_heatmap(matrix, title, output_path, roi_names, vmin=-1, vmax=1):
    """Create heatmap visualization of connectivity matrix."""
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Create mask for diagonal
    mask = np.eye(len(roi_names), dtype=bool)
    
    sns.heatmap(
        matrix,
        mask=mask,
        xticklabels=roi_names,
        yticklabels=roi_names,
        cmap='RdBu_r',
        vmin=vmin,
        vmax=vmax,
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={'shrink': 0.8, 'label': 'Correlation (r)'},
        ax=ax
    )
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.yticks(fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def create_difference_heatmap(diff_matrix, t_matrix, p_matrix, roi_names, output_path):
    """Create heatmap showing connectivity differences with significance."""
    fig, axes = plt.subplots(1, 2, figsize=(20, 8))
    
    # Difference matrix
    mask = np.eye(len(roi_names), dtype=bool)
    
    sns.heatmap(
        diff_matrix,
        mask=mask,
        xticklabels=roi_names,
        yticklabels=roi_names,
        cmap='RdBu_r',
        center=0,
        vmin=-0.3,
        vmax=0.3,
        square=True,
        linewidths=0.5,
        cbar_kws={'shrink': 0.8, 'label': 'Difference (AVH- minus AVH+)'},
        ax=axes[0]
    )
    axes[0].set_title('Connectivity Difference\n(AVH- minus AVH+)', fontsize=12, fontweight='bold')
    axes[0].set_xticklabels(roi_names, rotation=45, ha='right', fontsize=8)
    axes[0].set_yticklabels(roi_names, fontsize=8)
    
    # Significance matrix (show -log10 p-values)
    sig_matrix = -np.log10(p_matrix + 1e-10)
    sig_matrix[mask] = 0
    
    # Threshold for significance
    sig_thresh = -np.log10(0.05)
    
    sns.heatmap(
        sig_matrix,
        mask=mask,
        xticklabels=roi_names,
        yticklabels=roi_names,
        cmap='Reds',
        vmin=0,
        vmax=3,
        square=True,
        linewidths=0.5,
        cbar_kws={'shrink': 0.8, 'label': '-log10(p-value)'},
        ax=axes[1]
    )
    
    # Add significance threshold line to colorbar
    axes[1].set_title(f'Statistical Significance\n(threshold: -log10(0.05) = {sig_thresh:.2f})', 
                      fontsize=12, fontweight='bold')
    axes[1].set_xticklabels(roi_names, rotation=45, ha='right', fontsize=8)
    axes[1].set_yticklabels(roi_names, fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def create_network_graph(diff_matrix, p_matrix, roi_names, output_path):
    """Create network graph visualization of significant differences."""
    coords = list(ROIS.values())
    
    # Threshold to show only significant connections
    sig_mask = p_matrix < 0.05
    display_matrix = np.where(sig_mask, diff_matrix, 0)
    
    # Check if there are any significant connections
    if np.sum(np.abs(display_matrix) > 0) == 0:
        print("    No significant connections to display")
        display_matrix = diff_matrix  # Show all if none significant
    
    fig = plt.figure(figsize=(12, 8))
    
    try:
        plot_connectome(
            display_matrix,
            coords,
            node_color='#3498db',
            node_size=50,
            edge_threshold='5%',
            colorbar=True,
            title='Connectivity Differences: AVH- vs AVH+',
            edge_cmap='RdBu_r'
        )
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
    except Exception as e:
        print(f"    Could not create network graph: {e}")
    
    plt.close()


def main():
    """Run connectivity analysis."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("FUNCTIONAL CONNECTIVITY ANALYSIS")
    print("="*70)
    
    participants_df = load_participants()
    roi_names = list(ROIS.keys())
    
    # Compute group connectivity matrices
    print("\nExtracting ROI timeseries for AVH- group...")
    avh_minus_mean, avh_minus_matrices, avh_minus_subs = compute_group_connectivity(
        participants_df, 'AVH-'
    )
    print(f"  Processed {len(avh_minus_subs)} subjects")
    
    print("\nExtracting ROI timeseries for AVH+ group...")
    avh_plus_mean, avh_plus_matrices, avh_plus_subs = compute_group_connectivity(
        participants_df, 'AVH+'
    )
    print(f"  Processed {len(avh_plus_subs)} subjects")
    
    if avh_minus_mean is None or avh_plus_mean is None:
        print("\nError: Could not compute connectivity for one or both groups")
        return
    
    # Statistical comparison
    print("\nComparing connectivity between groups...")
    t_stats, p_values = compare_connectivity(
        avh_minus_matrices, avh_plus_matrices, roi_names
    )
    
    # Difference matrix
    diff_matrix = avh_minus_mean - avh_plus_mean
    
    # Find significant connections
    sig_connections = []
    for i in range(len(roi_names)):
        for j in range(i + 1, len(roi_names)):
            if p_values[i, j] < 0.05:
                sig_connections.append({
                    'roi1': roi_names[i],
                    'roi2': roi_names[j],
                    'diff': diff_matrix[i, j],
                    't_stat': t_stats[i, j],
                    'p_value': p_values[i, j]
                })
    
    print(f"  Found {len(sig_connections)} significant differences (p < 0.05 uncorrected)")
    
    # Create visualizations
    print("\nCreating visualizations...")
    
    # Individual group matrices
    create_connectivity_heatmap(
        avh_minus_mean, 'AVH- Connectivity Matrix',
        OUTPUT_DIR / 'connectivity_matrix_AVH-.png', roi_names
    )
    
    create_connectivity_heatmap(
        avh_plus_mean, 'AVH+ Connectivity Matrix',
        OUTPUT_DIR / 'connectivity_matrix_AVH+.png', roi_names
    )
    
    # Difference heatmap with significance
    create_difference_heatmap(
        diff_matrix, t_stats, p_values, roi_names,
        OUTPUT_DIR / 'connectivity_difference.png'
    )
    
    # Network graph
    create_network_graph(
        diff_matrix, p_values, roi_names,
        OUTPUT_DIR / 'network_differences.png'
    )
    
    # Save matrices
    np.save(OUTPUT_DIR / 'connectivity_AVH-.npy', avh_minus_mean)
    np.save(OUTPUT_DIR / 'connectivity_AVH+.npy', avh_plus_mean)
    np.save(OUTPUT_DIR / 'connectivity_difference.npy', diff_matrix)
    np.save(OUTPUT_DIR / 'connectivity_pvalues.npy', p_values)
    
    # Save significant connections
    if sig_connections:
        sig_df = pd.DataFrame(sig_connections)
        sig_df = sig_df.sort_values('p_value')
        sig_df.to_csv(OUTPUT_DIR / 'significant_connections.csv', index=False)
    
    # Save summary
    summary = {
        'analysis': 'ROI-to-ROI Functional Connectivity',
        'comparison': 'AVH- vs AVH+',
        'method': 'Pearson correlation with Fisher z-transform',
        'n_rois': len(roi_names),
        'n_avh_minus': len(avh_minus_subs),
        'n_avh_plus': len(avh_plus_subs),
        'n_significant_connections': len(sig_connections),
        'roi_names': roi_names,
        'roi_coordinates': {k: list(v) for k, v in ROIS.items()}
    }
    
    with open(OUTPUT_DIR / 'connectivity_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Create README
    readme = f"""# Functional Connectivity Analysis: AVH- vs AVH+

## Overview
ROI-to-ROI functional connectivity analysis comparing schizophrenia patients
with and without auditory hallucinations.

## Method
- Extracted timeseries from 12 speech/language ROIs (6mm spheres)
- Computed Pearson correlations between all ROI pairs
- Applied Fisher z-transformation for statistical comparison
- Compared connectivity between AVH- and AVH+ groups (independent t-tests)

## ROIs Analyzed
"""
    
    for roi, coords in ROIS.items():
        readme += f"- {roi}: MNI ({coords[0]}, {coords[1]}, {coords[2]})\n"
    
    readme += f"""
## Sample Size
- AVH-: {len(avh_minus_subs)} subjects
- AVH+: {len(avh_plus_subs)} subjects

## Results
- {len(sig_connections)} connections showed significant differences (p < 0.05 uncorrected)

## Files
- `connectivity_matrix_AVH-.png` - Mean connectivity for AVH- group
- `connectivity_matrix_AVH+.png` - Mean connectivity for AVH+ group
- `connectivity_difference.png` - Difference with significance overlay
- `network_differences.png` - 3D brain network visualization
- `significant_connections.csv` - Table of significant differences
- `*.npy` - Raw connectivity matrices for further analysis

## Interpretation
- Red in difference maps: Higher connectivity in AVH-
- Blue in difference maps: Higher connectivity in AVH+
- Significant connections may indicate disrupted speech processing networks
"""
    
    with open(OUTPUT_DIR / 'README.txt', 'w') as f:
        f.write(readme)
    
    print("\n" + "="*70)
    print(f"Results saved to: {OUTPUT_DIR}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
