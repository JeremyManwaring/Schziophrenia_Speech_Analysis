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
| sentences_vs_reversed | 50.0% | 0.319 | 0.347 |
| speech_vs_reversed | 47.5% | 0.360 | 0.455 |
| words_vs_sentences | 42.5% | 0.357 | 0.663 |
| words_vs_reversed | 42.5% | 0.328 | 0.663 |

## Best Performance
- Contrast: sentences_vs_reversed
- Accuracy: 50.0%
- p-value: 0.347

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
