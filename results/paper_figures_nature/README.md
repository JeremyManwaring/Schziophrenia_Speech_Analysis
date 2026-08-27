# Editorial Neuroscience Figure Package

This directory contains the publication-ready redesign of the complete figure
set. The visual language is inspired by the restraint and hierarchy of
high-impact neuroscience publishing without reproducing any specific journal
template or published figure.

Regenerate every file with:

    python code/python/paper_visualizations_nature.py

## Deliverables

Each figure is exported at an exact 7.2-inch page width as a 600 dpi PNG,
editable SVG, and vector PDF.

- `Figure_1_core_results` — adjusted post hoc ANCOVA effects and the primary
  symptom association are the focal results; L MTG and L STS raw distributions
  are coordinated in one supporting panel with violins, compact boxes, and all
  participant values.
- `Figure_2_effect_size_landscape` — the complete 12 ROI by 7 contrast Cohen's
  d matrix with a centered coral-to-navy scale and all exact cell values.
- `Figure_3_ROI_definitions` — full-width glass-brain views plus separate,
  compact left- and right-hemisphere coordinate tables.
- `Supplement_Figure_1_whole_brain_inference` — three descriptive whole-brain
  t maps sharing one horizontal color scale and the stored FWER result.
- `Supplement_Figure_2_MVPA` — stored accuracy, ROC AUC, permutation p values,
  chance reference, sample size, and cross-validation caveat.
- `Supplement_Figure_3_sample_and_QC` — participant-level age, IQ, motion,
  cohort, and sex summaries with observed sample sizes.
- `Supplement_Figure_4_exploratory_network` — uncorrected connectivity
  differences and the ten largest absolute laterality effects.

## Scientific fidelity

- Figures read stored records from `results/data/`; generation does not rerun
  or modify any statistical model.
- No observations, labels, group names, ROI names, contrasts, sample sizes, or
  statistical values are synthesized.
- Participant jitter is deterministic and changes horizontal position only.
- HC, AVH-, and AVH+ are redundantly encoded with color and marker shape.
- Negative AVH- versus AVH+ effects are coral and indicate higher activation
  in AVH+; positive effects are blue and indicate higher activation in AVH-.
- No omnibus ROI test survives within-contrast FDR, no whole-brain cluster
  survives maximum-cluster-size FWER p < .05, connectivity findings remain
  uncorrected, and the stored MVPA permutation caveat remains visible.

## Shared design system

- Helvetica Neue/Helvetica sans-serif typography
- Deep navy, muted blue, soft teal, muted coral, warm gray, and pale cool gray
- White background, hairline rules, low-contrast gridlines, and precise axes
- Short titles with methodological detail moved to compact subtitles and notes
- No shadows, 3D styling, glossy effects, decorative gradients, or heavy boxes

Source files:

- `code/python/nature_figure_style.py`
- `code/python/paper_visualizations_nature.py`
