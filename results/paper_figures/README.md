# Manuscript Figure Package

Generate the seven manuscript figures from `results/data/` with:

```bash
python code/python/paper_visualizations.py
```

Each of the seven figures is exported at 7.2-inch width as a 600 dpi PNG, an
editable SVG, and a PDF. Participant jitter is deterministic.

## Main figures

- `Figure_1_core_results`: post hoc adjusted effects, the primary symptom
  association, and participant-level L MTG/L STS values.
- `Figure_2_effect_size_landscape`: all 12 ROI by 7 contrast AVH- versus AVH+
  effect sizes with exact cell labels.
- `Figure_3_ROI_definitions`: MNI-space ROI locations, coordinates, and radii.

## Supplementary figures

- `Supplement_Figure_1_whole_brain_inference`: descriptive t maps and the
  stored 10,000-permutation FWER result.
- `Supplement_Figure_2_MVPA`: historical accuracy, ROC AUC, sample size,
  cross-validation design, and 100-permutation caveat.
- `Supplement_Figure_3_sample_and_QC`: age, IQ, motion, cohort, and sex.
- `Supplement_Figure_4_exploratory_network`: uncorrected connectivity and
  laterality effects with their limitations visible.

## Plot conventions

- Panels display the observations and statistics in `results/data/`.
- Negative AVH- minus AVH+ effects indicate higher activation in AVH+;
  positive effects indicate higher activation in AVH-.
- Color is paired with marker shape or direct labels where group identity is
  important.
- Distribution panels show individual participant values.
- Labels identify corrected, post hoc, historical, and exploratory results.

Sources: `code/python/paper_visualizations.py` and
`code/python/paper_figure_style.py`.
