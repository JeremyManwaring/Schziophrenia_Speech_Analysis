# MVPA Classification: AVH- vs AVH+

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
| sentences_vs_reversed | 52.5% | 0.239 | 0.802 |
| speech_vs_reversed | 45.0% | 0.246 | 0.574 |
| words_vs_sentences | 52.5% | 0.235 | 0.218 |
| words_vs_reversed | 60.0% | 0.222 | 0.663 |

## Best Performance
- Contrast: words_vs_reversed
- Accuracy: 60.0%
- p-value: 0.663

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
