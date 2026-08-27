"""
Publication-ready figures for the manuscript.

Builds a compact manuscript figure set into `results/paper_figures/`.
Every figure is exported as a 600 dpi PNG plus vector PDF and SVG:

- figure1_main_results.png : post hoc ANCOVA forest + targeted-ROI rainclouds
  (sentences > reversed) + the primary symptom correlation.
- effect_size_heatmap.png  : ROI x contrast Cohen's d (AVH- vs AVH+) heatmap with
  FDR-significant omnibus cells boxed.
- roi_definition_panel.png : the upgraded ROI glass-brain map + a compact
  ROI/MNI coordinate reference table.

All statistics are read from the consolidated outputs in `results/data/`.

Usage:
    python code/python/paper_visualizations.py
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from nilearn.image import load_img
from nilearn.plotting import plot_glass_brain

sys.path.insert(0, str(Path(__file__).parent))
from poster_style import (  # noqa: E402
    GROUP_ORDER,
    GRID_COLOR,
    INK,
    MUTED_INK,
    NEGATIVE_COLOR,
    OUTLINE_COLOR,
    PALETTE,
    PAPER_DPI,
    apply_style,
    format_contrast,
    format_roi,
    style_axis,
)
from surface_brain_plots import ROI_RADII, ROIS, _roi_display  # noqa: E402

warnings.filterwarnings("ignore")
apply_style()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "results" / "data"
POSTER_DIR = BASE_DIR / "results" / "poster"
PAPER_DIR = BASE_DIR / "results" / "paper_figures"
BRAIN_DIR = POSTER_DIR / "01_brain_maps"
PARTICIPANTS = BASE_DIR / "participants.tsv"

ROI_DIR = DATA_DIR / "roi_values"
EFFECT_DIR = DATA_DIR / "effect_sizes"
CORR_DIR = DATA_DIR / "correlations"
POSTHOC_DIR = DATA_DIR / "posthoc"

TARGET_CONTRAST = "sentences_vs_reversed"
TARGET_ROIS = ["L_MTG", "L_STS"]

ROI_ORDER = [
    "L_STG_posterior", "L_STG_anterior", "L_Heschl",
    "L_MTG", "L_STS", "L_IFG_triangularis", "L_IFG_opercularis",
    "R_STG_posterior", "R_STG_anterior", "R_Heschl",
    "R_MTG", "R_IFG",
]

CONTRAST_ORDER = [
    "sentences_vs_reversed", "words_vs_sentences", "speech_vs_reversed",
    "words_vs_reversed", "words_vs_baseline", "sentences_vs_baseline",
    "reversed_vs_baseline",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _save(fig, path: Path) -> None:
    """Export a journal-width raster plus editable vector copies."""
    path.parent.mkdir(parents=True, exist_ok=True)
    stem = path.with_suffix("")
    fig.savefig(stem.with_suffix(".png"), dpi=PAPER_DPI, bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _residualize(values: np.ndarray, covariates: np.ndarray) -> np.ndarray:
    """Return residuals after OLS adjustment for the supplied covariates."""
    values = np.asarray(values, dtype=float)
    covariates = np.asarray(covariates, dtype=float)
    design = np.column_stack([np.ones(len(values)), covariates])
    beta = np.linalg.lstsq(design, values, rcond=None)[0]
    return values - design @ beta


def _load_participants() -> pd.DataFrame:
    df = pd.read_csv(PARTICIPANTS, sep="\t")
    for col in ("age", "iq", "psyrats"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["group"] = pd.Categorical(df["group"], categories=GROUP_ORDER, ordered=True)
    return df


def _primary_correlation_hit() -> dict | None:
    """Top PSYRATS partial correlation surviving within-contrast FDR (< 0.05)."""
    path = CORR_DIR / "correlation_summary.json"
    if not path.exists():
        return None
    with open(path) as f:
        summary = json.load(f)
    best = None
    for contrast, blk in summary.items():
        raw = {r["roi"]: r for r in blk.get("correlations", [])}
        for pc in blk.get("partial_correlations", []):
            fdr = pc.get("partial_p_fdr_within_contrast")
            if fdr is None or fdr >= 0.05:
                continue
            rr = raw.get(pc["roi"], {})
            cand = {
                "contrast": contrast, "roi": pc["roi"],
                "partial_r": pc["partial_r"], "partial_p": pc["partial_p"],
                "partial_fdr": fdr, "raw_r": rr.get("pearson_r", float("nan")),
            }
            if best is None or fdr < best["partial_fdr"]:
                best = cand
    return best


def _omnibus_fdr_sig_cells() -> set[tuple[str, str]]:
    cells: set[tuple[str, str]] = set()
    for path in ROI_DIR.glob("*_roi_anova.csv"):
        contrast = path.name.replace("_roi_anova.csv", "")
        df = pd.read_csv(path)
        if "p_fdr" not in df.columns:
            continue
        for _, r in df[df["p_fdr"] < 0.05].iterrows():
            cells.add((contrast, r["roi"]))
    return cells


# ===========================================================================
# Figure 1: main results
# ===========================================================================
def figure1_main_results() -> None:
    parts = _load_participants()

    fig = plt.figure(figsize=(7.2, 6.35))
    gs = fig.add_gridspec(
        2, 2, hspace=0.52, wspace=0.34,
        left=0.09, right=0.985, top=0.96, bottom=0.095,
    )

    # (A) Targeted post hoc forest --------------------------------------------
    ax = fig.add_subplot(gs[0, 0])
    posthoc_path = POSTHOC_DIR / "posthoc_targeted.csv"
    if posthoc_path.exists():
        posthoc = pd.read_csv(posthoc_path)
        full = posthoc[posthoc["sample"].str.startswith("full")].copy()
        full["roi"] = pd.Categorical(full["roi"], categories=TARGET_ROIS, ordered=True)
        full = full.sort_values("roi")
        y = np.arange(len(full))
        ax.errorbar(
            full["d_adj"], y,
            xerr=[full["d_adj"] - full["d_adj_ci_lo"], full["d_adj_ci_hi"] - full["d_adj"]],
            fmt="none", ecolor=MUTED_INK, capsize=3, lw=1.0,
        )
        ax.scatter(
            full["d_adj"], y, c=NEGATIVE_COLOR, s=46,
            edgecolor=OUTLINE_COLOR, linewidth=0.7, zorder=5,
        )
        ax.axvline(0, color=OUTLINE_COLOR, lw=0.8, ls=(0, (3, 2)))
        ax.set_yticks(y)
        ax.set_yticklabels([format_roi(r) for r in full["roi"]])
        for yi, (d, p) in enumerate(zip(full["d_adj"], full["p_bonferroni"])):
            ax.annotate(
                f"d = {d:+.2f}; pBonf = {p:.3f}",
                (d, yi), textcoords="offset points", xytext=(0, 8),
                ha="center", va="bottom", fontsize=7.2,
            )
        ax.set_ylim(len(full) - 0.45, -0.55)
        ax.set_xlim(min(full["d_adj_ci_lo"].min(), -0.2) - 0.12, 0.22)
    ax.set_xlabel("Adjusted Cohen's d (AVH\N{MINUS SIGN} vs AVH+)")
    ax.set_title(
        "A  Adjusted group contrast\nPost hoc ANCOVA; sentences > reversed",
        loc="left", pad=7,
    )
    style_axis(ax, grid_axis="x")

    # (B) Primary symptom correlation -----------------------------------------
    ax = fig.add_subplot(gs[0, 1])
    hit = _primary_correlation_hit()
    avh = parts[parts["group"] == "AVH+"].dropna(subset=["psyrats", "age", "iq"])
    if hit is not None and not avh.empty:
        roi_path = ROI_DIR / f"{hit['contrast']}_roi_values.csv"
        if roi_path.exists():
            merged = pd.read_csv(roi_path).merge(
                avh[["participant_id", "psyrats", "age", "iq"]],
                left_on="subject_id", right_on="participant_id", how="inner")
            if hit["roi"] in merged.columns:
                x = merged[hit["roi"]].to_numpy(dtype=float)
                yv = merged["psyrats"].to_numpy(dtype=float)
                cov = merged[["age", "iq"]].to_numpy(dtype=float)
                m = np.isfinite(x) & np.isfinite(yv) & np.all(np.isfinite(cov), axis=1)
                x_res = _residualize(x[m], cov[m])
                y_res = _residualize(yv[m], cov[m])
                sns.regplot(
                    x=x_res, y=y_res, ax=ax, color=PALETTE["AVH+"], truncate=False,
                    scatter_kws=dict(s=25, edgecolor=OUTLINE_COLOR, linewidths=0.55, alpha=0.88),
                    line_kws=dict(color=OUTLINE_COLOR, lw=1.2),
                )
                ax.axhline(0, color=GRID_COLOR, lw=0.7, zorder=0)
                ax.axvline(0, color=GRID_COLOR, lw=0.7, zorder=0)
                ax.text(0.04, 0.96,
                        f"partial r = {hit['partial_r']:+.2f}\n"
                        f"p = {hit['partial_p']:.4f}; q = {hit['partial_fdr']:.3f}; n = {m.sum()}",
                        transform=ax.transAxes, va="top", ha="left", fontsize=7.4,
                        bbox=dict(boxstyle="round,pad=0.30", facecolor="white",
                                  edgecolor=PALETTE["AVH+"], linewidth=0.8, alpha=0.94))
        ax.set_xlabel("Activation residual (β)")
        ax.set_ylabel("PSYRATS residual")
        ax.set_title(
            f"B  Symptom association in AVH+\n{format_roi(hit['roi'])}; {format_contrast(hit['contrast'])}",
            loc="left", pad=7,
        )
        style_axis(ax, grid_axis=None)

    # (C, D) Targeted-ROI rainclouds (sentences > reversed) -------------------
    roi_path = ROI_DIR / f"{TARGET_CONTRAST}_roi_values.csv"
    roi_df = pd.read_csv(roi_path) if roi_path.exists() else None
    panel_axes = [fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])]
    panel_tags = ["C", "D"]
    for ax, roi, tag in zip(panel_axes, TARGET_ROIS, panel_tags):
        if roi_df is None or roi not in roi_df.columns:
            ax.axis("off")
            continue
        sub = roi_df[["group", roi]].copy()
        sub["group"] = pd.Categorical(sub["group"], categories=GROUP_ORDER, ordered=True)
        sub = sub.dropna()
        sns.violinplot(data=sub, x="group", y=roi, hue="group", order=GROUP_ORDER,
                       palette=PALETTE, inner=None, cut=0, linewidth=0.8,
                       saturation=0.9, legend=False, ax=ax)
        for c in ax.collections:
            c.set_alpha(0.32)
        sns.boxplot(data=sub, x="group", y=roi, order=GROUP_ORDER, width=0.18,
                    showcaps=True,
                    boxprops={"facecolor": "white", "edgecolor": OUTLINE_COLOR, "zorder": 5},
                    whiskerprops={"color": OUTLINE_COLOR, "linewidth": 0.8},
                    capprops={"color": OUTLINE_COLOR, "linewidth": 0.8},
                    showfliers=False,
                    medianprops={"color": OUTLINE_COLOR, "linewidth": 1.0}, ax=ax)
        sns.stripplot(data=sub, x="group", y=roi, hue="group", order=GROUP_ORDER,
                      palette=PALETTE, size=2.7, alpha=0.80, jitter=0.16, legend=False,
                      edgecolor="white", linewidth=0.25, ax=ax)
        ax.axhline(0, color=MUTED_INK, lw=0.7, ls=(0, (3, 2)))
        ax.set_xlabel("")
        ax.set_ylabel("Activation (β)")
        group_counts = sub.groupby("group", observed=True).size().reindex(GROUP_ORDER)
        ax.set_xticklabels([f"{g}\n(n = {int(group_counts[g])})" for g in GROUP_ORDER])
        ax.set_title(
            f"{tag}  Raw activation distribution\n{format_roi(roi)}; {format_contrast(TARGET_CONTRAST)}",
            loc="left", pad=7,
        )
        style_axis(ax, grid_axis="y")

    fig.text(
        0.09, 0.018,
        "A: covariate-adjusted effects (age, IQ, sex, mean FD). B: age- and IQ-residualized values. "
        "C-D: unadjusted subject-level distributions.",
        ha="left", va="bottom", fontsize=6.7, color=MUTED_INK,
    )
    _save(fig, PAPER_DIR / "Figure_1_core_results.png")
    print(f"  figure1 -> {PAPER_DIR / 'Figure_1_core_results.png'}")


# ===========================================================================
# Effect-size heatmap (ROI x contrast)
# ===========================================================================
def effect_size_heatmap() -> None:
    es_path = EFFECT_DIR / "effect_sizes_summary.csv"
    if not es_path.exists():
        return
    es = pd.read_csv(es_path)
    es = es[es["comparison"] == "AVH-_vs_AVH+"]
    pivot = es.pivot_table(index="roi", columns="contrast", values="cohens_d")
    rois = [r for r in ROI_ORDER if r in pivot.index]
    contrasts = [c for c in CONTRAST_ORDER if c in pivot.columns]
    pivot = pivot.reindex(index=rois, columns=contrasts)

    fig, ax = plt.subplots(figsize=(7.2, 4.85))
    vmax = max(1.0, float(np.nanmax(np.abs(pivot.to_numpy()))))
    cmap = sns.diverging_palette(245, 25, s=82, l=52, center="light", as_cmap=True)
    sns.heatmap(
        pivot, ax=ax, cmap=cmap, center=0, vmin=-vmax, vmax=vmax,
        annot=True, fmt=".2f", annot_kws={"fontsize": 6.5},
        linewidths=0.45, linecolor="white",
        cbar_kws={"label": "Cohen's d (AVH\N{MINUS SIGN} vs AVH+)", "shrink": 0.86},
        xticklabels=[format_contrast(c) for c in contrasts],
        yticklabels=[format_roi(r) for r in rois],
    )

    # Box the omnibus FDR-significant cells
    sig_cells = _omnibus_fdr_sig_cells()
    for (contrast, roi) in sig_cells:
        if roi in rois and contrast in contrasts:
            ci, ri = contrasts.index(contrast), rois.index(roi)
            ax.add_patch(Rectangle((ci, ri), 1, 1, fill=False,
                                   edgecolor="black", lw=2.6, zorder=6))
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title(
        "ROI effect-size landscape\nPairwise standardized differences across task contrasts",
        loc="left", pad=8,
    )
    plt.setp(ax.get_xticklabels(), rotation=32, ha="right", rotation_mode="anchor")
    plt.setp(ax.get_yticklabels(), rotation=0)
    sig_note = (
        "Outlined cells survive omnibus within-contrast FDR."
        if sig_cells else
        "No omnibus ROI test survives within-contrast FDR."
    )
    fig.text(
        0.02, 0.01,
        "Negative values indicate higher activation in AVH+. " + sig_note,
        ha="left", va="bottom", fontsize=6.8, color=MUTED_INK,
    )
    fig.subplots_adjust(left=0.20, right=0.93, top=0.88, bottom=0.27)
    _save(fig, PAPER_DIR / "Figure_2_effect_size_landscape.png")
    print(f"  heatmap -> {PAPER_DIR / 'Figure_2_effect_size_landscape.png'}")


# ===========================================================================
# ROI definition panel (map + coordinate table)
# ===========================================================================
def roi_definition_panel() -> None:
    fig = plt.figure(figsize=(7.2, 3.15))
    gs = fig.add_gridspec(
        1, 2, width_ratios=[1.35, 1.0], wspace=0.12,
        left=0.02, right=0.99, top=0.88, bottom=0.11,
    )

    ax_map = fig.add_subplot(gs[0, 0])
    display = plot_glass_brain(
        None, display_mode="lyrz", figure=fig, axes=ax_map,
        annotate=True, black_bg=False,
    )
    hemisphere_colors = {"L_": NEGATIVE_COLOR, "R_": "#E69F00"}
    for hemisphere, color in hemisphere_colors.items():
        for radius, size in ((8, 46), (6, 28)):
            coords = [
                coord for key, coord in ROIS.items()
                if key.startswith(hemisphere) and ROI_RADII[key] == radius
            ]
            if coords:
                display.add_markers(
                    coords, marker_color=color, marker_size=size,
                    edgecolor=OUTLINE_COLOR, alpha=0.92,
                )
    ax_map.set_title("A  ROI locations", loc="left", pad=7)
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=NEGATIVE_COLOR,
               markeredgecolor=OUTLINE_COLOR, markersize=5.5, label="Left hemisphere"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#E69F00",
               markeredgecolor=OUTLINE_COLOR, markersize=5.5, label="Right hemisphere"),
        Line2D([0], [0], marker="o", color=MUTED_INK, markerfacecolor="white",
               markersize=5.5, label="8 mm sphere"),
        Line2D([0], [0], marker="o", color=MUTED_INK, markerfacecolor="white",
               markersize=3.8, label="6 mm Heschl sphere"),
    ]
    ax_map.legend(
        handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.10),
        ncol=2, columnspacing=0.9, handletextpad=0.35,
    )

    ax_tbl = fig.add_subplot(gs[0, 1])
    ax_tbl.axis("off")
    ax_tbl.set_title("B  ROI definitions (MNI)", loc="left", pad=7)
    rows = []
    for key, (x, y, z) in ROIS.items():
        rows.append([
            _roi_display(key),
            f"{x:>4.0f}, {y:>4.0f}, {z:>4.0f}",
            f"{ROI_RADII[key]} mm",
        ])
    table = ax_tbl.table(
        cellText=rows,
        colLabels=["ROI", "MNI (x, y, z)", "Radius"],
        colWidths=[0.49, 0.34, 0.17], cellLoc="left", loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(6.4)
    table.scale(1, 1.08)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor(GRID_COLOR)
        cell.set_linewidth(0.45)
        cell.PAD = 0.08
        if r == 0:
            cell.set_facecolor("#E9EDF2")
            cell.set_text_props(color=INK, fontweight="semibold")
        elif r % 2 == 0:
            cell.set_facecolor("#F8F9FA")

    fig.text(
        0.02, 0.012,
        "Spheres may overlap; overlapping ROI means are therefore not statistically independent.",
        ha="left", va="bottom", fontsize=6.7, color=MUTED_INK,
    )
    _save(fig, PAPER_DIR / "Figure_3_ROI_definitions.png")
    print(f"  roi definition -> {PAPER_DIR / 'Figure_3_ROI_definitions.png'}")


# ===========================================================================
# Supplementary figure 1: whole-brain descriptive maps
# ===========================================================================
def supplement_whole_brain_inference() -> None:
    cluster_dir = DATA_DIR / "cluster_maps"
    meta_path = cluster_dir / "analysis_summary.json"
    if not meta_path.exists():
        return
    with open(meta_path) as f:
        meta = json.load(f)

    contrasts = ["sentences_vs_reversed", "speech_vs_reversed", "words_vs_sentences"]
    maps: list[tuple[str, object]] = []
    vmax = 0.0
    for contrast in contrasts:
        path = cluster_dir / f"{contrast}_AVH-_vs_AVH+_tstat.nii.gz"
        if not path.exists():
            continue
        img = load_img(str(path))
        values = np.asarray(img.get_fdata(), dtype=float)
        finite = np.abs(values[np.isfinite(values)])
        if finite.size:
            vmax = max(vmax, float(np.nanmax(finite)))
        maps.append((contrast, img))
    if not maps:
        return

    vmax = max(4.0, min(vmax, 6.0))
    fig = plt.figure(figsize=(7.2, 2.25))
    gs = fig.add_gridspec(
        1, len(maps), wspace=0.07,
        left=0.01, right=0.99, top=0.84, bottom=0.20,
    )
    for idx, (contrast, img) in enumerate(maps):
        ax = fig.add_subplot(gs[0, idx])
        plot_glass_brain(
            img, threshold=3.55, display_mode="lyrz", plot_abs=False,
            cmap="cold_hot", symmetric_cbar=True, vmax=vmax,
            colorbar=(idx == len(maps) - 1), figure=fig, axes=ax,
            black_bg=False,
        )
        ax.set_title(f"{chr(65 + idx)}  {format_contrast(contrast)}", loc="left", pad=5)

    n_perm = int(meta.get("n_permutations", 10_000))
    first_result = next(iter(meta.get("results", {}).values()), {})
    n_subjects = first_result.get("n_subjects", 45)
    fig.text(
        0.01, 0.055,
        f"Descriptive t maps at two-sided voxel p < .001; n = {n_subjects}; "
        f"{n_perm:,} permutations. No cluster survives maximum-cluster-size FWER p < .05.",
        ha="left", va="bottom", fontsize=6.7, color=MUTED_INK,
    )
    _save(fig, PAPER_DIR / "Supplement_Figure_1_whole_brain_inference.png")
    print(f"  whole brain -> {PAPER_DIR / 'Supplement_Figure_1_whole_brain_inference.png'}")


# ===========================================================================
# Supplementary figure 2: MVPA performance
# ===========================================================================
def supplement_mvpa() -> None:
    path = DATA_DIR / "svm_weights" / "classification_results.json"
    if not path.exists():
        return
    with open(path) as f:
        payload = json.load(f)
    rows = pd.DataFrame(payload.get("results", []))
    if rows.empty:
        return
    rows["label"] = rows["contrast"].map(format_contrast)
    rows = rows.iloc[::-1].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    y = np.arange(len(rows))
    ax.hlines(y, rows["auc"], rows["accuracy"], color=GRID_COLOR, linewidth=1.0, zorder=1)
    ax.scatter(
        rows["accuracy"], y, s=42, color=PALETTE["AVH-"], marker="o",
        edgecolor=OUTLINE_COLOR, linewidth=0.6, label="Accuracy", zorder=3,
    )
    ax.scatter(
        rows["auc"], y, s=42, color="#E69F00", marker="D",
        edgecolor=OUTLINE_COLOR, linewidth=0.6, label="ROC AUC", zorder=3,
    )
    ax.axvline(0.5, color=OUTLINE_COLOR, lw=0.8, ls=(0, (3, 2)))
    for yi, row in rows.iterrows():
        ax.text(
            max(row["accuracy"], row["auc"]) + 0.025, yi,
            f"p = {row['p_value']:.3f}", va="center", fontsize=7.2,
        )
    ax.set_yticks(y)
    ax.set_yticklabels(rows["label"])
    ax.set_xlim(0.20, 0.76)
    ax.set_xlabel("Cross-validated score")
    ax.set_title(
        "MVPA classification performance\nAVH\N{MINUS SIGN} versus AVH+; shuffled five-fold KFold CV",
        loc="left", pad=8,
    )
    ax.legend(loc="lower right", ncol=2)
    style_axis(ax, grid_axis="x")
    fig.text(
        0.02, 0.015,
        "Dashed line indicates chance (0.50). Permutation p values use the stored 100-permutation analysis; "
        "increase before confirmatory use.",
        ha="left", va="bottom", fontsize=6.7, color=MUTED_INK,
    )
    fig.subplots_adjust(left=0.25, right=0.98, top=0.80, bottom=0.23)
    _save(fig, PAPER_DIR / "Supplement_Figure_2_MVPA.png")
    print(f"  mvpa -> {PAPER_DIR / 'Supplement_Figure_2_MVPA.png'}")


# ===========================================================================
# Supplementary figure 3: sample characteristics and motion QC
# ===========================================================================
def supplement_sample_qc() -> None:
    parts = _load_participants()
    qc_path = DATA_DIR / "qc.csv"
    qc = pd.read_csv(qc_path) if qc_path.exists() else pd.DataFrame()
    if not qc.empty:
        qc = qc.merge(
            parts[["participant_id", "group"]],
            left_on="subject_id", right_on="participant_id", how="left",
        )
        qc["group"] = pd.Categorical(qc["group"], categories=GROUP_ORDER, ordered=True)

    fig, axes = plt.subplots(2, 3, figsize=(7.2, 4.55))

    def distribution(ax, data, variable: str, title: str, ylabel: str) -> None:
        sub = data.dropna(subset=[variable]).copy()
        sns.violinplot(
            data=sub, x="group", y=variable, order=GROUP_ORDER, hue="group",
            palette=PALETTE, inner=None, cut=0, linewidth=0.7, legend=False, ax=ax,
        )
        for collection in ax.collections:
            collection.set_alpha(0.25)
        sns.boxplot(
            data=sub, x="group", y=variable, order=GROUP_ORDER, width=0.20,
            showfliers=False, color="white",
            boxprops={"edgecolor": OUTLINE_COLOR, "linewidth": 0.7},
            whiskerprops={"color": OUTLINE_COLOR, "linewidth": 0.7},
            capprops={"color": OUTLINE_COLOR, "linewidth": 0.7},
            medianprops={"color": OUTLINE_COLOR, "linewidth": 0.9}, ax=ax,
        )
        sns.stripplot(
            data=sub, x="group", y=variable, order=GROUP_ORDER, hue="group",
            palette=PALETTE, size=2.1, alpha=0.72, jitter=0.16,
            edgecolor="white", linewidth=0.2, legend=False, ax=ax,
        )
        ax.set_title(title, loc="left", pad=5)
        ax.set_xlabel("")
        ax.set_ylabel(ylabel)
        style_axis(ax, grid_axis="y")

    distribution(axes[0, 0], parts, "age", "A  Age", "Years")
    distribution(axes[0, 1], parts, "iq", "B  IQ", "IQ score")
    if not qc.empty:
        distribution(axes[0, 2], qc, "mean_fd", "C  Mean framewise displacement", "Mean FD (mm)")
        axes[0, 2].axhline(0.5, color=OUTLINE_COLOR, lw=0.7, ls=(0, (3, 2)))
        distribution(axes[1, 0], qc, "pct_high_motion", "D  High-motion volumes", "Volumes (%)")
    else:
        axes[0, 2].axis("off")
        axes[1, 0].axis("off")

    counts = parts.groupby("group", observed=True).size().reindex(GROUP_ORDER)
    axes[1, 1].bar(
        GROUP_ORDER, counts.values, color=[PALETTE[g] for g in GROUP_ORDER],
        edgecolor=OUTLINE_COLOR, linewidth=0.6, width=0.62,
    )
    for idx, value in enumerate(counts.values):
        axes[1, 1].text(idx, value + 0.45, f"n = {int(value)}", ha="center", fontsize=7.2)
    axes[1, 1].set_ylim(0, max(counts.values) * 1.18)
    axes[1, 1].set_ylabel("Participants")
    axes[1, 1].set_title("E  Analysis cohort", loc="left", pad=5)
    style_axis(axes[1, 1], grid_axis="y")

    sex = (
        parts.groupby(["group", "sex"], observed=True).size()
        .unstack(fill_value=0).reindex(GROUP_ORDER)
    )
    props = sex.div(sex.sum(axis=1), axis=0)
    bottom = np.zeros(len(props))
    sex_colors = {"male": "#0072B2", "female": "#CC79A7"}
    for label in [c for c in ("male", "female") if c in props.columns]:
        values = props[label].to_numpy(dtype=float)
        axes[1, 2].bar(
            GROUP_ORDER, values, bottom=bottom, color=sex_colors[label],
            edgecolor="white", linewidth=0.5, width=0.62, label=label.capitalize(),
        )
        bottom += values
    axes[1, 2].set_ylim(0, 1)
    axes[1, 2].set_ylabel("Proportion")
    axes[1, 2].set_title("F  Sex distribution", loc="left", pad=5)
    axes[1, 2].legend(loc="upper right")
    style_axis(axes[1, 2], grid_axis="y")

    fig.text(
        0.02, 0.012,
        "Points represent participants; boxes show median and interquartile range. "
        "Dashed line in C marks mean FD = 0.5 mm.",
        ha="left", va="bottom", fontsize=6.7, color=MUTED_INK,
    )
    fig.subplots_adjust(left=0.08, right=0.99, top=0.96, bottom=0.12, hspace=0.48, wspace=0.40)
    _save(fig, PAPER_DIR / "Supplement_Figure_3_sample_and_QC.png")
    print(f"  sample/QC -> {PAPER_DIR / 'Supplement_Figure_3_sample_and_QC.png'}")


# ===========================================================================
# Supplementary figure 4: exploratory connectivity and laterality
# ===========================================================================
def supplement_exploratory_network() -> None:
    conn_path = DATA_DIR / "connectivity_significant.csv"
    lat_path = DATA_DIR / "laterality_stats.csv"
    if not conn_path.exists() and not lat_path.exists():
        return

    fig, axes = plt.subplots(
        2, 1, figsize=(7.2, 5.75),
        gridspec_kw={"height_ratios": [0.75, 2.35]},
    )
    ax = axes[0]
    if conn_path.exists():
        conn = pd.read_csv(conn_path).sort_values("diff")
        labels = [
            f"{format_roi(a)} \N{LEFT RIGHT ARROW} {format_roi(b)}"
            for a, b in zip(conn["roi1"], conn["roi2"])
        ]
        y = np.arange(len(conn))
        colors = [PALETTE["AVH-"] if value > 0 else PALETTE["AVH+"] for value in conn["diff"]]
        ax.barh(y, conn["diff"], color=colors, edgecolor=OUTLINE_COLOR, linewidth=0.6, height=0.56)
        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        for yi, row in conn.reset_index(drop=True).iterrows():
            ax.text(
                row["diff"] / 2, yi, f"p = {row['p_value']:.3f}",
                va="center", ha="center", fontsize=7.0, color="white",
            )
        ax.axvline(0, color=OUTLINE_COLOR, lw=0.8)
        ax.set_xlim(-0.23, 0.23)
        ax.set_xlabel("Difference in Fisher z (AVH\N{MINUS SIGN} \N{MINUS SIGN} AVH+)")
        ax.set_title("A  Connectivity differences\nUncorrected p < .05", loc="left", pad=7)
        style_axis(ax, grid_axis="x")
    else:
        ax.axis("off")

    ax = axes[1]
    if lat_path.exists():
        lat = pd.read_csv(lat_path)
        lat = lat[lat["comparison"] == "AVH-_vs_AVH+"].copy()
        lat["abs_d"] = lat["cohens_d"].abs()
        lat = lat.nlargest(10, "abs_d").sort_values("cohens_d")
        lat["label"] = [
            f"{format_contrast(c)}; {r.replace('_', ' ')}"
            for c, r in zip(lat["contrast"], lat["roi_pair"])
        ]
        y = np.arange(len(lat))
        ax.hlines(y, 0, lat["cohens_d"], color=GRID_COLOR, linewidth=1.1)
        ax.scatter(
            lat["cohens_d"], y, s=28, color=PALETTE["AVH-"],
            edgecolor=OUTLINE_COLOR, linewidth=0.55, zorder=3,
        )
        for yi, row in lat.reset_index(drop=True).iterrows():
            ax.text(
                0.56, yi, f"p = {row['p_value']:.3f}",
                va="center", ha="left", fontsize=6.7,
            )
        ax.axvline(0, color=OUTLINE_COLOR, lw=0.8)
        ax.set_xlim(-0.55, 0.72)
        ax.set_yticks(y)
        ax.set_yticklabels(lat["label"], fontsize=6.5)
        ax.set_xlabel("Cohen's d (AVH\N{MINUS SIGN} vs AVH+)")
        ax.set_title("B  Laterality effects\nTen largest absolute effects", loc="left", pad=7)
        style_axis(ax, grid_axis="x")
    else:
        ax.axis("off")

    fig.text(
        0.02, 0.012,
        "Exploratory results only. Connectivity differences are uncorrected and none survive FDR; "
        "no laterality comparison reaches p < .05.",
        ha="left", va="bottom", fontsize=6.7, color=MUTED_INK,
    )
    fig.subplots_adjust(left=0.33, right=0.98, top=0.96, bottom=0.105, hspace=0.62)
    _save(fig, PAPER_DIR / "Supplement_Figure_4_exploratory_network.png")
    print(f"  exploratory -> {PAPER_DIR / 'Supplement_Figure_4_exploratory_network.png'}")


# ===========================================================================
# README
# ===========================================================================
def write_readme() -> None:
    lines = [
        "# Paper Figures",
        "",
        "Journal-oriented figures generated by",
        "`code/python/paper_visualizations.py` from the consolidated stats in",
        "`results/data/`. Re-run with:",
        "",
        "    python code/python/paper_visualizations.py",
        "",
        "## Figures",
        "",
        "- **Figure_1_core_results** — Adjusted post hoc ANCOVA effects; age/IQ-residualized "
        "PSYRATS association; and raw subject-level activation distributions.",
        "- **Figure_2_effect_size_landscape** — ROI by contrast Cohen's d matrix for AVH- "
        "versus AVH+; no omnibus ROI cell survives within-contrast FDR.",
        "- **Figure_3_ROI_definitions** — Glass-brain ROI locations and MNI coordinate/radius table.",
        "- **Supplement_Figure_1_whole_brain_inference** — Descriptive whole-brain t maps with the null corrected result stated explicitly.",
        "- **Supplement_Figure_2_MVPA** — Cross-validated accuracy and ROC AUC with permutation p values and chance reference.",
        "- **Supplement_Figure_3_sample_and_QC** — Demographic distributions, cohort counts, sex, and motion diagnostics.",
        "- **Supplement_Figure_4_exploratory_network** — Uncorrected connectivity differences and the largest laterality effects.",
        "",
        "## Conventions",
        "",
        "- Each figure is exported as 600 dpi PNG, editable SVG, and vector PDF.",
        "- Figures are sized for a roughly 7.2-inch two-column journal width.",
        "- Groups use a color-vision-deficiency-safe gray/blue/vermillion palette.",
        "- Negative Cohen's d (AVH- vs AVH+) = higher activation in AVH+.",
        "- Statistical values are read from stored analysis outputs; figure generation does not rerun models.",
        "",
    ]
    (PAPER_DIR / "README.md").write_text("\n".join(lines))


def main() -> None:
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    print("\n" + "=" * 70)
    print("BUILDING results/paper_figures/")
    print("=" * 70)
    figure1_main_results()
    effect_size_heatmap()
    roi_definition_panel()
    supplement_whole_brain_inference()
    supplement_mvpa()
    supplement_sample_qc()
    supplement_exploratory_network()
    write_readme()
    print(f"\nDone. See {PAPER_DIR}\n")


if __name__ == "__main__":
    main()
