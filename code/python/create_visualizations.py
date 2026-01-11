#!/usr/bin/env python3
"""
Comprehensive Visualization Suite for fMRI Analysis Results
Creates publication-quality figures for QC, demographics, brain maps, and key findings.
"""

import os
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
from scipy import stats

# Set up paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
RESULTS_DIR = PROJECT_ROOT / 'results' / 'vm_analysis' / 'results'
FIGURES_DIR = PROJECT_ROOT / 'results' / 'figures'
PARTICIPANTS_PATH = PROJECT_ROOT / 'participants.tsv'

# Consistent color scheme
COLORS = {
    'HC': '#3498db',      # Blue
    'AVH-': '#e67e22',    # Orange  
    'AVH+': '#e74c3c',    # Red
}
GROUP_ORDER = ['HC', 'AVH-', 'AVH+']

# Plot styling
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.dpi': 100,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
})


def load_data():
    """Load all necessary data files."""
    data = {}
    
    # Load participants
    data['participants'] = pd.read_csv(PARTICIPANTS_PATH, sep='\t')
    
    # Load QC summary
    qc_path = RESULTS_DIR / 'qc' / 'qc_summary.csv'
    if qc_path.exists():
        data['qc'] = pd.read_csv(qc_path)
        # Merge with participants to get group info
        data['qc'] = data['qc'].merge(
            data['participants'][['participant_id', 'group']], 
            left_on='subject_id', 
            right_on='participant_id',
            how='left'
        )
    
    # Load effect sizes
    effect_path = RESULTS_DIR / 'effect_sizes' / 'effect_sizes_summary.csv'
    if effect_path.exists():
        data['effect_sizes'] = pd.read_csv(effect_path)
    
    # Load ROI values for key contrast
    roi_path = RESULTS_DIR / 'roi_analysis' / 'speech_vs_reversed_roi_values.csv'
    if roi_path.exists():
        data['roi_values'] = pd.read_csv(roi_path)
    
    # Load correlations
    corr_path = RESULTS_DIR / 'correlations' / 'speech_vs_reversed_psyrats_correlations.csv'
    if corr_path.exists():
        data['correlations'] = pd.read_csv(corr_path)
    
    return data


def create_qc_plots(data, output_dir):
    """Create QC visualization plots."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if 'qc' not in data:
        print("  No QC data available")
        return
    
    qc = data['qc']
    
    # 1. Framewise displacement by group - violin plot
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Create violin plot
    parts = ax.violinplot(
        [qc[qc['group'] == g]['mean_fd'].values for g in GROUP_ORDER],
        positions=range(len(GROUP_ORDER)),
        showmeans=True,
        showmedians=True
    )
    
    # Color the violins
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(COLORS[GROUP_ORDER[i]])
        pc.set_alpha(0.7)
    
    # Add individual points with jitter
    for i, group in enumerate(GROUP_ORDER):
        group_data = qc[qc['group'] == group]['mean_fd']
        x = np.random.normal(i, 0.04, size=len(group_data))
        ax.scatter(x, group_data, alpha=0.6, c=COLORS[group], s=30, edgecolor='white', linewidth=0.5)
    
    ax.set_xticks(range(len(GROUP_ORDER)))
    ax.set_xticklabels(GROUP_ORDER)
    ax.set_ylabel('Mean Framewise Displacement (mm)')
    ax.set_title('Head Motion by Group')
    ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='Typical threshold')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'motion_by_group.png')
    plt.savefig(output_dir / 'motion_by_group.svg')
    plt.close()
    
    # 2. Motion outliers scatter plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for group in GROUP_ORDER:
        group_data = qc[qc['group'] == group]
        ax.scatter(
            group_data['mean_fd'], 
            group_data['pct_high_motion'],
            c=COLORS[group],
            label=group,
            s=60,
            alpha=0.7,
            edgecolor='white',
            linewidth=0.5
        )
    
    # Highlight outliers (>20% high motion)
    outliers = qc[qc['pct_high_motion'] > 20]
    for _, row in outliers.iterrows():
        ax.annotate(
            row['subject_id'].replace('sub-', ''),
            (row['mean_fd'], row['pct_high_motion']),
            fontsize=9,
            xytext=(5, 5),
            textcoords='offset points'
        )
    
    ax.axhline(y=20, color='red', linestyle='--', alpha=0.5, label='Exclusion threshold (20%)')
    ax.set_xlabel('Mean Framewise Displacement (mm)')
    ax.set_ylabel('Percentage High-Motion Volumes (%)')
    ax.set_title('Motion Quality Control')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'motion_outliers.png')
    plt.savefig(output_dir / 'motion_outliers.svg')
    plt.close()
    
    # 3. FD distribution histogram
    fig, ax = plt.subplots(figsize=(8, 5))
    
    for group in GROUP_ORDER:
        group_data = qc[qc['group'] == group]['mean_fd']
        ax.hist(group_data, bins=15, alpha=0.5, label=group, color=COLORS[group], edgecolor='white')
    
    ax.axvline(x=0.5, color='red', linestyle='--', alpha=0.7, label='Threshold')
    ax.set_xlabel('Mean Framewise Displacement (mm)')
    ax.set_ylabel('Count')
    ax.set_title('Distribution of Head Motion')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fd_distribution.png')
    plt.savefig(output_dir / 'fd_distribution.svg')
    plt.close()
    
    print(f"  Saved QC plots to {output_dir}")


def create_demographics_plots(data, output_dir):
    """Create demographics visualization plots."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    participants = data['participants'].copy()
    
    # 1. Age by group - violin plot with points
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Prepare data
    age_data = [participants[participants['group'] == g]['age'].dropna().values for g in GROUP_ORDER]
    
    parts = ax.violinplot(age_data, positions=range(len(GROUP_ORDER)), showmeans=True, showmedians=True)
    
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(COLORS[GROUP_ORDER[i]])
        pc.set_alpha(0.7)
    
    # Add individual points
    for i, group in enumerate(GROUP_ORDER):
        group_data = participants[participants['group'] == group]['age'].dropna()
        x = np.random.normal(i, 0.04, size=len(group_data))
        ax.scatter(x, group_data, alpha=0.6, c=COLORS[group], s=30, edgecolor='white', linewidth=0.5)
    
    ax.set_xticks(range(len(GROUP_ORDER)))
    ax.set_xticklabels(GROUP_ORDER)
    ax.set_ylabel('Age (years)')
    ax.set_title('Age Distribution by Group')
    
    # Add sample sizes
    for i, group in enumerate(GROUP_ORDER):
        n = len(participants[participants['group'] == group])
        ax.text(i, ax.get_ylim()[0] - 2, f'n={n}', ha='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'age_by_group.png')
    plt.savefig(output_dir / 'age_by_group.svg')
    plt.close()
    
    # 2. IQ by group - box plot
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Filter out n/a values and convert to numeric
    participants['iq_numeric'] = pd.to_numeric(participants['iq'], errors='coerce')
    
    iq_data = []
    for group in GROUP_ORDER:
        group_iq = participants[participants['group'] == group]['iq_numeric'].dropna()
        iq_data.append(group_iq.values)
    
    bp = ax.boxplot(iq_data, positions=range(len(GROUP_ORDER)), patch_artist=True, widths=0.6)
    
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(COLORS[GROUP_ORDER[i]])
        patch.set_alpha(0.7)
    
    # Add individual points
    for i, group in enumerate(GROUP_ORDER):
        group_data = participants[participants['group'] == group]['iq_numeric'].dropna()
        x = np.random.normal(i, 0.04, size=len(group_data))
        ax.scatter(x, group_data, alpha=0.6, c=COLORS[group], s=30, edgecolor='white', linewidth=0.5, zorder=3)
    
    ax.set_xticks(range(len(GROUP_ORDER)))
    ax.set_xticklabels(GROUP_ORDER)
    ax.set_ylabel('IQ Score')
    ax.set_title('IQ Distribution by Group')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'iq_by_group.png')
    plt.savefig(output_dir / 'iq_by_group.svg')
    plt.close()
    
    # 3. Sex distribution - stacked bar chart
    fig, ax = plt.subplots(figsize=(8, 6))
    
    sex_counts = participants.groupby(['group', 'sex']).size().unstack(fill_value=0)
    sex_counts = sex_counts.reindex(GROUP_ORDER)
    
    x = np.arange(len(GROUP_ORDER))
    width = 0.6
    
    bottom = np.zeros(len(GROUP_ORDER))
    sex_colors = {'male': '#5dade2', 'female': '#f1948a'}
    
    for sex in ['male', 'female']:
        if sex in sex_counts.columns:
            values = sex_counts[sex].values
            ax.bar(x, values, width, label=sex.capitalize(), bottom=bottom, 
                   color=sex_colors[sex], edgecolor='white', linewidth=1)
            # Add count labels
            for i, v in enumerate(values):
                if v > 0:
                    ax.text(i, bottom[i] + v/2, str(int(v)), ha='center', va='center', fontweight='bold')
            bottom += values
    
    ax.set_xticks(x)
    ax.set_xticklabels(GROUP_ORDER)
    ax.set_ylabel('Count')
    ax.set_title('Sex Distribution by Group')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'sex_distribution.png')
    plt.savefig(output_dir / 'sex_distribution.svg')
    plt.close()
    
    # 4. PSYRATS distribution for AVH+ group
    fig, ax = plt.subplots(figsize=(8, 5))
    
    avh_plus = participants[participants['group'] == 'AVH+']
    psyrats = pd.to_numeric(avh_plus['psyrats'], errors='coerce').dropna()
    
    ax.hist(psyrats, bins=10, color=COLORS['AVH+'], alpha=0.7, edgecolor='white')
    ax.axvline(psyrats.mean(), color='black', linestyle='--', linewidth=2, label=f'Mean = {psyrats.mean():.1f}')
    ax.set_xlabel('PSYRATS Score (Auditory Hallucination Severity)')
    ax.set_ylabel('Count')
    ax.set_title('PSYRATS Distribution in AVH+ Group')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'psyrats_distribution.png')
    plt.savefig(output_dir / 'psyrats_distribution.svg')
    plt.close()
    
    print(f"  Saved demographics plots to {output_dir}")


def create_brain_maps(output_dir):
    """Create brain activation visualizations."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        from nilearn import plotting
        import nibabel as nib
    except ImportError:
        print("  Nilearn/nibabel not available, skipping brain maps")
        return
    
    second_level_dir = RESULTS_DIR / 'second_level'
    
    contrasts = ['speech_vs_reversed', 'sentences_vs_reversed', 'words_vs_reversed']
    
    for contrast in contrasts:
        contrast_dir = second_level_dir / contrast
        if not contrast_dir.exists():
            continue
        
        # Overall mean activation
        mean_map = contrast_dir / f'{contrast}_overall_mean_zstat.nii.gz'
        if mean_map.exists():
            try:
                fig, axes = plt.subplots(1, 1, figsize=(12, 4))
                plotting.plot_glass_brain(
                    str(mean_map),
                    display_mode='lyrz',
                    colorbar=True,
                    title=f'{contrast.replace("_", " ").title()} - Group Mean',
                    axes=axes,
                    threshold=2.0
                )
                plt.savefig(output_dir / f'{contrast}_group_glass_brain.png')
                plt.savefig(output_dir / f'{contrast}_group_glass_brain.svg')
                plt.close()
            except Exception as e:
                print(f"    Error creating glass brain for {contrast}: {e}")
        
        # Group difference maps
        for comparison in ['HC_vs_AVH+', 'AVH-_vs_AVH+', 'HC_vs_AVH-']:
            diff_map = contrast_dir / f'{contrast}_{comparison}_zstat.nii.gz'
            if diff_map.exists():
                try:
                    fig = plt.figure(figsize=(12, 4))
                    plotting.plot_glass_brain(
                        str(diff_map),
                        display_mode='lyrz',
                        colorbar=True,
                        title=f'{contrast.replace("_", " ").title()} - {comparison}',
                        threshold=1.5,
                        cmap='RdBu_r'
                    )
                    plt.savefig(output_dir / f'{contrast}_{comparison}_glass_brain.png')
                    plt.close()
                except Exception as e:
                    print(f"    Error creating glass brain for {contrast} {comparison}: {e}")
    
    # Create ROI locations visualization
    create_roi_location_plot(output_dir)
    
    print(f"  Saved brain maps to {output_dir}")


def create_roi_location_plot(output_dir):
    """Create a brain map showing ROI locations."""
    try:
        from nilearn import plotting
    except ImportError:
        return
    
    # ROI coordinates (MNI)
    rois = {
        'L_STG_post': (-58, -22, 4),
        'L_STG_ant': (-54, 4, -8),
        'L_MTG': (-60, -12, -12),
        'L_IFG_tri': (-48, 26, 14),
        'L_IFG_oper': (-48, 14, 8),
        'L_STS': (-54, -40, 4),
        'R_STG_post': (58, -22, 4),
        'R_STG_ant': (54, 4, -8),
        'R_MTG': (60, -12, -12),
        'R_IFG': (48, 20, 10),
        'L_Heschl': (-42, -22, 10),
        'R_Heschl': (42, -22, 10),
    }
    
    coords = list(rois.values())
    labels = list(rois.keys())
    
    # Node values - 1 for left hemisphere, 2 for right hemisphere
    node_values = np.array([1 if 'L_' in k else 2 for k in rois.keys()])
    
    fig = plt.figure(figsize=(12, 5))
    
    plotting.plot_markers(
        node_values,
        coords,
        node_size=100,
        node_cmap='RdBu_r',
        display_mode='lyrz',
        title='Speech/Language ROI Locations (MNI)\nBlue=Left, Red=Right',
        colorbar=False
    )
    
    plt.savefig(output_dir / 'roi_locations.png')
    plt.savefig(output_dir / 'roi_locations.svg')
    plt.close()


def create_summary_figure(data, output_dir):
    """Create multi-panel summary figure with key findings."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    # Panel A: ROI bar plot for significant ROIs (L_MTG, L_STS)
    ax_a = fig.add_subplot(gs[0, 0])
    create_significant_roi_panel(data, ax_a)
    ax_a.set_title('A. Activation in Key Speech Regions', fontweight='bold', fontsize=14)
    
    # Panel B: Effect size forest plot for large effects
    ax_b = fig.add_subplot(gs[0, 1])
    create_effect_size_panel(data, ax_b)
    ax_b.set_title('B. Large Effect Sizes (|d| ≥ 0.8)', fontweight='bold', fontsize=14)
    
    # Panel C: PSYRATS correlation
    ax_c = fig.add_subplot(gs[1, 0])
    create_correlation_panel(data, ax_c)
    ax_c.set_title('C. Brain-Behavior Correlation (AVH+ only)', fontweight='bold', fontsize=14)
    
    # Panel D: Summary statistics
    ax_d = fig.add_subplot(gs[1, 1])
    create_stats_summary_panel(data, ax_d)
    ax_d.set_title('D. Study Summary', fontweight='bold', fontsize=14)
    
    plt.suptitle('Speech Perception in Schizophrenia: Key Findings', fontsize=18, fontweight='bold', y=0.98)
    
    plt.savefig(output_dir / 'key_findings_figure.png')
    plt.savefig(output_dir / 'key_findings_figure.svg')
    plt.close()
    
    print(f"  Saved summary figure to {output_dir}")


def create_significant_roi_panel(data, ax):
    """Panel A: Bar plot for significant ROIs."""
    if 'roi_values' not in data:
        ax.text(0.5, 0.5, 'ROI data not available', ha='center', va='center', transform=ax.transAxes)
        return
    
    # Focus on L_MTG and L_STS for sentences_vs_reversed (highest effect sizes)
    # Load sentences_vs_reversed data
    sentences_roi_path = RESULTS_DIR / 'roi_analysis' / 'sentences_vs_reversed_roi_values.csv'
    if sentences_roi_path.exists():
        sent_df = pd.read_csv(sentences_roi_path)
    else:
        sent_df = data['roi_values'].copy()
    
    # The ROI CSV already has 'group' column, no need to merge
    
    rois_to_plot = ['L_MTG', 'L_STS']
    
    x = np.arange(len(rois_to_plot))
    width = 0.25
    
    for i, group in enumerate(GROUP_ORDER):
        group_data = sent_df[sent_df['group'] == group]
        means = [group_data[roi].mean() for roi in rois_to_plot]
        sems = [group_data[roi].std() / np.sqrt(len(group_data)) for roi in rois_to_plot]
        
        ax.bar(x + i*width, means, width, label=group, color=COLORS[group], 
               yerr=sems, capsize=3, alpha=0.8, edgecolor='white', linewidth=1)
    
    ax.set_xticks(x + width)
    ax.set_xticklabels([r.replace('_', ' ') for r in rois_to_plot])
    ax.set_ylabel('Mean Activation (β)')
    ax.set_xlabel('Region of Interest')
    ax.legend(title='Group', loc='upper right')
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)


def create_effect_size_panel(data, ax):
    """Panel B: Forest plot for large effect sizes."""
    if 'effect_sizes' not in data:
        ax.text(0.5, 0.5, 'Effect size data not available', ha='center', va='center', transform=ax.transAxes)
        return
    
    es_df = data['effect_sizes']
    
    # Get large effects
    large_effects = es_df[es_df['interpretation'] == 'large'].copy()
    
    if len(large_effects) == 0:
        large_effects = es_df.nlargest(6, 'cohens_d', keep='first')
    
    # Create forest plot
    y_positions = range(len(large_effects))
    
    # Plot effect sizes with CIs
    for i, (_, row) in enumerate(large_effects.iterrows()):
        color = '#2ecc71' if row['cohens_d'] > 0 else '#e74c3c'
        ax.plot([row['d_ci_lower'], row['d_ci_upper']], [i, i], color=color, linewidth=2)
        ax.scatter(row['cohens_d'], i, color=color, s=100, zorder=3, edgecolor='white', linewidth=1)
    
    # Labels
    labels = [f"{row['roi']}\n({row['comparison']}, {row['contrast'].replace('_', ' ')})" 
              for _, row in large_effects.iterrows()]
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=9)
    ax.axvline(x=0, color='gray', linestyle='--', linewidth=1)
    ax.axvline(x=0.8, color='green', linestyle=':', linewidth=1, alpha=0.5)
    ax.axvline(x=-0.8, color='green', linestyle=':', linewidth=1, alpha=0.5)
    ax.set_xlabel("Cohen's d (with 95% CI)")
    ax.set_xlim(-2, 2)


def create_correlation_panel(data, ax):
    """Panel C: PSYRATS correlation scatter."""
    participants = data['participants']
    
    # Load ROI values for speech_vs_reversed
    roi_path = RESULTS_DIR / 'roi_analysis' / 'speech_vs_reversed_roi_values.csv'
    if not roi_path.exists():
        ax.text(0.5, 0.5, 'Correlation data not available', ha='center', va='center', transform=ax.transAxes)
        return
    
    roi_df = pd.read_csv(roi_path)
    
    # ROI CSV already has 'group' column, just merge to get PSYRATS
    merged = roi_df.merge(
        participants[['participant_id', 'psyrats']],
        left_on='subject_id',
        right_on='participant_id',
        how='left'
    )
    
    # Filter AVH+ only with valid PSYRATS
    avh_plus = merged[merged['group'] == 'AVH+'].copy()
    avh_plus['psyrats_numeric'] = pd.to_numeric(avh_plus['psyrats'], errors='coerce')
    avh_plus = avh_plus.dropna(subset=['psyrats_numeric', 'R_STG_posterior'])
    
    if len(avh_plus) < 3:
        ax.text(0.5, 0.5, 'Insufficient data', ha='center', va='center', transform=ax.transAxes)
        return
    
    x = avh_plus['psyrats_numeric']
    y = avh_plus['R_STG_posterior']
    
    ax.scatter(x, y, c=COLORS['AVH+'], s=60, alpha=0.7, edgecolor='white', linewidth=1)
    
    # Add regression line
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    line_x = np.array([x.min(), x.max()])
    line_y = slope * line_x + intercept
    ax.plot(line_x, line_y, color='black', linestyle='--', linewidth=2)
    
    # Add stats annotation
    ax.text(0.05, 0.95, f'r = {r_value:.2f}\np = {p_value:.3f}\nn = {len(avh_plus)}',
            transform=ax.transAxes, fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.set_xlabel('PSYRATS Score (Hallucination Severity)')
    ax.set_ylabel('R STG Posterior Activation')


def create_stats_summary_panel(data, ax):
    """Panel D: Summary statistics table."""
    ax.axis('off')
    
    participants = data['participants']
    
    # Calculate summary stats
    summary_data = []
    for group in GROUP_ORDER:
        g_data = participants[participants['group'] == group]
        n = len(g_data)
        age_mean = g_data['age'].mean()
        age_std = g_data['age'].std()
        
        g_data['iq_numeric'] = pd.to_numeric(g_data['iq'], errors='coerce')
        iq_mean = g_data['iq_numeric'].mean()
        iq_std = g_data['iq_numeric'].std()
        
        n_male = len(g_data[g_data['sex'] == 'male'])
        n_female = len(g_data[g_data['sex'] == 'female'])
        
        summary_data.append([group, n, f'{age_mean:.1f} ± {age_std:.1f}', 
                            f'{iq_mean:.1f} ± {iq_std:.1f}', f'{n_male}/{n_female}'])
    
    # Create table
    columns = ['Group', 'N', 'Age (M ± SD)', 'IQ (M ± SD)', 'Sex (M/F)']
    
    table = ax.table(
        cellText=summary_data,
        colLabels=columns,
        loc='center',
        cellLoc='center',
        colColours=['#f0f0f0']*5
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 1.8)
    
    # Add key findings text below table
    ax.text(0.5, 0.15, 
            "Key Findings:\n"
            "• 4 large effect sizes (|d| ≥ 0.8) in AVH- vs AVH+ comparison\n"
            "• Significant correlation: R STG posterior & PSYRATS (r=0.59, p=.003)\n"
            "• Mean FD = 0.19mm (4 subjects flagged for >20% high-motion volumes)",
            ha='center', va='top', fontsize=10, transform=ax.transAxes,
            bbox=dict(boxstyle='round', facecolor='#fffacd', alpha=0.8))


def create_improved_roi_plots(data, output_dir):
    """Create improved ROI bar plots with consistent styling."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    roi_analysis_dir = RESULTS_DIR / 'roi_analysis'
    
    contrasts = [
        'words_vs_baseline', 'sentences_vs_baseline', 'reversed_vs_baseline',
        'words_vs_reversed', 'sentences_vs_reversed', 'speech_vs_reversed',
        'words_vs_sentences'
    ]
    
    for contrast in contrasts:
        roi_path = roi_analysis_dir / f'{contrast}_roi_values.csv'
        if not roi_path.exists():
            continue
        
        # ROI CSV already includes 'group' column
        roi_df = pd.read_csv(roi_path)
        
        # Get ROI columns (exclude metadata)
        roi_cols = [c for c in roi_df.columns if c not in ['subject_id', 'participant_id', 'group']]
        
        # Create bar plot
        fig, ax = plt.subplots(figsize=(14, 6))
        
        x = np.arange(len(roi_cols))
        width = 0.25
        
        for i, group in enumerate(GROUP_ORDER):
            group_data = roi_df[roi_df['group'] == group]
            means = [group_data[roi].mean() for roi in roi_cols]
            sems = [group_data[roi].std() / np.sqrt(len(group_data)) for roi in roi_cols]
            
            ax.bar(x + i*width, means, width, label=group, color=COLORS[group],
                   yerr=sems, capsize=2, alpha=0.8, edgecolor='white', linewidth=0.5)
        
        ax.set_xticks(x + width)
        ax.set_xticklabels([c.replace('_', '\n') for c in roi_cols], fontsize=9, rotation=45, ha='right')
        ax.set_ylabel('Mean Activation (β)')
        ax.set_xlabel('Region of Interest')
        ax.set_title(f'{contrast.replace("_", " ").title()}')
        ax.legend(title='Group', loc='upper right')
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        plt.savefig(output_dir / f'{contrast}_roi_barplot.png')
        plt.savefig(output_dir / f'{contrast}_roi_barplot.svg')
        plt.close()
    
    print(f"  Saved improved ROI plots to {output_dir}")


def create_improved_effect_size_heatmap(data, output_dir):
    """Create improved effect size heatmap."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if 'effect_sizes' not in data:
        print("  No effect size data available")
        return
    
    es_df = data['effect_sizes']
    
    # Create pivot table for heatmap (average across contrasts for each ROI x comparison)
    pivot_df = es_df.pivot_table(
        values='cohens_d',
        index='roi',
        columns='comparison',
        aggfunc='mean'
    )
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Create heatmap
    cmap = sns.diverging_palette(220, 20, as_cmap=True)
    
    sns.heatmap(
        pivot_df,
        cmap=cmap,
        center=0,
        vmin=-1,
        vmax=1,
        annot=True,
        fmt='.2f',
        square=True,
        linewidths=0.5,
        cbar_kws={'label': "Cohen's d", 'shrink': 0.8},
        ax=ax
    )
    
    ax.set_title('Effect Sizes Across ROIs and Group Comparisons\n(Average Across Contrasts)', fontsize=14)
    ax.set_xlabel('Group Comparison')
    ax.set_ylabel('Region of Interest')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'effect_size_heatmap.png')
    plt.savefig(output_dir / 'effect_size_heatmap.svg')
    plt.close()
    
    print(f"  Saved effect size heatmap to {output_dir}")


def create_improved_correlation_plots(data, output_dir):
    """Create improved correlation scatter plots."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    participants = data['participants']
    corr_dir = RESULTS_DIR / 'correlations'
    
    contrasts = ['speech_vs_reversed', 'sentences_vs_reversed', 'words_vs_reversed']
    
    # Focus on significant ROI: R_STG_posterior
    for contrast in contrasts:
        roi_path = RESULTS_DIR / 'roi_analysis' / f'{contrast}_roi_values.csv'
        corr_path = corr_dir / f'{contrast}_psyrats_correlations.csv'
        
        if not roi_path.exists() or not corr_path.exists():
            continue
        
        roi_df = pd.read_csv(roi_path)
        corr_df = pd.read_csv(corr_path)
        
        # ROI CSV already has 'group' column, just merge to get psyrats
        merged = roi_df.merge(
            participants[['participant_id', 'psyrats']],
            left_on='subject_id',
            right_on='participant_id',
            how='left'
        )
        
        # Filter AVH+ only
        avh_plus = merged[merged['group'] == 'AVH+'].copy()
        avh_plus['psyrats_numeric'] = pd.to_numeric(avh_plus['psyrats'], errors='coerce')
        
        # Get top 4 ROIs by correlation strength
        corr_df_sorted = corr_df.reindex(corr_df['pearson_r'].abs().sort_values(ascending=False).index)
        top_rois = corr_df_sorted.head(4)['roi'].tolist()
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()
        
        for i, roi in enumerate(top_rois):
            ax = axes[i]
            
            plot_df = avh_plus.dropna(subset=['psyrats_numeric', roi])
            if len(plot_df) < 3:
                ax.text(0.5, 0.5, 'Insufficient data', ha='center', va='center', transform=ax.transAxes)
                continue
            
            x = plot_df['psyrats_numeric']
            y = plot_df[roi]
            
            ax.scatter(x, y, c=COLORS['AVH+'], s=60, alpha=0.7, edgecolor='white', linewidth=1)
            
            # Regression line
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            line_x = np.array([x.min(), x.max()])
            line_y = slope * line_x + intercept
            ax.plot(line_x, line_y, color='black', linestyle='--', linewidth=2)
            
            # Stats annotation
            sig_marker = '*' if p_value < 0.05 else ''
            ax.text(0.05, 0.95, f'r = {r_value:.2f}{sig_marker}\np = {p_value:.3f}',
                    transform=ax.transAxes, fontsize=11, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            ax.set_xlabel('PSYRATS Score')
            ax.set_ylabel(f'{roi} Activation')
            ax.set_title(roi.replace('_', ' '))
        
        plt.suptitle(f'PSYRATS Correlations - {contrast.replace("_", " ").title()}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_dir / f'{contrast}_psyrats_scatter.png')
        plt.savefig(output_dir / f'{contrast}_psyrats_scatter.svg')
        plt.close()
    
    print(f"  Saved improved correlation plots to {output_dir}")


def main():
    """Main function to generate all visualizations."""
    print("=" * 60)
    print("Generating Comprehensive Visualizations")
    print("=" * 60)
    
    # Create output directories
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("\nLoading data...")
    data = load_data()
    print(f"  Loaded {len(data)} data sources")
    
    # Generate visualizations
    print("\n1. Creating QC plots...")
    create_qc_plots(data, FIGURES_DIR / 'qc')
    
    print("\n2. Creating demographics plots...")
    create_demographics_plots(data, FIGURES_DIR / 'demographics')
    
    print("\n3. Creating brain maps...")
    create_brain_maps(FIGURES_DIR / 'brain_maps')
    
    print("\n4. Creating summary figure...")
    create_summary_figure(data, FIGURES_DIR / 'summary')
    
    print("\n5. Creating improved ROI plots...")
    create_improved_roi_plots(data, FIGURES_DIR / 'improved')
    
    print("\n6. Creating improved effect size heatmap...")
    create_improved_effect_size_heatmap(data, FIGURES_DIR / 'improved')
    
    print("\n7. Creating improved correlation plots...")
    create_improved_correlation_plots(data, FIGURES_DIR / 'improved')
    
    print("\n" + "=" * 60)
    print("VISUALIZATION COMPLETE")
    print(f"All figures saved to: {FIGURES_DIR}")
    print("=" * 60)


if __name__ == '__main__':
    main()
