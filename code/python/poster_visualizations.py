"""
Poster-ready visualization orchestrator.

Reads the consolidated stats in `results/data/` and writes the entire
`results/poster/` tree (brain maps, ROI effects, correlations, classification,
connectivity, laterality, demographics/QC, and a hero summary figure) using a
single shared style.

Usage:
    python code/python/poster_visualizations.py
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
from matplotlib.patches import Patch
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from poster_style import (  # noqa: E402
    GROUP_ORDER,
    PALETTE,
    SEX_PALETTE,
    apply_style,
    format_contrast,
    format_roi,
)
import surface_brain_plots  # noqa: E402

warnings.filterwarnings("ignore")
apply_style()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "results" / "data"
POSTER_DIR = BASE_DIR / "results" / "poster"
PARTICIPANTS = BASE_DIR / "participants.tsv"

ROI_DIR = DATA_DIR / "roi_values"
EFFECT_DIR = DATA_DIR / "effect_sizes"
CORR_DIR = DATA_DIR / "correlations"

POSTER_SECTIONS = [
    "01_brain_maps",
    "02_roi_effects",
    "03_correlations",
    "04_classification",
    "05_connectivity",
    "06_laterality",
    "07_demographics_qc",
    "summary",
]

KEY_CONTRASTS = [
    "sentences_vs_reversed",
    "speech_vs_reversed",
    "words_vs_sentences",
    "words_vs_reversed",
]

ROI_ORDER = [
    "L_STG_posterior", "L_STG_anterior", "L_Heschl",
    "L_MTG", "L_STS", "L_IFG_triangularis", "L_IFG_opercularis",
    "R_STG_posterior", "R_STG_anterior", "R_Heschl",
    "R_MTG", "R_IFG",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ensure_sections() -> None:
    for s in POSTER_SECTIONS:
        (POSTER_DIR / s).mkdir(parents=True, exist_ok=True)


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _sig_marker(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    if p < 0.10:
        return "."
    return ""


def _load_participants() -> pd.DataFrame:
    df = pd.read_csv(PARTICIPANTS, sep="\t")
    for col in ("age", "iq", "psyrats"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["group"] = pd.Categorical(df["group"], categories=GROUP_ORDER, ordered=True)
    return df


# ===========================================================================
# 01 BRAIN MAPS - delegate to surface_brain_plots
# ===========================================================================
def make_brain_maps() -> None:
    surface_brain_plots.main()


# ===========================================================================
# 02 ROI EFFECTS - raincloud + grouped bar + forest plot
# ===========================================================================
def _melt_roi_values(contrast: str) -> pd.DataFrame | None:
    path = ROI_DIR / f"{contrast}_roi_values.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    rois = [c for c in df.columns if c not in ("subject_id", "group")]
    long = df.melt(id_vars=["subject_id", "group"], value_vars=rois,
                   var_name="roi", value_name="activation")
    long["group"] = pd.Categorical(long["group"], categories=GROUP_ORDER, ordered=True)
    long["roi"] = pd.Categorical(long["roi"], categories=ROI_ORDER, ordered=True)
    return long.dropna(subset=["activation"]).sort_values(["roi", "group"])


def _plot_raincloud_panel(ax, sub: pd.DataFrame, title: str) -> None:
    """Half-violin + box + strip per group on a single axis (one ROI)."""
    sns.violinplot(
        data=sub, x="group", y="activation", hue="group", ax=ax,
        order=GROUP_ORDER, palette=PALETTE, inner=None,
        cut=0, linewidth=1, saturation=0.85, legend=False,
    )
    for collection in ax.collections:
        collection.set_alpha(0.45)
    sns.boxplot(
        data=sub, x="group", y="activation", ax=ax, order=GROUP_ORDER,
        width=0.18, showcaps=True, boxprops={"facecolor": "white", "zorder": 5},
        showfliers=False, whiskerprops={"linewidth": 1.2}, medianprops={"color": "black", "linewidth": 1.5},
    )
    sns.stripplot(
        data=sub, x="group", y="activation", hue="group", ax=ax, order=GROUP_ORDER,
        palette=PALETTE, size=4, alpha=0.85, jitter=0.18, legend=False, edgecolor="white", linewidth=0.4,
    )
    ax.axhline(0, color="black", lw=0.6, ls="--", alpha=0.5)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Activation (β)")


def make_roi_effects() -> None:
    out = POSTER_DIR / "02_roi_effects"
    for contrast in KEY_CONTRASTS:
        long = _melt_roi_values(contrast)
        if long is None:
            continue

        # 12-ROI raincloud grid
        rois = [r for r in ROI_ORDER if r in long["roi"].unique()]
        n = len(rois)
        ncols = 4
        nrows = int(np.ceil(n / ncols))
        fig, axes = plt.subplots(nrows, ncols, figsize=(4.2 * ncols, 3.6 * nrows), sharey=False)
        axes = np.atleast_2d(axes).flatten()
        for i, roi in enumerate(rois):
            sub = long[long["roi"] == roi]
            _plot_raincloud_panel(axes[i], sub, format_roi(roi))
        for j in range(len(rois), len(axes)):
            axes[j].set_visible(False)
        handles = [Patch(facecolor=PALETTE[g], edgecolor="black", label=g) for g in GROUP_ORDER]
        fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.99, 0.99),
                   ncol=3, fontsize=12, frameon=True)
        fig.suptitle(f"{format_contrast(contrast)}: ROI Activation by Group",
                     fontsize=18, fontweight="bold", y=1.005)
        fig.tight_layout()
        _save(fig, out / f"{contrast}_raincloud.png")

        # Grouped bar with SE bars + significance
        agg = long.groupby(["roi", "group"], observed=True)["activation"].agg(["mean", "sem", "count"]).reset_index()
        pairwise_path = ROI_DIR / f"{contrast}_roi_pairwise.csv"
        sig_lookup: dict[tuple[str, str], float] = {}
        if pairwise_path.exists():
            pw = pd.read_csv(pairwise_path)
            for _, row in pw.iterrows():
                sig_lookup[(row["roi"], row["comparison"])] = row["p_value"]

        x = np.arange(len(rois))
        width = 0.26
        fig, ax = plt.subplots(figsize=(16, 7))
        for i, group in enumerate(GROUP_ORDER):
            sub = agg[agg["group"] == group].set_index("roi").reindex(rois)
            ax.bar(x + (i - 1) * width, sub["mean"], width, yerr=sub["sem"],
                   color=PALETTE[group], edgecolor="black", linewidth=0.8,
                   label=group, capsize=3, alpha=0.92)
        ax.axhline(0, color="black", lw=0.6, ls="--", alpha=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels([format_roi(r) for r in rois], rotation=35, ha="right")
        ax.set_ylabel("Mean Activation (β) ± SEM")
        ax.set_title(f"{format_contrast(contrast)}: Group Comparison",
                     fontsize=18, fontweight="bold")
        ax.legend(title="Group", loc="upper right", frameon=True)

        ymax = agg["mean"].max() + agg["sem"].max()
        for i, roi in enumerate(rois):
            p = sig_lookup.get((roi, "AVH+_vs_AVH-"))
            if p is not None and p < 0.10:
                ax.text(x[i] + width, ymax * 1.05, _sig_marker(p),
                        ha="center", va="bottom", fontsize=14, fontweight="bold")
        fig.tight_layout()
        _save(fig, out / f"{contrast}_grouped_bars.png")

    # Combined forest plot of effect sizes (HC vs AVH+ for the key contrasts)
    summary_path = EFFECT_DIR / "effect_sizes_summary.csv"
    if summary_path.exists():
        es = pd.read_csv(summary_path)
        fp = es[(es["contrast"].isin(KEY_CONTRASTS)) & (es["comparison"] == "AVH-_vs_AVH+")].copy()
        if not fp.empty:
            fp["roi_label"] = fp["roi"].map(format_roi)
            fp["contrast_label"] = fp["contrast"].map(format_contrast)
            fp["abs_d"] = fp["cohens_d"].abs()
            fp = fp.sort_values(["contrast_label", "abs_d"], ascending=[True, True])

            fig, ax = plt.subplots(figsize=(12, max(6, len(fp) * 0.35)))
            y = np.arange(len(fp))
            colors = ["#27ae60" if abs(d) >= 0.5 else "#3498db" if abs(d) >= 0.2 else "#95a5a6"
                      for d in fp["cohens_d"]]
            ax.errorbar(fp["cohens_d"], y,
                        xerr=[fp["cohens_d"] - fp["d_ci_lower"], fp["d_ci_upper"] - fp["cohens_d"]],
                        fmt="none", ecolor="gray", capsize=3, lw=1)
            ax.scatter(fp["cohens_d"], y, c=colors, s=80, edgecolor="black", zorder=5)
            ax.axvline(0, color="black", lw=0.6, ls="--", alpha=0.5)
            ax.set_yticks(y)
            ax.set_yticklabels([f"{c}  ·  {r}" for c, r in zip(fp["contrast_label"], fp["roi_label"])],
                               fontsize=10)
            ax.set_xlabel("Cohen's d (AVH- vs AVH+)  [95% CI]")
            ax.set_title("Effect Sizes: AVH- vs AVH+", fontsize=18, fontweight="bold")
            handles = [
                Line2D([0], [0], marker="o", color="w", markerfacecolor="#27ae60",
                       markersize=10, label="Medium / large (|d| ≥ 0.5)"),
                Line2D([0], [0], marker="o", color="w", markerfacecolor="#3498db",
                       markersize=10, label="Small (0.2 ≤ |d| < 0.5)"),
                Line2D([0], [0], marker="o", color="w", markerfacecolor="#95a5a6",
                       markersize=10, label="Negligible (|d| < 0.2)"),
            ]
            ax.legend(handles=handles, loc="lower right", frameon=True)
            fig.tight_layout()
            _save(fig, out / "effect_sizes_forest.png")


# ===========================================================================
# 03 CORRELATIONS (PSYRATS)
# ===========================================================================
def make_correlations() -> None:
    out = POSTER_DIR / "03_correlations"
    parts = _load_participants()
    avh = parts[parts["group"] == "AVH+"].dropna(subset=["psyrats"])
    if avh.empty:
        return

    for contrast in KEY_CONTRASTS:
        roi_path = ROI_DIR / f"{contrast}_roi_values.csv"
        corr_path = CORR_DIR / f"{contrast}_psyrats_correlations.csv"
        if not roi_path.exists() or not corr_path.exists():
            continue

        roi_df = pd.read_csv(roi_path)
        merged = roi_df.merge(avh[["participant_id", "psyrats"]],
                              left_on="subject_id", right_on="participant_id", how="inner")
        if merged.empty:
            continue
        corr_df = pd.read_csv(corr_path).set_index("roi")

        rois = [r for r in ROI_ORDER if r in roi_df.columns]
        ncols = 4
        nrows = int(np.ceil(len(rois) / ncols))
        fig, axes = plt.subplots(nrows, ncols, figsize=(4.2 * ncols, 3.6 * nrows))
        axes = np.atleast_2d(axes).flatten()
        for i, roi in enumerate(rois):
            ax = axes[i]
            x = merged[roi].values
            y = merged["psyrats"].values
            mask = np.isfinite(x) & np.isfinite(y)
            ax.scatter(x[mask], y[mask], color=PALETTE["AVH+"], s=55,
                       edgecolor="black", linewidth=0.6, alpha=0.85)
            if mask.sum() > 2:
                slope, intercept = np.polyfit(x[mask], y[mask], 1)
                xs = np.linspace(x[mask].min(), x[mask].max(), 30)
                ax.plot(xs, slope * xs + intercept, color="black", lw=1.3, ls="--", alpha=0.8)

            r = corr_df.loc[roi, "pearson_r"] if roi in corr_df.index else np.nan
            p = corr_df.loc[roi, "pearson_p"] if roi in corr_df.index else np.nan
            sig = _sig_marker(p) if np.isfinite(p) else ""
            color = SIG_OK if (np.isfinite(p) and p < 0.05) else "black"
            ax.set_title(f"{format_roi(roi)}\n r = {r:+.2f}, p = {p:.3f}{sig}",
                         fontsize=11, fontweight="bold", color=color)
            ax.set_xlabel("Activation (β)", fontsize=10)
            ax.set_ylabel("PSYRATS", fontsize=10)
        for j in range(len(rois), len(axes)):
            axes[j].set_visible(False)
        fig.suptitle(f"{format_contrast(contrast)}: ROI Activation vs PSYRATS (AVH+)",
                     fontsize=18, fontweight="bold", y=1.005)
        fig.tight_layout()
        _save(fig, out / f"{contrast}_psyrats_scatter.png")


SIG_OK = "#c0392b"  # title color when significant


# ===========================================================================
# 04 CLASSIFICATION (MVPA)
# ===========================================================================
def make_classification() -> None:
    out = POSTER_DIR / "04_classification"
    cls_path = DATA_DIR / "svm_weights" / "classification_results.json"
    if not cls_path.exists():
        return
    with open(cls_path) as f:
        data = json.load(f)
    rows = pd.DataFrame(data["results"])
    rows["contrast_label"] = rows["contrast"].map(format_contrast)

    # Accuracy + AUC bar plot
    x = np.arange(len(rows))
    width = 0.36
    fig, ax = plt.subplots(figsize=(11, 6))
    bars1 = ax.bar(x - width / 2, rows["accuracy"], width, color="#3498db",
                   edgecolor="black", lw=0.8, label="Accuracy")
    bars2 = ax.bar(x + width / 2, rows["auc"], width, color="#e67e22",
                   edgecolor="black", lw=0.8, label="ROC AUC")
    ax.axhline(0.5, color="black", lw=1.0, ls="--", alpha=0.7, label="Chance")
    ax.set_xticks(x)
    ax.set_xticklabels(rows["contrast_label"], rotation=15, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Score")
    ax.set_title("MVPA SVM: AVH- vs AVH+ Classification", fontsize=18, fontweight="bold")
    ax.legend(loc="upper right")
    for bar, p in zip(bars1, rows["p_value"]):
        sig = _sig_marker(p)
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"p = {p:.3f}{sig}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    _save(fig, out / "svm_accuracy.png")

    # Per-contrast permutation strip
    fig, ax = plt.subplots(figsize=(10, 5))
    accs = rows["accuracy"].values
    aucs = rows["auc"].values
    pvals = rows["p_value"].values
    labels = rows["contrast_label"].values
    yy = np.arange(len(rows))
    ax.scatter(accs, yy, s=140, color="#3498db", edgecolor="black", zorder=4, label="Accuracy")
    ax.scatter(aucs, yy, s=140, color="#e67e22", edgecolor="black", zorder=4, label="ROC AUC")
    for i, p in enumerate(pvals):
        ax.text(max(accs[i], aucs[i]) + 0.02, yy[i], f"p = {p:.3f}{_sig_marker(p)}",
                va="center", fontsize=10)
    ax.axvline(0.5, color="black", lw=1.0, ls="--", alpha=0.7)
    ax.set_yticks(yy)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Score")
    ax.set_title("Classification Performance with Permutation p-values",
                 fontsize=16, fontweight="bold")
    ax.legend(loc="lower right")
    fig.tight_layout()
    _save(fig, out / "svm_permutation_summary.png")


# ===========================================================================
# 05 CONNECTIVITY
# ===========================================================================
def make_connectivity() -> None:
    out = POSTER_DIR / "05_connectivity"
    summary_path = DATA_DIR / "connectivity.json"
    sig_path = DATA_DIR / "connectivity_significant.csv"
    if not summary_path.exists():
        return
    with open(summary_path) as f:
        meta = json.load(f)

    rois = meta["roi_names"]

    # Build a "difference" matrix from significant connections (sparse)
    n = len(rois)
    diff = np.zeros((n, n))
    pmat = np.ones((n, n))
    if sig_path.exists():
        sig = pd.read_csv(sig_path)
        idx = {r: i for i, r in enumerate(rois)}
        for _, row in sig.iterrows():
            i, j = idx[row["roi1"]], idx[row["roi2"]]
            diff[i, j] = diff[j, i] = row["diff"]
            pmat[i, j] = pmat[j, i] = row["p_value"]

    fig, ax = plt.subplots(figsize=(11, 9))
    vmax = max(0.05, np.abs(diff).max())
    sns.heatmap(diff, ax=ax, cmap="RdBu_r", center=0, vmin=-vmax, vmax=vmax,
                xticklabels=[format_roi(r) for r in rois],
                yticklabels=[format_roi(r) for r in rois],
                cbar_kws={"label": "AVH-  −  AVH+ (Δ Fisher z)"},
                square=True, linewidths=0.4, linecolor="white")
    ax.set_title("Functional Connectivity Difference: AVH- vs AVH+",
                 fontsize=16, fontweight="bold")
    plt.setp(ax.get_xticklabels(), rotation=40, ha="right")
    fig.tight_layout()
    _save(fig, out / "connectivity_matrix.png")

    if sig_path.exists():
        sig = pd.read_csv(sig_path).copy()
        sig["pair"] = [f"{format_roi(a)} ↔ {format_roi(b)}" for a, b in zip(sig["roi1"], sig["roi2"])]
        sig = sig.sort_values("diff")
        colors = [PALETTE["AVH-"] if d > 0 else PALETTE["AVH+"] for d in sig["diff"]]
        fig, ax = plt.subplots(figsize=(11, max(4, 0.55 * len(sig))))
        ax.barh(sig["pair"], sig["diff"], color=colors, edgecolor="black", lw=0.8)
        ax.axvline(0, color="black", lw=0.6, ls="--")
        ax.set_xlabel("Δ Fisher z (AVH- − AVH+)")
        ax.set_title("Significant Connectivity Differences (p < 0.05)",
                     fontsize=16, fontweight="bold")
        for i, (d, p) in enumerate(zip(sig["diff"], sig["p_value"])):
            ax.text(d + (0.005 if d > 0 else -0.005), i,
                    f" p = {p:.3f}{_sig_marker(p)}",
                    va="center", ha="left" if d > 0 else "right", fontsize=10)
        handles = [
            Patch(facecolor=PALETTE["AVH-"], label="Stronger in AVH-"),
            Patch(facecolor=PALETTE["AVH+"], label="Stronger in AVH+"),
        ]
        ax.legend(handles=handles, loc="lower right", frameon=True)
        fig.tight_layout()
        _save(fig, out / "significant_connections.png")


# ===========================================================================
# 06 LATERALITY
# ===========================================================================
def make_laterality() -> None:
    out = POSTER_DIR / "06_laterality"
    li_path = DATA_DIR / "laterality.csv"
    stats_path = DATA_DIR / "laterality_stats.csv"
    if not li_path.exists():
        return

    li = pd.read_csv(li_path)
    li["group"] = pd.Categorical(li["group"], categories=GROUP_ORDER, ordered=True)

    contrasts_present = sorted(li["contrast"].unique())
    rois_present = sorted(li["roi_pair"].unique())

    # Heatmap: mean LI per (contrast, ROI) for each group
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    vmax = float(li["mean_LI"].abs().max())
    for ax, group in zip(axes, GROUP_ORDER):
        pivot = (li[li["group"] == group]
                 .pivot_table(index="roi_pair", columns="contrast", values="mean_LI"))
        pivot = pivot.reindex(index=rois_present, columns=contrasts_present)
        sns.heatmap(pivot, ax=ax, cmap="RdBu_r", center=0, vmin=-vmax, vmax=vmax,
                    annot=True, fmt=".2f", cbar=(group == GROUP_ORDER[-1]),
                    cbar_kws={"label": "Mean LI  (-1 = R, +1 = L)"},
                    linewidths=0.4, linecolor="white",
                    xticklabels=[format_contrast(c) for c in pivot.columns])
        ax.set_title(group, fontsize=14, fontweight="bold", color=PALETTE[group])
        ax.set_xlabel("")
        ax.set_ylabel("")
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.suptitle("Laterality Index by Group", fontsize=18, fontweight="bold", y=1.02)
    fig.tight_layout()
    _save(fig, out / "laterality_heatmap.png")

    # Bar plot of group means with SEM, faceted by contrast
    fig, axes = plt.subplots(1, len(contrasts_present), figsize=(4.5 * len(contrasts_present), 5),
                             sharey=True)
    if len(contrasts_present) == 1:
        axes = [axes]
    width = 0.26
    for ax, contrast in zip(axes, contrasts_present):
        sub = li[li["contrast"] == contrast]
        rois = sorted(sub["roi_pair"].unique())
        x = np.arange(len(rois))
        for i, group in enumerate(GROUP_ORDER):
            vals = sub[sub["group"] == group].set_index("roi_pair").reindex(rois)
            ax.bar(x + (i - 1) * width, vals["mean_LI"], width,
                   yerr=vals["sem_LI"], color=PALETTE[group], edgecolor="black",
                   lw=0.8, capsize=3, label=group)
        ax.axhline(0, color="black", lw=0.6, ls="--", alpha=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(rois, rotation=25, ha="right")
        ax.set_title(format_contrast(contrast), fontsize=13, fontweight="bold")
        ax.set_ylabel("Laterality Index" if contrast == contrasts_present[0] else "")
    axes[-1].legend(title="Group", loc="upper right", frameon=True, fontsize=10)
    fig.suptitle("Hemispheric Laterality (Mean ± SEM)", fontsize=18, fontweight="bold", y=1.02)
    fig.tight_layout()
    _save(fig, out / "laterality_bars.png")

    # Effect size summary (AVH- vs AVH+)
    if stats_path.exists():
        st = pd.read_csv(stats_path)
        st = st[st["comparison"] == "AVH-_vs_AVH+"].copy()
        if not st.empty:
            st["label"] = [f"{format_contrast(c)}  ·  {r}" for c, r in zip(st["contrast"], st["roi_pair"])]
            st = st.sort_values("cohens_d", ascending=True)
            colors = [SIG_OK if p < 0.05 else "#3498db" if p < 0.10 else "#95a5a6" for p in st["p_value"]]
            fig, ax = plt.subplots(figsize=(12, max(4, 0.5 * len(st))))
            ax.barh(st["label"], st["cohens_d"], color=colors, edgecolor="black", lw=0.8)
            ax.axvline(0, color="black", lw=0.6, ls="--")
            ax.set_xlabel("Cohen's d  (AVH- vs AVH+)")
            ax.set_title("Laterality Group Differences", fontsize=16, fontweight="bold")
            for i, (d, p) in enumerate(zip(st["cohens_d"], st["p_value"])):
                ax.text(d + (0.02 if d >= 0 else -0.02), i,
                        f" d={d:.2f}, p={p:.3f}{_sig_marker(p)}",
                        va="center", ha="left" if d >= 0 else "right", fontsize=10)
            plt.subplots_adjust(left=0.35)
            fig.tight_layout()
            _save(fig, out / "laterality_effect_sizes.png")


# ===========================================================================
# 07 DEMOGRAPHICS / QC
# ===========================================================================
def make_demographics_qc() -> None:
    out = POSTER_DIR / "07_demographics_qc"
    parts = _load_participants()

    counts = parts.groupby("group", observed=True).size().to_dict()
    legend_handles = [Patch(facecolor=PALETTE[g], edgecolor="black",
                            label=f"{g}  (n = {counts.get(g, 0)})") for g in GROUP_ORDER]

    # Age + IQ side-by-side
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    for ax, var, ylabel in zip(axes, ["age", "iq"], ["Age (years)", "IQ"]):
        sns.violinplot(data=parts, x="group", y=var, order=GROUP_ORDER,
                       palette=PALETTE, hue="group", ax=ax, inner="quartile",
                       cut=0, legend=False, saturation=0.85)
        for c in ax.collections:
            c.set_alpha(0.55)
        sns.stripplot(data=parts, x="group", y=var, order=GROUP_ORDER,
                      palette=PALETTE, hue="group", ax=ax, jitter=0.18,
                      edgecolor="white", linewidth=0.4, size=5, alpha=0.9, legend=False)
        ax.set_xlabel("")
        ax.set_ylabel(ylabel)
        ax.set_title(ylabel.split()[0], fontsize=15, fontweight="bold")
    axes[0].legend(handles=legend_handles, loc="lower right", title="Group", frameon=True)
    fig.suptitle("Demographics", fontsize=18, fontweight="bold", y=1.02)
    fig.tight_layout()
    _save(fig, out / "demographics_age_iq.png")

    # Sex distribution
    sex_counts = (parts.groupby(["group", "sex"], observed=True).size()
                  .unstack(fill_value=0).reindex(GROUP_ORDER))
    sex_counts = sex_counts.div(sex_counts.sum(axis=1), axis=0)
    fig, ax = plt.subplots(figsize=(7, 5))
    bottom = np.zeros(len(sex_counts))
    for sex_label, color in SEX_PALETTE.items():
        if sex_label not in sex_counts.columns:
            continue
        vals = sex_counts[sex_label].values
        ax.bar(sex_counts.index.astype(str), vals, bottom=bottom,
               color=color, edgecolor="black", lw=0.8, label=sex_label.capitalize())
        for i, v in enumerate(vals):
            if v > 0.04:
                ax.text(i, bottom[i] + v / 2, f"{v * 100:.0f}%", ha="center", va="center",
                        fontsize=11, fontweight="bold", color="white")
        bottom += vals
    ax.set_ylim(0, 1)
    ax.set_ylabel("Proportion")
    ax.set_title("Sex Distribution", fontsize=15, fontweight="bold")
    ax.legend(loc="upper right", title="Sex", frameon=True)
    for i, g in enumerate(GROUP_ORDER):
        ax.text(i, 1.02, f"n = {counts.get(g, 0)}", ha="center", fontsize=11, fontweight="bold")
    fig.tight_layout()
    _save(fig, out / "demographics_sex.png")

    # Motion / QC
    qc_path = DATA_DIR / "qc.csv"
    if qc_path.exists():
        qc = pd.read_csv(qc_path)
        qc = qc.merge(parts[["participant_id", "group"]], left_on="subject_id",
                      right_on="participant_id", how="left")
        qc["group"] = pd.Categorical(qc["group"], categories=GROUP_ORDER, ordered=True)
        fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
        for ax, var, ylabel in zip(axes, ["mean_fd", "pct_high_motion"],
                                    ["Mean FD (mm)", "% High Motion Volumes"]):
            sns.boxplot(data=qc, x="group", y=var, order=GROUP_ORDER,
                        palette=PALETTE, hue="group", ax=ax, width=0.55, legend=False)
            sns.stripplot(data=qc, x="group", y=var, order=GROUP_ORDER, ax=ax,
                          color="black", size=4, alpha=0.6, jitter=0.18)
            ax.set_xlabel("")
            ax.set_ylabel(ylabel)
            ax.set_title(ylabel, fontsize=14, fontweight="bold")
        axes[0].axhline(0.5, color=SIG_OK, ls="--", lw=1.0, alpha=0.7,
                        label="Exclusion threshold (0.5 mm)")
        axes[0].legend(loc="upper right", frameon=True, fontsize=10)
        fig.suptitle("Quality Control: Head Motion", fontsize=18, fontweight="bold", y=1.02)
        fig.tight_layout()
        _save(fig, out / "qc_motion.png")


# ===========================================================================
# SUMMARY HERO FIGURE
# ===========================================================================
def make_summary() -> None:
    out = POSTER_DIR / "summary"
    parts = _load_participants()
    es_path = EFFECT_DIR / "effect_sizes_summary.csv"
    cls_path = DATA_DIR / "svm_weights" / "classification_results.json"
    if not es_path.exists():
        return

    es = pd.read_csv(es_path)
    es = es[es["comparison"] == "AVH-_vs_AVH+"]

    fig = plt.figure(figsize=(18, 11))
    gs = fig.add_gridspec(3, 3, hspace=0.45, wspace=0.32)

    # (1) Group sizes
    ax = fig.add_subplot(gs[0, 0])
    counts = parts.groupby("group", observed=True).size().reindex(GROUP_ORDER)
    bars = ax.bar(counts.index.astype(str), counts.values,
                  color=[PALETTE[g] for g in GROUP_ORDER], edgecolor="black", lw=0.8)
    for b, v in zip(bars, counts.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"n = {v}",
                ha="center", fontsize=11, fontweight="bold")
    ax.set_title("Sample Sizes", fontsize=14, fontweight="bold")
    ax.set_ylabel("Participants")
    ax.set_ylim(0, counts.max() * 1.18)

    # (2) Top effect sizes
    ax = fig.add_subplot(gs[0, 1:])
    top = es.assign(abs_d=lambda d: d["cohens_d"].abs()).sort_values("abs_d", ascending=False).head(10)
    top["label"] = [f"{format_contrast(c)}  ·  {format_roi(r)}"
                    for c, r in zip(top["contrast"], top["roi"])]
    colors = [SIG_OK if abs(d) >= 0.5 else "#3498db" if abs(d) >= 0.2 else "#95a5a6"
              for d in top["cohens_d"]]
    ax.barh(top["label"][::-1], top["cohens_d"][::-1],
            color=colors[::-1], edgecolor="black", lw=0.8)
    ax.axvline(0, color="black", lw=0.6, ls="--")
    ax.set_xlabel("Cohen's d  (AVH- vs AVH+)")
    ax.set_title("Top 10 ROI Effect Sizes", fontsize=14, fontweight="bold")

    # (3) Classification accuracy
    ax = fig.add_subplot(gs[1, 0])
    if cls_path.exists():
        with open(cls_path) as f:
            cls = json.load(f)
        rows = pd.DataFrame(cls["results"])
        x = np.arange(len(rows))
        ax.bar(x, rows["accuracy"], color="#3498db", edgecolor="black", lw=0.8)
        ax.axhline(0.5, color="black", lw=1.0, ls="--", alpha=0.7)
        ax.set_xticks(x)
        ax.set_xticklabels([format_contrast(c) for c in rows["contrast"]],
                           rotation=20, ha="right", fontsize=9)
        ax.set_ylim(0, 1)
        ax.set_ylabel("Accuracy")
        ax.set_title("MVPA Classification", fontsize=14, fontweight="bold")
        for xi, (a, p) in enumerate(zip(rows["accuracy"], rows["p_value"])):
            ax.text(xi, a + 0.02, f"p={p:.2f}", ha="center", fontsize=8)

    # (4) Connectivity sig
    ax = fig.add_subplot(gs[1, 1])
    sig_path = DATA_DIR / "connectivity_significant.csv"
    if sig_path.exists():
        sig = pd.read_csv(sig_path)
        if not sig.empty:
            labels = [f"{format_roi(a)}\n↔ {format_roi(b)}" for a, b in zip(sig["roi1"], sig["roi2"])]
            colors = [PALETTE["AVH-"] if d > 0 else PALETTE["AVH+"] for d in sig["diff"]]
            ax.barh(labels, sig["diff"], color=colors, edgecolor="black", lw=0.8)
            ax.axvline(0, color="black", lw=0.6, ls="--")
    ax.set_xlabel("Δ Connectivity")
    ax.set_title("Significant Connections", fontsize=14, fontweight="bold")

    # (5) PSYRATS distribution
    ax = fig.add_subplot(gs[1, 2])
    psy = parts[parts["group"] == "AVH+"].dropna(subset=["psyrats"])
    if not psy.empty:
        ax.hist(psy["psyrats"], bins=10, color=PALETTE["AVH+"],
                edgecolor="black", lw=0.8, alpha=0.85)
        ax.axvline(psy["psyrats"].mean(), color="black", ls="--",
                   label=f"Mean = {psy['psyrats'].mean():.1f}")
        ax.legend(loc="upper right")
    ax.set_xlabel("PSYRATS Total")
    ax.set_ylabel("Count (AVH+)")
    ax.set_title("Hallucination Severity", fontsize=14, fontweight="bold")

    # (6) Bottom-row callout box with key findings text
    ax = fig.add_subplot(gs[2, :])
    ax.axis("off")
    n_sig = int((es["cohens_d"].abs() >= 0.5).sum())
    n_med = int(((es["cohens_d"].abs() >= 0.2) & (es["cohens_d"].abs() < 0.5)).sum())
    msg = (
        "KEY FINDINGS  (AVH- vs AVH+)\n"
        f"  •  ROI effect sizes:  {n_sig} medium-large (|d| ≥ 0.5)   |   {n_med} small (0.2 ≤ |d| < 0.5)\n"
        f"  •  MVPA accuracy below chance — auditory ROIs do not discriminate AVH subgroups linearly\n"
        f"  •  Connectivity:  {len(pd.read_csv(sig_path)) if sig_path.exists() else 0} significant ROI-ROI differences (uncorrected p < 0.05)\n"
        f"  •  Laterality differences strongest in MTG and STG-posterior — see laterality panel for d & p"
    )
    ax.text(0.01, 0.95, msg, va="top", ha="left",
            fontsize=14, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.8", facecolor="#f4f6f7",
                      edgecolor="#2c3e50", linewidth=1.5))

    fig.suptitle("Schizophrenia Auditory Verbal Hallucinations  ·  Key Findings",
                 fontsize=22, fontweight="bold", y=1.005)
    _save(fig, out / "key_findings.png")


# ===========================================================================
# README
# ===========================================================================
def write_readme() -> None:
    es_path = EFFECT_DIR / "effect_sizes_summary.csv"
    sig_path = DATA_DIR / "connectivity_significant.csv"
    cls_path = DATA_DIR / "svm_weights" / "classification_results.json"

    sections = [
        ("01_brain_maps", "Glass brain + inflated fsaverage surface plots for the key contrasts, plus a 12-ROI reference."),
        ("02_roi_effects", "Raincloud + grouped-bar + forest plots of ROI activation by group."),
        ("03_correlations", "ROI activation vs PSYRATS scatter plots in the AVH+ group."),
        ("04_classification", "MVPA SVM accuracy / AUC + permutation summary."),
        ("05_connectivity", "Functional connectivity matrix and significant ROI-ROI group differences."),
        ("06_laterality", "Hemispheric laterality heatmap, bar plots, and effect-size summary."),
        ("07_demographics_qc", "Age, IQ, sex distribution, and motion QC."),
        ("summary", "Single hero figure with the headline finding."),
    ]
    lines = [
        "# Poster Figures",
        "",
        "All figures here are generated by `code/python/poster_visualizations.py`",
        "from the consolidated stats in `results/data/`. Re-run with:",
        "",
        "    python code/python/poster_visualizations.py",
        "",
        "## Sections",
        "",
    ]
    for s, desc in sections:
        lines.append(f"- **{s}/** — {desc}")

    if es_path.exists():
        es = pd.read_csv(es_path)
        es = es[es["comparison"] == "AVH-_vs_AVH+"]
        n_sig = int((es["cohens_d"].abs() >= 0.5).sum())
        n_med = int(((es["cohens_d"].abs() >= 0.2) & (es["cohens_d"].abs() < 0.5)).sum())
    else:
        n_sig = n_med = 0
    n_conn = len(pd.read_csv(sig_path)) if sig_path.exists() else 0
    cls_summary = ""
    if cls_path.exists():
        with open(cls_path) as f:
            cls = json.load(f)
        rows = pd.DataFrame(cls["results"])
        cls_summary = ", ".join(f"{format_contrast(r['contrast'])}: acc={r['accuracy']:.2f} (p={r['p_value']:.2f})"
                                for r in cls["results"])

    lines += [
        "",
        "## Key Findings (AVH- vs AVH+)",
        "",
        f"- ROI effect sizes (Cohen's d):  {n_sig} medium-large (|d| ≥ 0.5),  {n_med} small (0.2 ≤ |d| < 0.5).",
        f"- Significant ROI-ROI connectivity differences (p < 0.05): {n_conn}.",
        f"- MVPA classification: {cls_summary}.",
        "",
        "## Style Standards",
        "",
        "- 300 dpi PNG, white background, Arial/Helvetica.",
        "- Colors: HC = #7f8c8d (gray), AVH- = #3498db (blue), AVH+ = #e74c3c (red).",
        "- Significance markers: `*** p<0.001`,  `** p<0.01`,  `* p<0.05`,  `. p<0.10`.",
        "",
    ]

    (POSTER_DIR / "README.md").write_text("\n".join(lines))


# ===========================================================================
# Entry point
# ===========================================================================
def main() -> None:
    _ensure_sections()
    print("\n" + "=" * 70)
    print("BUILDING results/poster/ FROM results/data/")
    print("=" * 70)

    print("\n[1/8] Brain maps ...")
    try:
        make_brain_maps()
    except Exception as exc:
        print(f"  ! brain maps failed: {exc}")

    print("\n[2/8] ROI effects ...")
    make_roi_effects()
    print("\n[3/8] Correlations ...")
    make_correlations()
    print("\n[4/8] Classification ...")
    make_classification()
    print("\n[5/8] Connectivity ...")
    make_connectivity()
    print("\n[6/8] Laterality ...")
    make_laterality()
    print("\n[7/8] Demographics / QC ...")
    make_demographics_qc()
    print("\n[8/8] Summary hero ...")
    make_summary()

    write_readme()
    print(f"\nDone. See {POSTER_DIR}\n")


if __name__ == "__main__":
    main()
