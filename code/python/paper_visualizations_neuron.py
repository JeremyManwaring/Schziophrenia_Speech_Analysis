"""Rebuild the complete manuscript figure set in a restrained Neuron-like style.

The script reads stored statistical outputs only. It does not rerun models,
change contrasts, calculate replacement statistics, or synthesize observations.
Every figure is written to ``results/paper_figures_neuron/`` as an exact-width
600 dpi PNG plus editable SVG and vector PDF.
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
from matplotlib.patches import Patch, Rectangle
from nilearn.image import load_img
from nilearn.plotting import plot_glass_brain

sys.path.insert(0, str(Path(__file__).parent))
from neuron_figure_style import (  # noqa: E402
    AXIS_COLOR,
    DIVERGING_CMAP,
    FIGURE_WIDTH,
    GRID_COLOR,
    GROUP_MARKERS,
    GROUP_ORDER,
    HAIRLINE,
    INK,
    LIGHT_INK,
    MUTED_INK,
    NEUTRAL,
    PALETTE,
    apply_neuron_style,
    lighten,
    panel_header,
    save_figure,
    stable_jitter,
    style_axis,
    vectorize_scalar_images,
)
from surface_brain_plots import ROI_RADII, ROIS, _roi_display  # noqa: E402

warnings.filterwarnings("ignore")
apply_neuron_style()


# ---------------------------------------------------------------------------
# Paths and immutable display order
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "results" / "data"
OUTPUT_DIR = BASE_DIR / "results" / "paper_figures_neuron"
PARTICIPANTS = BASE_DIR / "participants.tsv"

ROI_DIR = DATA_DIR / "roi_values"
EFFECT_DIR = DATA_DIR / "effect_sizes"
CORR_DIR = DATA_DIR / "correlations"
POSTHOC_DIR = DATA_DIR / "posthoc"

TARGET_CONTRAST = "sentences_vs_reversed"
TARGET_ROIS = ["L_MTG", "L_STS"]

ROI_ORDER = [
    "L_STG_posterior",
    "L_STG_anterior",
    "L_Heschl",
    "L_MTG",
    "L_STS",
    "L_IFG_triangularis",
    "L_IFG_opercularis",
    "R_STG_posterior",
    "R_STG_anterior",
    "R_Heschl",
    "R_MTG",
    "R_IFG",
]

CONTRAST_ORDER = [
    "sentences_vs_reversed",
    "words_vs_sentences",
    "speech_vs_reversed",
    "words_vs_reversed",
    "words_vs_baseline",
    "sentences_vs_baseline",
    "reversed_vs_baseline",
]

CONTRAST_LABELS = {
    "sentences_vs_reversed": "Sentences vs Reversed",
    "words_vs_sentences": "Words vs Sentences",
    "speech_vs_reversed": "Speech vs Reversed",
    "words_vs_reversed": "Words vs Reversed",
    "words_vs_baseline": "Words vs Baseline",
    "sentences_vs_baseline": "Sentences vs Baseline",
    "reversed_vs_baseline": "Reversed vs Baseline",
}

ROI_LABELS = {
    "L_STG_posterior": "L STG posterior",
    "L_STG_anterior": "L STG anterior",
    "L_Heschl": "L Heschl",
    "L_MTG": "L MTG",
    "L_STS": "L STS",
    "L_IFG_triangularis": "L IFG triangularis",
    "L_IFG_opercularis": "L IFG opercularis",
    "R_STG_posterior": "R STG posterior",
    "R_STG_anterior": "R STG anterior",
    "R_Heschl": "R Heschl",
    "R_MTG": "R MTG",
    "R_IFG": "R IFG",
}


# ---------------------------------------------------------------------------
# Source readers and common chart primitives
# ---------------------------------------------------------------------------
def format_contrast(name: str) -> str:
    return CONTRAST_LABELS.get(name, name.replace("_", " ").title())


def format_roi(name: str) -> str:
    return ROI_LABELS.get(name, name.replace("_", " "))


def load_participants() -> pd.DataFrame:
    data = pd.read_csv(PARTICIPANTS, sep="\t")
    for column in ("age", "iq", "psyrats"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["group"] = pd.Categorical(
        data["group"], categories=GROUP_ORDER, ordered=True
    )
    return data


def residualize(values: np.ndarray, covariates: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    covariates = np.asarray(covariates, dtype=float)
    design = np.column_stack([np.ones(len(values)), covariates])
    beta = np.linalg.lstsq(design, values, rcond=None)[0]
    return values - design @ beta


def primary_correlation_hit() -> dict | None:
    """Read the strongest stored within-contrast FDR-surviving partial hit."""
    with open(CORR_DIR / "correlation_summary.json") as stream:
        summary = json.load(stream)
    best = None
    for contrast, block in summary.items():
        for row in block.get("partial_correlations", []):
            q_value = row.get("partial_p_fdr_within_contrast")
            if q_value is None or q_value >= 0.05:
                continue
            candidate = {
                "contrast": contrast,
                "roi": row["roi"],
                "partial_r": row["partial_r"],
                "partial_p": row["partial_p"],
                "partial_fdr": q_value,
                "n": row["n"],
                "df": row["df"],
            }
            if best is None or candidate["partial_fdr"] < best["partial_fdr"]:
                best = candidate
    return best


def omnibus_fdr_sig_cells() -> set[tuple[str, str]]:
    cells: set[tuple[str, str]] = set()
    for path in ROI_DIR.glob("*_roi_anova.csv"):
        contrast = path.name.replace("_roi_anova.csv", "")
        table = pd.read_csv(path)
        if "p_fdr" not in table.columns:
            continue
        for _, row in table[table["p_fdr"] < 0.05].iterrows():
            cells.add((contrast, row["roi"]))
    return cells


def draw_group_boxpoints(
    ax,
    data: pd.DataFrame,
    value_col: str,
    *,
    id_col: str | None = None,
    show_counts: bool = True,
) -> pd.Series:
    """Draw group box summaries with subordinate, participant-stable raw points."""
    sub = data[["group", value_col] + ([id_col] if id_col else [])].copy()
    sub["group"] = pd.Categorical(sub["group"], GROUP_ORDER, ordered=True)
    sub = sub.dropna(subset=["group", value_col])

    arrays = [
        sub.loc[sub["group"] == group, value_col].to_numpy(dtype=float)
        for group in GROUP_ORDER
    ]
    box = ax.boxplot(
        arrays,
        positions=np.arange(len(GROUP_ORDER)),
        widths=0.34,
        patch_artist=True,
        showfliers=False,
        manage_ticks=False,
        boxprops={"linewidth": 0.8, "edgecolor": AXIS_COLOR},
        whiskerprops={"linewidth": 0.75, "color": AXIS_COLOR},
        capprops={"linewidth": 0.75, "color": AXIS_COLOR},
        medianprops={"linewidth": 1.15, "color": INK},
        zorder=3,
    )
    for patch, group in zip(box["boxes"], GROUP_ORDER):
        patch.set_facecolor(lighten(PALETTE[group], 0.78))

    for position, group in enumerate(GROUP_ORDER):
        group_data = sub[sub["group"] == group]
        if id_col:
            identifiers = group_data[id_col].astype(str).tolist()
        else:
            identifiers = group_data.index.astype(str).tolist()
        x = position + stable_jitter(identifiers, group, width=0.13)
        ax.scatter(
            x,
            group_data[value_col],
            s=10.5,
            marker=GROUP_MARKERS[group],
            facecolor=PALETTE[group],
            edgecolor="white",
            linewidth=0.28,
            alpha=0.58,
            zorder=2,
        )

    counts = sub.groupby("group", observed=True).size().reindex(GROUP_ORDER)
    tick_labels = [
        f"{group}\n(n = {int(counts[group])})" if show_counts else group
        for group in GROUP_ORDER
    ]
    ax.set_xticks(np.arange(len(GROUP_ORDER)))
    ax.set_xticklabels(tick_labels)
    ax.set_xlim(-0.55, len(GROUP_ORDER) - 0.45)
    style_axis(ax, grid_axis="y")
    return counts


def add_note(fig, text: str, *, x: float = 0.06, y: float = 0.018) -> None:
    fig.text(
        x,
        y,
        text,
        ha="left",
        va="bottom",
        fontsize=6.25,
        color=MUTED_INK,
        linespacing=1.25,
    )


# ---------------------------------------------------------------------------
# Figure 1: core results
# ---------------------------------------------------------------------------
def figure_1_core_results() -> None:
    participants = load_participants()
    roi_values = pd.read_csv(ROI_DIR / f"{TARGET_CONTRAST}_roi_values.csv")

    fig = plt.figure(figsize=(FIGURE_WIDTH, 6.2))
    grid = fig.add_gridspec(
        2,
        2,
        width_ratios=[0.94, 1.08],
        height_ratios=[0.93, 1.07],
        left=0.09,
        right=0.985,
        top=0.925,
        bottom=0.135,
        hspace=0.50,
        wspace=0.36,
    )

    # A. Stored targeted post hoc ANCOVA effects.
    ax = fig.add_subplot(grid[0, 0])
    posthoc = pd.read_csv(POSTHOC_DIR / "posthoc_targeted.csv")
    full = posthoc[posthoc["sample"] == "full_n69"].copy()
    full["roi"] = pd.Categorical(full["roi"], TARGET_ROIS, ordered=True)
    full = full.sort_values("roi").reset_index(drop=True)
    y = np.arange(len(full))
    ax.errorbar(
        full["d_adj"],
        y,
        xerr=[
            full["d_adj"] - full["d_adj_ci_lo"],
            full["d_adj_ci_hi"] - full["d_adj"],
        ],
        fmt="none",
        ecolor=AXIS_COLOR,
        elinewidth=0.95,
        capsize=3.0,
        capthick=0.8,
        zorder=2,
    )
    ax.scatter(
        full["d_adj"],
        y,
        s=35,
        marker="D",
        facecolor=PALETTE["AVH+"],
        edgecolor=INK,
        linewidth=0.55,
        zorder=4,
    )
    for yi, row in full.iterrows():
        ax.text(
            row["d_adj"],
            yi - 0.18,
            f"d = {row['d_adj']:+.2f}; pBonf = {row['p_bonferroni']:.3f}",
            ha="center",
            va="bottom",
            fontsize=6.35,
            color=INK,
        )
    ax.axvline(0, color=AXIS_COLOR, linewidth=0.75, linestyle=(0, (2.4, 2.2)))
    ax.set_yticks(y)
    ax.set_yticklabels([format_roi(roi) for roi in full["roi"]])
    ax.set_ylim(len(full) - 0.47, -0.55)
    ax.set_xlim(-1.75, 0.25)
    ax.set_xticks([-1.5, -1.0, -0.5, 0.0])
    ax.set_xlabel("Adjusted Cohen's d (AVH- vs AVH+)")
    panel_header(
        ax,
        "A",
        "Post hoc adjusted effects",
        "Targeted ANCOVA | Sentences vs Reversed",
    )
    style_axis(ax, grid_axis="x")

    # B. Stored primary AVH+ symptom association.
    ax = fig.add_subplot(grid[0, 1])
    hit = primary_correlation_hit()
    if hit is None:
        raise RuntimeError("No stored within-contrast FDR-surviving partial correlation.")
    avh_plus = participants[participants["group"] == "AVH+"].dropna(
        subset=["psyrats", "age", "iq"]
    )
    correlation_values = pd.read_csv(
        ROI_DIR / f"{hit['contrast']}_roi_values.csv"
    ).merge(
        avh_plus[["participant_id", "psyrats", "age", "iq"]],
        left_on="subject_id",
        right_on="participant_id",
        how="inner",
    )
    x_raw = correlation_values[hit["roi"]].to_numpy(dtype=float)
    y_raw = correlation_values["psyrats"].to_numpy(dtype=float)
    covariates = correlation_values[["age", "iq"]].to_numpy(dtype=float)
    keep = (
        np.isfinite(x_raw)
        & np.isfinite(y_raw)
        & np.all(np.isfinite(covariates), axis=1)
    )
    x_res = residualize(x_raw[keep], covariates[keep])
    y_res = residualize(y_raw[keep], covariates[keep])
    sns.regplot(
        x=x_res,
        y=y_res,
        ax=ax,
        color=PALETTE["AVH+"],
        marker=GROUP_MARKERS["AVH+"],
        truncate=False,
        ci=95,
        n_boot=2000,
        seed=20260824,
        scatter_kws={
            "s": 18,
            "facecolor": PALETTE["AVH+"],
            "edgecolor": "white",
            "linewidths": 0.35,
            "alpha": 0.68,
        },
        line_kws={"color": AXIS_COLOR, "linewidth": 1.15},
    )
    ax.axhline(0, color=GRID_COLOR, linewidth=0.6, zorder=0)
    ax.axvline(0, color=GRID_COLOR, linewidth=0.6, zorder=0)
    ax.text(
        0.03,
        0.97,
        f"partial r = {hit['partial_r']:+.2f}\n"
        f"p = {hit['partial_p']:.4f}; q = {hit['partial_fdr']:.3f}\n"
        f"n = {hit['n']}; df = {hit['df']}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.65,
        color=INK,
        linespacing=1.30,
    )
    ax.set_xlabel("Activation residual (beta)")
    ax.set_ylabel("PSYRATS residual")
    panel_header(
        ax,
        "B",
        "Symptom association in AVH+",
        f"{format_roi(hit['roi'])} | {format_contrast(hit['contrast'])}",
    )
    style_axis(ax, grid_axis=None)

    # C-D. Raw participant-level distributions with shared beta scale.
    global_values = np.concatenate(
        [roi_values[roi].dropna().to_numpy(dtype=float) for roi in TARGET_ROIS]
    )
    spread = float(np.nanmax(global_values) - np.nanmin(global_values))
    lower = float(np.nanmin(global_values) - spread * 0.07)
    upper = float(np.nanmax(global_values) + spread * 0.07)
    for cell, roi, label in zip(
        [grid[1, 0], grid[1, 1]], TARGET_ROIS, ["C", "D"]
    ):
        ax = fig.add_subplot(cell)
        draw_group_boxpoints(
            ax,
            roi_values,
            roi,
            id_col="subject_id",
            show_counts=True,
        )
        ax.axhline(0, color=AXIS_COLOR, linewidth=0.65, linestyle=(0, (2.4, 2.2)))
        ax.set_ylim(lower, upper)
        ax.set_xlabel("")
        ax.set_ylabel("Activation (beta)")
        panel_header(
            ax,
            label,
            f"{format_roi(roi)} activation",
            "Raw values | Sentences vs Reversed",
        )

    add_note(
        fig,
        "A: post hoc targeted ANCOVA adjusted for age, IQ, sex, and mean FD (full n = 69); "
        "negative d indicates higher adjusted activation in AVH+.\n"
        "B: age- and IQ-residualized values; shaded band is the 95% CI. "
        "C-D: unadjusted participant-level distributions.",
        x=0.09,
        y=0.025,
    )
    save_figure(fig, OUTPUT_DIR / "Figure_1_core_results")


# ---------------------------------------------------------------------------
# Figure 2: effect-size landscape
# ---------------------------------------------------------------------------
def figure_2_effect_size_landscape() -> None:
    effect_sizes = pd.read_csv(EFFECT_DIR / "effect_sizes_summary.csv")
    effect_sizes = effect_sizes[
        effect_sizes["comparison"] == "AVH-_vs_AVH+"
    ].copy()
    matrix = effect_sizes.pivot_table(
        index="roi", columns="contrast", values="cohens_d"
    )
    rois = [roi for roi in ROI_ORDER if roi in matrix.index]
    contrasts = [contrast for contrast in CONTRAST_ORDER if contrast in matrix.columns]
    matrix = matrix.reindex(index=rois, columns=contrasts)

    fig = plt.figure(figsize=(FIGURE_WIDTH, 4.9))
    ax = fig.add_axes([0.22, 0.24, 0.66, 0.61])
    cbar_ax = fig.add_axes([0.91, 0.31, 0.018, 0.47])
    heatmap = sns.heatmap(
        matrix,
        ax=ax,
        cmap=DIVERGING_CMAP,
        center=0,
        vmin=-1.0,
        vmax=1.0,
        annot=True,
        fmt=".2f",
        annot_kws={"fontsize": 6.1},
        linewidths=0.55,
        linecolor="white",
        cbar=True,
        cbar_ax=cbar_ax,
        cbar_kws={"ticks": [-1.0, -0.5, 0.0, 0.5, 1.0]},
        xticklabels=[format_contrast(contrast) for contrast in contrasts],
        yticklabels=[format_roi(roi) for roi in rois],
    )
    values = matrix.to_numpy(dtype=float)
    for text, value in zip(heatmap.texts, values.ravel()):
        text.set_color("white" if abs(value) >= 0.58 else INK)
        text.set_fontweight("semibold" if abs(value) >= 0.75 else "normal")

    significant_cells = omnibus_fdr_sig_cells()
    for contrast, roi in significant_cells:
        if contrast in contrasts and roi in rois:
            col = contrasts.index(contrast)
            row = rois.index(roi)
            ax.add_patch(
                Rectangle(
                    (col, row),
                    1,
                    1,
                    fill=False,
                    edgecolor=INK,
                    linewidth=1.6,
                    zorder=6,
                )
            )
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(length=0)
    plt.setp(
        ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor"
    )
    plt.setp(ax.get_yticklabels(), rotation=0)
    cbar_ax.set_ylabel("Cohen's d (AVH- vs AVH+)", rotation=90, labelpad=6)
    cbar_ax.tick_params(length=2.3, width=0.5)

    fig.text(
        0.06,
        0.945,
        "ROI effect-size landscape",
        ha="left",
        va="top",
        fontsize=10.4,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.06,
        0.895,
        "Pairwise standardized differences across task contrasts",
        ha="left",
        va="top",
        fontsize=7.0,
        color=MUTED_INK,
    )
    fdr_note = (
        "Outlined cells survive omnibus within-contrast FDR."
        if significant_cells
        else "No omnibus ROI test survives within-contrast FDR."
    )
    add_note(
        fig,
        "Negative values indicate higher activation in AVH+. " + fdr_note,
        x=0.06,
        y=0.030,
    )
    save_figure(fig, OUTPUT_DIR / "Figure_2_effect_size_landscape")


# ---------------------------------------------------------------------------
# Figure 3: ROI definitions
# ---------------------------------------------------------------------------
def figure_3_roi_definitions() -> None:
    fig = plt.figure(figsize=(FIGURE_WIDTH, 3.7))
    grid = fig.add_gridspec(
        1,
        2,
        width_ratios=[1.18, 1.0],
        left=0.025,
        right=0.985,
        top=0.84,
        bottom=0.16,
        wspace=0.10,
    )

    ax_map = fig.add_subplot(grid[0, 0])
    display = plot_glass_brain(
        None,
        display_mode="lyrz",
        figure=fig,
        axes=ax_map,
        annotate=True,
        black_bg=False,
    )
    for hemisphere, color in (("L_", PALETTE["AVH-"]), ("R_", PALETTE["AVH+"])):
        for radius, size in ((8, 45), (6, 27)):
            coordinates = [
                coordinate
                for key, coordinate in ROIS.items()
                if key.startswith(hemisphere) and ROI_RADII[key] == radius
            ]
            if coordinates:
                display.add_markers(
                    coordinates,
                    marker_color=color,
                    marker_size=size,
                    edgecolor=INK,
                    alpha=0.88,
                )
    panel_header(ax_map, "A", "ROI locations", "MNI space | marker size encodes radius")
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=PALETTE["AVH-"],
            markeredgecolor=INK,
            markeredgewidth=0.5,
            markersize=5.2,
            label="Left hemisphere",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=PALETTE["AVH+"],
            markeredgecolor=INK,
            markeredgewidth=0.5,
            markersize=5.2,
            label="Right hemisphere",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color=AXIS_COLOR,
            markerfacecolor="white",
            markersize=5.2,
            label="8 mm sphere",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color=AXIS_COLOR,
            markerfacecolor="white",
            markersize=3.7,
            label="6 mm Heschl sphere",
        ),
    ]
    ax_map.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.14),
        ncol=2,
        columnspacing=1.0,
        handletextpad=0.35,
    )

    ax_table = fig.add_subplot(grid[0, 1])
    ax_table.axis("off")
    panel_header(ax_table, "B", "ROI definitions", "MNI coordinates and sphere radii")
    rows = [
        [
            _roi_display(key),
            f"{coordinate[0]:.0f}, {coordinate[1]:.0f}, {coordinate[2]:.0f}",
            f"{ROI_RADII[key]} mm",
        ]
        for key, coordinate in ROIS.items()
    ]
    table = ax_table.table(
        cellText=rows,
        colLabels=["ROI", "MNI (x, y, z)", "Radius"],
        colWidths=[0.48, 0.35, 0.17],
        cellLoc="left",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(6.15)
    table.scale(1.0, 1.12)
    for (row, _column), cell in table.get_celld().items():
        cell.PAD = 0.07
        cell.set_edgecolor(HAIRLINE)
        cell.set_linewidth(0.45)
        if row == 0:
            cell.visible_edges = "TB"
            cell.set_facecolor(NEUTRAL)
            cell.set_text_props(fontweight="semibold", color=INK)
        else:
            cell.visible_edges = "B"
            cell.set_facecolor("white")

    add_note(
        fig,
        "Spheres may overlap; overlapping ROI means are therefore not statistically independent.",
        x=0.025,
        y=0.028,
    )
    save_figure(fig, OUTPUT_DIR / "Figure_3_ROI_definitions")


# ---------------------------------------------------------------------------
# Supplementary Figure 1: whole-brain inference
# ---------------------------------------------------------------------------
def supplement_figure_1_whole_brain() -> None:
    cluster_dir = DATA_DIR / "cluster_maps"
    with open(cluster_dir / "analysis_summary.json") as stream:
        metadata = json.load(stream)

    contrasts = [
        "sentences_vs_reversed",
        "speech_vs_reversed",
        "words_vs_sentences",
    ]
    maps: list[tuple[str, object]] = []
    vmax = 0.0
    for contrast in contrasts:
        image = load_img(
            str(cluster_dir / f"{contrast}_AVH-_vs_AVH+_tstat.nii.gz")
        )
        finite = np.abs(np.asarray(image.get_fdata(), dtype=float))
        finite = finite[np.isfinite(finite)]
        if finite.size:
            vmax = max(vmax, float(np.nanmax(finite)))
        maps.append((contrast, image))
    vmax = max(4.0, min(vmax, 6.0))

    fig = plt.figure(figsize=(FIGURE_WIDTH, 2.55))
    grid = fig.add_gridspec(
        1,
        3,
        left=0.025,
        right=0.985,
        top=0.78,
        bottom=0.25,
        wspace=0.08,
    )
    for index, (contrast, image) in enumerate(maps):
        ax = fig.add_subplot(grid[0, index])
        plot_glass_brain(
            image,
            threshold=3.55,
            display_mode="lyrz",
            plot_abs=False,
            cmap=DIVERGING_CMAP,
            symmetric_cbar=True,
            vmax=vmax,
            colorbar=index == len(maps) - 1,
            figure=fig,
            axes=ax,
            black_bg=False,
        )
        panel_header(
            ax,
            chr(65 + index),
            format_contrast(contrast),
            "Descriptive t map | AVH- vs AVH+",
        )

    first_result = next(iter(metadata["results"].values()))
    add_note(
        fig,
        f"Two-sided voxel p < .001; n = {first_result['n_subjects']} "
        f"(AVH- = {first_result['n_avh_minus']}, AVH+ = {first_result['n_avh_plus']}); "
        f"{metadata['n_permutations']:,} permutations; covariates: age, IQ, and sex.\n"
        "No cluster survives maximum-cluster-size FWER p < .05. Positive t is higher in AVH-; "
        "negative t is higher in AVH+.",
        x=0.025,
        y=0.035,
    )
    vectorize_scalar_images(fig)
    save_figure(fig, OUTPUT_DIR / "Supplement_Figure_1_whole_brain_inference")


# ---------------------------------------------------------------------------
# Supplementary Figure 2: MVPA
# ---------------------------------------------------------------------------
def supplement_figure_2_mvpa() -> None:
    with open(DATA_DIR / "svm_weights" / "classification_results.json") as stream:
        payload = json.load(stream)
    rows = pd.DataFrame(payload["results"])
    rows["label"] = rows["contrast"].map(format_contrast)

    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, 3.25))
    y = np.arange(len(rows))
    ax.hlines(
        y,
        rows["auc"],
        rows["accuracy"],
        color=HAIRLINE,
        linewidth=1.0,
        zorder=1,
    )
    ax.scatter(
        rows["accuracy"],
        y,
        s=35,
        marker="o",
        facecolor=PALETTE["AVH-"],
        edgecolor=INK,
        linewidth=0.55,
        label="Accuracy",
        zorder=3,
    )
    ax.scatter(
        rows["auc"],
        y,
        s=38,
        marker="D",
        facecolor="white",
        edgecolor=INK,
        linewidth=0.8,
        label="ROC AUC",
        zorder=3,
    )
    ax.axvline(0.50, color=AXIS_COLOR, linewidth=0.75, linestyle=(0, (2.4, 2.2)))
    for yi, row in rows.iterrows():
        ax.text(
            row["accuracy"] + 0.012,
            yi,
            f"{row['accuracy']:.3f}",
            ha="left",
            va="center",
            fontsize=6.3,
            color=PALETTE["AVH-"],
        )
        ax.text(
            row["auc"] - 0.012,
            yi,
            f"{row['auc']:.3f}",
            ha="right",
            va="center",
            fontsize=6.3,
            color=INK,
        )
        ax.text(
            0.735,
            yi,
            f"p = {row['p_value']:.3f}",
            ha="right",
            va="center",
            fontsize=6.4,
            color=MUTED_INK,
        )
    ax.set_yticks(y)
    ax.set_yticklabels(rows["label"])
    ax.invert_yaxis()
    ax.set_xlim(0.20, 0.76)
    ax.set_xlabel("Cross-validated score")
    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.0, 1.12),
        ncol=2,
        handletextpad=0.45,
        columnspacing=1.1,
    )
    panel_header(
        ax,
        "A",
        "MVPA classification performance",
        "AVH- vs AVH+ | n = 40 (20/20) | shuffled five-fold KFold CV",
    )
    style_axis(ax, grid_axis="x")
    fig.subplots_adjust(left=0.25, right=0.98, top=0.80, bottom=0.24)
    add_note(
        fig,
        "Dashed line indicates chance (0.50). Permutation p values use the stored 100-permutation "
        "analysis; increase before confirmatory use. KFold random_state = 42.",
        x=0.025,
        y=0.025,
    )
    save_figure(fig, OUTPUT_DIR / "Supplement_Figure_2_MVPA")


# ---------------------------------------------------------------------------
# Supplementary Figure 3: sample and quality control
# ---------------------------------------------------------------------------
def supplement_figure_3_sample_qc() -> None:
    participants = load_participants()
    qc = pd.read_csv(DATA_DIR / "qc.csv").merge(
        participants[["participant_id", "group"]],
        left_on="subject_id",
        right_on="participant_id",
        how="left",
    )
    qc["group"] = pd.Categorical(qc["group"], GROUP_ORDER, ordered=True)

    fig, axes = plt.subplots(2, 3, figsize=(FIGURE_WIDTH, 4.75))

    def distribution(
        ax,
        data: pd.DataFrame,
        variable: str,
        label: str,
        title: str,
        ylabel: str,
        id_col: str,
    ) -> None:
        draw_group_boxpoints(
            ax,
            data,
            variable,
            id_col=id_col,
            show_counts=True,
        )
        ax.set_xlabel("")
        ax.set_ylabel(ylabel)
        panel_header(ax, label, title)

    distribution(
        axes[0, 0], participants, "age", "A", "Age", "Years", "participant_id"
    )
    distribution(
        axes[0, 1], participants, "iq", "B", "IQ", "IQ score", "participant_id"
    )
    distribution(
        axes[0, 2], qc, "mean_fd", "C", "Mean framewise displacement", "Mean FD (mm)", "subject_id"
    )
    axes[0, 2].axhline(
        0.5, color=AXIS_COLOR, linewidth=0.75, linestyle=(0, (2.4, 2.2))
    )
    axes[0, 2].text(
        2.47,
        0.5,
        "0.5 mm",
        ha="right",
        va="bottom",
        fontsize=6.0,
        color=MUTED_INK,
    )
    distribution(
        axes[1, 0],
        qc,
        "pct_high_motion",
        "D",
        "High-motion volumes",
        "Volumes (%)",
        "subject_id",
    )

    counts = (
        participants.groupby("group", observed=True).size().reindex(GROUP_ORDER)
    )
    axes[1, 1].bar(
        GROUP_ORDER,
        counts.to_numpy(dtype=float),
        width=0.60,
        color=[PALETTE[group] for group in GROUP_ORDER],
        edgecolor=INK,
        linewidth=0.55,
        zorder=2,
    )
    for index, value in enumerate(counts):
        axes[1, 1].text(
            index,
            value + 0.50,
            f"n = {int(value)}",
            ha="center",
            va="bottom",
            fontsize=6.4,
        )
    axes[1, 1].set_ylim(0, max(counts) * 1.20)
    axes[1, 1].set_ylabel("Participants")
    panel_header(axes[1, 1], "E", "Analysis cohort")
    style_axis(axes[1, 1], grid_axis="y")

    sex_counts = (
        participants.groupby(["group", "sex"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reindex(GROUP_ORDER)
    )
    sex_proportions = sex_counts.div(sex_counts.sum(axis=1), axis=0)
    bottom = np.zeros(len(GROUP_ORDER), dtype=float)
    sex_styles = {
        "male": {"color": "#555B61", "hatch": ""},
        "female": {"color": "#D9DCDE", "hatch": "////"},
    }
    for sex in [value for value in ("male", "female") if value in sex_counts.columns]:
        values = sex_proportions[sex].to_numpy(dtype=float)
        bars = axes[1, 2].bar(
            GROUP_ORDER,
            values,
            bottom=bottom,
            width=0.60,
            color=sex_styles[sex]["color"],
            hatch=sex_styles[sex]["hatch"],
            edgecolor="white" if sex == "male" else AXIS_COLOR,
            linewidth=0.45,
            label=sex.capitalize(),
            zorder=2,
        )
        for index, (bar, proportion) in enumerate(zip(bars, values)):
            if proportion >= 0.10:
                axes[1, 2].text(
                    bar.get_x() + bar.get_width() / 2,
                    bottom[index] + proportion / 2,
                    str(int(sex_counts.iloc[index][sex])),
                    ha="center",
                    va="center",
                    fontsize=6.0,
                    color="white" if sex == "male" else INK,
                )
        bottom += values
    axes[1, 2].set_ylim(0, 1)
    axes[1, 2].set_ylabel("Proportion")
    panel_header(axes[1, 2], "F", "Sex distribution")
    axes[1, 2].legend(
        loc="upper right",
        bbox_to_anchor=(1.0, 1.16),
        ncol=2,
        handlelength=1.0,
        handletextpad=0.35,
        columnspacing=0.65,
    )
    style_axis(axes[1, 2], grid_axis="y")

    fig.subplots_adjust(
        left=0.075,
        right=0.99,
        top=0.92,
        bottom=0.14,
        hspace=0.57,
        wspace=0.38,
    )
    add_note(
        fig,
        "Points represent participants; boxes show median and interquartile range. Dashed line in C "
        "marks mean FD = 0.5 mm. Panel F numbers are participant counts within sex strata.",
        x=0.025,
        y=0.025,
    )
    save_figure(fig, OUTPUT_DIR / "Supplement_Figure_3_sample_and_QC")


# ---------------------------------------------------------------------------
# Supplementary Figure 4: exploratory connectivity and laterality
# ---------------------------------------------------------------------------
def supplement_figure_4_exploratory_network() -> None:
    connectivity = pd.read_csv(DATA_DIR / "connectivity_significant.csv").sort_values(
        "diff"
    )
    laterality = pd.read_csv(DATA_DIR / "laterality_stats.csv")
    laterality = laterality[
        laterality["comparison"] == "AVH-_vs_AVH+"
    ].copy()
    laterality["abs_d"] = laterality["cohens_d"].abs()
    laterality = laterality.nlargest(10, "abs_d").sort_values("cohens_d")

    fig = plt.figure(figsize=(FIGURE_WIDTH, 5.55))
    grid = fig.add_gridspec(
        2,
        1,
        height_ratios=[0.80, 2.45],
        left=0.33,
        right=0.975,
        top=0.92,
        bottom=0.13,
        hspace=0.58,
    )

    ax = fig.add_subplot(grid[0])
    labels = [
        f"{format_roi(roi1)} to {format_roi(roi2)}"
        for roi1, roi2 in zip(connectivity["roi1"], connectivity["roi2"])
    ]
    y = np.arange(len(connectivity))
    colors = [
        PALETTE["AVH-"] if value > 0 else PALETTE["AVH+"]
        for value in connectivity["diff"]
    ]
    bars = ax.barh(
        y,
        connectivity["diff"],
        color=colors,
        edgecolor=INK,
        linewidth=0.5,
        height=0.54,
        zorder=2,
    )
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    for bar, (_, row) in zip(bars, connectivity.iterrows()):
        ax.text(
            row["diff"] / 2,
            bar.get_y() + bar.get_height() / 2,
            f"{row['diff']:+.3f}; p = {row['p_value']:.3f}",
            ha="center",
            va="center",
            fontsize=6.15,
            color="white",
        )
    ax.axvline(0, color=AXIS_COLOR, linewidth=0.75)
    ax.set_xlim(-0.23, 0.23)
    ax.set_xlabel("Difference in Fisher z (AVH- minus AVH+)")
    panel_header(ax, "A", "Connectivity differences", "Uncorrected p < .05")
    style_axis(ax, grid_axis="x")

    ax = fig.add_subplot(grid[1])
    laterality_labels = [
        f"{format_contrast(contrast)}; {roi_pair.replace('_', ' ')}"
        for contrast, roi_pair in zip(laterality["contrast"], laterality["roi_pair"])
    ]
    y = np.arange(len(laterality))
    ax.hlines(
        y,
        0,
        laterality["cohens_d"],
        color=HAIRLINE,
        linewidth=1.0,
        zorder=1,
    )
    for yi, (_, row) in enumerate(laterality.iterrows()):
        positive = row["cohens_d"] > 0
        ax.scatter(
            row["cohens_d"],
            yi,
            s=25,
            marker="o" if positive else "^",
            facecolor=PALETTE["AVH-"] if positive else PALETTE["AVH+"],
            edgecolor=INK,
            linewidth=0.45,
            zorder=3,
        )
        ax.text(
            0.56,
            yi,
            f"d = {row['cohens_d']:+.3f}; p = {row['p_value']:.3f}",
            ha="left",
            va="center",
            fontsize=6.15,
            color=MUTED_INK,
        )
    ax.axvline(0, color=AXIS_COLOR, linewidth=0.75)
    ax.set_xlim(-0.55, 0.75)
    ax.set_yticks(y)
    ax.set_yticklabels(laterality_labels, fontsize=6.3)
    ax.set_xlabel("Cohen's d (AVH- vs AVH+)")
    panel_header(ax, "B", "Laterality effects", "Ten largest absolute effects")
    style_axis(ax, grid_axis="x")

    add_note(
        fig,
        "Exploratory results only. Connectivity differences are uncorrected and none survive FDR; "
        "no laterality comparison reaches p < .05.",
        x=0.025,
        y=0.025,
    )
    save_figure(fig, OUTPUT_DIR / "Supplement_Figure_4_exploratory_network")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    figure_1_core_results()
    figure_2_effect_size_landscape()
    figure_3_roi_definitions()
    supplement_figure_1_whole_brain()
    supplement_figure_2_mvpa()
    supplement_figure_3_sample_qc()
    supplement_figure_4_exploratory_network()
    print(f"Created seven redesigned figure triplets in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
