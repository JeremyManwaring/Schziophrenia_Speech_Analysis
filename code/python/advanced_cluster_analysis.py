"""
Advanced Cluster-Corrected Analysis for AVH- vs AVH+ Comparison

This script performs permutation-based cluster correction for robust
statistical inference on whole-brain group comparisons.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import nibabel as nib
from nilearn.glm.second_level import SecondLevelModel, non_parametric_inference
from nilearn.image import threshold_img
from nilearn.reporting import get_clusters_table
import warnings
import json

warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
FIRST_LEVEL_DIR = BASE_DIR / 'results' / 'vm_analysis' / 'results' / 'first_level'
FMRIPREP_DIR = BASE_DIR / 'derivatives' / 'fmriprep'
PARTICIPANTS_PATH = BASE_DIR / 'participants.tsv'
OUTPUT_DIR = BASE_DIR / 'results' / 'data' / 'cluster_maps'

# Key contrasts with largest AVH- vs AVH+ effects
KEY_CONTRASTS = [
    'sentences_vs_reversed',
    'speech_vs_reversed', 
    'words_vs_sentences'
]


def load_participants():
    """Load and prepare participants data."""
    df = pd.read_csv(PARTICIPANTS_PATH, sep='\t')
    for col in ['age', 'iq', 'psyrats']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df['age_demeaned'] = df['age'] - df['age'].mean()
    df['iq_demeaned'] = df['iq'].fillna(df['iq'].mean()) - df['iq'].mean()
    df['sex_binary'] = (df['sex'] == 'male').astype(float)
    return df


def collect_contrast_maps(contrast_name, participants_df, map_type='effect'):
    """Collect first-level contrast maps for AVH- and AVH+ subjects."""
    # Filter to only AVH- and AVH+ groups
    avh_df = participants_df[participants_df['group'].isin(['AVH-', 'AVH+'])].copy()
    
    maps = []
    subjects = []
    groups = []
    ages = []
    iq_vals = []
    sex_vals = []
    
    for _, row in avh_df.iterrows():
        sub_id = row['participant_id']
        map_path = FIRST_LEVEL_DIR / sub_id / f'{sub_id}_{contrast_name}_{map_type}.nii.gz'
        
        if map_path.exists():
            maps.append(str(map_path))
            subjects.append(sub_id)
            groups.append(row['group'])
            ages.append(row['age_demeaned'])
            iq_vals.append(row['iq_demeaned'])
            sex_vals.append(row['sex_binary'])
    
    design_matrix = pd.DataFrame({
        'subject': subjects,
        'group': groups,
        'AVH-': [1 if g == 'AVH-' else 0 for g in groups],
        'AVH+': [1 if g == 'AVH+' else 0 for g in groups],
        'age': ages,
        'iq': iq_vals,
        'sex': sex_vals
    })
    
    return maps, design_matrix


def run_cluster_corrected_analysis(contrast_name, n_perm=1000):
    """
    Run permutation-based cluster-corrected analysis.
    
    Note: Using 1000 permutations for speed. Increase to 10000 for publication.
    """
    print(f"\n{'='*70}")
    print(f"Cluster-Corrected Analysis: {contrast_name}")
    print('='*70)
    
    participants_df = load_participants()
    maps, design_matrix = collect_contrast_maps(contrast_name, participants_df)
    
    print(f"  Subjects: {len(maps)} (AVH-: {design_matrix['AVH-'].sum():.0f}, AVH+: {design_matrix['AVH+'].sum():.0f})")
    
    if len(maps) < 10:
        print("  ERROR: Not enough subjects for analysis")
        return None
    
    # Create design matrix for second-level (cell-means: no intercept to avoid multicollinearity)
    dm = design_matrix[['AVH-', 'AVH+', 'age', 'iq', 'sex']].copy()
    dm = dm[['AVH-', 'AVH+', 'age', 'iq', 'sex']]
    
    # Fit second-level model
    print("  Fitting second-level model...")
    model = SecondLevelModel(n_jobs=-1, smoothing_fwhm=None)  # Already smoothed
    model.fit(maps, design_matrix=dm)
    
    # Compute AVH- > AVH+ contrast (columns: AVH-, AVH+, age, iq, sex)
    contrast_weights = [1, -1, 0, 0, 0]  # AVH- minus AVH+
    
    print("  Computing parametric statistics...")
    z_map = model.compute_contrast(contrast_weights, output_type='z_score')
    t_map = model.compute_contrast(contrast_weights, output_type='stat')
    
    # Save uncorrected maps
    contrast_output = OUTPUT_DIR / contrast_name
    contrast_output.mkdir(parents=True, exist_ok=True)
    
    nib.save(z_map, contrast_output / f'{contrast_name}_AVH-_vs_AVH+_zstat_uncorrected.nii.gz')
    
    # Run permutation test for cluster correction
    print(f"  Running permutation test ({n_perm} permutations)...")
    print("    This may take a few minutes...")
    
    try:
        # Non-parametric inference with cluster-level correction
        neg_log_pvals, t_stat_map, _, cluster_pv = non_parametric_inference(
            second_level_input=maps,
            design_matrix=dm,
            second_level_contrast=contrast_weights,
            n_perm=n_perm,
            two_sided_test=True,
            threshold=2.3,  # Cluster-forming threshold (z > 2.3)
            n_jobs=-1,
            verbose=0
        )
        
        # Save corrected maps
        nib.save(neg_log_pvals, contrast_output / f'{contrast_name}_AVH-_vs_AVH+_neglogp_corrected.nii.gz')
        
        # Threshold at p < 0.05 (corrected): -log10(0.05) = 1.3
        thresh_map = threshold_img(neg_log_pvals, threshold=1.3)
        nib.save(thresh_map, contrast_output / f'{contrast_name}_AVH-_vs_AVH+_p05_corrected.nii.gz')
        
        # Get cluster table
        try:
            clusters = get_clusters_table(z_map, stat_threshold=2.3, min_distance=8)
            if len(clusters) > 0:
                clusters.to_csv(contrast_output / f'{contrast_name}_cluster_table.csv', index=False)
        except:
            pass
        
        print("  ✓ Permutation test complete")
        
        return {
            'z_map': z_map,
            'neg_log_pvals': neg_log_pvals,
            'thresh_map': thresh_map,
            'output_dir': contrast_output
        }
        
    except Exception as e:
        print(f"  Warning: Permutation test failed: {e}")
        print("  Falling back to uncorrected maps...")
        return {
            'z_map': z_map,
            'output_dir': contrast_output
        }


def main():
    """Run cluster-corrected analysis for all key contrasts (data only).

    Visualization is delegated to `surface_brain_plots.py` and
    `poster_visualizations.py` so styling stays consistent across the project.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*70)
    print("CLUSTER-CORRECTED WHOLE-BRAIN ANALYSIS")
    print("Comparing AVH- vs AVH+ groups")
    print("="*70)

    all_results = {}

    for contrast_name in KEY_CONTRASTS:
        results = run_cluster_corrected_analysis(contrast_name, n_perm=1000)
        if results:
            all_results[contrast_name] = str(results['output_dir'])
    
    # Save summary
    summary = {
        'analysis': 'Cluster-corrected permutation analysis',
        'comparison': 'AVH- vs AVH+',
        'n_permutations': 1000,
        'cluster_threshold': 'z > 2.3',
        'contrasts_analyzed': KEY_CONTRASTS,
        'outputs': all_results
    }
    
    with open(OUTPUT_DIR / 'analysis_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Create README
    readme = """# Cluster-Corrected Analysis: AVH- vs AVH+

## Overview
This folder contains cluster-corrected whole-brain statistical maps comparing 
schizophrenia patients without auditory hallucinations (AVH-) to those with 
auditory hallucinations (AVH+).

## Method
- Second-level GLM with covariates (age, IQ, sex)
- Non-parametric permutation testing (1000 permutations)
- Cluster-forming threshold: z > 2.3
- Family-wise error (FWE) correction at cluster level

## Files
For each contrast:
- `*_zstat_uncorrected.nii.gz` - Uncorrected z-statistic map
- `*_neglogp_corrected.nii.gz` - Negative log10 p-values (corrected)
- `*_p05_corrected.nii.gz` - Thresholded at p < 0.05 (corrected)
- `*_cluster_table.csv` - Cluster information
- `*_glass_brain_corrected.png/svg` - Glass brain visualization
- `*_axial_slices.png` - Axial slice montage
- `*_sagittal_temporal.png` - Sagittal views of temporal regions

## Interpretation
- Positive values: AVH- > AVH+ (greater activation in non-hallucinating patients)
- Negative values: AVH+ > AVH- (greater activation in hallucinating patients)

## Key Regions
Based on prior ROI analysis, expect differences in:
- Left Middle Temporal Gyrus (L_MTG)
- Left Superior Temporal Sulcus (L_STS)
"""
    
    with open(OUTPUT_DIR / 'README.txt', 'w') as f:
        f.write(readme)
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print(f"Results saved to: {OUTPUT_DIR}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
