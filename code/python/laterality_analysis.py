"""
Laterality Index Analysis: AVH- vs AVH+

Computes laterality indices for bilateral ROI pairs and compares
hemisphere dominance between patient groups.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from statsmodels.stats.multitest import multipletests
import matplotlib.pyplot as plt
import seaborn as sns
import json
import warnings

warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
ROI_DIR = BASE_DIR / 'results' / 'vm_analysis' / 'results' / 'roi_analysis'
PARTICIPANTS_PATH = BASE_DIR / 'participants.tsv'
OUTPUT_DIR = BASE_DIR / 'results' / 'visualizations' / '05_laterality'

# Bilateral ROI pairs (left, right)
BILATERAL_PAIRS = {
    'STG_posterior': ('L_STG_posterior', 'R_STG_posterior'),
    'STG_anterior': ('L_STG_anterior', 'R_STG_anterior'),
    'MTG': ('L_MTG', 'R_MTG'),
    'Heschl': ('L_Heschl', 'R_Heschl'),
    'IFG': ('L_IFG_opercularis', 'R_IFG'),  # L_IFG_opercularis matches R_IFG location
}

# Key contrasts to analyze
CONTRASTS = [
    'sentences_vs_reversed',
    'speech_vs_reversed',
    'words_vs_sentences',
    'words_vs_reversed'
]

# Colors
COLORS = {
    'HC': '#7f8c8d',
    'AVH-': '#3498db',
    'AVH+': '#e74c3c'
}


def load_participants():
    """Load participant data."""
    return pd.read_csv(PARTICIPANTS_PATH, sep='\t')


def load_roi_data(contrast_name):
    """Load ROI activation values."""
    roi_file = ROI_DIR / f'{contrast_name}_roi_values.csv'
    
    if roi_file.exists():
        return pd.read_csv(roi_file)
    return None


def compute_laterality_index(left_val, right_val):
    """
    Compute laterality index.
    
    LI = (L - R) / (|L| + |R|)
    
    LI > 0: Left-lateralized
    LI < 0: Right-lateralized
    LI = 0: Bilateral/symmetric
    """
    denominator = np.abs(left_val) + np.abs(right_val)
    
    # Avoid division by zero
    if denominator == 0 or np.isnan(denominator):
        return np.nan
    
    return (left_val - right_val) / denominator


def compute_all_laterality_indices(data, roi_pair):
    """Compute laterality indices for all subjects."""
    left_roi, right_roi = roi_pair
    
    # Determine the subject ID column name
    if 'subject_id' in data.columns:
        id_col = 'subject_id'
    elif 'subject' in data.columns:
        id_col = 'subject'
    else:
        id_col = 'participant_id'
    
    # Handle different data formats
    if 'roi' in data.columns:
        # Long format
        left_data = data[data['roi'] == left_roi][[id_col, 'group', 'activation']]
        right_data = data[data['roi'] == right_roi][[id_col, 'activation']]
        
        merged = left_data.merge(
            right_data, on=id_col, suffixes=('_left', '_right')
        )
        
        merged['LI'] = merged.apply(
            lambda row: compute_laterality_index(row['activation_left'], row['activation_right']),
            axis=1
        )
        
        merged = merged.rename(columns={id_col: 'participant_id'})
        return merged[['participant_id', 'group', 'LI']]
    else:
        # Wide format - ROIs as columns
        if left_roi in data.columns and right_roi in data.columns:
            result = data[[id_col, 'group']].copy()
            result = result.rename(columns={id_col: 'participant_id'})
            
            result['LI'] = data.apply(
                lambda row: compute_laterality_index(row[left_roi], row[right_roi]),
                axis=1
            )
            return result
    
    return None


def analyze_laterality(contrast_name):
    """Analyze laterality for all ROI pairs in a contrast."""
    data = load_roi_data(contrast_name)
    
    if data is None:
        print(f"  No data found for {contrast_name}")
        return None
    
    results = []
    
    for pair_name, (left_roi, right_roi) in BILATERAL_PAIRS.items():
        li_data = compute_all_laterality_indices(data, (left_roi, right_roi))
        
        if li_data is None:
            continue
        
        # Compute group statistics
        for group in ['HC', 'AVH-', 'AVH+']:
            group_li = li_data[li_data['group'] == group]['LI'].dropna()
            
            if len(group_li) > 0:
                results.append({
                    'contrast': contrast_name,
                    'roi_pair': pair_name,
                    'group': group,
                    'mean_LI': group_li.mean(),
                    'std_LI': group_li.std(),
                    'sem_LI': stats.sem(group_li),
                    'n': len(group_li),
                    'lateralization': 'Left' if group_li.mean() > 0.1 else ('Right' if group_li.mean() < -0.1 else 'Bilateral')
                })
        
        # Statistical comparison: AVH- vs AVH+
        avh_minus_li = li_data[li_data['group'] == 'AVH-']['LI'].dropna()
        avh_plus_li = li_data[li_data['group'] == 'AVH+']['LI'].dropna()
        
        if len(avh_minus_li) > 2 and len(avh_plus_li) > 2:
            t_stat, p_value = stats.ttest_ind(avh_minus_li, avh_plus_li)
            
            # Cohen's d
            pooled_std = np.sqrt(
                ((len(avh_minus_li) - 1) * avh_minus_li.std()**2 + 
                 (len(avh_plus_li) - 1) * avh_plus_li.std()**2) /
                (len(avh_minus_li) + len(avh_plus_li) - 2)
            )
            cohens_d = (avh_minus_li.mean() - avh_plus_li.mean()) / pooled_std if pooled_std > 0 else 0
            
            results.append({
                'contrast': contrast_name,
                'roi_pair': pair_name,
                'comparison': 'AVH-_vs_AVH+',
                't_statistic': t_stat,
                'p_value': p_value,
                'cohens_d': cohens_d
            })
    
    return results


def create_laterality_barplot(all_results, output_dir):
    """Create bar plot showing laterality indices by group."""
    # Filter to group means
    group_data = [r for r in all_results if 'mean_LI' in r]
    
    if not group_data:
        return
    
    df = pd.DataFrame(group_data)
    
    # Create separate plot for each contrast
    for contrast in df['contrast'].unique():
        contrast_df = df[df['contrast'] == contrast]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        roi_pairs = contrast_df['roi_pair'].unique()
        x = np.arange(len(roi_pairs))
        width = 0.25
        
        for i, group in enumerate(['HC', 'AVH-', 'AVH+']):
            group_df = contrast_df[contrast_df['group'] == group]
            
            means = [group_df[group_df['roi_pair'] == rp]['mean_LI'].values[0] 
                     if len(group_df[group_df['roi_pair'] == rp]) > 0 else 0 
                     for rp in roi_pairs]
            sems = [group_df[group_df['roi_pair'] == rp]['sem_LI'].values[0]
                    if len(group_df[group_df['roi_pair'] == rp]) > 0 else 0
                    for rp in roi_pairs]
            
            ax.bar(x + i * width, means, width, yerr=sems, 
                   label=group, color=COLORS[group], alpha=0.7,
                   capsize=3, edgecolor='black', linewidth=0.5)
        
        ax.set_xlabel('ROI Pair', fontsize=12)
        ax.set_ylabel('Laterality Index (LI)', fontsize=12)
        ax.set_title(f'Laterality Index by Group\n{contrast}', fontsize=13, fontweight='bold')
        ax.set_xticks(x + width)
        ax.set_xticklabels(roi_pairs, rotation=45, ha='right')
        ax.legend(title='Group')
        
        # Add reference lines
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=1)
        ax.axhline(y=0.2, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
        ax.axhline(y=-0.2, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
        
        # Add annotations
        ax.text(len(roi_pairs) - 0.5, 0.9, 'Left Dominant →', ha='right', fontsize=10, style='italic')
        ax.text(len(roi_pairs) - 0.5, -0.9, '← Right Dominant', ha='right', fontsize=10, style='italic')
        
        ax.set_ylim(-1, 1)
        
        plt.tight_layout()
        plt.savefig(output_dir / f'{contrast}_laterality_barplot.png', dpi=150, bbox_inches='tight')
        plt.savefig(output_dir / f'{contrast}_laterality_barplot.svg', bbox_inches='tight')
        plt.close()


def create_summary_heatmap(all_results, output_dir):
    """Create heatmap summarizing laterality across contrasts and groups."""
    group_data = [r for r in all_results if 'mean_LI' in r]
    
    if not group_data:
        return
    
    df = pd.DataFrame(group_data)
    
    # AVH- vs AVH+ comparison focus
    avh_groups = df[df['group'].isin(['AVH-', 'AVH+'])]
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    
    for idx, group in enumerate(['AVH-', 'AVH+']):
        group_df = avh_groups[avh_groups['group'] == group]
        
        # Pivot to create heatmap data
        pivot = group_df.pivot(index='roi_pair', columns='contrast', values='mean_LI')
        
        sns.heatmap(
            pivot,
            cmap='RdBu_r',
            center=0,
            vmin=-0.5,
            vmax=0.5,
            annot=True,
            fmt='.2f',
            cbar_kws={'label': 'Laterality Index'},
            ax=axes[idx]
        )
        
        axes[idx].set_title(f'{group} Laterality', fontsize=12, fontweight='bold')
        axes[idx].set_xlabel('Contrast', fontsize=11)
        axes[idx].set_ylabel('ROI Pair', fontsize=11)
        plt.setp(axes[idx].get_xticklabels(), rotation=45, ha='right')
    
    plt.suptitle('Laterality Index Comparison: AVH- vs AVH+', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'laterality_heatmap.png', dpi=150, bbox_inches='tight')
    plt.savefig(output_dir / 'laterality_heatmap.svg', bbox_inches='tight')
    plt.close()


def create_statistical_summary(all_results, output_dir):
    """Create table of statistical comparisons (uses FDR-corrected p when available)."""
    stat_data = [r for r in all_results if 'p_value' in r]
    
    if not stat_data:
        return
    
    df = pd.DataFrame(stat_data)
    sort_col = 'p_fdr' if 'p_fdr' in df.columns else 'p_value'
    df = df.sort_values(sort_col)
    df.to_csv(output_dir / 'laterality_stats.csv', index=False)
    
    p_col = 'p_fdr' if 'p_fdr' in df.columns else 'p_value'
    p_vals = df[p_col].values
    
    # Create visualization of significant results
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Color by significance (FDR-corrected when available)
    colors = ['#e74c3c' if p < 0.05 else '#3498db' for p in p_vals]
    
    y_pos = np.arange(len(df))
    
    # Plot Cohen's d
    bars = ax.barh(y_pos, df['cohens_d'], color=colors, alpha=0.7, edgecolor='black')
    
    # Labels
    labels = [f"{row['contrast']}\n{row['roi_pair']}" for _, row in df.iterrows()]
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    
    ax.set_xlabel("Cohen's d (AVH- minus AVH+)", fontsize=11)
    ax.set_title('Laterality Differences: Effect Sizes (FDR-corrected)', fontsize=12, fontweight='bold')
    ax.axvline(x=0, color='gray', linestyle='-', linewidth=1)
    
    # Add p-values
    for i, (_, row) in enumerate(df.iterrows()):
        p = row[p_col]
        sig = '*' if p < 0.05 else ''
        ax.text(row['cohens_d'] + 0.02, i, f"p={p:.3f}{sig}", 
                va='center', fontsize=8)
    
    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#e74c3c', alpha=0.7, label='p < 0.05 (FDR)'),
        Patch(facecolor='#3498db', alpha=0.7, label='p ≥ 0.05')
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'laterality_effect_sizes.png', dpi=150, bbox_inches='tight')
    plt.close()


def main():
    """Run laterality analysis."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("LATERALITY INDEX ANALYSIS")
    print("="*70)
    
    all_results = []
    
    for contrast in CONTRASTS:
        print(f"\nAnalyzing {contrast}...")
        results = analyze_laterality(contrast)
        
        if results:
            all_results.extend(results)
    
    if not all_results:
        print("\nNo results generated. Check ROI data files.")
        return
    
    # FDR correction across all ROI-pair x contrast comparisons
    stat_data = [r for r in all_results if 'p_value' in r]
    if stat_data:
        p_vals = [r['p_value'] for r in stat_data]
        _, p_fdr, _, _ = multipletests(p_vals, alpha=0.05, method='fdr_bh')
        for r, q in zip(stat_data, p_fdr):
            r['p_fdr'] = float(q)
    
    # Create visualizations
    print("\nCreating visualizations...")
    create_laterality_barplot(all_results, OUTPUT_DIR)
    create_summary_heatmap(all_results, OUTPUT_DIR)
    create_statistical_summary(all_results, OUTPUT_DIR)
    
    # Save full results
    df = pd.DataFrame(all_results)
    df.to_csv(OUTPUT_DIR / 'laterality_all_results.csv', index=False)
    
    # Find significant differences (FDR-corrected)
    sig_results = [r for r in all_results if r.get('p_fdr') is not None and r['p_fdr'] < 0.05]
    
    # Summary statistics
    summary = {
        'analysis': 'Laterality Index Analysis',
        'comparison': 'AVH- vs AVH+',
        'formula': 'LI = (L - R) / (|L| + |R|)',
        'interpretation': {
            'LI > 0': 'Left hemisphere dominant',
            'LI < 0': 'Right hemisphere dominant',
            'LI ≈ 0': 'Bilateral/symmetric'
        },
        'roi_pairs_analyzed': list(BILATERAL_PAIRS.keys()),
        'contrasts_analyzed': CONTRASTS,
        'n_significant_differences': len(sig_results)
    }
    
    with open(OUTPUT_DIR / 'laterality_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Create README
    readme = f"""# Laterality Index Analysis: AVH- vs AVH+

## Overview
Laterality indices were computed to assess hemisphere dominance for speech
processing in schizophrenia patients with and without auditory hallucinations.

## Method
Laterality Index (LI) = (Left - Right) / (|Left| + |Right|)

- LI > 0: Left hemisphere dominant
- LI < 0: Right hemisphere dominant
- LI ≈ 0: Bilateral/symmetric

## ROI Pairs Analyzed
"""
    
    for pair_name, (left, right) in BILATERAL_PAIRS.items():
        readme += f"- {pair_name}: {left} vs {right}\n"
    
    readme += f"""
## Contrasts Analyzed
- sentences_vs_reversed (speech comprehension)
- speech_vs_reversed (overall speech processing)
- words_vs_sentences
- words_vs_reversed

## Results
- {len(sig_results)} significant laterality differences between AVH- and AVH+ (p < 0.05 FDR-corrected)

## Files
- `*_laterality_barplot.png/svg` - Bar plots for each contrast
- `laterality_heatmap.png/svg` - Summary heatmap
- `laterality_effect_sizes.png` - Cohen's d for group comparisons
- `laterality_stats.csv` - Statistical test results
- `laterality_all_results.csv` - Complete results table

## Interpretation
Differences in laterality between AVH- and AVH+ may indicate:
- Altered language network organization
- Compensatory hemisphere recruitment
- Disrupted interhemispheric processing
"""
    
    with open(OUTPUT_DIR / 'README.txt', 'w') as f:
        f.write(readme)
    
    print("\n" + "="*70)
    print(f"Found {len(sig_results)} significant laterality differences")
    print(f"Results saved to: {OUTPUT_DIR}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
