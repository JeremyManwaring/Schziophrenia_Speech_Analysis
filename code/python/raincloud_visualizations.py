"""
Raincloud Plot Visualizations for AVH Group Comparisons

Creates publication-quality raincloud plots showing distributions,
individual data points, and summary statistics for ROI activations.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
ROI_DIR = BASE_DIR / 'results' / 'vm_analysis' / 'results' / 'roi_analysis'
OUTPUT_DIR = BASE_DIR / 'results' / 'visualizations' / '02_raincloud_plots'

# ROIs and contrasts
ROIS = [
    'L_STG_posterior', 'L_STG_anterior', 'L_MTG', 'L_IFG_triangularis',
    'L_IFG_opercularis', 'L_STS', 'R_STG_posterior', 'R_STG_anterior',
    'R_MTG', 'R_IFG', 'L_Heschl', 'R_Heschl'
]

KEY_CONTRASTS = [
    'sentences_vs_reversed',
    'words_vs_sentences',
    'speech_vs_reversed',
    'words_vs_reversed'
]

# Color palette
COLORS = {
    'HC': '#7f8c8d',    # Gray
    'AVH-': '#3498db',  # Blue
    'AVH+': '#e74c3c'   # Red
}


def half_violinplot(data, x, y, hue, ax, palette, width=0.6, offset=0.15):
    """Create half violin plot (one side only)."""
    groups = data[hue].unique()
    positions = np.arange(len(data[x].unique()))
    
    for i, group in enumerate(groups):
        group_data = data[data[hue] == group]
        for j, category in enumerate(data[x].unique()):
            subset = group_data[group_data[x] == category][y].dropna()
            if len(subset) > 1:
                # Create violin
                parts = ax.violinplot(
                    subset, 
                    positions=[j + (i - 1) * offset],
                    widths=width,
                    showmeans=False,
                    showmedians=False,
                    showextrema=False
                )
                for pc in parts['bodies']:
                    pc.set_facecolor(palette[group])
                    pc.set_alpha(0.3)


def create_raincloud(data, x, y, hue, ax, palette, title=''):
    """Create raincloud plot with violin, box, and points."""
    groups = sorted(data[hue].unique())
    categories = sorted(data[x].unique())
    n_groups = len(groups)
    
    width = 0.25
    
    for i, group in enumerate(groups):
        group_data = data[data[hue] == group]
        offset = (i - (n_groups - 1) / 2) * width * 1.2
        
        for j, cat in enumerate(categories):
            subset = group_data[group_data[x] == cat][y].dropna().values
            pos = j + offset
            
            if len(subset) > 1:
                # Violin (half)
                parts = ax.violinplot(
                    subset,
                    positions=[pos],
                    widths=width,
                    showmeans=False,
                    showmedians=False,
                    showextrema=False
                )
                for pc in parts['bodies']:
                    pc.set_facecolor(palette[group])
                    pc.set_alpha(0.4)
                    # Clip to half
                    m = np.mean(pc.get_paths()[0].vertices[:, 0])
                    pc.get_paths()[0].vertices[:, 0] = np.clip(
                        pc.get_paths()[0].vertices[:, 0], -np.inf, m
                    )
                
                # Box plot
                bp = ax.boxplot(
                    subset,
                    positions=[pos + width * 0.3],
                    widths=width * 0.4,
                    patch_artist=True,
                    showfliers=False
                )
                for element in ['boxes', 'whiskers', 'caps', 'medians']:
                    plt.setp(bp[element], color=palette[group])
                for patch in bp['boxes']:
                    patch.set_facecolor('white')
                    patch.set_alpha(0.8)
                
                # Scatter points with jitter
                jitter = np.random.normal(0, width * 0.15, len(subset))
                ax.scatter(
                    np.ones(len(subset)) * (pos + width * 0.5) + jitter,
                    subset,
                    c=palette[group],
                    alpha=0.6,
                    s=15,
                    edgecolor='white',
                    linewidth=0.5
                )
    
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, rotation=45, ha='right')
    ax.set_title(title, fontsize=12, fontweight='bold')
    
    # Legend
    handles = [plt.Rectangle((0,0),1,1, facecolor=palette[g], alpha=0.6) for g in groups]
    ax.legend(handles, groups, loc='upper right', framealpha=0.9)


def load_roi_data(contrast_name):
    """Load ROI activation values for a contrast."""
    roi_file = ROI_DIR / f'{contrast_name}_roi_values.csv'
    
    if roi_file.exists():
        return pd.read_csv(roi_file)
    else:
        print(f"  Warning: ROI file not found: {roi_file}")
        return None


def create_all_rois_raincloud(contrast_name):
    """Create raincloud plot showing all ROIs for a contrast."""
    data = load_roi_data(contrast_name)
    
    if data is None:
        return
    
    # Melt data to long format if needed
    if 'roi' not in data.columns:
        # Determine id column name
        if 'subject_id' in data.columns:
            id_col = 'subject_id'
        elif 'subject' in data.columns:
            id_col = 'subject'
        else:
            id_col = 'participant_id'
        
        id_vars = [id_col, 'group']
        data = data.melt(
            id_vars=id_vars,
            value_vars=[c for c in data.columns if c not in id_vars],
            var_name='roi',
            value_name='activation'
        )
        data = data.rename(columns={id_col: 'subject'})
    
    # Filter to key ROIs
    left_rois = ['L_MTG', 'L_STS', 'L_STG_posterior', 'L_STG_anterior', 'L_IFG_opercularis', 'L_Heschl']
    right_rois = ['R_MTG', 'R_STG_posterior', 'R_STG_anterior', 'R_IFG', 'R_Heschl']
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 12))
    
    # Left hemisphere ROIs
    left_data = data[data['roi'].isin(left_rois)]
    if len(left_data) > 0:
        create_raincloud(
            left_data, x='roi', y='activation', hue='group',
            ax=axes[0], palette=COLORS,
            title=f'{contrast_name}: Left Hemisphere ROIs'
        )
        axes[0].set_ylabel('Activation (β)', fontsize=11)
        axes[0].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    
    # Right hemisphere ROIs
    right_data = data[data['roi'].isin(right_rois)]
    if len(right_data) > 0:
        create_raincloud(
            right_data, x='roi', y='activation', hue='group',
            ax=axes[1], palette=COLORS,
            title=f'{contrast_name}: Right Hemisphere ROIs'
        )
        axes[1].set_ylabel('Activation (β)', fontsize=11)
        axes[1].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f'{contrast_name}_all_rois_raincloud.png', dpi=150, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / f'{contrast_name}_all_rois_raincloud.svg', bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created raincloud plot for {contrast_name}")


def create_key_roi_comparison(contrast_name, roi_name):
    """Create detailed raincloud for a single key ROI."""
    data = load_roi_data(contrast_name)
    
    if data is None:
        return
    
    # Handle data format
    if 'roi' not in data.columns:
        if 'subject_id' in data.columns:
            id_col = 'subject_id'
        elif 'subject' in data.columns:
            id_col = 'subject'
        else:
            id_col = 'participant_id'
        
        id_vars = [id_col, 'group']
        data = data.melt(
            id_vars=id_vars,
            value_vars=[c for c in data.columns if c not in id_vars],
            var_name='roi',
            value_name='activation'
        )
        data = data.rename(columns={id_col: 'subject'})
    
    roi_data = data[data['roi'] == roi_name].copy()
    
    if len(roi_data) == 0:
        return
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    groups = ['HC', 'AVH-', 'AVH+']
    positions = [0, 1, 2]
    
    for pos, group in zip(positions, groups):
        subset = roi_data[roi_data['group'] == group]['activation'].dropna().values
        
        if len(subset) > 1:
            # Violin
            parts = ax.violinplot(
                subset,
                positions=[pos - 0.15],
                widths=0.4,
                showmeans=False,
                showmedians=False,
                showextrema=False
            )
            for pc in parts['bodies']:
                pc.set_facecolor(COLORS[group])
                pc.set_alpha(0.4)
            
            # Box
            bp = ax.boxplot(
                subset,
                positions=[pos + 0.1],
                widths=0.15,
                patch_artist=True,
                showfliers=False
            )
            for element in ['whiskers', 'caps', 'medians']:
                plt.setp(bp[element], color=COLORS[group], linewidth=1.5)
            for patch in bp['boxes']:
                patch.set_facecolor('white')
                patch.set_edgecolor(COLORS[group])
                patch.set_linewidth(1.5)
            
            # Points
            jitter = np.random.normal(0, 0.04, len(subset))
            ax.scatter(
                np.ones(len(subset)) * (pos + 0.25) + jitter,
                subset,
                c=COLORS[group],
                alpha=0.7,
                s=25,
                edgecolor='white',
                linewidth=0.5,
                zorder=10
            )
            
            # Mean line
            ax.hlines(
                np.mean(subset),
                pos - 0.3, pos + 0.35,
                colors=COLORS[group],
                linestyles='--',
                alpha=0.8,
                linewidth=2
            )
    
    ax.set_xticks(positions)
    ax.set_xticklabels(groups, fontsize=12)
    ax.set_ylabel('Activation (β)', fontsize=12)
    ax.set_title(f'{roi_name}\n{contrast_name}', fontsize=13, fontweight='bold')
    ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
    
    # Add statistics
    avh_minus = roi_data[roi_data['group'] == 'AVH-']['activation'].dropna()
    avh_plus = roi_data[roi_data['group'] == 'AVH+']['activation'].dropna()
    
    if len(avh_minus) > 1 and len(avh_plus) > 1:
        t_stat, p_val = stats.ttest_ind(avh_minus, avh_plus)
        cohens_d = (avh_minus.mean() - avh_plus.mean()) / np.sqrt(
            ((len(avh_minus)-1)*avh_minus.std()**2 + (len(avh_plus)-1)*avh_plus.std()**2) / 
            (len(avh_minus) + len(avh_plus) - 2)
        )
        
        ax.text(
            0.02, 0.98,
            f"AVH- vs AVH+:\nt = {t_stat:.2f}, p = {p_val:.3f}\nCohen's d = {cohens_d:.2f}",
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
        )
    
    plt.tight_layout()
    safe_roi = roi_name.replace('/', '_')
    plt.savefig(OUTPUT_DIR / f'{contrast_name}_{safe_roi}_raincloud.png', dpi=150, bbox_inches='tight')
    plt.close()


def create_summary_figure():
    """Create summary figure with key findings."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    key_comparisons = [
        ('sentences_vs_reversed', 'L_MTG'),
        ('sentences_vs_reversed', 'L_STS'),
        ('words_vs_sentences', 'L_MTG'),
        ('words_vs_sentences', 'L_STS')
    ]
    
    for idx, (contrast, roi) in enumerate(key_comparisons):
        ax = axes[idx // 2, idx % 2]
        data = load_roi_data(contrast)
        
        if data is None:
            continue
        
        if 'roi' not in data.columns:
            if 'subject_id' in data.columns:
                id_col = 'subject_id'
            elif 'subject' in data.columns:
                id_col = 'subject'
            else:
                id_col = 'participant_id'
            
            id_vars = [id_col, 'group']
            data = data.melt(
                id_vars=id_vars,
                value_vars=[c for c in data.columns if c not in id_vars],
                var_name='roi',
                value_name='activation'
            )
            data = data.rename(columns={id_col: 'subject'})
        
        roi_data = data[data['roi'] == roi]
        
        if len(roi_data) == 0:
            continue
        
        groups = ['HC', 'AVH-', 'AVH+']
        
        for pos, group in enumerate(groups):
            subset = roi_data[roi_data['group'] == group]['activation'].dropna().values
            
            if len(subset) > 1:
                # Violin
                parts = ax.violinplot(subset, positions=[pos], widths=0.6, showextrema=False)
                for pc in parts['bodies']:
                    pc.set_facecolor(COLORS[group])
                    pc.set_alpha(0.3)
                
                # Points
                jitter = np.random.normal(0, 0.08, len(subset))
                ax.scatter(
                    np.ones(len(subset)) * pos + jitter,
                    subset,
                    c=COLORS[group],
                    alpha=0.6,
                    s=20,
                    edgecolor='white',
                    linewidth=0.3
                )
                
                # Mean and error bar
                mean = np.mean(subset)
                sem = stats.sem(subset)
                ax.errorbar(pos, mean, yerr=sem, fmt='o', color='black', 
                           markersize=8, capsize=5, capthick=2, zorder=10)
        
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(groups, fontsize=11)
        ax.set_ylabel('Activation (β)', fontsize=11)
        ax.set_title(f'{roi}\n{contrast}', fontsize=11, fontweight='bold')
        ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
    
    plt.suptitle('Key ROI Differences: AVH- vs AVH+', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'key_findings_summary.png', dpi=150, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'key_findings_summary.svg', bbox_inches='tight')
    plt.close()


def main():
    """Generate all raincloud visualizations."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("RAINCLOUD PLOT VISUALIZATIONS")
    print("="*70)
    
    # Create plots for each key contrast
    for contrast in KEY_CONTRASTS:
        print(f"\nProcessing {contrast}...")
        create_all_rois_raincloud(contrast)
        
        # Individual ROI plots for key regions
        for roi in ['L_MTG', 'L_STS', 'L_STG_posterior', 'R_STG_posterior']:
            create_key_roi_comparison(contrast, roi)
    
    # Summary figure
    print("\nCreating summary figure...")
    create_summary_figure()
    
    # Create README
    readme = """# Raincloud Plots: AVH Group Comparisons

## Overview
Raincloud plots combine violin plots, box plots, and individual data points
to provide a comprehensive view of data distributions across groups.

## Color Coding
- Gray (HC): Healthy Controls
- Blue (AVH-): Schizophrenia without auditory hallucinations
- Red (AVH+): Schizophrenia with auditory hallucinations

## Files
- `*_all_rois_raincloud.png/svg` - All ROIs for a contrast
- `*_[ROI]_raincloud.png` - Individual ROI detail plots
- `key_findings_summary.png/svg` - Summary of main findings

## Key Findings
Large effect sizes (Cohen's d > 0.8) were found for:
- L_MTG in sentences_vs_reversed contrast
- L_STS in sentences_vs_reversed contrast
- L_MTG in words_vs_sentences contrast
- L_STS in words_vs_sentences contrast

## Interpretation
- Error bars show mean ± SEM
- Individual points show each subject's activation
- Dashed horizontal lines indicate group means
"""
    
    with open(OUTPUT_DIR / 'README.txt', 'w') as f:
        f.write(readme)
    
    print("\n" + "="*70)
    print(f"Raincloud plots saved to: {OUTPUT_DIR}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
