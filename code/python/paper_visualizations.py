"""
Publication-ready figures for the manuscript.

Builds a small set of composite figures tuned for a paper (rather than a poster)
into `results/poster/paper_visualizations/`:

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

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).parent))
from poster_style import (  # noqa: E402
    GROUP_ORDER,
    PALETTE,
    apply_style,
    format_contrast,
    format_roi,
)
from surface_brain_plots import ROI_RADII, ROIS, _roi_display, plot_roi_locations  # noqa: E402

warnings.filterwarnings("ignore")
apply_style()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "results" / "data"
POSTER_DIR = BASE_DIR / "results" / "poster"
PAPER_DIR = POSTER_DIR / "paper_visualizations"
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
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=400, bbox_inches="tight", facecolor="white")
    plt.close(fig)


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

    fig = plt.figure(figsize=(15, 11))
    gs = fig.add_gridspec(2, 2, hspace=0.38, wspace=0.26,
                          left=0.08, right=0.96, top=0.9, bottom=0.07)

    # (A) Targeted post hoc forest --------------------------------------------
    ax = fig.add_subplot(gs[0, 0])
    posthoc_path = POSTHOC_DIR / "posthoc_targeted.csv"
    if posthoc_path.exists():
        posthoc = pd.read_csv(posthoc_path)
        full = posthoc[posthoc["sample"].str.startswith("full")].sort_values("d_adj")
        y = np.arange(len(full))
        colors = ["#27ae60" if s else "#e67e22" for s in full["survives_bonferroni"]]
        ax.errorbar(full["d_adj"], y,
                    xerr=[full["d_adj"] - full["d_adj_ci_lo"], full["d_adj_ci_hi"] - full["d_adj"]],
                    fmt="none", ecolor="gray", capsize=4, lw=1.3)
        ax.scatter(full["d_adj"], y, c=colors, s=150, edgecolor="black", zorder=5)
        ax.axvline(0, color="black", lw=0.7, ls="--", alpha=0.6)
        ax.set_yticks(y)
        ax.set_yticklabels([format_roi(r) for r in full["roi"]])
        for yi, (d, p) in enumerate(zip(full["d_adj"], full["p_bonferroni"])):
            ax.annotate(f"d={d:+.2f}, p_bonf={p:.3f}", (d, yi),
                        textcoords="offset points", xytext=(0, 11),
                        ha="center", fontsize=9, fontweight="bold")
        ax.set_xlim(min(full["d_adj_ci_lo"].min(), -0.2) - 0.25, 0.35)
    ax.set_xlabel("Adjusted Cohen's d  (AVH- vs AVH+)")
    ax.set_title("A  Post hoc targeted ROIs (ANCOVA)\nsentences > reversed, Bonferroni m=2",
                 fontsize=13, fontweight="bold", loc="left")

    # (B) Primary symptom correlation -----------------------------------------
    ax = fig.add_subplot(gs[0, 1])
    hit = _primary_correlation_hit()
    avh = parts[parts["group"] == "AVH+"].dropna(subset=["psyrats"])
    if hit is not None and not avh.empty:
        roi_path = ROI_DIR / f"{hit['contrast']}_roi_values.csv"
        if roi_path.exists():
            merged = pd.read_csv(roi_path).merge(
                avh[["participant_id", "psyrats"]],
                left_on="subject_id", right_on="participant_id", how="inner")
            if hit["roi"] in merged.columns:
                x = merged[hit["roi"]].to_numpy(dtype=float)
                yv = merged["psyrats"].to_numpy(dtype=float)
                m = np.isfinite(x) & np.isfinite(yv)
                sns.regplot(x=x[m], y=yv[m], ax=ax, color=PALETTE["AVH+"], truncate=False,
                            scatter_kws=dict(s=70, edgecolor="black", linewidths=0.6, alpha=0.85),
                            line_kws=dict(color="black", lw=1.6, ls="--"))
                ax.text(0.04, 0.96,
                        f"partial r = {hit['partial_r']:+.2f}  (age, IQ)\n"
                        f"p = {hit['partial_p']:.4f}    FDR p = {hit['partial_fdr']:.3f}",
                        transform=ax.transAxes, va="top", ha="left", fontsize=10,
                        fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.45", facecolor="white",
                                  edgecolor="#c0392b", linewidth=1.2, alpha=0.92))
        ax.set_xlabel("Activation (β)")
        ax.set_ylabel("PSYRATS Total")
        ax.set_title(f"B  Symptom correlation (AVH+)\n{format_roi(hit['roi'])}  ·  "
                     f"{format_contrast(hit['contrast'])}",
                     fontsize=13, fontweight="bold", loc="left")

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
                       palette=PALETTE, inner=None, cut=0, linewidth=1,
                       saturation=0.85, legend=False, ax=ax)
        for c in ax.collections:
            c.set_alpha(0.4)
        sns.boxplot(data=sub, x="group", y=roi, order=GROUP_ORDER, width=0.18,
                    showcaps=True, boxprops={"facecolor": "white", "zorder": 5},
                    showfliers=False, medianprops={"color": "black", "linewidth": 1.5}, ax=ax)
        sns.stripplot(data=sub, x="group", y=roi, hue="group", order=GROUP_ORDER,
                      palette=PALETTE, size=4, alpha=0.85, jitter=0.18, legend=False,
                      edgecolor="white", linewidth=0.4, ax=ax)
        ax.axhline(0, color="black", lw=0.6, ls="--", alpha=0.5)
        ax.set_xlabel("")
        ax.set_ylabel("Activation (β)")
        ax.set_title(f"{tag}  {format_roi(roi)}  ·  {format_contrast(TARGET_CONTRAST)}",
                     fontsize=13, fontweight="bold", loc="left")

    fig.suptitle("Figure 1.  Group differences and symptom correlation in AVH",
                 fontsize=19, fontweight="bold", y=0.965)
    _save(fig, PAPER_DIR / "figure1_main_results.png")
    print(f"  figure1 -> {PAPER_DIR / 'figure1_main_results.png'}")


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

    fig, ax = plt.subplots(figsize=(11, 8))
    vmax = float(np.nanmax(np.abs(pivot.to_numpy())))
    sns.heatmap(pivot, ax=ax, cmap="RdBu_r", center=0, vmin=-vmax, vmax=vmax,
                annot=True, fmt=".2f", annot_kws={"fontsize": 9},
                linewidths=0.5, linecolor="white",
                cbar_kws={"label": "Cohen's d  (AVH- vs AVH+)"},
                xticklabels=[format_contrast(c) for c in contrasts],
                yticklabels=[format_roi(r) for r in rois])

    # Box the omnibus FDR-significant cells
    sig_cells = _omnibus_fdr_sig_cells()
    for (contrast, roi) in sig_cells:
        if roi in rois and contrast in contrasts:
            ci, ri = contrasts.index(contrast), rois.index(roi)
            ax.add_patch(Rectangle((ci, ri), 1, 1, fill=False,
                                   edgecolor="black", lw=2.6, zorder=6))
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title("ROI x Contrast Effect Sizes (AVH- vs AVH+)\n"
                 "black boxes = omnibus within-contrast FDR < 0.05",
                 fontsize=15, fontweight="bold")
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    fig.tight_layout()
    _save(fig, PAPER_DIR / "effect_size_heatmap.png")
    print(f"  heatmap -> {PAPER_DIR / 'effect_size_heatmap.png'}")


# ===========================================================================
# ROI definition panel (map + coordinate table)
# ===========================================================================
def roi_definition_panel() -> None:
    map_path = BRAIN_DIR / "roi_locations.png"
    if not map_path.exists():
        plot_roi_locations(map_path)

    fig = plt.figure(figsize=(16, 7))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.45, 1.0], wspace=0.05)

    ax_map = fig.add_subplot(gs[0, 0])
    ax_map.imshow(mpimg.imread(str(map_path)))
    ax_map.axis("off")
    ax_map.set_title("A  ROI locations (glass brain)", fontsize=14,
                     fontweight="bold", loc="left")

    ax_tbl = fig.add_subplot(gs[0, 1])
    ax_tbl.axis("off")
    ax_tbl.set_title("B  ROI definitions (MNI)", fontsize=14, fontweight="bold", loc="left")
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
        colWidths=[0.5, 0.34, 0.16], cellLoc="left", loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.6)
    # Style header.
    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#2c3e50")
            cell.set_text_props(color="white", fontweight="bold")

    fig.suptitle("Region-of-interest definitions", fontsize=17, fontweight="bold", y=1.0)
    _save(fig, PAPER_DIR / "roi_definition_panel.png")
    print(f"  roi definition -> {PAPER_DIR / 'roi_definition_panel.png'}")


# ===========================================================================
# README
# ===========================================================================
def write_readme() -> None:
    lines = [
        "# Paper Visualizations",
        "",
        "Publication-tuned composites generated by",
        "`code/python/paper_visualizations.py` from the consolidated stats in",
        "`results/data/`. Re-run with:",
        "",
        "    python code/python/paper_visualizations.py",
        "",
        "## Figures",
        "",
        "- **figure1_main_results.png** — Core results figure. (A) Post hoc targeted "
        "ANCOVA forest for sentences > reversed (L MTG, L STS; Bonferroni m=2). "
        "(B) Primary PSYRATS symptom correlation (R STG posterior, partial r | age, IQ, "
        "FDR < 0.05). (C, D) Activation rainclouds by group for the two targeted ROIs.",
        "- **effect_size_heatmap.png** — ROI x contrast Cohen's d (AVH- vs AVH+); cells "
        "passing the omnibus within-contrast FDR (< 0.05) are outlined in black.",
        "- **roi_definition_panel.png** — Glass-brain ROI map plus an MNI-coordinate "
        "reference table with the extraction radius for each sphere. Overlapping spheres are not independent.",
        "",
        "## Conventions",
        "",
        "- 400 dpi PNG, white background, Arial/Helvetica.",
        "- Groups: HC = gray, AVH- = blue, AVH+ = red.",
        "- Negative Cohen's d (AVH- vs AVH+) = higher activation in AVH+.",
        "",
    ]
    (PAPER_DIR / "README.md").write_text("\n".join(lines))


def main() -> None:
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    print("\n" + "=" * 70)
    print("BUILDING results/poster/paper_visualizations/")
    print("=" * 70)
    figure1_main_results()
    effect_size_heatmap()
    roi_definition_panel()
    write_readme()
    print(f"\nDone. See {PAPER_DIR}\n")


if __name__ == "__main__":
    main()
