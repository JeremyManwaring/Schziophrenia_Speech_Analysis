# Laterality Index Analysis: AVH- vs AVH+

## Overview
Laterality indices were computed to assess hemisphere dominance for speech
processing in schizophrenia patients with and without auditory hallucinations.

## Method
Laterality Index (LI) = (Left - Right) / (|Left| + |Right|)

- LI > 0: Left hemisphere dominant
- LI < 0: Right hemisphere dominant
- LI ≈ 0: Bilateral/symmetric

## ROI Pairs Analyzed
- STG_posterior: L_STG_posterior vs R_STG_posterior
- STG_anterior: L_STG_anterior vs R_STG_anterior
- MTG: L_MTG vs R_MTG
- Heschl: L_Heschl vs R_Heschl
- IFG: L_IFG_opercularis vs R_IFG

## Contrasts Analyzed
- sentences_vs_reversed (speech comprehension)
- speech_vs_reversed (overall speech processing)
- words_vs_sentences
- words_vs_reversed

## Results
- 0 significant laterality differences between AVH- and AVH+ (p < 0.05)

## Files
- `*_laterality_barplot.png/svg` - Bar plots for each contrast
- `laterality_heatmap.png/svg` - Summary heatmap
- `laterality_effect_sizes.png` - Cohen's d for group comparisons
- `laterality_stats.csv` - Statistical test results
- `laterality_all_results.csv` - Complete results table

## Interpretation
Differences in laterality between AVH- and AVH+ may indicate:
- Altered language network organization
- Compensatory hemisphere recruitment
- Disrupted interhemispheric processing
