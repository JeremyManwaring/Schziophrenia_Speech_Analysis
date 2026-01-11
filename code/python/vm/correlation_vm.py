"""
Correlation Analysis (VM Version)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import pearsonr, spearmanr
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


def partial_correlation(x, y, covariates):
    """Calculate partial correlation."""
    x = np.array(x)
    y = np.array(y)
    if isinstance(covariates, pd.DataFrame):
        covariates = covariates.values
    
    valid_mask = ~(np.isnan(x) | np.isnan(y))
    if len(covariates.shape) == 1:
        valid_mask &= ~np.isnan(covariates)
    else:
        valid_mask &= ~np.any(np.isnan(covariates), axis=1)
    
    x, y, covariates = x[valid_mask], y[valid_mask], covariates[valid_mask]
    
    if len(x) < 5:
        return np.nan, np.nan
    
    if len(covariates.shape) == 1:
        covariates = covariates.reshape(-1, 1)
    
    C = np.column_stack([np.ones(len(x)), covariates])
    
    beta_x = np.linalg.lstsq(C, x, rcond=None)[0]
    res_x = x - C @ beta_x
    
    beta_y = np.linalg.lstsq(C, y, rcond=None)[0]
    res_y = y - C @ beta_y
    
    r, p = pearsonr(res_x, res_y)
    return r, p


def correlate_psyrats_with_activation(roi_df, participants_df, output_dir, contrast_name):
    """Correlate PSYRATS with ROI activation in AVH+ group."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    merged = roi_df.merge(
        participants_df[['participant_id', 'age', 'iq', 'psyrats']],
        left_on='subject_id', right_on='participant_id', how='left'
    )
    
    avh_plus = merged[merged['group'] == 'AVH+'].copy()
    
    if len(avh_plus) == 0:
        return {'error': 'No AVH+ subjects'}
    
    print(f"  AVH+ subjects: {len(avh_plus)}, PSYRATS: {avh_plus['psyrats'].min():.0f}-{avh_plus['psyrats'].max():.0f}")
    
    roi_cols = [col for col in roi_df.columns if col not in ['subject_id', 'group']]
    
    results = {
        'contrast': contrast_name, 'n_subjects': len(avh_plus),
        'correlations': [], 'partial_correlations': []
    }
    
    for roi in roi_cols:
        roi_data = avh_plus[roi].values
        psyrats = avh_plus['psyrats'].values
        valid = ~(np.isnan(roi_data) | np.isnan(psyrats))
        
        if valid.sum() >= 5:
            r, p = pearsonr(roi_data[valid], psyrats[valid])
            results['correlations'].append({'roi': roi, 'pearson_r': r, 'pearson_p': p, 'n': int(valid.sum())})
            
            if p < 0.05:
                print(f"    * {roi}: r={r:.3f}, p={p:.4f}")
        
        # Partial correlation
        covariates = avh_plus[['age', 'iq']].values
        r_partial, p_partial = partial_correlation(roi_data, psyrats, covariates)
        results['partial_correlations'].append({
            'roi': roi, 'partial_r': r_partial, 'partial_p': p_partial
        })
    
    pd.DataFrame(results['correlations']).to_csv(output_dir / f'{contrast_name}_psyrats_correlations.csv', index=False)
    pd.DataFrame(results['partial_correlations']).to_csv(output_dir / f'{contrast_name}_psyrats_partial.csv', index=False)
    
    return results


def create_correlation_plot(roi_df, participants_df, output_dir, contrast_name):
    """Create scatter plots for top correlations."""
    output_dir = Path(output_dir) / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    merged = roi_df.merge(
        participants_df[['participant_id', 'psyrats']],
        left_on='subject_id', right_on='participant_id', how='left'
    )
    avh_plus = merged[merged['group'] == 'AVH+'].copy()
    
    if len(avh_plus) < 5:
        return
    
    roi_cols = [col for col in roi_df.columns if col not in ['subject_id', 'group']]
    
    # Find top correlations
    correlations = []
    for roi in roi_cols:
        roi_data = avh_plus[roi].values
        psyrats = avh_plus['psyrats'].values
        valid = ~(np.isnan(roi_data) | np.isnan(psyrats))
        if valid.sum() >= 5:
            r, p = pearsonr(roi_data[valid], psyrats[valid])
            correlations.append({'roi': roi, 'r': r, 'abs_r': abs(r)})
    
    if len(correlations) == 0:
        return
    
    correlations = sorted(correlations, key=lambda x: -x['abs_r'])[:4]
    
    fig, axes = plt.subplots(1, len(correlations), figsize=(5*len(correlations), 5))
    if len(correlations) == 1:
        axes = [axes]
    
    for i, c in enumerate(correlations):
        roi = c['roi']
        ax = axes[i]
        
        roi_data = avh_plus[roi].values
        psyrats = avh_plus['psyrats'].values
        valid = ~(np.isnan(roi_data) | np.isnan(psyrats))
        
        ax.scatter(psyrats[valid], roi_data[valid], alpha=0.7, s=50, c='#e74c3c')
        z = np.polyfit(psyrats[valid], roi_data[valid], 1)
        p = np.poly1d(z)
        x_line = np.linspace(psyrats[valid].min(), psyrats[valid].max(), 100)
        ax.plot(x_line, p(x_line), 'k--', alpha=0.7)
        
        r, pval = pearsonr(roi_data[valid], psyrats[valid])
        ax.set_xlabel('PSYRATS Score')
        ax.set_ylabel('Parameter Estimate')
        ax.set_title(f'{roi}\nr={r:.3f}, p={pval:.4f}')
    
    plt.suptitle(f'{contrast_name}: PSYRATS Correlations', fontsize=12)
    plt.tight_layout()
    plt.savefig(output_dir / f'{contrast_name}_psyrats_scatter.png', dpi=150, bbox_inches='tight')
    plt.close()


def run_correlation_analysis(roi_dir, participants_path, output_dir):
    """Run correlation analysis for all contrasts."""
    roi_dir = Path(roi_dir)
    output_dir = Path(output_dir)
    
    participants_df = pd.read_csv(participants_path, sep='\t')
    for col in ['age', 'iq', 'psyrats']:
        if col in participants_df.columns:
            participants_df[col] = pd.to_numeric(participants_df[col], errors='coerce')
    
    avh_plus = participants_df[participants_df['group'] == 'AVH+']
    print(f"\nAVH+ subjects: {len(avh_plus)}, PSYRATS: mean={avh_plus['psyrats'].mean():.1f}")
    
    print(f"\n{'='*70}")
    print("PSYRATS CORRELATION ANALYSIS")
    print("="*70)
    
    all_results = {}
    
    for contrast_name in CONTRASTS:
        print(f"\nProcessing: {contrast_name}")
        
        try:
            roi_file = roi_dir / f'{contrast_name}_roi_values.csv'
            if not roi_file.exists():
                continue
            
            roi_df = pd.read_csv(roi_file)
            results = correlate_psyrats_with_activation(roi_df, participants_df, output_dir, contrast_name)
            all_results[contrast_name] = results
            
            create_correlation_plot(roi_df, participants_df, output_dir, contrast_name)
        except Exception as e:
            print(f"  ERROR: {e}")
    
    # Save summary
    def clean_json(obj):
        if isinstance(obj, dict):
            return {k: clean_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_json(i) for i in obj]
        elif isinstance(obj, float) and np.isnan(obj):
            return None
        return obj
    
    with open(output_dir / 'correlation_summary.json', 'w') as f:
        json.dump(clean_json(all_results), f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_dir}")
    print("="*70 + "\n")
    
    return all_results
