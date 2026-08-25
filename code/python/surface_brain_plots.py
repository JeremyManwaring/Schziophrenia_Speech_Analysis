"""
Brain map plotting utilities (poster-ready).

Provides:
- `plot_cluster_glass(...)` -> single-panel cleaned glass brain for cluster maps
- `plot_cluster_surface(...)` -> fsaverage surface projection of a stat map
- `plot_svm_surface(...)` -> smoothed/thresholded SVM weight surface projection
- `plot_roi_locations(...)` -> labeled ROI sphere reference figure
- `main()` -> generates all brain maps for the poster from `results/data/`

The functions are designed to be importable from `poster_visualizations.py`.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from nilearn import datasets
from nilearn.image import load_img, math_img, smooth_img
from nilearn.masking import compute_brain_mask
from nilearn.plotting import (
    plot_glass_brain,
    plot_img_on_surf,
    plot_stat_map,
)

sys.path.insert(0, str(Path(__file__).parent))
from poster_style import apply_style, format_contrast  # noqa: E402
from roi_analysis import SPEECH_ROIS  # noqa: E402

warnings.filterwarnings("ignore")
apply_style()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent.parent
DATA_CLUSTER = BASE_DIR / "results" / "data" / "cluster_maps"
DATA_SVM = BASE_DIR / "results" / "data" / "svm_weights"
POSTER_BRAIN = BASE_DIR / "results" / "poster" / "01_brain_maps"

KEY_CONTRASTS = ["sentences_vs_reversed", "speech_vs_reversed", "words_vs_sentences"]
SVM_CONTRASTS = KEY_CONTRASTS + ["words_vs_reversed"]

# Use the extraction definitions as the single source of truth for maps/tables.
ROIS = {name: definition["coords"] for name, definition in SPEECH_ROIS.items()}
ROI_RADII = {name: definition["radius"] for name, definition in SPEECH_ROIS.items()}


def _roi_display(key: str) -> str:
    """'L_STG_post' -> 'L STG posterior' for legend labels."""
    repl = {"post": "posterior", "ant": "anterior", "tri": "triangularis",
            "oper": "opercularis", "stg": "STG", "mtg": "MTG", "sts": "STS",
            "ifg": "IFG"}
    out = []
    for tok in key.split("_"):
        low = tok.lower()
        if tok in ("L", "R"):
            out.append(tok)
        elif low in repl:
            out.append(repl[low])
        else:
            out.append(tok.capitalize())
    return " ".join(out)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _resolve_cluster_map(contrast: str) -> Path | None:
    """Prefer verified cluster-size FWER output, then a descriptive t map."""
    corrected = DATA_CLUSTER / f"{contrast}_AVH-_vs_AVH+_cluster_fwer_p05_tstat.nii.gz"
    if corrected.exists() and np.any(load_img(str(corrected)).get_fdata()):
        return corrected
    descriptive = DATA_CLUSTER / f"{contrast}_AVH-_vs_AVH+_tstat.nii.gz"
    if descriptive.exists():
        return descriptive
    return None


def _cluster_map_label(stat_path: Path) -> str:
    if "cluster_fwer_p05" in stat_path.name:
        return "cluster-size FWER p < .05; CFT p < .001; 10,000 permutations"
    return (
        "descriptive t map at two-sided voxel p < .001; "
        "no cluster survives cluster-size FWER p < .05; 10,000 permutations"
    )


def _display_threshold(stat_path: Path) -> float:
    """Corrected maps are pre-thresholded; descriptive maps use the CFT t."""
    return 0.0 if "cluster_fwer_p05" in stat_path.name else 3.55


def _smooth_and_mask(stat_path: Path, fwhm: float = 6.0):
    """Smooth a stat map and mask it to the brain to reduce speckle."""
    img = load_img(str(stat_path))
    img = smooth_img(img, fwhm=fwhm)
    brain = compute_brain_mask(img)
    return math_img("img * mask", img=img, mask=brain)


def _abs_threshold(img, percentile: float = 90.0) -> float:
    """Pick a threshold equal to the given percentile of the absolute voxel values."""
    data = np.abs(img.get_fdata())
    data = data[np.isfinite(data) & (data > 0)]
    if data.size == 0:
        return 0.0
    return float(np.percentile(data, percentile))


# ---------------------------------------------------------------------------
# Plot: cluster glass brain (single clean panel)
# ---------------------------------------------------------------------------
def plot_cluster_glass(contrast: str, out_path: Path, threshold: float = 0.0) -> bool:
    """Render a single-panel cleaned glass brain for the cluster map."""
    stat_path = _resolve_cluster_map(contrast)
    if stat_path is None:
        return False

    img = load_img(str(stat_path))

    fig = plt.figure(figsize=(14, 5))
    plot_glass_brain(
        img,
        threshold=_display_threshold(stat_path),
        display_mode="lyrz",
        colorbar=True,
        cmap="cold_hot",
        plot_abs=False,
        symmetric_cbar=True,
        title=(f"{format_contrast(contrast)} - AVH- vs AVH+\n"
               f"{_cluster_map_label(stat_path)}"),
        figure=fig,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return True


# ---------------------------------------------------------------------------
# Plot: cluster surface (fsaverage, inflated)
# ---------------------------------------------------------------------------
def plot_cluster_surface(contrast: str, out_path: Path, threshold: float = 0.0) -> bool:
    """Project the cluster map onto an inflated fsaverage surface."""
    stat_path = _resolve_cluster_map(contrast)
    if stat_path is None:
        return False

    img = load_img(str(stat_path))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    title = (f"{format_contrast(contrast)}: AVH- vs AVH+\n"
             f"{_cluster_map_label(stat_path)}")
    plot_img_on_surf(
        stat_map=img,
        surf_mesh="fsaverage",
        threshold=_display_threshold(stat_path),
        cmap="cold_hot",
        views=["lateral", "medial"],
        hemispheres=["left", "right"],
        colorbar=True,
        symmetric_cbar=True,
        inflate=True,
        title=title,
        output_file=str(out_path),
    )
    return True


# ---------------------------------------------------------------------------
# Plot: cluster anatomical slices
# ---------------------------------------------------------------------------
def plot_cluster_stat_slices_grid(
    contrasts: list[str],
    out_path: Path,
    threshold: float = 0.0,
) -> bool:
    """Render AVH- vs AVH+ anatomical slices side by side."""
    maps = []
    for contrast in contrasts:
        stat_path = _resolve_cluster_map(contrast)
        if stat_path is None:
            continue
        maps.append((contrast, stat_path, load_img(str(stat_path))))

    if not maps:
        return False

    mni_bg = datasets.load_mni152_template()
    fig = plt.figure(figsize=(18, 5.5), facecolor="white")
    displays = []
    panel_width = 0.30

    for idx, (contrast, stat_path, img) in enumerate(maps):
        left = 0.02 + idx * 0.32
        display = plot_stat_map(
            stat_map_img=img,
            bg_img=mni_bg,
            threshold=_display_threshold(stat_path),
            display_mode="ortho",
            cut_coords=(-52, -24, 6),
            cmap="cold_hot",
            symmetric_cbar=True,
            black_bg=False,
            dim=0.25,
            annotate=True,
            colorbar=True,
            draw_cross=False,
            vmax=3.0,
            title=(f"{format_contrast(contrast)}\nAVH- vs AVH+\n"
                   f"{_cluster_map_label(stat_path)}"),
            figure=fig,
            axes=(left, 0.12, panel_width, 0.78),
        )
        displays.append(display)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    for display in displays:
        display.close()
    plt.close(fig)
    return True


# ---------------------------------------------------------------------------
# Plot: SVM weight surface (smoothed + percentile-thresholded)
# ---------------------------------------------------------------------------
def plot_svm_surface(contrast: str, out_path: Path, percentile: float = 92.0) -> bool:
    """Project SVM weights onto fsaverage after smoothing + abs-percentile thresholding."""
    weight_path = DATA_SVM / f"{contrast}_svm_weights.nii.gz"
    if not weight_path.exists():
        return False

    img = _smooth_and_mask(weight_path, fwhm=8.0)
    thr = _abs_threshold(img, percentile=percentile)
    if thr <= 0:
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    title = f"{format_contrast(contrast)}: SVM Weights (top {100 - percentile:.0f}%)"
    plot_img_on_surf(
        stat_map=img,
        surf_mesh="fsaverage",
        threshold=thr,
        cmap="cold_hot",
        views=["lateral", "medial"],
        hemispheres=["left", "right"],
        colorbar=True,
        symmetric_cbar=True,
        inflate=True,
        title=title,
        output_file=str(out_path),
    )
    return True


def plot_svm_glass(contrast: str, out_path: Path, percentile: float = 92.0) -> bool:
    """Single-panel glass brain of SVM weights, smoothed + thresholded."""
    weight_path = DATA_SVM / f"{contrast}_svm_weights.nii.gz"
    if not weight_path.exists():
        return False

    img = _smooth_and_mask(weight_path, fwhm=8.0)
    thr = _abs_threshold(img, percentile=percentile)
    if thr <= 0:
        return False

    fig = plt.figure(figsize=(14, 5))
    plot_glass_brain(
        img,
        threshold=thr,
        display_mode="lyrz",
        colorbar=True,
        cmap="cold_hot",
        plot_abs=False,
        symmetric_cbar=True,
        title=f"{format_contrast(contrast)}: SVM Weights (top {100 - percentile:.0f}%)",
        figure=fig,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return True


# ---------------------------------------------------------------------------
# Plot: ROI reference figure
# ---------------------------------------------------------------------------
def plot_roi_locations(out_path: Path) -> None:
    """Reference figure using the exact extraction coordinates and radii."""
    from matplotlib.lines import Line2D

    L_COLOR, R_COLOR = "#3498db", "#e67e22"

    fig = plt.figure(figsize=(16, 6))
    display = plot_glass_brain(
        None, display_mode="lyrz", figure=fig,
        title="Speech / Language ROIs (MNI)",
    )
    for hemisphere, color in (("L_", L_COLOR), ("R_", R_COLOR)):
        for radius, size in ((8, 150), (6, 95)):
            coords = [
                coord for key, coord in ROIS.items()
                if key.startswith(hemisphere) and ROI_RADII[key] == radius
            ]
            if coords:
                display.add_markers(coords, marker_color=color, marker_size=size,
                                    edgecolor="black", alpha=0.95)

    handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=L_COLOR,
               markeredgecolor="black", markersize=11, label="Left hemisphere ROI"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=R_COLOR,
               markeredgecolor="black", markersize=11, label="Right hemisphere ROI"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#7f8c8d",
               markeredgecolor="black", markersize=11, label="8 mm cortical sphere"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#7f8c8d",
               markeredgecolor="black", markersize=8, label="6 mm Heschl sphere"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=True,
               fontsize=11, bbox_to_anchor=(0.5, -0.04))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=400, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    POSTER_BRAIN.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("BRAIN MAPS (poster-ready)")
    print("=" * 70)

    plot_roi_locations(POSTER_BRAIN / "roi_locations.png")
    print("  ROI reference saved")

    ok_a = plot_cluster_stat_slices_grid(
        KEY_CONTRASTS,
        POSTER_BRAIN / "avh_group_stat_slices.png",
    )
    print(f"  anatomical stat slices: combined={ok_a}")

    for contrast in KEY_CONTRASTS:
        ok_g = plot_cluster_glass(contrast, POSTER_BRAIN / f"{contrast}_glass.png")
        ok_s = plot_cluster_surface(contrast, POSTER_BRAIN / f"{contrast}_surface.png")
        print(f"  {contrast}: glass={ok_g} surface={ok_s}")

    for contrast in SVM_CONTRASTS:
        ok_g = plot_svm_glass(contrast, POSTER_BRAIN / f"{contrast}_svm_glass.png")
        ok_s = plot_svm_surface(contrast, POSTER_BRAIN / f"{contrast}_svm_surface.png")
        print(f"  SVM {contrast}: glass={ok_g} surface={ok_s}")

    print(f"\nBrain maps saved to: {POSTER_BRAIN}\n")


if __name__ == "__main__":
    main()
