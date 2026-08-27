# Redesigned Paper Figures

Publication-ready redesign of the complete manuscript figure set. The source
figures in `results/paper_figures/` are preserved unchanged. Regenerate this
set with:

    python code/python/paper_visualizations_neuron.py

## Deliverables

- `Figure_1_core_results` - post hoc adjusted ANCOVA effects, the primary
  age/IQ-residualized PSYRATS association, and raw participant-level activation
  distributions.
- `Figure_2_effect_size_landscape` - ROI by contrast Cohen's d matrix for
  AVH- versus AVH+; no omnibus ROI test survives within-contrast FDR.
- `Figure_3_ROI_definitions` - glass-brain ROI locations and the complete MNI
  coordinate/radius table.
- `Supplement_Figure_1_whole_brain_inference` - descriptive whole-brain t maps
  and the null maximum-cluster-size FWER result.
- `Supplement_Figure_2_MVPA` - stored cross-validated accuracy, ROC AUC,
  permutation p values, chance reference, sample size, and CV caveat.
- `Supplement_Figure_3_sample_and_QC` - participant-level age, IQ, motion,
  cohort, and sex summaries with observed sample sizes.
- `Supplement_Figure_4_exploratory_network` - uncorrected connectivity
  differences and the ten largest absolute laterality effects.

Each figure is exported as an exact 7.2-inch-wide 600 dpi PNG, editable SVG,
and vector PDF.

## Scientific fidelity

- Statistical values are read from the stored records in `results/data/`;
  figure generation does not rerun or modify any model.
- HC, AVH-, and AVH+ use neutral gray, muted scientific blue, and muted
  vermillion. Participant points also use circle, square, and triangle markers
  so group identity remains legible in grayscale.
- Signed AVH- versus AVH+ effects use a vermillion-neutral-blue diverging scale:
  negative values indicate higher activation in AVH+, and positive values
  indicate higher activation in AVH-.
- Raw participant-level points are deterministic, semi-transparent, and
  subordinate to box summaries. Jitter changes x position only and never data.
- Targeted L MTG and L STS ANCOVA results are explicitly labeled post hoc.
- Whole-brain maps remain descriptive: two-sided voxel p < .001, 10,000
  permutations, n = 45 (AVH- = 22, AVH+ = 23), covariates age/IQ/sex, and no
  cluster surviving maximum-cluster-size FWER p < .05.
- MVPA results remain the stored shuffled five-fold KFold analysis
  (`random_state = 42`) with 100 permutations; the figure retains the warning
  to increase permutations before confirmatory use.
- Connectivity results remain uncorrected and none survives FDR; no laterality
  comparison reaches p < .05.
- ROI spheres may overlap, so overlapping ROI means are not statistically
  independent.

## Source-study context retained from the project README

- Dataset: Soler-Vidal et al. (2022), *Brain correlates of speech perception
  in schizophrenia patients with and without auditory hallucinations*.
- Cohort: 71 participants - HC = 25, AVH- = 23, AVH+ = 23.
- Task: block-design speech perception with word lists, sentence lists,
  reversed speech, and a white-noise baseline.
- The first five volumes (10 seconds) were discarded before analysis, although
  the complete sequence remains in the dataset. Event timing begins with the
  first acquired volume after that discard.
- White-noise periods appear in the event files but were not modeled in the
  original publication and therefore served as an implicit baseline.

## Stored statistical methods and caveats

- ROI omnibus tests use Welch's one-way ANOVA with the weighted between-group
  term divided by `k - 1`, Welch denominator/denominator degrees of freedom,
  and F survival-function p values.
- Each ROI includes all three genuine Games-Howell group comparisons, with
  Welch-Satterthwaite degrees of freedom and the studentized-range distribution.
- Benjamini-Hochberg FDR is applied within each contrast across its 12 ROI
  omnibus tests.
- AVH+ partial correlations control age and IQ and use `df = n - k - 2`; all
  stored rows have n = 23 and df = 19. Each FDR family is the 12 ROIs within a
  contrast.
- The targeted L MTG/L STS ANCOVA is post hoc. Complete-case labels are
  `full_n69` and `motion_clean_n65`; the corresponding source cohorts contain
  71 and 67 participants.
- Whole-brain AVH- versus AVH+ inference uses 10,000 permutations, two-sided
  tests, voxelwise cluster-forming p < .001, maximum-cluster-size FWER p < .05,
  and random seed 20260824. Complete covariates give n = 45 (AVH- = 22,
  AVH+ = 23); sub-28 is excluded for missing IQ.
- Stored MVPA uses shuffled five-fold `KFold` cross-validation with
  `random_state = 42`.

## ROI overlap and corrected-result record

- Ten cortical spheres use an 8 mm radius; bilateral Heschl's gyri use 6 mm.
- Three sphere pairs intentionally share voxels and are not independent:
  L posterior STG-L STS center distance = 10.198 mm; L MTG-L STS = 8.246 mm;
  L IFG triangularis-L IFG opercularis = 14.967 mm.
- No ROI omnibus test survives within-contrast FDR. For Sentences vs Reversed,
  the smallest values are L STS (raw p = .0104, q = .0995) and L MTG
  (raw p = .0166, q = .0995).
- The post hoc targeted ANCOVA survives Bonferroni correction over L MTG and
  L STS in both complete-case models: full n = 69 (adjusted d = -.90 and -.84)
  and motion-clean n = 65 (adjusted d = -.87 and -.82). These results are not
  presented as a priori.
- In AVH+ participants, Speech vs Reversed activation in right posterior STG
  correlates with PSYRATS after controlling age and IQ: partial r = .647,
  p = .00152, within-contrast q = .0182, n = 23, df = 19.
- No cluster survives the valid 10,000-permutation cluster-size FWER analysis
  in any of the three tested contrasts.
- Historical MVPA accuracy remains .425-.500, with all permutation p >= .347,
  using shuffled five-fold KFold cross-validation.

Dataset DOI: `10.18112/openneuro.ds004302.v1.0.1`. Study DOI:
`10.1371/journal.pone.0276975`.

## Shared visual system

- Typeface: Arial with Helvetica and DejaVu Sans fallbacks.
- Group colors: HC `#7C8084`, AVH- `#3F7096`, AVH+ `#C45B45`.
- Quiet charcoal axes, subtle gray gridlines, white background, no shadows,
  decorative gradients, or unnecessary borders.
- Comparable panels share marker size, line weight, confidence-band opacity,
  and annotation treatment.
