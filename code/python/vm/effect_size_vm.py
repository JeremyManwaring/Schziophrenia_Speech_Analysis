"""
Effect Size Analysis (VM Version)
"""

import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import json
import warnings

warnings.filterwarnings('ignore')

CONTRASTS = [
    'words_vs_baseline', 'sentences_vs_baseline', 'reversed_vs_baseline',
    'words_vs_reversed', 'sentences_vs_reversed', 'speech_vs_reversed', 'words_vs_sentences',
]


def cohens_d_with_ci(group1, group2, n_bootstrap=1000):
    """Calculate Cohen's d with bootstrap CI."""
    g1 = np.array(group1)[~np.isnan(group1)]
    g2 = np.array(group2)[~np.isnan(group2)]
    
    if len(g1) < 2 or len(g2) < 2:
        return np.nan, np.nan, np.nan
    
    n1, n2 = len(g1), len(g2)
    var1, var2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return np.nan, np.nan, np.nan
    
    d = (np.mean(g1) - np.mean(g2)) / pooled_std
    
    # Bootstrap
    d_bootstrap = []
    for _ in range(n_bootstrap):
        g1_boot = np.random.choice(g1, size=len(g1), replace=True)
        g2_boot = np.random.choice(g2, size=len(g2), replace=True)
        var1_boot, var2_boot = np.var(g1_boot, ddof=1), np.var(g2_boot, ddof=1)
        pooled_boot = np.sqrt(((n1 - 1) * var1_boot + (n2 - 1) * var2_boot) / (n1 + n2 - 2))
        if pooled_boot > 0:
            d_bootstrap.append((np.mean(g1_boot) - np.mean(g2_boot)) / pooled_boot)
    
    ci_lower = np.percentile(d_bootstrap, 2.5) if d_bootstrap else np.nan
    ci_upper = np.percentile(d_bootstrap, 97.5) if d_bootstrap else np.nan
    
    return d, ci_lower, ci_upper


def interpret_d(d):
    """Interpret Cohen's d."""
    if np.isnan(d):
        return "N/A"
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    return "large"


def calculate_effect_sizes(roi_df, output_dir, contrast_name):
    """Calculate effect sizes for group comparisons."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    roi_names = [col for col in roi_df.columns if col not in ['subject_id', 'group']]
    groups = roi_df['group'].values
    unique_groups = sorted(roi_df['group'].unique())
    
    results = {'contrast': contrast_name, 'pairwise_effects': []}
    
    comparisons = [('HC', 'AVH-'), ('HC', 'AVH+'), ('AVH-', 'AVH+')]
    
    for roi in roi_names:
        data = roi_df[roi].values
        
        for g1, g2 in comparisons:
            d1 = data[groups == g1]
            d2 = data[groups == g2]
            
            d, ci_lower, ci_upper = cohens_d_with_ci(d1, d2)
            
            results['pairwise_effects'].append({
                'roi': roi,
                'comparison': f'{g1}_vs_{g2}',
                'cohens_d': d,
                'd_ci_lower': ci_lower,
                'd_ci_upper': ci_upper,
                'interpretation': interpret_d(d)
            })
    
    pd.DataFrame(results['pairwise_effects']).to_csv(
        output_dir / f'{contrast_name}_effect_sizes.csv', index=False
    )
    
    return results


def create_forest_plot(effect_df, output_dir, contrast_name, comparison):
    """Create forest plot for effect sizes."""
    output_dir = Path(output_dir) / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    comp_df = effect_df[effect_df['comparison'] == comparison].copy()
    if len(comp_df) == 0:
        return
    
    comp_df = comp_df.sort_values('cohens_d')
    
    fig, ax = plt.subplots(figsize=(10, max(6, len(comp_df) * 0.4)))
    
    y_pos = np.arange(len(comp_df))
    
    ax.errorbar(
        comp_df['cohens_d'], y_pos,
        xerr=[comp_df['cohens_d'] - comp_df['d_ci_lower'],
              comp_df['d_ci_upper'] - comp_df['cohens_d']],
        fmt='o', color='steelblue', capsize=3, markersize=8
    )
    
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    for thresh in [-0.2, 0.2, -0.5, 0.5, -0.8, 0.8]:
        ax.axvline(x=thresh, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(comp_df['roi'].str.replace('_', ' '))
    ax.set_xlabel("Cohen's d")
    ax.set_title(f'{contrast_name}: {comparison}')
    
    plt.tight_layout()
    plt.savefig(output_dir / f'{contrast_name}_{comparison}_forest.png', dpi=150, bbox_inches='tight')
    plt.close()


def create_effect_heatmap(all_results, output_dir):
    """Create heatmap of effect sizes."""
    output_dir = Path(output_dir) / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    effect_data = []
    for contrast_name, results in all_results.items():
        if 'error' in results:
            continue
        for effect in results['pairwise_effects']:
            if effect['comparison'] == 'HC_vs_AVH+':
                effect_data.append({
                    'contrast': contrast_name,
                    'roi': effect['roi'],
                    'cohens_d': effect['cohens_d']
                })
    
    if len(effect_data) == 0:
        return
    
    effect_df = pd.DataFrame(effect_data)
    pivot_df = effect_df.pivot(index='roi', columns='contrast', values='cohens_d')
    
    key_rois = ['L_STG_posterior', 'L_IFG_triangularis', 'L_MTG', 'R_STG_posterior',
                'L_STG_anterior', 'L_STS', 'L_Heschl', 'R_Heschl']
    key_rois = [r for r in key_rois if r in pivot_df.index]
    if key_rois:
        pivot_df = pivot_df.loc[key_rois]
    
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(pivot_df, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
                linewidths=0.5, cbar_kws={'label': "Cohen's d"}, ax=ax)
    ax.set_title("Effect Sizes (Cohen's d): HC vs AVH+")
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_dir / 'effect_size_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()


def run_effect_size_analysis(roi_dir, output_dir):
    """Run effect size analysis for all contrasts."""
    roi_dir = Path(roi_dir)
    output_dir = Path(output_dir)
    
    print(f"\n{'='*70}")
    print("EFFECT SIZE ANALYSIS")
    print("="*70)
    
    all_results = {}
    all_effects = []
    
    for contrast_name in CONTRASTS:
        print(f"\nProcessing: {contrast_name}")
        
        try:
            roi_file = roi_dir / f'{contrast_name}_roi_values.csv'
            if not roi_file.exists():
                continue
            
            roi_df = pd.read_csv(roi_file)
            results = calculate_effect_sizes(roi_df, output_dir, contrast_name)
            all_results[contrast_name] = results
            
            effect_df = pd.DataFrame(results['pairwise_effects'])
            all_effects.extend([{**e, 'contrast': contrast_name} for e in results['pairwise_effects']])
            
            for comparison in ['HC_vs_AVH-', 'HC_vs_AVH+', 'AVH-_vs_AVH+']:
                create_forest_plot(effect_df, output_dir, contrast_name, comparison)
            
            large = effect_df[effect_df['interpretation'] == 'large']
            if len(large) > 0:
                print(f"  Large effects: {len(large)}")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    # Create heatmap
    create_effect_heatmap(all_results, output_dir)
    
    # Save summary
    if all_effects:
        pd.DataFrame(all_effects).to_csv(output_dir / 'effect_sizes_summary.csv', index=False)
    
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_dir}")
    print("="*70 + "\n")
    
    return all_results
