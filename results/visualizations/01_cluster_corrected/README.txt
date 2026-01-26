# Cluster-Corrected Analysis: AVH- vs AVH+

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
