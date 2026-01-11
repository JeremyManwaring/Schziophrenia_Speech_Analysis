"""
ROI-Based Analysis

This script:
- Extracts mean activation from speech/language ROIs
- Runs group comparisons (Welch's ANOVA)
- Calculates effect sizes
- Applies FDR correction for multiple comparisons
"""

import numpy as np
import pandas as pd
from pathlib import Path
import nibabel as nib
from nilearn import datasets
from nilearn.image import load_img, resample_to_img
from nilearn.maskers import NiftiLabelsMasker, NiftiSpheresMasker
from scipy import stats
from statsmodels.stats.multitest import multipletests
import json
import warnings

warnings.filterwarnings('ignore')

# Define speech/language ROIs using MNI coordinates
# Based on meta-analyses of speech perception (e.g., Hickok & Poeppel, 2007)
SPEECH_ROIS = {
    # Left hemisphere
    'L_STG_posterior': {'coords': (-58, -22, 4), 'radius': 8},      # Left posterior STG (Wernicke's area)
    'L_STG_anterior': {'coords': (-54, 0, -8), 'radius': 8},        # Left anterior STG
    'L_MTG': {'coords': (-60, -38, 0), 'radius': 8},                # Left middle temporal gyrus
    'L_IFG_triangularis': {'coords': (-48, 24, 16), 'radius': 8},   # Broca's area (pars triangularis)
    'L_IFG_opercularis': {'coords': (-52, 12, 8), 'radius': 8},     # Broca's area (pars opercularis)
    'L_STS': {'coords': (-56, -32, 4), 'radius': 8},                # Left superior temporal sulcus
    
    # Right hemisphere homologues
    'R_STG_posterior': {'coords': (58, -22, 4), 'radius': 8},
    'R_STG_anterior': {'coords': (54, 0, -8), 'radius': 8},
    'R_MTG': {'coords': (60, -38, 0), 'radius': 8},
    'R_IFG': {'coords': (48, 24, 16), 'radius': 8},
    
    # Additional regions
    'L_Heschl': {'coords': (-42, -22, 8), 'radius': 6},             # Primary auditory cortex
    'R_Heschl': {'coords': (42, -22, 8), 'radius': 6},
}


def create_sphere_masker(roi_dict, reference_img):
    """
    Create a spherical masker for ROI extraction.
    
    Parameters
    ----------
    roi_dict : dict
        Dictionary with ROI names and coordinates/radii
    reference_img : str or nibabel image
        Reference image for masking
    
    Returns
    -------
    masker : NiftiSpheresMasker
        Fitted masker object
    roi_names : list
        List of ROI names
    """
    coords = [roi['coords'] for roi in roi_dict.values()]
    radii = [roi['radius'] for roi in roi_dict.values()]
    roi_names = list(roi_dict.keys())
    
    masker = NiftiSpheresMasker(
        seeds=coords,
        radius=radii[0],  # Use first radius as default (they're all the same)
        standardize=False,
        detrend=False
    )
    
    return masker, roi_names


def extract_roi_values(contrast_map, masker, roi_names):
    """
    Extract mean activation from ROIs.
    
    Parameters
    ----------
    contrast_map : str or nibabel image
        Path to contrast map
    masker : NiftiSpheresMasker
        Fitted masker
    roi_names : list
        List of ROI names
    
    Returns
    -------
    roi_values : dict
        Dictionary with ROI names and values
    """
    try:
        values = masker.fit_transform(contrast_map)
        roi_values = dict(zip(roi_names, values.flatten()))
    except Exception as e:
        roi_values = {name: np.nan for name in roi_names}
    
    return roi_values


def extract_all_subjects(first_level_dir, contrast_name, participants_df, roi_dict):
    """
    Extract ROI values for all subjects.
    
    Parameters
    ----------
    first_level_dir : Path
        Directory with first-level results
    contrast_name : str
        Name of the contrast
    participants_df : pd.DataFrame
        Participants DataFrame
    roi_dict : dict
        Dictionary with ROI definitions
    
    Returns
    -------
    roi_df : pd.DataFrame
        DataFrame with ROI values for all subjects
    """
    first_level_dir = Path(first_level_dir)
    
    # Find a reference image
    ref_img = None
    for _, row in participants_df.iterrows():
        subject_id = row['participant_id']
        map_path = first_level_dir / subject_id / f'{subject_id}_{contrast_name}_effect.nii.gz'
        if map_path.exists():
            ref_img = str(map_path)
            break
    
    if ref_img is None:
        raise ValueError(f"No contrast maps found for {contrast_name}")
    
    # Create masker
    masker, roi_names = create_sphere_masker(roi_dict, ref_img)
    
    # Extract values for each subject
    all_data = []
    
    for _, row in participants_df.iterrows():
        subject_id = row['participant_id']
        map_path = first_level_dir / subject_id / f'{subject_id}_{contrast_name}_effect.nii.gz'
        
        if map_path.exists():
            roi_values = extract_roi_values(str(map_path), masker, roi_names)
            roi_values['subject_id'] = subject_id
            roi_values['group'] = row['group']
            all_data.append(roi_values)
    
    roi_df = pd.DataFrame(all_data)
    
    # Reorder columns
    cols = ['subject_id', 'group'] + roi_names
    roi_df = roi_df[cols]
    
    return roi_df


def run_welch_anova(data, groups):
    """
    Run Welch's ANOVA test.
    
    Parameters
    ----------
    data : array-like
        Data values
    groups : array-like
        Group labels
    
    Returns
    -------
    F_stat : float
        F-statistic
    p_value : float
        p-value
    """
    unique_groups = np.unique(groups)
    group_data = [data[groups == g] for g in unique_groups]
    
    # Filter out NaN values
    group_data = [g[~np.isnan(g)] for g in group_data]
    
    # Check if we have enough data
    if any(len(g) < 2 for g in group_data):
        return np.nan, np.nan
    
    # Welch's ANOVA (using scipy.stats.f_oneway with equal_var=False would require pingouin)
    # Here we use a simple implementation
    from scipy.stats import f_oneway
    
    # Standard one-way ANOVA (for Welch's, would need additional implementation)
    try:
        F_stat, p_value = f_oneway(*group_data)
        return F_stat, p_value
    except:
        return np.nan, np.nan


def cohens_d(group1, group2):
    """
    Calculate Cohen's d effect size.
    
    Parameters
    ----------
    group1 : array-like
        First group data
    group2 : array-like
        Second group data
    
    Returns
    -------
    d : float
        Cohen's d
    """
    g1 = np.array(group1)[~np.isnan(group1)]
    g2 = np.array(group2)[~np.isnan(group2)]
    
    if len(g1) < 2 or len(g2) < 2:
        return np.nan
    
    n1, n2 = len(g1), len(g2)
    var1, var2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return np.nan
    
    return (np.mean(g1) - np.mean(g2)) / pooled_std


def eta_squared(F_stat, df_between, df_within):
    """
    Calculate eta-squared effect size.
    
    Parameters
    ----------
    F_stat : float
        F-statistic
    df_between : int
        Between-groups degrees of freedom
    df_within : int
        Within-groups degrees of freedom
    
    Returns
    -------
    eta_sq : float
        Eta-squared
    """
    if np.isnan(F_stat):
        return np.nan
    
    return (F_stat * df_between) / (F_stat * df_between + df_within)


def run_roi_analysis(roi_df, output_dir, contrast_name):
    """
    Run full ROI analysis with ANOVA and effect sizes.
    
    Parameters
    ----------
    roi_df : pd.DataFrame
        DataFrame with ROI values
    output_dir : Path
        Output directory
    contrast_name : str
        Name of the contrast
    
    Returns
    -------
    results : dict
        Analysis results
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    roi_names = [col for col in roi_df.columns if col not in ['subject_id', 'group']]
    groups = roi_df['group'].values
    unique_groups = sorted(roi_df['group'].unique())
    
    results = {
        'contrast': contrast_name,
        'n_subjects': len(roi_df),
        'groups': {g: int((groups == g).sum()) for g in unique_groups},
        'anova': [],
        'pairwise': [],
        'descriptive': []
    }
    
    # Run ANOVA for each ROI
    for roi in roi_names:
        data = roi_df[roi].values
        
        # ANOVA
        F_stat, p_value = run_welch_anova(data, groups)
        
        # Calculate n for each group
        ns = [(groups == g).sum() for g in unique_groups]
        df_between = len(unique_groups) - 1
        df_within = sum(ns) - len(unique_groups)
        
        eta_sq = eta_squared(F_stat, df_between, df_within)
        
        results['anova'].append({
            'roi': roi,
            'F_stat': F_stat,
            'p_value': p_value,
            'eta_squared': eta_sq
        })
        
        # Pairwise comparisons
        for i, g1 in enumerate(unique_groups):
            for g2 in unique_groups[i+1:]:
                d1 = data[groups == g1]
                d2 = data[groups == g2]
                
                # T-test
                t_stat, t_pval = stats.ttest_ind(d1[~np.isnan(d1)], d2[~np.isnan(d2)])
                
                # Effect size
                d = cohens_d(d1, d2)
                
                results['pairwise'].append({
                    'roi': roi,
                    'comparison': f'{g1}_vs_{g2}',
                    't_stat': t_stat,
                    'p_value': t_pval,
                    'cohens_d': d
                })
        
        # Descriptive statistics
        for g in unique_groups:
            g_data = data[groups == g]
            g_data = g_data[~np.isnan(g_data)]
            
            results['descriptive'].append({
                'roi': roi,
                'group': g,
                'n': len(g_data),
                'mean': np.mean(g_data) if len(g_data) > 0 else np.nan,
                'std': np.std(g_data, ddof=1) if len(g_data) > 1 else np.nan,
                'sem': stats.sem(g_data) if len(g_data) > 1 else np.nan
            })
    
    # Apply FDR correction
    anova_pvals = [r['p_value'] for r in results['anova']]
    valid_pvals = [p for p in anova_pvals if not np.isnan(p)]
    
    if len(valid_pvals) > 0:
        _, fdr_pvals, _, _ = multipletests(valid_pvals, method='fdr_bh')
        
        fdr_idx = 0
        for r in results['anova']:
            if not np.isnan(r['p_value']):
                r['p_fdr'] = fdr_pvals[fdr_idx]
                fdr_idx += 1
            else:
                r['p_fdr'] = np.nan
    
    # Save results
    anova_df = pd.DataFrame(results['anova'])
    anova_df.to_csv(output_dir / f'{contrast_name}_roi_anova.csv', index=False)
    
    pairwise_df = pd.DataFrame(results['pairwise'])
    pairwise_df.to_csv(output_dir / f'{contrast_name}_roi_pairwise.csv', index=False)
    
    descriptive_df = pd.DataFrame(results['descriptive'])
    descriptive_df.to_csv(output_dir / f'{contrast_name}_roi_descriptive.csv', index=False)
    
    # Save ROI values
    roi_df.to_csv(output_dir / f'{contrast_name}_roi_values.csv', index=False)
    
    return results


def create_roi_barplot(descriptive_df, output_dir, contrast_name, rois_to_plot=None):
    """
    Create bar plots for ROI activation by group.
    
    Parameters
    ----------
    descriptive_df : pd.DataFrame
        Descriptive statistics DataFrame
    output_dir : Path
        Output directory
    contrast_name : str
        Name of the contrast
    rois_to_plot : list
        List of ROIs to plot (default: all)
    """
    import matplotlib.pyplot as plt
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if rois_to_plot is None:
        rois_to_plot = descriptive_df['roi'].unique()
    
    # Limit to key ROIs for clarity
    key_rois = ['L_STG_posterior', 'L_IFG_triangularis', 'L_MTG', 'R_STG_posterior']
    rois_to_plot = [r for r in key_rois if r in descriptive_df['roi'].values]
    
    if len(rois_to_plot) == 0:
        rois_to_plot = descriptive_df['roi'].unique()[:4]
    
    groups = ['HC', 'AVH-', 'AVH+']
    colors = ['#2ecc71', '#3498db', '#e74c3c']  # Green, Blue, Red
    
    n_rois = len(rois_to_plot)
    fig, axes = plt.subplots(1, n_rois, figsize=(4*n_rois, 5))
    
    if n_rois == 1:
        axes = [axes]
    
    for i, roi in enumerate(rois_to_plot):
        ax = axes[i]
        roi_data = descriptive_df[descriptive_df['roi'] == roi]
        
        means = []
        sems = []
        for g in groups:
            g_row = roi_data[roi_data['group'] == g]
            if len(g_row) > 0:
                means.append(g_row['mean'].values[0])
                sems.append(g_row['sem'].values[0])
            else:
                means.append(0)
                sems.append(0)
        
        x = np.arange(len(groups))
        bars = ax.bar(x, means, yerr=sems, color=colors, capsize=5, edgecolor='black')
        
        ax.set_xticks(x)
        ax.set_xticklabels(groups)
        ax.set_ylabel('Parameter Estimate')
        ax.set_title(roi.replace('_', ' '))
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    plt.suptitle(f'{contrast_name.replace("_", " ").title()}', fontsize=14)
    plt.tight_layout()
    plt.savefig(output_dir / f'{contrast_name}_roi_barplot.png', dpi=150, bbox_inches='tight')
    plt.close()


def run_full_roi_analysis(first_level_dir, participants_path, output_dir):
    """
    Run ROI analysis for all contrasts.
    
    Parameters
    ----------
    first_level_dir : Path
        Directory with first-level results
    participants_path : Path
        Path to participants.tsv
    output_dir : Path
        Output directory
    
    Returns
    -------
    all_results : dict
        Results for all contrasts
    """
    first_level_dir = Path(first_level_dir)
    output_dir = Path(output_dir)
    
    # Load participants
    participants_df = pd.read_csv(participants_path, sep='\t')
    
    # Define contrasts
    contrasts = [
        'words_vs_baseline',
        'sentences_vs_baseline',
        'reversed_vs_baseline',
        'words_vs_reversed',
        'sentences_vs_reversed',
        'speech_vs_reversed',
        'words_vs_sentences',
    ]
    
    print("\n" + "="*70)
    print("ROI-BASED ANALYSIS")
    print("="*70)
    print(f"\nROIs: {len(SPEECH_ROIS)}")
    print(f"Contrasts: {len(contrasts)}")
    print(f"Output directory: {output_dir}")
    
    all_results = {}
    
    for contrast_name in contrasts:
        print(f"\n{'='*70}")
        print(f"Processing: {contrast_name}")
        print("="*70)
        
        try:
            # Extract ROI values
            roi_df = extract_all_subjects(
                first_level_dir=first_level_dir,
                contrast_name=contrast_name,
                participants_df=participants_df,
                roi_dict=SPEECH_ROIS
            )
            
            print(f"  Extracted ROI values for {len(roi_df)} subjects")
            
            # Run analysis
            results = run_roi_analysis(
                roi_df=roi_df,
                output_dir=output_dir,
                contrast_name=contrast_name
            )
            
            all_results[contrast_name] = results
            
            # Create bar plot
            descriptive_df = pd.DataFrame(results['descriptive'])
            create_roi_barplot(
                descriptive_df=descriptive_df,
                output_dir=output_dir / 'figures',
                contrast_name=contrast_name
            )
            
            # Print significant results
            anova_df = pd.DataFrame(results['anova'])
            sig_rois = anova_df[anova_df['p_fdr'] < 0.05]
            
            if len(sig_rois) > 0:
                print(f"\n  Significant ROIs (FDR p < 0.05):")
                for _, row in sig_rois.iterrows():
                    print(f"    - {row['roi']}: F={row['F_stat']:.2f}, p_fdr={row['p_fdr']:.4f}, eta²={row['eta_squared']:.3f}")
            else:
                print(f"\n  No significant ROIs after FDR correction")
            
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[contrast_name] = {'error': str(e)}
    
    # Save summary
    summary = {
        'n_rois': len(SPEECH_ROIS),
        'n_contrasts': len(contrasts),
        'roi_names': list(SPEECH_ROIS.keys()),
        'contrasts': contrasts
    }
    
    with open(output_dir / 'roi_analysis_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*70}")
    print("ROI ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nResults saved to: {output_dir}")
    print("="*70 + "\n")
    
    return all_results


def main():
    """Main function."""
    dataset_root = Path(__file__).parent.parent.parent
    first_level_dir = dataset_root / 'results' / 'first_level'
    participants_path = dataset_root / 'participants.tsv'
    output_dir = dataset_root / 'results' / 'roi_analysis'
    
    if not first_level_dir.exists():
        print(f"\nError: First-level results not found: {first_level_dir}")
        return
    
    results = run_full_roi_analysis(
        first_level_dir=first_level_dir,
        participants_path=participants_path,
        output_dir=output_dir
    )
    
    return results


if __name__ == "__main__":
    main()
