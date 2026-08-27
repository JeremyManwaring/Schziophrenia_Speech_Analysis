"""Build the canonical manuscript figure set from stored analysis records.

This script only renders figures. It does not rerun statistical models or
alter values under ``results/data``.
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
from matplotlib.cm import ScalarMappable
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from nilearn import datasets
from nilearn.image import load_img, new_img_like
from nilearn.plotting import plot_anat, plot_glass_brain

sys.path.insert(0, str(Path(__file__).parent))
from paper_figure_style import (
    AXIS_COLOR,
    COOL_PAPER,
    CORAL,
    DIVERGING_CMAP,
    FIGURE_WIDTH,
    GRID_COLOR,
    GROUP_MARKERS,
    GROUP_ORDER,
    HAIRLINE,
    INK,
    MUTED_BLUE,
    MUTED_INK,
    NAVY,
    PALE_BLUE,
    PALETTE,
    PAPER,
    SOFT_TEAL,
    add_note,
    apply_figure_style,
    clean_axis,
    figure_title,
    lighten,
    panel_header,
    save_figure,
    stable_jitter,
    style_axis,
    vectorize_scalar_images,
)
from surface_brain_plots import ROI_RADII, ROIS, _roi_display

warnings.filterwarnings("ignore")
apply_figure_style()


# ---------------------------------------------------------------------------
# Paths and immutable display orders
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "results" / "data"
OUTPUT_DIR = BASE_DIR / "results" / "paper_figures"
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
# Source readers and shared visual primitives
# ---------------------------------------------------------------------------
def format_contrast(name: str) -> str:
    return CONTRAST_LABELS.get(name, name.replace("_", " ").title())


def format_roi(name: str) -> str:
    return ROI_LABELS.get(name, name.replace("_", " "))


def load_participants() -> pd.DataFrame:
    data = pd.read_csv(PARTICIPANTS, sep="\t")
    for column in ("age", "iq", "psyrats"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["group"] = pd.Categorical(data["group"], GROUP_ORDER, ordered=True)
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


def draw_group_distribution(
    ax,
    data: pd.DataFrame,
    value_col: str,
    *,
    id_col: str | None = None,
    show_counts: bool = True,
    positions: list[float] | np.ndarray | None = None,
) -> pd.Series:
    """Draw restrained violins, compact boxes, and all participant values."""
    columns = ["group", value_col] + ([id_col] if id_col else [])
    sub = data[columns].copy()
    sub["group"] = pd.Categorical(sub["group"], GROUP_ORDER, ordered=True)
    sub = sub.dropna(subset=["group", value_col])
    arrays = [
        sub.loc[sub["group"] == group, value_col].to_numpy(dtype=float)
        for group in GROUP_ORDER
    ]
    plot_positions = (
        np.arange(len(GROUP_ORDER), dtype=float)
        if positions is None
        else np.asarray(positions, dtype=float)
    )
    if len(plot_positions) != len(GROUP_ORDER):
        raise ValueError("positions must contain one location per group")

    violins = ax.violinplot(
        arrays,
        positions=plot_positions,
        widths=0.72,
        showmeans=False,
        showmedians=False,
        showextrema=False,
        bw_method=0.28,
    )
    for body, group in zip(violins["bodies"], GROUP_ORDER):
        body.set_facecolor(lighten(PALETTE[group], 0.72))
        body.set_edgecolor(PALETTE[group])
        body.set_linewidth(0.55)
        body.set_alpha(0.78)
        body.set_zorder(1)

    box = ax.boxplot(
        arrays,
        positions=plot_positions,
        widths=0.20,
        patch_artist=True,
        showfliers=False,
        manage_ticks=False,
        boxprops={"linewidth": 0.62, "edgecolor": AXIS_COLOR},
        whiskerprops={"linewidth": 0.58, "color": AXIS_COLOR},
        capprops={"linewidth": 0.58, "color": AXIS_COLOR},
        medianprops={"linewidth": 1.0, "color": NAVY},
        zorder=3,
    )
    for patch in box["boxes"]:
        patch.set_facecolor((1, 1, 1, 0.80))

    for position, group in zip(plot_positions, GROUP_ORDER):
        group_data = sub[sub["group"] == group]
        identifiers = (
            group_data[id_col].astype(str).tolist()
            if id_col
            else group_data.index.astype(str).tolist()
        )
        x = position + stable_jitter(identifiers, group, width=0.16)
        ax.scatter(
            x,
            group_data[value_col],
            s=7.0,
            marker=GROUP_MARKERS[group],
            facecolor=PALETTE[group],
            edgecolor="white",
            linewidth=0.18,
            alpha=0.48,
            zorder=2,
        )

    counts = sub.groupby("group", observed=True).size().reindex(GROUP_ORDER)
    tick_labels = [
        f"{group}\nn = {int(counts[group])}" if show_counts else group
        for group in GROUP_ORDER
    ]
    ax.set_xticks(plot_positions)
    ax.set_xticklabels(tick_labels)
    ax.set_xlim(float(plot_positions.min() - 0.52), float(plot_positions.max() + 0.52))
    style_axis(ax, grid_axis="y")
    clean_axis(ax)
    return counts


def compact_table(ax, rows: list[list[str]], hemisphere: str, color: str) -> None:
    """Render a light editorial coordinate table for one hemisphere."""
    ax.axis("off")
    ax.text(
        0.0,
        1.02,
        "●",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=7.4,
        color=color,
        clip_on=False,
    )
    ax.text(
        0.038,
        1.02,
        f"{hemisphere} hemisphere",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=6.75,
        fontweight="semibold",
        color=INK,
        clip_on=False,
    )
    table_height = min(0.94, 0.118 * (len(rows) + 1))
    table = ax.table(
        cellText=rows,
        colLabels=["ROI", "x", "y", "z", "r (mm)"],
        colWidths=[0.56, 0.10, 0.10, 0.10, 0.14],
        cellLoc="left",
        bbox=[0.0, 0.94 - table_height, 1.0, table_height],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(5.7)
    for (row, column), cell in table.get_celld().items():
        cell.PAD = 0.045
        cell.set_edgecolor(HAIRLINE)
        cell.set_linewidth(0.38)
        if row == 0:
            cell.visible_edges = "B"
            cell.set_facecolor(COOL_PAPER)
            cell.set_text_props(fontweight="semibold", color=MUTED_INK)
        else:
            cell.visible_edges = "B"
            cell.set_facecolor(PAPER)
        if column in (1, 2, 3):
            cell.get_text().set_ha("center")
        if column == 4:
            cell.get_text().set_ha("right")


# ---------------------------------------------------------------------------
# Figure 1: core results
# ---------------------------------------------------------------------------
def figure_1_core_results() -> None:
    participants = load_participants()
    roi_values = pd.read_csv(ROI_DIR / f"{TARGET_CONTRAST}_roi_values.csv")

    fig = plt.figure(figsize=(FIGURE_WIDTH, 5.35))
    grid = fig.add_gridspec(
        2,
        2,
        width_ratios=[0.96, 1.08],
        height_ratios=[1.0, 0.94],
        left=0.09,
        right=0.985,
        top=0.90,
        bottom=0.125,
        hspace=0.52,
        wspace=0.33,
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
        ecolor=MUTED_INK,
        elinewidth=0.82,
        capsize=2.8,
        capthick=0.7,
        zorder=2,
    )
    ax.scatter(
        full["d_adj"],
        y,
        s=34,
        marker="D",
        facecolor=CORAL,
        edgecolor=NAVY,
        linewidth=0.48,
        zorder=4,
    )
    for yi, row in full.iterrows():
        ax.text(
            row["d_adj"],
            yi - 0.18,
            f"d = {row['d_adj']:+.2f}  ·  Bonf. p = {row['p_bonferroni']:.3f}",
            ha="center",
            va="bottom",
            fontsize=6.1,
            color=INK,
        )
    ax.axvline(0, color=AXIS_COLOR, linewidth=0.62, linestyle=(0, (2.2, 2.2)))
    ax.set_yticks(y)
    ax.set_yticklabels([format_roi(roi) for roi in full["roi"]])
    ax.set_ylim(len(full) - 0.44, -0.55)
    ax.set_xlim(-1.72, 0.18)
    ax.set_xticks([-1.5, -1.0, -0.5, 0.0])
    ax.set_xlabel("Cohen's d (AVH− vs AVH+)")
    panel_header(
        ax,
        "A",
        "Adjusted effects",
        "Sentences vs Reversed · 95% CI",
    )
    style_axis(ax, grid_axis="x")
    clean_axis(ax)

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
        color=SOFT_TEAL,
        marker=GROUP_MARKERS["AVH+"],
        truncate=False,
        ci=95,
        n_boot=2000,
        seed=20260824,
        scatter_kws={
            "s": 15,
            "facecolor": CORAL,
            "edgecolor": "white",
            "linewidths": 0.26,
            "alpha": 0.64,
        },
        line_kws={"color": NAVY, "linewidth": 1.05},
    )
    ax.axhline(0, color=GRID_COLOR, linewidth=0.5, zorder=0)
    ax.axvline(0, color=GRID_COLOR, linewidth=0.5, zorder=0)
    ax.text(
        0.025,
        0.97,
        f"partial r = {hit['partial_r']:+.2f}\n"
        f"p = {hit['partial_p']:.4f}  ·  q = {hit['partial_fdr']:.3f}\n"
        f"n = {hit['n']}  ·  df = {hit['df']}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.25,
        color=INK,
        linespacing=1.28,
    )
    ax.set_xlabel("Activation residual (beta)")
    ax.set_ylabel("PSYRATS residual")
    panel_header(
        ax,
        "B",
        "Symptom association",
        f"AVH+ · {format_roi(hit['roi'])} · {format_contrast(hit['contrast'])}",
    )
    style_axis(ax, grid_axis=None)
    clean_axis(ax)

    # C. One coordinated participant-level view of both targeted ROIs.
    ax = fig.add_subplot(grid[1, :])
    global_values = np.concatenate(
        [roi_values[roi].dropna().to_numpy(dtype=float) for roi in TARGET_ROIS]
    )
    spread = float(np.nanmax(global_values) - np.nanmin(global_values))
    lower = float(np.nanmin(global_values) - spread * 0.07)
    upper = float(np.nanmax(global_values) + spread * 0.11)
    distribution_positions = ([0.0, 1.0, 2.0], [4.0, 5.0, 6.0])
    counts_by_roi: dict[str, pd.Series] = {}
    for positions, roi in zip(distribution_positions, TARGET_ROIS):
        counts_by_roi[roi] = draw_group_distribution(
            ax,
            roi_values,
            roi,
            id_col="subject_id",
            show_counts=False,
            positions=positions,
        )
    ax.axhline(0, color=AXIS_COLOR, linewidth=0.55, linestyle=(0, (2.2, 2.2)))
    ax.axvline(3.0, color=HAIRLINE, linewidth=0.55, zorder=0)
    ax.set_ylim(lower, upper)
    ax.set_xlim(-0.62, 6.62)
    ax.set_xlabel("")
    ax.set_ylabel("Activation (beta)")
    combined_ticks: list[float] = []
    combined_labels: list[str] = []
    for positions, roi in zip(distribution_positions, TARGET_ROIS):
        for position, group in zip(positions, GROUP_ORDER):
            combined_ticks.append(position)
            combined_labels.append(
                f"{group}\nn = {int(counts_by_roi[roi][group])}"
            )
    ax.set_xticks(combined_ticks)
    ax.set_xticklabels(combined_labels)
    for center, roi in zip((1.0, 5.0), TARGET_ROIS):
        ax.text(
            center,
            0.965,
            format_roi(roi),
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="bottom",
            fontsize=6.9,
            fontweight="semibold",
            color=NAVY,
            clip_on=False,
        )
    panel_header(
        ax,
        "C",
        "Regional activation",
        "Sentences vs Reversed",
        header_y=1.15,
    )
    style_axis(ax, grid_axis="y")
    clean_axis(ax)
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

    fig = plt.figure(figsize=(FIGURE_WIDTH, 4.05))
    ax = fig.add_axes([0.205, 0.255, 0.755, 0.605])
    cbar_ax = fig.add_axes([0.335, 0.105, 0.40, 0.020])
    annotation_labels = matrix.map(
        lambda value: "0.00" if abs(float(value)) < 0.005 else f"{value:.2f}"
    )
    heatmap = sns.heatmap(
        matrix,
        ax=ax,
        cmap=DIVERGING_CMAP,
        center=0,
        vmin=-1.0,
        vmax=1.0,
        annot=annotation_labels,
        fmt="",
        annot_kws={"fontsize": 5.65},
        linewidths=0.38,
        linecolor=PAPER,
        cbar=True,
        cbar_ax=cbar_ax,
        cbar_kws={"orientation": "horizontal", "ticks": [-1.0, -0.5, 0.0, 0.5, 1.0]},
        xticklabels=[format_contrast(value).replace(" vs ", "\nvs ") for value in contrasts],
        yticklabels=[format_roi(roi) for roi in rois],
    )
    values = matrix.to_numpy(dtype=float)
    for text, value in zip(heatmap.texts, values.ravel()):
        text.set_color("white" if abs(value) >= 0.60 else INK)
        text.set_fontweight("semibold" if abs(value) >= 0.80 else "normal")

    # Quietly separate task contrasts, baseline contrasts, and hemispheres.
    ax.axvline(4, color=NAVY, linewidth=0.72, alpha=0.7, zorder=5)
    ax.axhline(7, color=NAVY, linewidth=0.72, alpha=0.48, zorder=5)
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
                    edgecolor=NAVY,
                    linewidth=1.15,
                    zorder=6,
                )
            )
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(length=0, pad=3)
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center", linespacing=1.05)
    plt.setp(ax.get_yticklabels(), rotation=0)

    cbar_ax.set_xlabel("Cohen's d (AVH− vs AVH+)", labelpad=3)
    cbar_ax.tick_params(length=1.9, width=0.42, pad=1.5)

    fig.text(
        0.5,
        0.965,
        "Effect-size landscape",
        ha="center",
        va="top",
        fontsize=9.4,
        fontweight="semibold",
        color=NAVY,
    )
    save_figure(fig, OUTPUT_DIR / "Figure_2_effect_size_landscape")


# ---------------------------------------------------------------------------
# Figure 3: ROI definitions
# ---------------------------------------------------------------------------
def _roi_sphere_masks() -> tuple[object, dict[str, object]]:
    """Rasterize the declared MNI spheres on a 2 mm anatomical template."""
    template = datasets.load_mni152_template(resolution=2)
    shape = template.shape[:3]
    voxel_grid = np.indices(shape, dtype=np.float32)
    world_grid = np.einsum(
        "ij,jxyz->ixyz",
        np.asarray(template.affine[:3, :3], dtype=np.float32),
        voxel_grid,
    )
    world_grid += np.asarray(template.affine[:3, 3], dtype=np.float32)[
        :, None, None, None
    ]

    masks: dict[str, object] = {}
    for hemisphere in ("L_", "R_"):
        mask = np.zeros(shape, dtype=np.uint8)
        for key, center in ROIS.items():
            if not key.startswith(hemisphere):
                continue
            squared_distance = np.zeros(shape, dtype=np.float32)
            for axis, coordinate in enumerate(center):
                delta = world_grid[axis] - float(coordinate)
                squared_distance += delta * delta
            mask[squared_distance <= float(ROI_RADII[key] ** 2)] = 1
        masks[hemisphere] = new_img_like(template, mask)
    return template, masks


def figure_3_roi_definitions() -> None:
    fig = plt.figure(figsize=(FIGURE_WIDTH, 4.25))
    fig.text(
        0.5,
        0.965,
        "ROI definitions",
        ha="center",
        va="top",
        fontsize=9.4,
        fontweight="semibold",
        color=NAVY,
    )

    template, masks = _roi_sphere_masks()
    left_cmap = ListedColormap([MUTED_BLUE, MUTED_BLUE], name="roi_left")
    right_cmap = ListedColormap([CORAL, CORAL], name="roi_right")
    slice_specs = [
        ("x", -52),
        ("x", 52),
        ("y", -24),
        ("y", 20),
        ("z", 6),
        ("z", 16),
    ]
    map_left = 0.055
    map_right = 0.945
    map_gap = 0.008
    map_width = (map_right - map_left - map_gap * (len(slice_specs) - 1)) / len(
        slice_specs
    )
    for index, (mode, coordinate) in enumerate(slice_specs):
        left = map_left + index * (map_width + map_gap)
        ax_map = fig.add_axes([left, 0.585, map_width, 0.245])
        display = plot_anat(
            template,
            display_mode=mode,
            cut_coords=[coordinate],
            figure=fig,
            axes=ax_map,
            annotate=False,
            threshold=1e-6,
            draw_cross=False,
            black_bg=False,
            dim=-0.15,
            colorbar=False,
        )
        display.annotate(left_right=True, positions=False, size=5.2)
        for mask, cmap, outline in (
            (masks["L_"], left_cmap, NAVY),
            (masks["R_"], right_cmap, CORAL),
        ):
            display.add_overlay(
                mask,
                threshold=0.5,
                cmap=cmap,
                alpha=0.76,
                colorbar=False,
            )
            display.add_contours(
                mask,
                levels=[0.5],
                colors=[outline],
                linewidths=0.42,
                alpha=0.9,
            )
        fig.text(
            left + map_width / 2,
            0.575,
            f"{mode} = {coordinate}",
            ha="center",
            va="top",
            fontsize=5.2,
            color=MUTED_INK,
        )

    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=MUTED_BLUE,
            markeredgecolor=NAVY,
            markeredgewidth=0.45,
            markersize=4.6,
            label="Left hemisphere",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=CORAL,
            markeredgecolor=NAVY,
            markeredgewidth=0.45,
            markersize=4.6,
            label="Right hemisphere",
        ),
    ]
    ax_legend = fig.add_axes([0.055, 0.515, 0.89, 0.035])
    ax_legend.axis("off")
    ax_legend.legend(
        handles=handles,
        loc="center",
        ncol=2,
        columnspacing=1.3,
        handletextpad=0.35,
        frameon=False,
    )

    left_keys = [key for key in ROIS if key.startswith("L_")]
    right_keys = [key for key in ROIS if key.startswith("R_")]
    left_rows = [
        [
            _roi_display(key),
            f"{ROIS[key][0]:.0f}",
            f"{ROIS[key][1]:.0f}",
            f"{ROIS[key][2]:.0f}",
            f"{ROI_RADII[key]}",
        ]
        for key in left_keys
    ]
    right_rows = [
        [
            _roi_display(key),
            f"{ROIS[key][0]:.0f}",
            f"{ROIS[key][1]:.0f}",
            f"{ROIS[key][2]:.0f}",
            f"{ROI_RADII[key]}",
        ]
        for key in right_keys
    ]
    ax_left = fig.add_axes([0.055, 0.075, 0.42, 0.355])
    ax_right = fig.add_axes([0.525, 0.075, 0.42, 0.355])
    compact_table(ax_left, left_rows, "Left", MUTED_BLUE)
    compact_table(ax_right, right_rows, "Right", CORAL)
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

    fig = plt.figure(figsize=(FIGURE_WIDTH, 3.0))
    figure_title(
        fig,
        "Whole-brain group contrasts",
        "Descriptive AVH- versus AVH+ t maps",
        x=0.035,
        y=0.965,
    )
    grid = fig.add_gridspec(
        1,
        3,
        left=0.035,
        right=0.965,
        top=0.78,
        bottom=0.34,
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
            colorbar=False,
            annotate=False,
            figure=fig,
            axes=ax,
            black_bg=False,
        )
        ax.text(
            0.0,
            1.06,
            chr(65 + index),
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=8.3,
            fontweight="bold",
            color=NAVY,
            clip_on=False,
        )
        ax.text(
            0.10,
            1.06,
            format_contrast(contrast),
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=6.8,
            fontweight="semibold",
            color=INK,
            clip_on=False,
        )

    cbar_ax = fig.add_axes([0.36, 0.235, 0.28, 0.024])
    scalar = ScalarMappable(norm=Normalize(vmin=-vmax, vmax=vmax), cmap=DIVERGING_CMAP)
    cbar = fig.colorbar(scalar, cax=cbar_ax, orientation="horizontal")
    cbar.set_ticks([-vmax, 0, vmax])
    cbar.set_ticklabels([f"-{vmax:.1f}", "0", f"{vmax:.1f}"])
    cbar.ax.tick_params(length=1.8, width=0.4, pad=1.2, labelsize=5.8)
    cbar.set_label("t statistic", fontsize=6.0, labelpad=1.5)
    cbar.outline.set_linewidth(0.4)

    first_result = next(iter(metadata["results"].values()))
    add_note(
        fig,
        f"Two-sided voxel p < .001; n = {first_result['n_subjects']} (AVH- = {first_result['n_avh_minus']}, AVH+ = {first_result['n_avh_plus']}); "
        f"{metadata['n_permutations']:,} permutations; covariates: age, IQ, and sex.\n"
        "No cluster survives maximum-cluster-size FWER p < .05. Positive t is higher in AVH-; negative t is higher in AVH+.",
        x=0.035,
        y=0.025,
        width_rule=0.93,
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

    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, 3.15))
    figure_title(
        fig,
        "MVPA performance",
        "AVH- vs AVH+ · n = 40 (20/20) · shuffled five-fold KFold cross-validation",
        x=0.055,
        y=0.955,
    )
    y = np.arange(len(rows))
    ax.hlines(
        y,
        rows["auc"],
        rows["accuracy"],
        color=HAIRLINE,
        linewidth=0.85,
        zorder=1,
    )
    ax.scatter(
        rows["accuracy"],
        y,
        s=30,
        marker="o",
        facecolor=MUTED_BLUE,
        edgecolor=NAVY,
        linewidth=0.48,
        label="Accuracy",
        zorder=3,
    )
    ax.scatter(
        rows["auc"],
        y,
        s=34,
        marker="D",
        facecolor=PAPER,
        edgecolor=SOFT_TEAL,
        linewidth=0.85,
        label="ROC AUC",
        zorder=3,
    )
    ax.axvline(0.50, color=AXIS_COLOR, linewidth=0.62, linestyle=(0, (2.2, 2.2)))
    for yi, row in rows.iterrows():
        ax.text(
            row["accuracy"] + 0.012,
            yi,
            f"{row['accuracy']:.3f}",
            ha="left",
            va="center",
            fontsize=5.95,
            color=MUTED_BLUE,
        )
        ax.text(
            row["auc"] - 0.012,
            yi,
            f"{row['auc']:.3f}",
            ha="right",
            va="center",
            fontsize=5.95,
            color=SOFT_TEAL,
        )
        ax.text(
            0.735,
            yi,
            f"p = {row['p_value']:.3f}",
            ha="right",
            va="center",
            fontsize=6.0,
            color=MUTED_INK,
        )
    ax.set_yticks(y)
    ax.set_yticklabels(rows["label"])
    ax.invert_yaxis()
    ax.set_xlim(0.20, 0.76)
    ax.set_xlabel("Cross-validated score")
    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.0, 1.13),
        ncol=2,
        handletextpad=0.38,
        columnspacing=1.0,
    )
    style_axis(ax, grid_axis="x")
    clean_axis(ax)
    fig.subplots_adjust(left=0.255, right=0.98, top=0.76, bottom=0.24)
    add_note(
        fig,
        "Dashed line marks chance (0.50). Permutation p values use the stored 100-permutation analysis; increase before confirmatory use. KFold random_state = 42.",
        x=0.055,
        y=0.025,
        width_rule=0.925,
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

    fig, axes = plt.subplots(2, 3, figsize=(FIGURE_WIDTH, 4.85))
    figure_title(
        fig,
        "Sample and quality control",
        "Participant-level distributions and cohort composition",
        x=0.055,
        y=0.97,
    )

    def distribution(
        ax,
        data: pd.DataFrame,
        variable: str,
        label: str,
        title: str,
        ylabel: str,
        id_col: str,
    ) -> None:
        draw_group_distribution(
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
        axes[0, 2],
        qc,
        "mean_fd",
        "C",
        "Mean framewise displacement",
        "Mean FD (mm)",
        "subject_id",
    )
    axes[0, 2].axhline(
        0.5, color=AXIS_COLOR, linewidth=0.62, linestyle=(0, (2.2, 2.2))
    )
    axes[0, 2].text(
        2.46,
        0.5,
        "0.5 mm",
        ha="right",
        va="bottom",
        fontsize=5.65,
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

    counts = participants.groupby("group", observed=True).size().reindex(GROUP_ORDER)
    axes[1, 1].bar(
        GROUP_ORDER,
        counts.to_numpy(dtype=float),
        width=0.56,
        color=[lighten(PALETTE[group], 0.12) for group in GROUP_ORDER],
        edgecolor=[PALETTE[group] for group in GROUP_ORDER],
        linewidth=0.62,
        zorder=2,
    )
    for index, value in enumerate(counts):
        axes[1, 1].text(
            index,
            value + 0.50,
            f"n = {int(value)}",
            ha="center",
            va="bottom",
            fontsize=6.0,
        )
    axes[1, 1].set_ylim(0, max(counts) * 1.20)
    axes[1, 1].set_ylabel("Participants")
    panel_header(axes[1, 1], "E", "Analysis cohort")
    style_axis(axes[1, 1], grid_axis="y")
    clean_axis(axes[1, 1])

    sex_counts = (
        participants.groupby(["group", "sex"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reindex(GROUP_ORDER)
    )
    sex_proportions = sex_counts.div(sex_counts.sum(axis=1), axis=0)
    bottom = np.zeros(len(GROUP_ORDER), dtype=float)
    sex_styles = {
        "male": {"color": NAVY, "hatch": ""},
        "female": {"color": PALE_BLUE, "hatch": "////"},
    }
    for sex in [value for value in ("male", "female") if value in sex_counts.columns]:
        values = sex_proportions[sex].to_numpy(dtype=float)
        bars = axes[1, 2].bar(
            GROUP_ORDER,
            values,
            bottom=bottom,
            width=0.56,
            color=sex_styles[sex]["color"],
            hatch=sex_styles[sex]["hatch"],
            edgecolor=PAPER if sex == "male" else AXIS_COLOR,
            linewidth=0.42,
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
                    fontsize=5.8,
                    color=PAPER if sex == "male" else INK,
                )
        bottom += values
    axes[1, 2].set_ylim(0, 1)
    axes[1, 2].set_ylabel("Proportion")
    panel_header(axes[1, 2], "F", "Sex distribution")
    axes[1, 2].legend(
        loc="upper right",
        bbox_to_anchor=(1.0, 1.14),
        ncol=2,
        handlelength=0.95,
        handletextpad=0.30,
        columnspacing=0.60,
    )
    style_axis(axes[1, 2], grid_axis="y")
    clean_axis(axes[1, 2])

    fig.subplots_adjust(
        left=0.075,
        right=0.99,
        top=0.84,
        bottom=0.14,
        hspace=0.62,
        wspace=0.38,
    )
    add_note(
        fig,
        "Points are participants; violins show density and boxes show median and IQR. Dashed line in C marks mean FD = 0.5 mm. Panel F numbers are participant counts within sex strata.",
        x=0.055,
        y=0.025,
        width_rule=0.935,
    )
    save_figure(fig, OUTPUT_DIR / "Supplement_Figure_3_sample_and_QC")


# ---------------------------------------------------------------------------
# Supplementary Figure 4: exploratory connectivity and laterality
# ---------------------------------------------------------------------------
def supplement_figure_4_exploratory_network() -> None:
    connectivity = pd.read_csv(DATA_DIR / "connectivity_uncorrected_edges.csv").sort_values(
        "diff"
    )
    laterality = pd.read_csv(DATA_DIR / "laterality_stats.csv")
    laterality = laterality[laterality["comparison"] == "AVH-_vs_AVH+"].copy()
    laterality["abs_d"] = laterality["cohens_d"].abs()
    laterality = laterality.nlargest(10, "abs_d").sort_values("cohens_d")

    fig = plt.figure(figsize=(FIGURE_WIDTH, 5.45))
    figure_title(
        fig,
        "Exploratory network effects",
        "Connectivity and laterality comparisons",
        x=0.055,
        y=0.97,
    )
    grid = fig.add_gridspec(
        2,
        1,
        height_ratios=[0.82, 2.42],
        left=0.33,
        right=0.96,
        top=0.82,
        bottom=0.13,
        hspace=0.57,
    )

    ax = fig.add_subplot(grid[0])
    labels = [
        f"{format_roi(roi1)} to {format_roi(roi2)}"
        for roi1, roi2 in zip(connectivity["roi1"], connectivity["roi2"])
    ]
    y = np.arange(len(connectivity))
    ax.hlines(y, 0, connectivity["diff"], color=HAIRLINE, linewidth=1.1, zorder=1)
    for yi, (_, row) in enumerate(connectivity.iterrows()):
        positive = row["diff"] > 0
        color = MUTED_BLUE if positive else CORAL
        ax.scatter(
            row["diff"],
            yi,
            s=30,
            marker="o" if positive else "^",
            facecolor=color,
            edgecolor=NAVY,
            linewidth=0.45,
            zorder=3,
        )
        offset = 0.014
        ax.text(
            row["diff"] + offset,
            yi + (0.10 if not positive else 0.0),
            f"{row['diff']:+.3f}  ·  p = {row['p_value']:.3f}",
            ha="left",
            va="center",
            fontsize=5.9,
            color=MUTED_INK,
        )
    ax.axvline(0, color=AXIS_COLOR, linewidth=0.62)
    ax.set_xlim(-0.25, 0.25)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Difference in Fisher z (AVH- minus AVH+)")
    panel_header(
        ax,
        "A",
        "Connectivity differences",
        "Uncorrected p < .05",
        header_y=1.24,
    )
    style_axis(ax, grid_axis="x")
    clean_axis(ax)

    ax = fig.add_subplot(grid[1])
    laterality_labels = [
        f"{format_contrast(contrast)}; {roi_pair.replace('_', ' ')}"
        for contrast, roi_pair in zip(laterality["contrast"], laterality["roi_pair"])
    ]
    y = np.arange(len(laterality))
    ax.hlines(y, 0, laterality["cohens_d"], color=HAIRLINE, linewidth=0.92, zorder=1)
    for yi, (_, row) in enumerate(laterality.iterrows()):
        positive = row["cohens_d"] > 0
        ax.scatter(
            row["cohens_d"],
            yi,
            s=24,
            marker="o" if positive else "^",
            facecolor=MUTED_BLUE if positive else CORAL,
            edgecolor=NAVY,
            linewidth=0.42,
            zorder=3,
        )
        ax.text(
            0.55,
            yi,
            f"d = {row['cohens_d']:+.3f}  ·  p = {row['p_value']:.3f}",
            ha="left",
            va="center",
            fontsize=5.85,
            color=MUTED_INK,
        )
    ax.axvline(0, color=AXIS_COLOR, linewidth=0.62)
    ax.set_xlim(-0.55, 0.76)
    ax.set_yticks(y)
    ax.set_yticklabels(laterality_labels, fontsize=6.05)
    ax.set_xlabel("Cohen's d (AVH- vs AVH+)")
    panel_header(ax, "B", "Laterality effects", "Ten largest absolute effects")
    style_axis(ax, grid_axis="x")
    clean_axis(ax)

    add_note(
        fig,
        "Exploratory results only. Connectivity differences are uncorrected and none survive FDR; no laterality comparison reaches p < .05.",
        x=0.055,
        y=0.025,
        width_rule=0.905,
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
    print(f"Created seven manuscript figure triplets in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
