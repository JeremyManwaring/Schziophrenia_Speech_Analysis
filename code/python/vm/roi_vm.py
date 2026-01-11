"""
ROI-Based Analysis (VM Version)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from nilearn.maskers import NiftiSpheresMasker
from scipy import stats
from statsmodels.stats.multitest import multipletests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import warnings

warnings.filterwarnings('ignore')

# Speech/language ROIs (MNI coordinates)
SPEECH_ROIS = {
    'L_STG_posterior': {'coords': (-58, -22, 4), 'radius': 8},
    'L_STG_anterior': {'coords': (-54, 0, -8), 'radius': 8},
    'L_MTG': {'coords': (-60, -38, 0), 'radius': 8},
    'L_IFG_triangularis': {'coords': (-48, 24, 16), 'radius': 8},
    'L_IFG_opercularis': {'coords': (-52, 12, 8), 'radius': 8},
    'L_STS': {'coords': (-56, -32, 4), 'radius': 8},
    'R_STG_posterior': {'coords': (58, -22, 4), 'radius': 8},
    'R_STG_anterior': {'coords': (54, 0, -8), 'radius': 8},
    'R_MTG': {'coords': (60, -38, 0), 'radius': 8},
    'R_IFG': {'coords': (48, 24, 16), 'radius': 8},
    'L_Heschl': {'coords': (-42, -22, 8), 'radius': 6},
    'R_Heschl': {'coords': (42, -22, 8), 'radius': 6},
}

CONTRASTS = [
    'words_vs_baseline', 'sentences_vs_baseline', 'reversed_vs_baseline',
    'words_vs_reversed', 'sentences_vs_reversed', 'speech_vs_reversed', 'words_vs_sentences',
]


def extract_roi_values(contrast_map, coords, roi_names):
    """Extract mean activation from ROIs."""
    masker = NiftiSpheresMasker(seeds=coords, radius=8, standardize=False, allow_overlap=True)
    try:
        values = masker.fit_transform(contrast_map)
        return dict(zip(roi_names, values.flatten()))
    except Exception as e:
        print(f"    ROI extraction error: {e}")
        return {name: np.nan for name in roi_names}


def extract_all_subjects(first_level_dir, contrast_name, participants_df, roi_dict):
    """Extract ROI values for all subjects."""
    first_level_dir = Path(first_level_dir)
    
    coords = [roi['coords'] for roi in roi_dict.values()]
    roi_names = list(roi_dict.keys())
    
    all_data = []
    for _, row in participants_df.iterrows():
        subject_id = row['participant_id']
        map_path = first_level_dir / subject_id / f'{subject_id}_{contrast_name}_effect.nii.gz'
        
        if map_path.exists():
            roi_values = extract_roi_values(str(map_path), coords, roi_names)
            roi_values['subject_id'] = subject_id
            roi_values['group'] = row['group']
            all_data.append(roi_values)
    
    roi_df = pd.DataFrame(all_data)
    cols = ['subject_id', 'group'] + roi_names
    return roi_df[cols]


def cohens_d(group1, group2):
    """Calculate Cohen's d."""
    g1 = np.array(group1)[~np.isnan(group1)]
    g2 = np.array(group2)[~np.isnan(group2)]
    if len(g1) < 2 or len(g2) < 2:
        return np.nan
    n1, n2 = len(g1), len(g2)
    var1, var2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    return (np.mean(g1) - np.mean(g2)) / pooled_std if pooled_std > 0 else np.nan


def run_roi_analysis(roi_df, output_dir, contrast_name):
    """Run ROI analysis with ANOVA and effect sizes."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    roi_names = [col for col in roi_df.columns if col not in ['subject_id', 'group']]
    groups = roi_df['group'].values
    unique_groups = sorted(roi_df['group'].unique())
    
    results = {'contrast': contrast_name, 'anova': [], 'pairwise': [], 'descriptive': []}
    
    for roi in roi_names:
        data = roi_df[roi].values
        
        # ANOVA
        group_data = [data[groups == g] for g in unique_groups]
        group_data = [g[~np.isnan(g)] for g in group_data]
        
        try:
            F_stat, p_value = stats.f_oneway(*[g for g in group_data if len(g) > 0])
        except:
            F_stat, p_value = np.nan, np.nan
        
        results['anova'].append({'roi': roi, 'F_stat': F_stat, 'p_value': p_value})
        
        # Pairwise
        for i, g1 in enumerate(unique_groups):
            for g2 in unique_groups[i+1:]:
                d1 = data[groups == g1]
                d2 = data[groups == g2]
                d1_clean = d1[~np.isnan(d1)]
                d2_clean = d2[~np.isnan(d2)]
                
                try:
                    t_stat, t_pval = stats.ttest_ind(d1_clean, d2_clean)
                except:
                    t_stat, t_pval = np.nan, np.nan
                
                results['pairwise'].append({
                    'roi': roi, 'comparison': f'{g1}_vs_{g2}',
                    't_stat': t_stat, 'p_value': t_pval, 'cohens_d': cohens_d(d1, d2)
                })
        
        # Descriptive
        for g in unique_groups:
            g_data = data[groups == g]
            g_data = g_data[~np.isnan(g_data)]
            results['descriptive'].append({
                'roi': roi, 'group': g, 'n': len(g_data),
                'mean': np.mean(g_data) if len(g_data) > 0 else np.nan,
                'std': np.std(g_data, ddof=1) if len(g_data) > 1 else np.nan,
                'sem': stats.sem(g_data) if len(g_data) > 1 else np.nan
            })
    
    # FDR correction
    anova_pvals = [r['p_value'] for r in results['anova'] if not np.isnan(r['p_value'])]
    if len(anova_pvals) > 0:
        _, fdr_pvals, _, _ = multipletests(anova_pvals, method='fdr_bh')
        fdr_idx = 0
        for r in results['anova']:
            if not np.isnan(r['p_value']):
                r['p_fdr'] = fdr_pvals[fdr_idx]
                fdr_idx += 1
            else:
                r['p_fdr'] = np.nan
    
    # Save
    pd.DataFrame(results['anova']).to_csv(output_dir / f'{contrast_name}_roi_anova.csv', index=False)
    pd.DataFrame(results['pairwise']).to_csv(output_dir / f'{contrast_name}_roi_pairwise.csv', index=False)
    pd.DataFrame(results['descriptive']).to_csv(output_dir / f'{contrast_name}_roi_descriptive.csv', index=False)
    roi_df.to_csv(output_dir / f'{contrast_name}_roi_values.csv', index=False)
    
    return results


def create_roi_barplot(descriptive_df, output_dir, contrast_name):
    """Create bar plots for ROI activation."""
    output_dir = Path(output_dir) / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    key_rois = ['L_STG_posterior', 'L_IFG_triangularis', 'L_MTG', 'R_STG_posterior']
    rois_to_plot = [r for r in key_rois if r in descriptive_df['roi'].values]
    if len(rois_to_plot) == 0:
        return
    
    groups = ['HC', 'AVH-', 'AVH+']
    colors = ['#2ecc71', '#3498db', '#e74c3c']
    
    fig, axes = plt.subplots(1, len(rois_to_plot), figsize=(4*len(rois_to_plot), 5))
    if len(rois_to_plot) == 1:
        axes = [axes]
    
    for i, roi in enumerate(rois_to_plot):
        ax = axes[i]
        roi_data = descriptive_df[descriptive_df['roi'] == roi]
        
        means = [roi_data[roi_data['group'] == g]['mean'].values[0] if len(roi_data[roi_data['group'] == g]) > 0 else 0 for g in groups]
        sems = [roi_data[roi_data['group'] == g]['sem'].values[0] if len(roi_data[roi_data['group'] == g]) > 0 else 0 for g in groups]
        
        x = np.arange(len(groups))
        ax.bar(x, means, yerr=sems, color=colors, capsize=5, edgecolor='black')
        ax.set_xticks(x)
        ax.set_xticklabels(groups)
        ax.set_ylabel('Parameter Estimate')
        ax.set_title(roi.replace('_', ' '))
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    plt.suptitle(f'{contrast_name}', fontsize=14)
    plt.tight_layout()
    plt.savefig(output_dir / f'{contrast_name}_roi_barplot.png', dpi=150, bbox_inches='tight')
    plt.close()


def run_full_roi_analysis(first_level_dir, participants_path, output_dir):
    """Run ROI analysis for all contrasts."""
    participants_df = pd.read_csv(participants_path, sep='\t')
    output_dir = Path(output_dir)
    
    print(f"\n{'='*70}")
    print("ROI-BASED ANALYSIS")
    print("="*70)
    print(f"\nROIs: {len(SPEECH_ROIS)}, Contrasts: {len(CONTRASTS)}")
    
    all_results = {}
    
    for contrast_name in CONTRASTS:
        print(f"\nProcessing: {contrast_name}")
        
        try:
            roi_df = extract_all_subjects(first_level_dir, contrast_name, participants_df, SPEECH_ROIS)
            print(f"  Extracted {len(roi_df)} subjects")
            
            results = run_roi_analysis(roi_df, output_dir, contrast_name)
            all_results[contrast_name] = results
            
            descriptive_df = pd.DataFrame(results['descriptive'])
            create_roi_barplot(descriptive_df, output_dir, contrast_name)
            
            anova_df = pd.DataFrame(results['anova'])
            if 'p_fdr' in anova_df.columns:
                sig = anova_df[anova_df['p_fdr'] < 0.05]
                if len(sig) > 0:
                    print(f"  Significant ROIs: {len(sig)}")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    with open(output_dir / 'roi_analysis_summary.json', 'w') as f:
        json.dump({'n_rois': len(SPEECH_ROIS), 'n_contrasts': len(CONTRASTS), 
                   'roi_names': list(SPEECH_ROIS.keys()), 'contrasts': CONTRASTS}, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_dir}")
    print("="*70 + "\n")
    
    return all_results
