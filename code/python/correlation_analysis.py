"""
Correlation Analysis

This script:
- Correlates PSYRATS scores with brain activation in AVH+ group
- Performs partial correlations controlling for age/IQ
- Generates correlation matrices and visualizations
"""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import matplotlib.pyplot as plt
import seaborn as sns
import json
import warnings

warnings.filterwarnings('ignore')


def partial_correlation(x, y, covariates):
    """
    Calculate partial correlation between x and y, controlling for covariates.
    
    Parameters
    ----------
    x : array-like
        First variable
    y : array-like
        Second variable  
    covariates : pd.DataFrame or array-like
        Variables to control for
    
    Returns
    -------
    r : float
        Partial correlation coefficient
    p : float
        p-value
    """
    x = np.array(x)
    y = np.array(y)
    
    if isinstance(covariates, pd.DataFrame):
        covariates = covariates.values
    
    # Remove NaN
    valid_mask = ~(np.isnan(x) | np.isnan(y))
    if len(covariates.shape) == 1:
        valid_mask &= ~np.isnan(covariates)
    else:
        valid_mask &= ~np.any(np.isnan(covariates), axis=1)
    
    x = x[valid_mask]
    y = y[valid_mask]
    covariates = covariates[valid_mask]
    
    if len(x) < 5:
        return np.nan, np.nan
    
    # Residualize x and y on covariates
    if len(covariates.shape) == 1:
        covariates = covariates.reshape(-1, 1)
    
    # Add intercept
    C = np.column_stack([np.ones(len(x)), covariates])
    
    # Regress out covariates from x
    beta_x = np.linalg.lstsq(C, x, rcond=None)[0]
    res_x = x - C @ beta_x
    
    # Regress out covariates from y
    beta_y = np.linalg.lstsq(C, y, rcond=None)[0]
    res_y = y - C @ beta_y
    
    # Correlate residuals
    r, p = pearsonr(res_x, res_y)
    
    return r, p


def load_roi_data(roi_dir, contrast_name):
    """
    Load ROI activation values.
    
    Parameters
    ----------
    roi_dir : Path
        Directory with ROI analysis results
    contrast_name : str
        Name of the contrast
    
    Returns
    -------
    roi_df : pd.DataFrame
        DataFrame with ROI values
    """
    roi_file = roi_dir / f'{contrast_name}_roi_values.csv'
    
    if not roi_file.exists():
        raise FileNotFoundError(f"ROI file not found: {roi_file}")
    
    return pd.read_csv(roi_file)


def load_participants(participants_path):
    """
    Load participants data.
    
    Parameters
    ----------
    participants_path : Path
        Path to participants.tsv
    
    Returns
    -------
    df : pd.DataFrame
        Participants DataFrame
    """
    df = pd.read_csv(participants_path, sep='\t')
    
    # Clean numeric columns
    for col in ['age', 'iq', 'psyrats']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def correlate_psyrats_with_activation(roi_df, participants_df, output_dir, contrast_name):
    """
    Correlate PSYRATS scores with ROI activation in AVH+ group.
    
    Parameters
    ----------
    roi_df : pd.DataFrame
        DataFrame with ROI values
    participants_df : pd.DataFrame
        Participants DataFrame
    output_dir : Path
        Output directory
    contrast_name : str
        Name of the contrast
    
    Returns
    -------
    results : dict
        Correlation results
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Merge ROI data with participants
    merged = roi_df.merge(
        participants_df[['participant_id', 'age', 'iq', 'psyrats']],
        left_on='subject_id',
        right_on='participant_id',
        how='left'
    )
    
    # Filter to AVH+ group only
    avh_plus = merged[merged['group'] == 'AVH+'].copy()
    
    if len(avh_plus) == 0:
        return {'error': 'No AVH+ subjects found'}
    
    print(f"  AVH+ subjects: {len(avh_plus)}")
    print(f"  PSYRATS range: {avh_plus['psyrats'].min():.0f} - {avh_plus['psyrats'].max():.0f}")
    
    # Get ROI columns
    roi_cols = [col for col in roi_df.columns if col not in ['subject_id', 'group']]
    
    results = {
        'contrast': contrast_name,
        'n_subjects': len(avh_plus),
        'psyrats_range': [float(avh_plus['psyrats'].min()), float(avh_plus['psyrats'].max())],
        'correlations': [],
        'partial_correlations': []
    }
    
    # Simple correlations
    print("\n  Simple correlations (PSYRATS vs ROI activation):")
    
    for roi in roi_cols:
        roi_data = avh_plus[roi].values
        psyrats = avh_plus['psyrats'].values
        
        # Remove NaN
        valid = ~(np.isnan(roi_data) | np.isnan(psyrats))
        
        if valid.sum() >= 5:
            r, p = pearsonr(roi_data[valid], psyrats[valid])
            rho, p_spearman = spearmanr(roi_data[valid], psyrats[valid])
            
            results['correlations'].append({
                'roi': roi,
                'pearson_r': r,
                'pearson_p': p,
                'spearman_rho': rho,
                'spearman_p': p_spearman,
                'n': int(valid.sum())
            })
            
            if p < 0.05:
                print(f"    * {roi}: r={r:.3f}, p={p:.4f}")
        else:
            results['correlations'].append({
                'roi': roi,
                'pearson_r': np.nan,
                'pearson_p': np.nan,
                'n': int(valid.sum())
            })
    
    # Partial correlations (controlling for age and IQ)
    print("\n  Partial correlations (controlling for age, IQ):")
    
    for roi in roi_cols:
        roi_data = avh_plus[roi].values
        psyrats = avh_plus['psyrats'].values
        covariates = avh_plus[['age', 'iq']].values
        
        r_partial, p_partial = partial_correlation(roi_data, psyrats, covariates)
        
        results['partial_correlations'].append({
            'roi': roi,
            'partial_r': r_partial,
            'partial_p': p_partial,
            'controlling_for': ['age', 'iq']
        })
        
        if not np.isnan(p_partial) and p_partial < 0.05:
            print(f"    * {roi}: r_partial={r_partial:.3f}, p={p_partial:.4f}")
    
    # Save results
    corr_df = pd.DataFrame(results['correlations'])
    corr_df.to_csv(output_dir / f'{contrast_name}_psyrats_correlations.csv', index=False)
    
    partial_df = pd.DataFrame(results['partial_correlations'])
    partial_df.to_csv(output_dir / f'{contrast_name}_psyrats_partial_correlations.csv', index=False)
    
    return results


def create_correlation_plot(roi_df, participants_df, output_dir, contrast_name, top_n=4):
    """
    Create scatter plots for top correlations.
    
    Parameters
    ----------
    roi_df : pd.DataFrame
        DataFrame with ROI values
    participants_df : pd.DataFrame
        Participants DataFrame
    output_dir : Path
        Output directory
    contrast_name : str
        Name of the contrast
    top_n : int
        Number of top correlations to plot
    """
    output_dir = Path(output_dir)
    (output_dir / 'figures').mkdir(parents=True, exist_ok=True)
    
    # Merge data
    merged = roi_df.merge(
        participants_df[['participant_id', 'psyrats']],
        left_on='subject_id',
        right_on='participant_id',
        how='left'
    )
    
    avh_plus = merged[merged['group'] == 'AVH+'].copy()
    
    if len(avh_plus) < 5:
        return
    
    # Get ROI columns
    roi_cols = [col for col in roi_df.columns if col not in ['subject_id', 'group']]
    
    # Calculate correlations
    correlations = []
    for roi in roi_cols:
        roi_data = avh_plus[roi].values
        psyrats = avh_plus['psyrats'].values
        
        valid = ~(np.isnan(roi_data) | np.isnan(psyrats))
        if valid.sum() >= 5:
            r, p = pearsonr(roi_data[valid], psyrats[valid])
            correlations.append({'roi': roi, 'r': r, 'p': p, 'abs_r': abs(r)})
    
    if len(correlations) == 0:
        return
    
    # Sort by absolute correlation
    correlations = sorted(correlations, key=lambda x: -x['abs_r'])
    top_rois = [c['roi'] for c in correlations[:top_n]]
    
    # Create plots
    fig, axes = plt.subplots(1, min(top_n, len(top_rois)), figsize=(5*min(top_n, len(top_rois)), 5))
    
    if len(top_rois) == 1:
        axes = [axes]
    
    for i, roi in enumerate(top_rois):
        ax = axes[i]
        
        roi_data = avh_plus[roi].values
        psyrats = avh_plus['psyrats'].values
        
        valid = ~(np.isnan(roi_data) | np.isnan(psyrats))
        
        ax.scatter(psyrats[valid], roi_data[valid], alpha=0.7, s=50, c='#e74c3c')
        
        # Add regression line
        z = np.polyfit(psyrats[valid], roi_data[valid], 1)
        p = np.poly1d(z)
        x_line = np.linspace(psyrats[valid].min(), psyrats[valid].max(), 100)
        ax.plot(x_line, p(x_line), 'k--', alpha=0.7)
        
        # Get correlation
        r, pval = pearsonr(roi_data[valid], psyrats[valid])
        
        ax.set_xlabel('PSYRATS Score')
        ax.set_ylabel('Parameter Estimate')
        ax.set_title(f'{roi.replace("_", " ")}\nr={r:.3f}, p={pval:.4f}')
    
    plt.suptitle(f'{contrast_name.replace("_", " ").title()}\nAVH+ Group: PSYRATS Correlations', 
                 fontsize=12, y=1.05)
    plt.tight_layout()
    plt.savefig(output_dir / 'figures' / f'{contrast_name}_psyrats_scatterplots.png', 
                dpi=150, bbox_inches='tight')
    plt.close()


def create_correlation_heatmap(roi_df, participants_df, output_dir, contrast_name):
    """
    Create correlation heatmap of ROIs and behavioral measures.
    
    Parameters
    ----------
    roi_df : pd.DataFrame
        DataFrame with ROI values
    participants_df : pd.DataFrame
        Participants DataFrame
    output_dir : Path
        Output directory
    contrast_name : str
        Name of the contrast
    """
    output_dir = Path(output_dir)
    (output_dir / 'figures').mkdir(parents=True, exist_ok=True)
    
    # Merge data
    merged = roi_df.merge(
        participants_df[['participant_id', 'age', 'iq', 'psyrats', 'group']],
        left_on='subject_id',
        right_on='participant_id',
        how='left'
    )
    
    # Get key ROIs
    key_rois = ['L_STG_posterior', 'L_IFG_triangularis', 'L_MTG', 'R_STG_posterior', 
                'L_STG_anterior', 'L_STS']
    roi_cols = [col for col in key_rois if col in merged.columns]
    
    if len(roi_cols) == 0:
        roi_cols = [col for col in roi_df.columns if col not in ['subject_id', 'group']][:6]
    
    # Create correlation matrix for AVH+ group
    avh_plus = merged[merged['group'] == 'AVH+'].copy()
    
    if len(avh_plus) < 5:
        return
    
    cols_to_correlate = roi_cols + ['age', 'iq', 'psyrats']
    cols_to_correlate = [c for c in cols_to_correlate if c in avh_plus.columns]
    
    corr_matrix = avh_plus[cols_to_correlate].corr()
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 10))
    
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    
    sns.heatmap(
        corr_matrix,
        mask=mask,
        annot=True,
        fmt='.2f',
        cmap='RdBu_r',
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={'shrink': 0.8},
        ax=ax
    )
    
    ax.set_title(f'{contrast_name.replace("_", " ").title()}\nAVH+ Group Correlation Matrix', fontsize=14)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'figures' / f'{contrast_name}_correlation_heatmap.png', 
                dpi=150, bbox_inches='tight')
    plt.close()


def run_correlation_analysis(roi_dir, participants_path, output_dir):
    """
    Run correlation analysis for all contrasts.
    
    Parameters
    ----------
    roi_dir : Path
        Directory with ROI analysis results
    participants_path : Path
        Path to participants.tsv
    output_dir : Path
        Output directory
    
    Returns
    -------
    all_results : dict
        Results for all contrasts
    """
    roi_dir = Path(roi_dir)
    output_dir = Path(output_dir)
    
    # Load participants
    participants_df = load_participants(participants_path)
    
    # Get AVH+ stats
    avh_plus = participants_df[participants_df['group'] == 'AVH+']
    print(f"\nAVH+ subjects: {len(avh_plus)}")
    print(f"PSYRATS: mean={avh_plus['psyrats'].mean():.1f}, SD={avh_plus['psyrats'].std():.1f}")
    
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
    print("PSYRATS CORRELATION ANALYSIS (AVH+ Group)")
    print("="*70)
    
    all_results = {}
    
    for contrast_name in contrasts:
        print(f"\n{'='*70}")
        print(f"Processing: {contrast_name}")
        print("="*70)
        
        try:
            # Load ROI data
            roi_df = load_roi_data(roi_dir, contrast_name)
            
            # Run correlation analysis
            results = correlate_psyrats_with_activation(
                roi_df=roi_df,
                participants_df=participants_df,
                output_dir=output_dir,
                contrast_name=contrast_name
            )
            
            all_results[contrast_name] = results
            
            # Create visualizations
            create_correlation_plot(
                roi_df=roi_df,
                participants_df=participants_df,
                output_dir=output_dir,
                contrast_name=contrast_name
            )
            
            create_correlation_heatmap(
                roi_df=roi_df,
                participants_df=participants_df,
                output_dir=output_dir,
                contrast_name=contrast_name
            )
            
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[contrast_name] = {'error': str(e)}
    
    # Save summary
    with open(output_dir / 'correlation_summary.json', 'w') as f:
        # Convert NaN to None for JSON
        def clean_for_json(obj):
            if isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(i) for i in obj]
            elif isinstance(obj, float) and np.isnan(obj):
                return None
            else:
                return obj
        
        json.dump(clean_for_json(all_results), f, indent=2)
    
    print(f"\n{'='*70}")
    print("CORRELATION ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nResults saved to: {output_dir}")
    print("="*70 + "\n")
    
    return all_results


def main():
    """Main function."""
    dataset_root = Path(__file__).parent.parent.parent
    roi_dir = dataset_root / 'results' / 'roi_analysis'
    participants_path = dataset_root / 'participants.tsv'
    output_dir = dataset_root / 'results' / 'correlations'
    
    if not roi_dir.exists():
        print(f"\nError: ROI analysis results not found: {roi_dir}")
        print("Please run ROI analysis first.")
        return
    
    results = run_correlation_analysis(
        roi_dir=roi_dir,
        participants_path=participants_path,
        output_dir=output_dir
    )
    
    return results


if __name__ == "__main__":
    main()
