"""
Second-Level GLM Analysis (VM Version)
"""

import numpy as np
import pandas as pd
from pathlib import Path
import nibabel as nib
from nilearn.glm.second_level import SecondLevelModel
from nilearn.reporting import get_clusters_table
import matplotlib.pyplot as plt
import json
import warnings

warnings.filterwarnings('ignore')

FIRST_LEVEL_CONTRASTS = [
    'words_vs_baseline', 'sentences_vs_baseline', 'reversed_vs_baseline',
    'words_vs_reversed', 'sentences_vs_reversed', 'speech_vs_reversed', 'words_vs_sentences',
]


def load_participants(participants_path):
    """Load and clean participants data."""
    df = pd.read_csv(participants_path, sep='\t')
    for col in ['age', 'iq', 'psyrats']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df['sex_binary'] = (df['sex'] == 'male').astype(float)
    df['age_demeaned'] = df['age'] - df['age'].mean()
    if 'iq' in df.columns:
        df['iq_demeaned'] = df['iq'] - df['iq'].mean()
    return df


def collect_first_level_maps(first_level_dir, contrast_name, participants_df, map_type='effect'):
    """Collect first-level contrast maps for all subjects."""
    first_level_dir = Path(first_level_dir)
    
    maps = []
    subject_ids = []
    groups = []
    ages = []
    iq_vals = []
    sex_vals = []
    
    for _, row in participants_df.iterrows():
        subject_id = row['participant_id']
        map_path = first_level_dir / subject_id / f'{subject_id}_{contrast_name}_{map_type}.nii.gz'
        
        if map_path.exists():
            maps.append(str(map_path))
            subject_ids.append(subject_id)
            groups.append(row['group'])
            ages.append(row.get('age_demeaned', 0))
            iq_vals.append(row.get('iq_demeaned', 0) if pd.notna(row.get('iq_demeaned')) else 0)
            sex_vals.append(row.get('sex_binary', 0))
    
    design_matrix = pd.DataFrame({
        'subject_id': subject_ids, 'group': groups, 'age': ages, 'iq': iq_vals, 'sex': sex_vals
    })
    design_matrix['HC'] = (design_matrix['group'] == 'HC').astype(float)
    design_matrix['AVH-'] = (design_matrix['group'] == 'AVH-').astype(float)
    design_matrix['AVH+'] = (design_matrix['group'] == 'AVH+').astype(float)
    
    return maps, design_matrix


def run_group_anova(maps, design_matrix, output_dir, contrast_name):
    """Run one-way ANOVA comparing groups."""
    output_dir = Path(output_dir)
    contrast_output = output_dir / contrast_name
    contrast_output.mkdir(parents=True, exist_ok=True)
    
    dm = design_matrix[['HC', 'AVH-', 'AVH+', 'age', 'iq', 'sex']].copy()
    dm['intercept'] = 1
    dm = dm[['intercept', 'HC', 'AVH-', 'AVH+', 'age', 'iq', 'sex']]
    
    print(f"    Design matrix: {dm.shape}, Groups: HC={int(dm['HC'].sum())}, AVH-={int(dm['AVH-'].sum())}, AVH+={int(dm['AVH+'].sum())}")
    
    second_level_model = SecondLevelModel(n_jobs=-1)
    second_level_model.fit(maps, design_matrix=dm)
    
    results = {'contrast_name': contrast_name, 'tests': {}}
    
    # Pairwise comparisons
    pairwise_contrasts = {
        'HC_vs_AVH-': [0, 1, -1, 0, 0, 0, 0],
        'HC_vs_AVH+': [0, 1, 0, -1, 0, 0, 0],
        'AVH-_vs_AVH+': [0, 0, 1, -1, 0, 0, 0],
    }
    
    for name, contrast_weights in pairwise_contrasts.items():
        print(f"    Computing {name}...")
        try:
            z_map = second_level_model.compute_contrast(contrast_weights, output_type='z_score')
            nib.save(z_map, contrast_output / f'{contrast_name}_{name}_zstat.nii.gz')
            results['tests'][name] = str(contrast_output / f'{contrast_name}_{name}_zstat.nii.gz')
        except Exception as e:
            print(f"    Warning: Could not compute {name}: {e}")
    
    # Overall mean
    try:
        mean_map = second_level_model.compute_contrast([1, 0, 0, 0, 0, 0, 0], output_type='z_score')
        nib.save(mean_map, contrast_output / f'{contrast_name}_overall_mean_zstat.nii.gz')
    except:
        pass
    
    dm.to_csv(contrast_output / f'{contrast_name}_design_matrix.csv', index=False)
    return results


def run_all_contrasts(first_level_dir, participants_path, output_dir):
    """Run second-level analysis for all contrasts."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    participants_df = load_participants(participants_path)
    
    print(f"\n{'='*70}")
    print("SECOND-LEVEL GROUP ANALYSIS")
    print("="*70)
    print(f"\nParticipants: {len(participants_df)}")
    print(f"Groups: {participants_df['group'].value_counts().to_dict()}")
    
    all_results = {}
    
    for contrast_name in FIRST_LEVEL_CONTRASTS:
        print(f"\n{'='*70}")
        print(f"Processing: {contrast_name}")
        print("="*70)
        
        try:
            maps, design_matrix = collect_first_level_maps(first_level_dir, contrast_name, participants_df)
            print(f"  Found {len(maps)} subjects")
            results = run_group_anova(maps, design_matrix, output_dir, contrast_name)
            all_results[contrast_name] = results
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[contrast_name] = {'error': str(e)}
    
    with open(output_dir / 'second_level_summary.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_dir}")
    print("="*70 + "\n")
    
    return all_results
