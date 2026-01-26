"""
MVPA Classification: AVH- vs AVH+

Multivariate Pattern Analysis using SVM to classify patients
with and without auditory hallucinations based on brain activation patterns.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import nibabel as nib
from nilearn.maskers import NiftiMasker
from nilearn.image import load_img, mean_img
from nilearn.plotting import plot_stat_map, plot_glass_brain
from sklearn.svm import SVC
from sklearn.model_selection import LeaveOneOut, cross_val_score, permutation_test_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score, classification_report
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
import seaborn as sns
import json
import warnings

warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
FIRST_LEVEL_DIR = BASE_DIR / 'results' / 'vm_analysis' / 'results' / 'first_level'
FMRIPREP_DIR = BASE_DIR / 'derivatives' / 'fmriprep'
PARTICIPANTS_PATH = BASE_DIR / 'participants.tsv'
OUTPUT_DIR = BASE_DIR / 'results' / 'visualizations' / '03_mvpa_classification'

# Contrasts to test
CONTRASTS = [
    'sentences_vs_reversed',
    'speech_vs_reversed',
    'words_vs_sentences',
    'words_vs_reversed'
]


def load_participants():
    """Load participant data."""
    df = pd.read_csv(PARTICIPANTS_PATH, sep='\t')
    return df


def get_brain_mask():
    """Get a brain mask from fMRIPrep outputs."""
    # Use first available subject's brain mask
    mask_pattern = FMRIPREP_DIR / 'sub-01' / 'func' / '*_desc-brain_mask.nii.gz'
    masks = list(FMRIPREP_DIR.glob('sub-*/func/*_desc-brain_mask.nii.gz'))
    
    if masks:
        return str(masks[0])
    else:
        return None


def load_contrast_data(contrast_name, participants_df):
    """Load contrast maps for AVH- and AVH+ subjects."""
    avh_df = participants_df[participants_df['group'].isin(['AVH-', 'AVH+'])].copy()
    
    maps = []
    labels = []
    subjects = []
    
    for _, row in avh_df.iterrows():
        sub_id = row['participant_id']
        map_path = FIRST_LEVEL_DIR / sub_id / f'{sub_id}_{contrast_name}_zstat.nii.gz'
        
        if not map_path.exists():
            map_path = FIRST_LEVEL_DIR / sub_id / f'{sub_id}_{contrast_name}_effect.nii.gz'
        
        if map_path.exists():
            maps.append(str(map_path))
            labels.append(0 if row['group'] == 'AVH-' else 1)
            subjects.append(sub_id)
    
    return maps, np.array(labels), subjects


def run_svm_classification(contrast_name, participants_df):
    """Run SVM classification with leave-one-out cross-validation."""
    print(f"\n  Processing {contrast_name}...")
    
    maps, labels, subjects = load_contrast_data(contrast_name, participants_df)
    
    if len(maps) < 10:
        print(f"    Not enough subjects: {len(maps)}")
        return None
    
    n_avh_minus = np.sum(labels == 0)
    n_avh_plus = np.sum(labels == 1)
    print(f"    Subjects: {len(maps)} (AVH-: {n_avh_minus}, AVH+: {n_avh_plus})")
    
    # Create masker
    mask = get_brain_mask()
    masker = NiftiMasker(
        mask_img=mask,
        standardize=True,
        smoothing_fwhm=None,  # Already smoothed
        memory='nilearn_cache',
        memory_level=1
    )
    
    # Extract features
    print("    Extracting features...")
    X = masker.fit_transform(maps)
    y = labels
    
    print(f"    Feature matrix shape: {X.shape}")
    
    # SVM classifier
    clf = Pipeline([
        ('scaler', StandardScaler()),
        ('svm', SVC(kernel='linear', C=1.0, probability=True))
    ])
    
    # Leave-one-out cross-validation
    print("    Running LOO cross-validation...")
    loo = LeaveOneOut()
    
    predictions = []
    probabilities = []
    
    for train_idx, test_idx in loo.split(X):
        clf.fit(X[train_idx], y[train_idx])
        pred = clf.predict(X[test_idx])
        prob = clf.predict_proba(X[test_idx])[:, 1]
        predictions.append(pred[0])
        probabilities.append(prob[0])
    
    predictions = np.array(predictions)
    probabilities = np.array(probabilities)
    
    # Calculate metrics
    accuracy = accuracy_score(y, predictions)
    
    try:
        auc = roc_auc_score(y, probabilities)
    except:
        auc = 0.5
    
    cm = confusion_matrix(y, predictions)
    
    # Permutation test for significance
    print("    Running permutation test (100 permutations)...")
    try:
        clf_perm = Pipeline([
            ('scaler', StandardScaler()),
            ('svm', SVC(kernel='linear', C=1.0))
        ])
        score, perm_scores, p_value = permutation_test_score(
            clf_perm, X, y, scoring='accuracy', cv=5, n_permutations=100, n_jobs=-1
        )
    except:
        p_value = 1.0
        perm_scores = np.zeros(100)
    
    # Get feature weights (train on all data)
    clf.fit(X, y)
    weights = clf.named_steps['svm'].coef_[0]
    
    # Map weights back to brain space
    weight_img = masker.inverse_transform(weights)
    
    print(f"    Accuracy: {accuracy:.1%}")
    print(f"    AUC: {auc:.3f}")
    print(f"    p-value: {p_value:.3f}")
    
    return {
        'contrast': contrast_name,
        'accuracy': accuracy,
        'auc': auc,
        'p_value': p_value,
        'confusion_matrix': cm,
        'predictions': predictions,
        'probabilities': probabilities,
        'labels': y,
        'subjects': subjects,
        'weight_img': weight_img,
        'perm_scores': perm_scores,
        'n_subjects': len(maps),
        'n_avh_minus': n_avh_minus,
        'n_avh_plus': n_avh_plus
    }


def create_accuracy_plot(all_results):
    """Create bar plot of classification accuracies."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    contrasts = [r['contrast'] for r in all_results]
    accuracies = [r['accuracy'] * 100 for r in all_results]
    p_values = [r['p_value'] for r in all_results]
    
    colors = ['#e74c3c' if p < 0.05 else '#3498db' for p in p_values]
    
    bars = ax.bar(range(len(contrasts)), accuracies, color=colors, alpha=0.7, edgecolor='black')
    
    # Add chance level line
    ax.axhline(y=50, color='gray', linestyle='--', linewidth=2, label='Chance (50%)')
    
    # Add significance stars
    for i, (acc, p) in enumerate(zip(accuracies, p_values)):
        if p < 0.05:
            ax.text(i, acc + 2, '*', ha='center', fontsize=16, fontweight='bold')
        ax.text(i, acc + 0.5, f'{acc:.1f}%', ha='center', fontsize=10)
    
    ax.set_xticks(range(len(contrasts)))
    ax.set_xticklabels([c.replace('_', '\n') for c in contrasts], fontsize=10)
    ax.set_ylabel('Classification Accuracy (%)', fontsize=12)
    ax.set_xlabel('Contrast', fontsize=12)
    ax.set_title('SVM Classification: AVH- vs AVH+\n(Leave-One-Out Cross-Validation)', fontsize=13, fontweight='bold')
    ax.set_ylim(0, 100)
    
    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#e74c3c', alpha=0.7, label='p < 0.05'),
        Patch(facecolor='#3498db', alpha=0.7, label='p ≥ 0.05'),
        plt.Line2D([0], [0], color='gray', linestyle='--', label='Chance level')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'classification_accuracy.png', dpi=150, bbox_inches='tight')
    plt.savefig(OUTPUT_DIR / 'classification_accuracy.svg', bbox_inches='tight')
    plt.close()


def create_confusion_matrices(all_results):
    """Create confusion matrix plots."""
    n_results = len(all_results)
    fig, axes = plt.subplots(1, n_results, figsize=(4 * n_results, 4))
    
    if n_results == 1:
        axes = [axes]
    
    for ax, result in zip(axes, all_results):
        cm = result['confusion_matrix']
        
        # Normalize
        cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        
        sns.heatmap(
            cm_norm, annot=True, fmt='.1%', cmap='Blues',
            xticklabels=['AVH-', 'AVH+'],
            yticklabels=['AVH-', 'AVH+'],
            ax=ax, cbar=False,
            annot_kws={'size': 14}
        )
        
        # Add raw counts
        for i in range(2):
            for j in range(2):
                ax.text(j + 0.5, i + 0.7, f'(n={cm[i, j]})', 
                       ha='center', va='center', fontsize=10, color='gray')
        
        ax.set_xlabel('Predicted', fontsize=11)
        ax.set_ylabel('Actual', fontsize=11)
        ax.set_title(result['contrast'].replace('_', '\n'), fontsize=11)
    
    plt.suptitle('Confusion Matrices', fontsize=13, fontweight='bold', y=1.05)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'confusion_matrices.png', dpi=150, bbox_inches='tight')
    plt.close()


def create_weight_maps(all_results):
    """Create brain maps showing discriminative features."""
    for result in all_results:
        contrast = result['contrast']
        weight_img = result['weight_img']
        
        # Glass brain
        fig = plt.figure(figsize=(12, 5))
        
        plot_glass_brain(
            weight_img,
            threshold='auto',
            title=f'{contrast}\nSVM Weights (AVH- vs AVH+)',
            display_mode='lyrz',
            colorbar=True,
            cmap='RdBu_r'
        )
        
        plt.savefig(OUTPUT_DIR / f'{contrast}_svm_weights_glass.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        # Axial slices
        fig = plt.figure(figsize=(15, 4))
        plot_stat_map(
            weight_img,
            threshold='auto',
            cut_coords=[-20, 0, 20, 40, 60],
            display_mode='z',
            title=f'{contrast}: SVM Weights',
            colorbar=True,
            cmap='RdBu_r'
        )
        plt.savefig(OUTPUT_DIR / f'{contrast}_svm_weights_axial.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        # Save weight map
        nib.save(weight_img, OUTPUT_DIR / f'{contrast}_svm_weights.nii.gz')


def create_permutation_plot(all_results):
    """Create permutation test distribution plot."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    
    for ax, result in zip(axes, all_results):
        perm_scores = result['perm_scores']
        actual_score = result['accuracy']
        p_value = result['p_value']
        
        ax.hist(perm_scores, bins=20, color='#3498db', alpha=0.7, edgecolor='black')
        ax.axvline(x=actual_score, color='#e74c3c', linewidth=3, linestyle='--',
                  label=f'Actual: {actual_score:.1%}')
        ax.axvline(x=0.5, color='gray', linewidth=2, linestyle=':',
                  label='Chance: 50%')
        
        ax.set_xlabel('Accuracy', fontsize=11)
        ax.set_ylabel('Count', fontsize=11)
        ax.set_title(f"{result['contrast']}\np = {p_value:.3f}", fontsize=11)
        ax.legend(fontsize=9)
    
    plt.suptitle('Permutation Test Distributions', fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'permutation_distributions.png', dpi=150, bbox_inches='tight')
    plt.close()


def main():
    """Run MVPA classification analysis."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("MVPA CLASSIFICATION: AVH- vs AVH+")
    print("="*70)
    
    participants_df = load_participants()
    all_results = []
    
    for contrast in CONTRASTS:
        result = run_svm_classification(contrast, participants_df)
        if result:
            all_results.append(result)
    
    if not all_results:
        print("\nNo results generated. Check that contrast maps exist.")
        return
    
    # Create visualizations
    print("\nCreating visualizations...")
    create_accuracy_plot(all_results)
    create_confusion_matrices(all_results)
    create_weight_maps(all_results)
    create_permutation_plot(all_results)
    
    # Save summary
    summary = {
        'analysis': 'MVPA SVM Classification',
        'comparison': 'AVH- vs AVH+',
        'method': 'Leave-One-Out Cross-Validation',
        'results': []
    }
    
    for result in all_results:
        summary['results'].append({
            'contrast': result['contrast'],
            'accuracy': float(result['accuracy']),
            'auc': float(result['auc']),
            'p_value': float(result['p_value']),
            'n_subjects': int(result['n_subjects']),
            'n_avh_minus': int(result['n_avh_minus']),
            'n_avh_plus': int(result['n_avh_plus'])
        })
    
    with open(OUTPUT_DIR / 'classification_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Best result
    best = max(all_results, key=lambda x: x['accuracy'])
    
    # Create README
    readme = f"""# MVPA Classification: AVH- vs AVH+

## Overview
Support Vector Machine (SVM) classification was used to determine if brain
activation patterns can distinguish schizophrenia patients with auditory
hallucinations (AVH+) from those without (AVH-).

## Method
- Classifier: Linear SVM (C=1.0)
- Validation: Leave-One-Out Cross-Validation
- Features: Whole-brain voxel activation patterns
- Statistical test: Permutation test (100 permutations)

## Results Summary
| Contrast | Accuracy | AUC | p-value |
|----------|----------|-----|---------|
"""
    
    for r in all_results:
        sig = '*' if r['p_value'] < 0.05 else ''
        readme += f"| {r['contrast']} | {r['accuracy']:.1%} | {r['auc']:.3f} | {r['p_value']:.3f}{sig} |\n"
    
    readme += f"""
## Best Performance
- Contrast: {best['contrast']}
- Accuracy: {best['accuracy']:.1%}
- p-value: {best['p_value']:.3f}

## Files
- `classification_accuracy.png/svg` - Bar plot of accuracies
- `confusion_matrices.png` - Confusion matrices for each contrast
- `*_svm_weights*.png` - Brain maps of discriminative features
- `*_svm_weights.nii.gz` - NIfTI weight maps
- `permutation_distributions.png` - Permutation test results
- `classification_results.json` - Detailed results

## Interpretation
- Accuracy > 50%: Better than chance classification
- p < 0.05: Statistically significant discrimination
- Weight maps show regions most important for classification
"""
    
    with open(OUTPUT_DIR / 'README.txt', 'w') as f:
        f.write(readme)
    
    print("\n" + "="*70)
    print(f"Best accuracy: {best['accuracy']:.1%} ({best['contrast']})")
    print(f"Results saved to: {OUTPUT_DIR}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
