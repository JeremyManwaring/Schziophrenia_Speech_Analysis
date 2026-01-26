# Advanced Analysis Visualizations: AVH- vs AVH+

This folder contains comprehensive visualizations from advanced analyses comparing schizophrenia patients **without** auditory hallucinations (AVH-) to those **with** auditory hallucinations (AVH+).

---

## Folder Structure

### 01_cluster_corrected/
**Whole-Brain Statistical Maps with Cluster Correction**

Permutation-based cluster analysis showing brain regions with different activation patterns between AVH- and AVH+ groups.

| File Type | Description |
|-----------|-------------|
| `*_glass_brain_corrected.png` | 3D glass brain visualizations |
| `*_axial_slices.png` | Axial slice montages |
| `*_sagittal_temporal.png` | Sagittal views of temporal regions |
| `*_zstat_uncorrected.nii.gz` | Z-statistic maps |

---

### 02_raincloud_plots/
**Publication-Quality Distribution Visualizations**

Raincloud plots showing individual data points, distributions, and group means for ROI activations.

| File Type | Description |
|-----------|-------------|
| `*_all_rois_raincloud.png/svg` | All ROIs for each contrast |
| `*_[ROI]_raincloud.png` | Individual ROI detail plots |
| `key_findings_summary.png/svg` | Summary of main findings |

**Key**: Gray = HC, Blue = AVH-, Red = AVH+

---

### 03_mvpa_classification/
**Machine Learning Classification Results**

SVM classification testing if brain activation patterns can distinguish AVH- from AVH+.

| File Type | Description |
|-----------|-------------|
| `classification_accuracy.png/svg` | Accuracy bar plot |
| `confusion_matrices.png` | Classification confusion matrices |
| `permutation_distributions.png` | Permutation test null distributions |
| `*_svm_weights_glass.png` | Discriminative brain regions |
| `*_svm_weights.nii.gz` | NIfTI weight maps |

---

### 04_connectivity/
**Functional Connectivity Analysis**

ROI-to-ROI correlation analysis comparing network connectivity between groups.

| File Type | Description |
|-----------|-------------|
| `connectivity_matrix_AVH-.png` | AVH- group connectivity |
| `connectivity_matrix_AVH+.png` | AVH+ group connectivity |
| `connectivity_difference.png` | Difference with significance |
| `network_differences.png` | 3D network visualization |
| `significant_connections.csv` | Table of significant differences |

---

### 05_laterality/
**Hemisphere Dominance Analysis**

Laterality indices comparing left vs right hemisphere activation between groups.

| File Type | Description |
|-----------|-------------|
| `*_laterality_barplot.png/svg` | LI by group for each contrast |
| `laterality_heatmap.png/svg` | Summary across all contrasts |
| `laterality_effect_sizes.png` | Cohen's d for group comparisons |
| `laterality_stats.csv` | Statistical test results |

**Interpretation**: LI > 0 = Left dominant, LI < 0 = Right dominant

---

## Key Findings

### 1. ROI Differences (Raincloud Plots)
- **L_MTG** and **L_STS** show large effect sizes (Cohen's d > 0.8) between AVH- and AVH+
- Most prominent in `sentences_vs_reversed` contrast

### 2. Classification (MVPA)
- Best accuracy: **60%** for `words_vs_reversed` contrast
- Classification not significantly above chance (p > 0.05)
- Suggests distributed rather than focal differences

### 3. Connectivity
- **2 significant connections** differ between groups (p < 0.05 uncorrected)
- Check `significant_connections.csv` for details

### 4. Laterality
- No significant laterality differences between groups
- Both groups show similar hemisphere dominance patterns

---

## Analysis Details

| Analysis | Method | Subjects |
|----------|--------|----------|
| Cluster | Permutation test (1000 perm) | 40 (20 AVH-, 20 AVH+) |
| MVPA | Linear SVM, LOO-CV | 40 (20 AVH-, 20 AVH+) |
| Connectivity | Pearson correlation, Fisher z | 46 (23 AVH-, 23 AVH+) |
| Laterality | LI = (L-R)/(|L|+|R|) | 71 (all subjects) |

---

## How to Use These Files

### For Publication
Use `.svg` files for vector graphics (scalable, editable)
Use `.png` files at 150 DPI for raster graphics

### For Further Analysis
- `.nii.gz` files can be opened in FSLeyes, MRIcroGL, or nilearn
- `.npy` files contain numpy arrays (load with `np.load()`)
- `.csv` files contain tabular data for statistical software

### For Presentations
The `key_findings_summary.png` provides an overview of main ROI results

---

*Generated: January 22, 2026*
*Dataset: ds004302 - Speech Perception in Schizophrenia*
