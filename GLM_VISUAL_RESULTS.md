# GLM Analysis: T-tests and F-tests Visual Results Guide

## 📊 Analysis Overview

This document describes the t-tests and F-tests that will be performed on your data and how to visualize the results.

## 🎯 T-Test Contrasts (7 tests)

### 1. Words > Baseline
- **Weights**: `[1 0 0]`
- **Purpose**: Tests activation for words vs white-noise baseline
- **Expected**: Activations in auditory cortex, language areas
- **Visualize**: `show_glm_results('01', 1)`

### 2. Sentences > Baseline  
- **Weights**: `[0 1 0]`
- **Purpose**: Tests activation for sentences vs white-noise baseline
- **Expected**: Activations in superior temporal gyrus, language network
- **Visualize**: `show_glm_results('01', 2)`

### 3. Reversed > Baseline
- **Weights**: `[0 0 1]`
- **Purpose**: Tests activation for reversed speech vs baseline
- **Expected**: Activations in primary auditory cortex
- **Visualize**: `show_glm_results('01', 3)`

### 4. Words > Reversed
- **Weights**: `[1 0 -1]`
- **Purpose**: Tests intelligible (words) vs unintelligible (reversed) speech
- **Expected**: Language-specific activations (left temporal lobe, inferior frontal)
- **Visualize**: `show_glm_results('01', 4)`

### 5. Sentences > Reversed
- **Weights**: `[0 1 -1]`
- **Purpose**: Tests intelligible (sentences) vs unintelligible speech
- **Expected**: Complex language processing areas
- **Visualize**: `show_glm_results('01', 5)`

### 6. (Words + Sentences) > Reversed
- **Weights**: `[1 1 -2]`
- **Purpose**: Tests intelligible speech (words+sentences) vs unintelligible
- **Expected**: Language comprehension network
- **Visualize**: `show_glm_results('01', 6)`

### 7. Words > Sentences
- **Weights**: `[1 -1 0]`
- **Purpose**: Tests words vs sentences (within intelligible speech)
- **Expected**: Regions sensitive to sentence-level processing
- **Visualize**: `show_glm_results('01', 7)`

## 🔬 F-Test Contrasts (2 omnibus tests)

### F-test 1: All Conditions
- **Matrix**: `eye(3)` (Identity matrix)
- **Purpose**: Tests if ANY of the three conditions show significant activation
- **Interpretation**: High F-value indicates significant effects present
- **Use case**: Initial screening for task-related activation
- **Visualize**: `show_glm_results('01', 1, true)`

### F-test 2: Condition Differences
- **Matrix**: `[1 -1 0; 1 0 -1]`
- **Purpose**: Tests if there are ANY differences between conditions
- **Tests**: 
  - Words vs Sentences
  - Words vs Reversed
- **Interpretation**: High F-value indicates condition differences exist
- **Use case**: Identify regions showing differential responses
- **Visualize**: `show_glm_results('01', 2, true)`

## 📈 How to Run and Visualize

### Step 1: Preprocessing (Required First)
```matlab
cd matlab
start_matlab_spm
batch_preprocessing  % This will take time - processes all subjects
```

### Step 2: Run GLM Analysis
```matlab
run_glm_tests  % Complete pipeline
% Or step by step:
voxelwise_glm_tests(true, true, true, true)
```

### Step 3: Visualize Results

#### View Individual T-tests
```matlab
% Words > Baseline
show_glm_results('01', 1)

% Sentences > Baseline  
show_glm_results('01', 2)

% Words > Reversed (most interesting for language)
show_glm_results('01', 4)
```

#### View F-tests
```matlab
% All Conditions
show_glm_results('01', 1, true)

% Condition Differences
show_glm_results('01', 2, true)
```

#### Generate Statistics Reports
```matlab
% Detailed report with cluster analysis
report_glm_statistics('first_level', '01', 1, 0.001, 10)

% Group-level report
report_glm_statistics('second_level', 'Words_Baseline', 1, 0.001, 10)
```

## 🖼️ Visual Results in SPM

When you run the visualization commands, SPM will:

1. **Open Results Viewer**: Shows statistical maps overlaid on brain
2. **Display Slices**: Axial, coronal, sagittal views
3. **Show Thresholded Maps**: Only significant voxels displayed
4. **Interactive Exploration**: Click to see coordinates and statistics

### What You'll See:

**T-test Maps:**
- **Red/Yellow**: Positive activations (condition > baseline/comparison)
- **Blue**: Negative activations (deactivations)
- **Color intensity**: Strength of effect (T-value)

**F-test Maps:**
- **Warm colors**: Regions with significant effects
- **No direction**: F-tests don't show direction, only presence of effects

### Expected Brain Regions:

Based on speech perception literature, expect activations in:

1. **Primary Auditory Cortex** (Heschl's gyrus)
2. **Superior Temporal Gyrus** (STG)
3. **Middle Temporal Gyrus** (MTG) - language processing
4. **Inferior Frontal Gyrus** (IFG) - language production/comprehension
5. **Angular Gyrus** - semantic processing
6. **Supramarginal Gyrus** - phonological processing

## 📊 Results Interpretation

### T-test Results

**Positive Values (Red/Yellow):**
- Indicate activation (condition shows higher signal than comparison)
- Example: Words > Baseline shows where words activate more than white noise

**Negative Values (Blue):**
- Indicate deactivation (condition shows lower signal than comparison)
- Often seen in default mode network areas

**Magnitude:**
- Higher T-values = stronger effects
- Typical threshold: p < 0.001 (uncorrected)
- For publication: use FWE or FDR correction

### F-test Results

**High F-values:**
- Indicate significant effects are present
- Doesn't tell you direction - use t-tests for that

**All Conditions F-test:**
- Shows regions activated by ANY task condition
- Good for overall task effect

**Condition Differences F-test:**
- Shows regions that respond differently to conditions
- Useful for finding language-specific areas

## 🔍 Multiple Comparisons Correction

### Correction Methods:

1. **Uncorrected** (default: p < 0.001)
   - Liberal, may have false positives
   - Good for exploratory analysis

2. **FWE Correction** (Family-Wise Error)
   - Conservative, controls overall error rate
   - Recommended for publication

3. **FDR Correction** (False Discovery Rate)
   - Moderate, controls expected false positives
   - Good balance

4. **Cluster-Level Inference**
   - Corrects for multiple clusters
   - Less conservative than voxel-level

### Apply Correction in SPM:
- Results GUI → Set contrasts → Choose correction method

## 📁 Output Files

### First-Level (per subject):
```
sub-*/spm/first_level/
├── SPM.mat              # GLM specification
├── beta_*.nii           # Parameter estimates
├── con_0001.nii         # Words > Baseline contrast
├── con_0002.nii         # Sentences > Baseline
├── con_0003.nii         # Reversed > Baseline
├── con_0004.nii         # Words > Reversed
├── con_0005.nii         # Sentences > Reversed
├── con_0006.nii         # (Words+Sentences) > Reversed
├── con_0007.nii         # Words > Sentences
├── spmT_0001.nii        # T-statistics
├── ...
├── spmF_0001.nii        # All Conditions F-test
└── spmF_0002.nii        # Condition Differences F-test
```

### Second-Level (group):
```
spm/second_level/
├── Words_Baseline/SPM.mat
├── Sentences_Baseline/SPM.mat
└── Reversed_Baseline/SPM.mat
```

## 🚀 Quick Start Commands

```matlab
% Complete workflow
cd matlab
start_matlab_spm
run_glm_tests
show_glm_results('01', 1)  % View first result
```

## 📝 Notes

- **Preprocessing Required**: Data must be preprocessed before GLM
- **Processing Time**: First-level GLM takes ~5-10 min per subject
- **Storage**: Each subject's results ~50-100 MB
- **Group Analysis**: Run after all first-level analyses complete

## 📚 References

- SPM Manual: https://www.fil.ion.ucl.ac.uk/spm/doc/
- Speech perception networks: Hickok & Poeppel (2007)
- GLM methodology: Friston et al. (1995)

---

*Generated for ds004302: Speech perception in schizophrenia dataset*

