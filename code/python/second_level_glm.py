"""
Second-Level GLM Analysis (Group-Level)

This script performs second-level GLM analysis:
- One-way ANOVA comparing HC, AVH-, AVH+ groups
- Post-hoc pairwise comparisons
- Covariates: age, sex, IQ
"""

import numpy as np
import pandas as pd
from pathlib import Path
import nibabel as nib
from nilearn.glm.second_level import SecondLevelModel, non_parametric_inference
from nilearn.image import load_img, concat_imgs, mean_img
from nilearn.plotting import plot_stat_map, plot_glass_brain
from nilearn.reporting import get_clusters_table
import matplotlib.pyplot as plt
import json
import warnings

warnings.filterwarnings('ignore')

# Define contrasts from first-level
FIRST_LEVEL_CONTRASTS = [
    'words_vs_baseline',
    'sentences_vs_baseline', 
    'reversed_vs_baseline',
    'words_vs_reversed',
    'sentences_vs_reversed',
    'speech_vs_reversed',
    'words_vs_sentences',
]


def load_participants(participants_path):
    """
    Load and clean participants data.
    
    Parameters
    ----------
    participants_path : Path
        Path to participants.tsv
    
    Returns
    -------
    df : pd.DataFrame
        Cleaned participants DataFrame
    """
    df = pd.read_csv(participants_path, sep='\t')
    
    # Clean numeric columns
    for col in ['age', 'iq', 'psyrats']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Create binary sex variable
    df['sex_binary'] = (df['sex'] == 'male').astype(float)
    
    # Demean continuous covariates
    df['age_demeaned'] = df['age'] - df['age'].mean()
    if 'iq' in df.columns:
        df['iq_demeaned'] = df['iq'] - df['iq'].mean()
    
    return df


def collect_first_level_maps(first_level_dir, contrast_name, participants_df, 
                              map_type='effect'):
    """
    Collect first-level contrast maps for all subjects.
    
    Parameters
    ----------
    first_level_dir : Path
        Directory containing first-level results
    contrast_name : str
        Name of the contrast
    participants_df : pd.DataFrame
        Participants DataFrame
    map_type : str
        Type of map to collect ('effect', 'zstat', 'tstat')
    
    Returns
    -------
    maps : list
        List of contrast map paths
    design_matrix : pd.DataFrame
        Design matrix for second-level analysis
    """
    first_level_dir = Path(first_level_dir)
    
    maps = []
    subject_ids = []
    groups = []
    ages = []
    iq_vals = []
    sex_vals = []
    
    for _, row in participants_df.iterrows():
        subject_id = row['participant_id']
        
        # Find contrast map
        map_pattern = f'{subject_id}_{contrast_name}_{map_type}.nii.gz'
        map_path = first_level_dir / subject_id / map_pattern
        
        if map_path.exists():
            maps.append(str(map_path))
            subject_ids.append(subject_id)
            groups.append(row['group'])
            ages.append(row.get('age_demeaned', 0))
            iq_vals.append(row.get('iq_demeaned', 0) if pd.notna(row.get('iq_demeaned')) else 0)
            sex_vals.append(row.get('sex_binary', 0))
    
    if len(maps) == 0:
        raise ValueError(f"No contrast maps found for {contrast_name}")
    
    # Create design matrix with group dummy variables
    design_matrix = pd.DataFrame({
        'subject_id': subject_ids,
        'group': groups,
        'age': ages,
        'iq': iq_vals,
        'sex': sex_vals
    })
    
    # Create group dummy variables (HC as reference)
    design_matrix['HC'] = (design_matrix['group'] == 'HC').astype(float)
    design_matrix['AVH-'] = (design_matrix['group'] == 'AVH-').astype(float)
    design_matrix['AVH+'] = (design_matrix['group'] == 'AVH+').astype(float)
    
    return maps, design_matrix


def run_group_anova(maps, design_matrix, output_dir, contrast_name, 
                    n_perm=5000, cluster_threshold=None):
    """
    Run one-way ANOVA comparing groups.
    
    Parameters
    ----------
    maps : list
        List of first-level contrast maps
    design_matrix : pd.DataFrame
        Design matrix with group membership and covariates
    output_dir : Path
        Output directory
    contrast_name : str
        Name of the first-level contrast
    n_perm : int
        Number of permutations for non-parametric inference
    cluster_threshold : float
        Cluster-forming threshold (uncorrected p)
    
    Returns
    -------
    results : dict
        Dictionary with ANOVA results
    """
    output_dir = Path(output_dir)
    contrast_output = output_dir / contrast_name
    contrast_output.mkdir(parents=True, exist_ok=True)
    
    # Create design matrix for ANOVA (cell-means: no intercept to avoid multicollinearity)
    dm = design_matrix[['HC', 'AVH-', 'AVH+', 'age', 'iq', 'sex']].copy()
    dm = dm[['HC', 'AVH-', 'AVH+', 'age', 'iq', 'sex']]
    
    print(f"\n    Design matrix shape: {dm.shape}")
    print(f"    Subjects per group: HC={int(dm['HC'].sum())}, AVH-={int(dm['AVH-'].sum())}, AVH+={int(dm['AVH+'].sum())}")
    
    # Fit second-level model
    second_level_model = SecondLevelModel(n_jobs=-1)
    second_level_model.fit(maps, design_matrix=dm)
    
    results = {'contrast_name': contrast_name, 'tests': {}}
    
    # 1. Main effect of group (F-test)
    print("    Computing main effect of group (F-test)...")
    
    # F-test: test if any group mean differs (columns: HC, AVH-, AVH+, age, iq, sex)
    f_contrast = np.array([
        [1, -1, 0, 0, 0, 0],   # HC vs AVH-
        [1, 0, -1, 0, 0, 0],   # HC vs AVH+
    ])
    
    try:
        f_map = second_level_model.compute_contrast(
            f_contrast, 
            stat_type='F',
            output_type='z_score'
        )
        nib.save(f_map, contrast_output / f'{contrast_name}_group_effect_fstat.nii.gz')
        results['tests']['group_effect'] = str(contrast_output / f'{contrast_name}_group_effect_fstat.nii.gz')
    except Exception as e:
        print(f"    Warning: Could not compute F-test: {e}")
    
    # 2. Pairwise comparisons (T-tests) (columns: HC, AVH-, AVH+, age, iq, sex)
    pairwise_contrasts = {
        'HC_vs_AVH-': [1, -1, 0, 0, 0, 0],
        'HC_vs_AVH+': [1, 0, -1, 0, 0, 0],
        'AVH-_vs_AVH+': [0, 1, -1, 0, 0, 0],
    }
    
    for name, contrast_weights in pairwise_contrasts.items():
        print(f"    Computing {name}...")
        try:
            z_map = second_level_model.compute_contrast(
                contrast_weights,
                output_type='z_score'
            )
            nib.save(z_map, contrast_output / f'{contrast_name}_{name}_zstat.nii.gz')
            
            # Also compute t-stat
            t_map = second_level_model.compute_contrast(
                contrast_weights,
                output_type='stat'
            )
            nib.save(t_map, contrast_output / f'{contrast_name}_{name}_tstat.nii.gz')
            
            results['tests'][name] = {
                'z_map': str(contrast_output / f'{contrast_name}_{name}_zstat.nii.gz'),
                't_map': str(contrast_output / f'{contrast_name}_{name}_tstat.nii.gz')
            }
            
            # Get cluster table
            try:
                clusters = get_clusters_table(z_map, stat_threshold=2.3, min_distance=8)
                if len(clusters) > 0:
                    clusters.to_csv(contrast_output / f'{contrast_name}_{name}_clusters.csv', index=False)
            except:
                pass
                
        except Exception as e:
            print(f"    Warning: Could not compute {name}: {e}")
    
    # 3. Overall mean (one-sample t-test across all subjects)
    print("    Computing overall mean...")
    try:
        mean_contrast = [1/3, 1/3, 1/3, 0, 0, 0]  # Average of three group means (cell-means model)
        mean_map = second_level_model.compute_contrast(
            mean_contrast,
            output_type='z_score'
        )
        nib.save(mean_map, contrast_output / f'{contrast_name}_overall_mean_zstat.nii.gz')
        results['tests']['overall_mean'] = str(contrast_output / f'{contrast_name}_overall_mean_zstat.nii.gz')
    except Exception as e:
        print(f"    Warning: Could not compute overall mean: {e}")
    
    # Save design matrix
    dm.to_csv(contrast_output / f'{contrast_name}_design_matrix.csv', index=False)
    
    return results


def create_group_summary_figure(results_dir, contrast_name, output_dir):
    """
    Create summary figure for group comparisons.
    
    Parameters
    ----------
    results_dir : Path
        Directory with second-level results
    contrast_name : str
        Name of the contrast
    output_dir : Path
        Output directory for figures
    """
    results_dir = Path(results_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    contrast_dir = results_dir / contrast_name
    
    comparisons = ['HC_vs_AVH-', 'HC_vs_AVH+', 'AVH-_vs_AVH+']
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    for i, comparison in enumerate(comparisons):
        z_map_path = contrast_dir / f'{contrast_name}_{comparison}_zstat.nii.gz'
        
        if z_map_path.exists():
            try:
                plot_glass_brain(
                    str(z_map_path),
                    threshold=2.3,
                    title=comparison.replace('_', ' '),
                    axes=axes[i],
                    display_mode='lyrz',
                    colorbar=True
                )
            except:
                axes[i].text(0.5, 0.5, 'Error loading map', ha='center', va='center')
                axes[i].set_title(comparison)
        else:
            axes[i].text(0.5, 0.5, 'Map not found', ha='center', va='center')
            axes[i].set_title(comparison)
    
    plt.suptitle(f'{contrast_name}: Group Comparisons', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / f'{contrast_name}_group_comparisons.png', dpi=150, bbox_inches='tight')
    plt.close()


def run_all_contrasts(first_level_dir, participants_path, output_dir):
    """
    Run second-level analysis for all first-level contrasts.
    
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
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load participants
    participants_df = load_participants(participants_path)
    
    print("\n" + "="*70)
    print("SECOND-LEVEL GROUP ANALYSIS")
    print("="*70)
    print(f"\nParticipants: {len(participants_df)}")
    print(f"Groups: {participants_df['group'].value_counts().to_dict()}")
    print(f"Output directory: {output_dir}")
    
    all_results = {}
    
    for contrast_name in FIRST_LEVEL_CONTRASTS:
        print(f"\n{'='*70}")
        print(f"Processing: {contrast_name}")
        print("="*70)
        
        try:
            # Collect first-level maps
            maps, design_matrix = collect_first_level_maps(
                first_level_dir, contrast_name, participants_df, map_type='effect'
            )
            
            print(f"  Found {len(maps)} subjects with contrast maps")
            
            # Run group ANOVA
            results = run_group_anova(
                maps=maps,
                design_matrix=design_matrix,
                output_dir=output_dir,
                contrast_name=contrast_name
            )
            
            all_results[contrast_name] = results
            
            # Create summary figure
            try:
                create_group_summary_figure(
                    results_dir=output_dir,
                    contrast_name=contrast_name,
                    output_dir=output_dir / 'figures'
                )
            except Exception as e:
                print(f"  Warning: Could not create figure: {e}")
            
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[contrast_name] = {'error': str(e)}
    
    # Save summary
    summary_path = output_dir / 'second_level_summary.json'
    
    # Make paths serializable
    def make_serializable(obj):
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, Path):
            return str(obj)
        else:
            return obj
    
    with open(summary_path, 'w') as f:
        json.dump(make_serializable(all_results), f, indent=2)
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print("="*70)
    print(f"\nProcessed {len(FIRST_LEVEL_CONTRASTS)} contrasts")
    print(f"Results saved to: {output_dir}")
    print(f"Summary saved to: {summary_path}")
    print("="*70 + "\n")
    
    return all_results


def main():
    """Main function to run second-level analysis."""
    # Set paths
    dataset_root = Path(__file__).parent.parent.parent
    first_level_dir = dataset_root / 'results' / 'first_level'
    participants_path = dataset_root / 'participants.tsv'
    output_dir = dataset_root / 'results' / 'second_level'
    
    # Check if first-level results exist
    if not first_level_dir.exists():
        print(f"\nError: First-level results not found: {first_level_dir}")
        print("Please run first-level GLM first.")
        return
    
    # Run second-level analysis
    results = run_all_contrasts(
        first_level_dir=first_level_dir,
        participants_path=participants_path,
        output_dir=output_dir
    )
    
    return results


if __name__ == "__main__":
    main()
