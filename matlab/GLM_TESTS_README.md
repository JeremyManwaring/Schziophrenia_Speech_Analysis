# Voxel-wise GLM Tests: T-tests and F-tests

Complete pipeline for voxel-wise General Linear Model (GLM) analysis using SPM, including t-tests and F-tests.

## Overview

This analysis pipeline performs:
1. **First-level GLM**: Subject-level statistical modeling
2. **T-test Contrasts**: Tests for specific condition comparisons
3. **F-tests**: Omnibus tests for overall activation patterns
4. **Second-level Analysis**: Group-level inference

## Quick Start

### Run Complete Pipeline
```matlab
cd matlab
start_matlab_spm  % Initialize SPM
run_glm_tests     % Run complete analysis
```

### Run Individual Steps
```matlab
% Just run first-level GLM
voxelwise_glm_tests(true, false, false, false)

% Create contrasts only
voxelwise_glm_tests(false, true, false, false)

% Create F-tests only
voxelwise_glm_tests(false, false, true, false)

% Second-level group analysis only
voxelwise_glm_tests(false, false, false, true)
```

## T-Test Contrasts

The pipeline creates the following t-test contrasts:

1. **Words > Baseline**: Words vs. white-noise baseline
2. **Sentences > Baseline**: Sentences vs. white-noise baseline
3. **Reversed > Baseline**: Reversed speech vs. white-noise baseline
4. **Words > Reversed**: Words vs. reversed speech
5. **Sentences > Reversed**: Sentences vs. reversed speech
6. **(Words + Sentences) > Reversed**: Intelligible vs. unintelligible speech
7. **Words > Sentences**: Words vs. sentences

### Contrast Weights

The GLM models three conditions (in order):
- Condition 1: Words
- Condition 2: Sentences
- Condition 3: Reversed

Example contrast weights:
- `[1 0 0]`: Words > Baseline
- `[0 1 0]`: Sentences > Baseline
- `[1 0 -1]`: Words > Reversed
- `[1 -1 0]`: Words > Sentences

## F-Tests

F-tests are omnibus tests that assess whether there are any significant effects across multiple conditions:

1. **All Conditions**: Tests if any of the three task conditions show significant activation
   - Contrast matrix: `eye(3)` (identity matrix)
   - Tests: words, sentences, AND reversed separately

2. **Condition Differences**: Tests if there are any differences between conditions
   - Contrast matrix: `[1 -1 0; 1 0 -1]`
   - Tests differences: words vs. sentences, words vs. reversed

## Viewing Results

### Interactive Visualization
```matlab
% View first-level result
visualize_glm_results('first_level', '01', 1)

% View second-level result
visualize_glm_results('second_level', 'Words_Baseline', 1)
```

### Statistical Reports
```matlab
% Generate detailed report
report_glm_statistics('first_level', '01', 1, 0.001, 10)

% Report with different threshold
report_glm_statistics('second_level', 'Words_Baseline', 1, 0.05, 20)
```

### Using SPM GUI
1. Open SPM: `spm`
2. Click **Results**
3. Select `SPM.mat` file
4. Choose contrast
5. Set thresholds
6. Explore results

## File Structure

After running the analysis:

```
ds004302/
├── sub-01/
│   └── spm/
│       └── first_level/
│           ├── SPM.mat              % GLM specification
│           ├── beta_*.nii           % Parameter estimates
│           ├── con_0001.nii         % Contrast images
│           ├── con_0002.nii
│           ├── ...
│           ├── spmT_0001.nii        % T-statistic images
│           ├── spmT_0002.nii
│           ├── ...
│           ├── spmF_0001.nii        % F-statistic images
│           └── spmF_0002.nii
└── spm/
    └── second_level/
        ├── Words_Baseline/
        │   ├── SPM.mat
        │   ├── con_0001.nii
        │   └── spmT_0001.nii
        ├── Sentences_Baseline/
        └── Reversed_Baseline/
```

## Statistical Thresholds

### Voxel-level Thresholds
- **Uncorrected**: p < 0.001 (default)
- **FWE corrected**: Family-wise error rate correction
- **FDR corrected**: False discovery rate correction

### Cluster-level Inference
- **Cluster extent**: Minimum cluster size (default: 10 voxels)
- **Cluster p-value**: Probability threshold for cluster significance

## Multiple Comparisons Correction

SPM provides several correction methods:

### Family-Wise Error (FWE)
- Controls probability of ANY false positive across all voxels
- Most conservative
- Use: `SPM > Results > Set contrasts > FWE correction`

### False Discovery Rate (FDR)
- Controls expected proportion of false positives
- Less conservative than FWE
- Use: `SPM > Results > Set contrasts > FDR correction`

### Cluster-level Inference
- Corrects for multiple clusters
- Use: `SPM > Results > Set contrasts > Cluster-level inference`

## Example Workflow

```matlab
%% Complete Analysis Workflow

% 1. Initialize
start_matlab_spm

% 2. Run complete pipeline
run_glm_tests

% 3. View first-level results for subject 01
visualize_glm_results('first_level', '01', 1)  % Words > Baseline

% 4. Generate statistical report
report_glm_statistics('first_level', '01', 1, 0.001, 10)

% 5. View group results
visualize_glm_results('second_level', 'Words_Baseline', 1)

% 6. Generate group report
report_glm_statistics('second_level', 'Words_Baseline', 1, 0.001, 10)
```

## Interpretation

### T-test Results
- **Positive values**: Activation (condition > baseline)
- **Negative values**: Deactivation (condition < baseline)
- **Magnitude**: Strength of effect
- **Significance**: Statistical reliability

### F-test Results
- **High F-values**: Significant effects present
- **Interprets as**: "Is there ANY effect across these conditions?"
- **Follow-up**: Use t-tests to identify specific effects

### Second-level Results
- **Group inference**: Effects consistent across subjects
- **Statistical power**: Combines information from all subjects
- **Population inference**: Generalizable to population

## Troubleshooting

### "Contrast images not found"
- Ensure first-level analysis completed: `voxelwise_glm_tests(true, true, false, false)`
- Check file paths in subject directories

### "SPM.mat not found"
- Verify preprocessing completed: `batch_preprocessing`
- Check SPM directory structure

### Low statistical power
- Check preprocessing quality
- Verify design matrix specification
- Consider increasing sample size

## References

- SPM Manual: https://www.fil.ion.ucl.ac.uk/spm/doc/
- Friston et al. (2007). Statistical Parametric Mapping
- Penny et al. (2011). Statistical Parametric Mapping: The Analysis of Functional Brain Images

