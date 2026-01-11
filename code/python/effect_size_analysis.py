"""
Effect Size Analysis

This script:
- Calculates Cohen's d for pairwise group comparisons
- Calculates eta-squared (η²) for ANOVA effects
- Computes bootstrap confidence intervals
- Generates summary tables and visualizations
"""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import json
import warnings

warnings.filterwarnings('ignore')


def cohens_d(group1, group2):
    """
    Calculate Cohen's d effect size with 95% CI using bootstrap.
    
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
    ci_lower : float
        Lower 95% CI
    ci_upper : float
        Upper 95% CI
    """
    g1 = np.array(group1)[~np.isnan(group1)]
    g2 = np.array(group2)[~np.isnan(group2)]
    
    if len(g1) < 2 or len(g2) < 2:
        return np.nan, np.nan, np.nan
    
    n1, n2 = len(g1), len(g2)
    var1, var2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return np.nan, np.nan, np.nan
    
    d = (np.mean(g1) - np.mean(g2)) / pooled_std
    
    # Bootstrap CI
    n_bootstrap = 1000
    d_bootstrap = []
    
    for _ in range(n_bootstrap):
        g1_boot = np.random.choice(g1, size=len(g1), replace=True)
        g2_boot = np.random.choice(g2, size=len(g2), replace=True)
        
        var1_boot = np.var(g1_boot, ddof=1)
        var2_boot = np.var(g2_boot, ddof=1)
        pooled_std_boot = np.sqrt(((n1 - 1) * var1_boot + (n2 - 1) * var2_boot) / (n1 + n2 - 2))
        
        if pooled_std_boot > 0:
            d_boot = (np.mean(g1_boot) - np.mean(g2_boot)) / pooled_std_boot
            d_bootstrap.append(d_boot)
    
    if len(d_bootstrap) > 0:
        ci_lower = np.percentile(d_bootstrap, 2.5)
        ci_upper = np.percentile(d_bootstrap, 97.5)
    else:
        ci_lower, ci_upper = np.nan, np.nan
    
    return d, ci_lower, ci_upper


def hedges_g(group1, group2):
    """
    Calculate Hedges' g (corrected effect size for small samples).
    
    Parameters
    ----------
    group1 : array-like
        First group data
    group2 : array-like
        Second group data
    
    Returns
    -------
    g : float
        Hedges' g
    """
    d, _, _ = cohens_d(group1, group2)
    
    if np.isnan(d):
        return np.nan
    
    g1 = np.array(group1)[~np.isnan(group1)]
    g2 = np.array(group2)[~np.isnan(group2)]
    
    n1, n2 = len(g1), len(g2)
    
    # Correction factor
    correction = 1 - (3 / (4 * (n1 + n2) - 9))
    
    return d * correction


def eta_squared(ss_between, ss_total):
    """
    Calculate eta-squared from sum of squares.
    
    Parameters
    ----------
    ss_between : float
        Between-groups sum of squares
    ss_total : float
        Total sum of squares
    
    Returns
    -------
    eta_sq : float
        Eta-squared
    """
    if ss_total == 0:
        return np.nan
    return ss_between / ss_total


def partial_eta_squared(ss_effect, ss_error):
    """
    Calculate partial eta-squared.
    
    Parameters
    ----------
    ss_effect : float
        Effect sum of squares
    ss_error : float
        Error sum of squares
    
    Returns
    -------
    partial_eta_sq : float
        Partial eta-squared
    """
    if ss_effect + ss_error == 0:
        return np.nan
    return ss_effect / (ss_effect + ss_error)


def omega_squared(ss_between, ss_total, df_between, ms_within):
    """
    Calculate omega-squared (less biased than eta-squared).
    
    Parameters
    ----------
    ss_between : float
        Between-groups sum of squares
    ss_total : float
        Total sum of squares
    df_between : int
        Between-groups degrees of freedom
    ms_within : float
        Within-groups mean square
    
    Returns
    -------
    omega_sq : float
        Omega-squared
    """
    numerator = ss_between - df_between * ms_within
    denominator = ss_total + ms_within
    
    if denominator == 0:
        return np.nan
    
    return numerator / denominator


def interpret_cohens_d(d):
    """
    Interpret Cohen's d using conventional thresholds.
    
    Parameters
    ----------
    d : float
        Cohen's d value
    
    Returns
    -------
    interpretation : str
        Size interpretation
    """
    if np.isnan(d):
        return "N/A"
    
    abs_d = abs(d)
    
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"


def interpret_eta_squared(eta_sq):
    """
    Interpret eta-squared using conventional thresholds.
    
    Parameters
    ----------
    eta_sq : float
        Eta-squared value
    
    Returns
    -------
    interpretation : str
        Size interpretation
    """
    if np.isnan(eta_sq):
        return "N/A"
    
    if eta_sq < 0.01:
        return "negligible"
    elif eta_sq < 0.06:
        return "small"
    elif eta_sq < 0.14:
        return "medium"
    else:
        return "large"


def calculate_effect_sizes_from_roi(roi_df, output_dir, contrast_name):
    """
    Calculate effect sizes for group comparisons from ROI data.
    
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
        Effect size results
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    roi_cols = [col for col in roi_df.columns if col not in ['subject_id', 'group']]
    groups = sorted(roi_df['group'].unique())
    
    results = {
        'contrast': contrast_name,
        'pairwise_effects': [],
        'anova_effects': []
    }
    
    # Pairwise effect sizes
    comparisons = [
        ('HC', 'AVH-'),
        ('HC', 'AVH+'),
        ('AVH-', 'AVH+')
    ]
    
    for roi in roi_cols:
        for g1, g2 in comparisons:
            data1 = roi_df[roi_df['group'] == g1][roi].values
            data2 = roi_df[roi_df['group'] == g2][roi].values
            
            d, ci_lower, ci_upper = cohens_d(data1, data2)
            g = hedges_g(data1, data2)
            
            results['pairwise_effects'].append({
                'roi': roi,
                'comparison': f'{g1}_vs_{g2}',
                'cohens_d': d,
                'd_ci_lower': ci_lower,
                'd_ci_upper': ci_upper,
                'hedges_g': g,
                'interpretation': interpret_cohens_d(d)
            })
        
        # ANOVA effect size (eta-squared)
        group_data = [roi_df[roi_df['group'] == g][roi].dropna().values for g in groups]
        
        # Calculate sum of squares
        all_data = np.concatenate(group_data)
        grand_mean = np.mean(all_data)
        
        ss_total = np.sum((all_data - grand_mean)**2)
        ss_between = sum(len(g) * (np.mean(g) - grand_mean)**2 for g in group_data if len(g) > 0)
        ss_within = ss_total - ss_between
        
        df_between = len(groups) - 1
        df_within = len(all_data) - len(groups)
        
        if df_within > 0:
            ms_within = ss_within / df_within
        else:
            ms_within = np.nan
        
        eta_sq = eta_squared(ss_between, ss_total)
        omega_sq = omega_squared(ss_between, ss_total, df_between, ms_within)
        
        results['anova_effects'].append({
            'roi': roi,
            'eta_squared': eta_sq,
            'omega_squared': omega_sq,
            'interpretation': interpret_eta_squared(eta_sq)
        })
    
    # Save results
    pairwise_df = pd.DataFrame(results['pairwise_effects'])
    pairwise_df.to_csv(output_dir / f'{contrast_name}_pairwise_effect_sizes.csv', index=False)
    
    anova_df = pd.DataFrame(results['anova_effects'])
    anova_df.to_csv(output_dir / f'{contrast_name}_anova_effect_sizes.csv', index=False)
    
    return results


def create_effect_size_forest_plot(effect_df, output_dir, contrast_name, comparison):
    """
    Create forest plot for effect sizes.
    
    Parameters
    ----------
    effect_df : pd.DataFrame
        DataFrame with effect sizes
    output_dir : Path
        Output directory
    contrast_name : str
        Name of the contrast
    comparison : str
        Comparison name
    """
    output_dir = Path(output_dir) / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Filter to specific comparison
    comp_df = effect_df[effect_df['comparison'] == comparison].copy()
    
    if len(comp_df) == 0:
        return
    
    # Sort by effect size
    comp_df = comp_df.sort_values('cohens_d')
    
    fig, ax = plt.subplots(figsize=(10, max(6, len(comp_df) * 0.4)))
    
    y_pos = np.arange(len(comp_df))
    
    # Plot effect sizes with error bars
    ax.errorbar(
        comp_df['cohens_d'],
        y_pos,
        xerr=[comp_df['cohens_d'] - comp_df['d_ci_lower'],
              comp_df['d_ci_upper'] - comp_df['cohens_d']],
        fmt='o',
        color='steelblue',
        capsize=3,
        markersize=8
    )
    
    # Add reference lines
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    ax.axvline(x=-0.2, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
    ax.axvline(x=0.2, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
    ax.axvline(x=-0.5, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
    ax.axvline(x=0.5, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
    ax.axvline(x=-0.8, color='gray', linestyle='-.', linewidth=0.5, alpha=0.5)
    ax.axvline(x=0.8, color='gray', linestyle='-.', linewidth=0.5, alpha=0.5)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(comp_df['roi'].str.replace('_', ' '))
    ax.set_xlabel("Cohen's d")
    ax.set_title(f'{contrast_name.replace("_", " ").title()}\n{comparison.replace("_", " ")}')
    
    plt.tight_layout()
    plt.savefig(output_dir / f'{contrast_name}_{comparison}_forest_plot.png', 
                dpi=150, bbox_inches='tight')
    plt.close()


def create_effect_size_heatmap(all_results, output_dir):
    """
    Create heatmap showing effect sizes across contrasts and ROIs.
    
    Parameters
    ----------
    all_results : dict
        Results for all contrasts
    output_dir : Path
        Output directory
    """
    output_dir = Path(output_dir) / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect all effect sizes for HC vs AVH+ (most clinically relevant)
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
    
    # Pivot for heatmap
    pivot_df = effect_df.pivot(index='roi', columns='contrast', values='cohens_d')
    
    # Select key ROIs
    key_rois = ['L_STG_posterior', 'L_IFG_triangularis', 'L_MTG', 'R_STG_posterior',
                'L_STG_anterior', 'L_STS', 'L_Heschl', 'R_Heschl']
    key_rois = [r for r in key_rois if r in pivot_df.index]
    
    if len(key_rois) > 0:
        pivot_df = pivot_df.loc[key_rois]
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(14, 8))
    
    sns.heatmap(
        pivot_df,
        annot=True,
        fmt='.2f',
        cmap='RdBu_r',
        center=0,
        linewidths=0.5,
        cbar_kws={'label': "Cohen's d"},
        ax=ax
    )
    
    ax.set_xlabel('Contrast')
    ax.set_ylabel('ROI')
    ax.set_title("Effect Sizes (Cohen's d): HC vs AVH+\nAcross Contrasts and ROIs")
    
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_dir / 'effect_size_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()


def run_effect_size_analysis(roi_dir, output_dir):
    """
    Run effect size analysis for all contrasts.
    
    Parameters
    ----------
    roi_dir : Path
        Directory with ROI analysis results
    output_dir : Path
        Output directory
    
    Returns
    -------
    all_results : dict
        Results for all contrasts
    """
    roi_dir = Path(roi_dir)
    output_dir = Path(output_dir)
    
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
    print("EFFECT SIZE ANALYSIS")
    print("="*70)
    
    all_results = {}
    
    for contrast_name in contrasts:
        print(f"\nProcessing: {contrast_name}")
        
        try:
            # Load ROI data
            roi_file = roi_dir / f'{contrast_name}_roi_values.csv'
            
            if not roi_file.exists():
                print(f"  ROI file not found: {roi_file}")
                continue
            
            roi_df = pd.read_csv(roi_file)
            
            # Calculate effect sizes
            results = calculate_effect_sizes_from_roi(
                roi_df=roi_df,
                output_dir=output_dir,
                contrast_name=contrast_name
            )
            
            all_results[contrast_name] = results
            
            # Create forest plots for each comparison
            effect_df = pd.DataFrame(results['pairwise_effects'])
            
            for comparison in ['HC_vs_AVH-', 'HC_vs_AVH+', 'AVH-_vs_AVH+']:
                create_effect_size_forest_plot(
                    effect_df=effect_df,
                    output_dir=output_dir,
                    contrast_name=contrast_name,
                    comparison=comparison
                )
            
            # Print summary of large effects
            large_effects = effect_df[effect_df['interpretation'] == 'large']
            if len(large_effects) > 0:
                print(f"  Large effects found:")
                for _, row in large_effects.iterrows():
                    print(f"    - {row['roi']} ({row['comparison']}): d={row['cohens_d']:.2f}")
            
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[contrast_name] = {'error': str(e)}
    
    # Create summary heatmap
    if len(all_results) > 0:
        create_effect_size_heatmap(all_results, output_dir)
    
    # Create summary table
    summary_data = []
    for contrast_name, results in all_results.items():
        if 'error' in results:
            continue
        
        for effect in results['pairwise_effects']:
            summary_data.append({
                'contrast': contrast_name,
                'roi': effect['roi'],
                'comparison': effect['comparison'],
                'cohens_d': effect['cohens_d'],
                'd_ci_lower': effect['d_ci_lower'],
                'd_ci_upper': effect['d_ci_upper'],
                'interpretation': effect['interpretation']
            })
    
    if len(summary_data) > 0:
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(output_dir / 'effect_sizes_summary.csv', index=False)
    
    print(f"\n{'='*70}")
    print("EFFECT SIZE ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nResults saved to: {output_dir}")
    print("="*70 + "\n")
    
    return all_results


def main():
    """Main function."""
    dataset_root = Path(__file__).parent.parent.parent
    roi_dir = dataset_root / 'results' / 'roi_analysis'
    output_dir = dataset_root / 'results' / 'effect_sizes'
    
    if not roi_dir.exists():
        print(f"\nError: ROI analysis results not found: {roi_dir}")
        print("Please run ROI analysis first.")
        return
    
    results = run_effect_size_analysis(
        roi_dir=roi_dir,
        output_dir=output_dir
    )
    
    return results


if __name__ == "__main__":
    main()
