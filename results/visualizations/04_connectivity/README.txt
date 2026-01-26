# Functional Connectivity Analysis: AVH- vs AVH+

## Overview
ROI-to-ROI functional connectivity analysis comparing schizophrenia patients
with and without auditory hallucinations.

## Method
- Extracted timeseries from 12 speech/language ROIs (6mm spheres)
- Computed Pearson correlations between all ROI pairs
- Applied Fisher z-transformation for statistical comparison
- Compared connectivity between AVH- and AVH+ groups (independent t-tests)

## ROIs Analyzed
- L_STG_posterior: MNI (-58, -32, 8)
- L_STG_anterior: MNI (-54, 4, -8)
- L_MTG: MNI (-58, -22, -10)
- L_IFG_triangularis: MNI (-48, 30, 8)
- L_IFG_opercularis: MNI (-52, 14, 16)
- L_STS: MNI (-54, -40, 4)
- L_Heschl: MNI (-42, -22, 8)
- R_STG_posterior: MNI (58, -32, 8)
- R_STG_anterior: MNI (54, 4, -8)
- R_MTG: MNI (58, -22, -10)
- R_IFG: MNI (48, 30, 8)
- R_Heschl: MNI (42, -22, 8)

## Sample Size
- AVH-: 23 subjects
- AVH+: 23 subjects

## Results
- 2 connections showed significant differences (p < 0.05 uncorrected)

## Files
- `connectivity_matrix_AVH-.png` - Mean connectivity for AVH- group
- `connectivity_matrix_AVH+.png` - Mean connectivity for AVH+ group
- `connectivity_difference.png` - Difference with significance overlay
- `network_differences.png` - 3D brain network visualization
- `significant_connections.csv` - Table of significant differences
- `*.npy` - Raw connectivity matrices for further analysis

## Interpretation
- Red in difference maps: Higher connectivity in AVH-
- Blue in difference maps: Higher connectivity in AVH+
- Significant connections may indicate disrupted speech processing networks
