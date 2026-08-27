"""Shared style primitives for the source-faithful manuscript figure redesign.

The system is intentionally restrained: exact 7.2-inch canvases, quiet axes,
Arial typography, a muted Okabe-Ito-derived group palette, and redundant
shape/line encodings for grayscale legibility.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from matplotlib.transforms import Bbox


FIGURE_WIDTH = 7.2
PAPER_DPI = 600

INK = "#202428"
MUTED_INK = "#5C636A"
LIGHT_INK = "#7B8288"
AXIS_COLOR = "#4F565C"
GRID_COLOR = "#E5E8EA"
HAIRLINE = "#D4D8DB"
PAPER = "#FFFFFF"
NEUTRAL = "#F4F3F0"

# Muted, publication-safe derivatives of the Okabe-Ito blue and vermillion.
PALETTE = {
    "HC": "#7C8084",
    "AVH-": "#3F7096",
    "AVH+": "#C45B45",
}
GROUP_ORDER = ["HC", "AVH-", "AVH+"]
GROUP_MARKERS = {"HC": "o", "AVH-": "s", "AVH+": "^"}

DIVERGING_CMAP = LinearSegmentedColormap.from_list(
    "neuro_blue_neutral_vermillion",
    [PALETTE["AVH+"], NEUTRAL, PALETTE["AVH-"]],
    N=256,
)


def lighten(color: str, amount: float = 0.72) -> tuple[float, float, float]:
    """Blend a color toward white by ``amount``."""
    rgb = np.asarray(to_rgb(color), dtype=float)
    return tuple(rgb + (1.0 - rgb) * amount)


def apply_neuron_style() -> None:
    """Apply journal-scale, vector-safe Matplotlib defaults."""
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 7.4,
            "font.weight": "normal",
            "text.color": INK,
            "axes.titlesize": 8.4,
            "axes.titleweight": "semibold",
            "axes.labelsize": 7.6,
            "axes.labelcolor": INK,
            "axes.edgecolor": AXIS_COLOR,
            "axes.linewidth": 0.65,
            "axes.facecolor": PAPER,
            "xtick.labelsize": 6.8,
            "ytick.labelsize": 6.8,
            "xtick.color": INK,
            "ytick.color": INK,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.size": 2.7,
            "ytick.major.size": 2.7,
            "xtick.major.width": 0.55,
            "ytick.major.width": 0.55,
            "legend.fontsize": 6.8,
            "legend.title_fontsize": 6.8,
            "legend.frameon": False,
            "figure.dpi": 150,
            "figure.facecolor": PAPER,
            "savefig.dpi": PAPER_DPI,
            "savefig.facecolor": PAPER,
            "savefig.transparent": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "lines.linewidth": 1.0,
            "lines.markersize": 4.0,
            "errorbar.capsize": 2.4,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def style_axis(
    ax,
    *,
    grid_axis: str | None = "y",
    zero_line: bool = False,
) -> None:
    """Apply the common quiet axis system."""
    if grid_axis:
        ax.grid(
            True,
            axis=grid_axis,
            color=GRID_COLOR,
            linewidth=0.42,
            alpha=0.9,
            zorder=0,
        )
        ax.set_axisbelow(True)
    if zero_line:
        if grid_axis == "x":
            ax.axvline(0, color=AXIS_COLOR, linewidth=0.75, zorder=1)
        else:
            ax.axhline(0, color=AXIS_COLOR, linewidth=0.75, zorder=1)
    ax.tick_params(pad=2.0)


def panel_header(ax, label: str, title: str, subtitle: str | None = None) -> None:
    """Place a compact panel label and title without a decorative box."""
    ax.text(
        0.0,
        1.075,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9.4,
        fontweight="bold",
        color=INK,
        clip_on=False,
    )
    ax.text(
        0.085,
        1.075,
        title,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.3,
        fontweight="semibold",
        color=INK,
        clip_on=False,
    )
    if subtitle:
        ax.text(
            0.085,
            1.015,
            subtitle,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=6.5,
            color=MUTED_INK,
            clip_on=False,
        )


def stable_jitter(ids, group: str, width: float = 0.115) -> np.ndarray:
    """Return deterministic, participant-stable horizontal jitter."""
    offsets = []
    for index, value in enumerate(ids):
        token = f"{group}|{value if value is not None else index}".encode("utf-8")
        digest = hashlib.sha1(token).digest()
        unit = int.from_bytes(digest[:8], "big") / float(2**64 - 1)
        offsets.append((unit * 2.0 - 1.0) * width)
    return np.asarray(offsets, dtype=float)


def vectorize_scalar_images(fig) -> None:
    """Replace nearest-neighbor scalar image layers with editable vector cells.

    Nilearn uses ``AxesImage`` for thresholded statistical projections. The
    transformation below preserves the displayed masked array, extent, color
    normalization, and nearest-neighbor geometry while emitting a vector
    ``QuadMesh`` in SVG/PDF.
    """
    for ax in fig.axes:
        for image in list(ax.images):
            array = np.ma.asarray(image.get_array())
            if array.ndim != 2:
                continue
            left, right, bottom, top = [float(value) for value in image.get_extent()]
            rows, columns = array.shape
            x_edges = np.linspace(left, right, columns + 1)
            y_edges = np.linspace(bottom, top, rows + 1)
            if image.origin == "upper":
                array = np.flipud(array)
            ax.pcolormesh(
                x_edges,
                y_edges,
                array,
                cmap=image.get_cmap(),
                norm=image.norm,
                alpha=image.get_alpha(),
                shading="flat",
                edgecolors="none",
                antialiased=False,
                zorder=image.get_zorder(),
            )
            image.remove()


def save_figure(fig, output_stem: Path) -> None:
    """Save an exact-size 600 dpi PNG and editable vector PDF/SVG."""
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    # ``surface_brain_plots`` imports a legacy style that requests tight
    # bounding boxes. Override it here so every export keeps the exact journal
    # canvas specified by ``figsize``.
    width, height = fig.get_size_inches()
    exact_canvas = Bbox.from_bounds(0.0, 0.0, float(width), float(height))
    for ax in fig.axes:
        for collection in ax.collections:
            collection.set_rasterized(False)
    with plt.rc_context({"savefig.bbox": None, "savefig.pad_inches": 0.0}):
        fig.savefig(
            output_stem.with_suffix(".png"),
            dpi=PAPER_DPI,
            bbox_inches=exact_canvas,
            pad_inches=0.0,
        )
        fig.savefig(
            output_stem.with_suffix(".pdf"),
            bbox_inches=exact_canvas,
            pad_inches=0.0,
        )
        fig.savefig(
            output_stem.with_suffix(".svg"),
            bbox_inches=exact_canvas,
            pad_inches=0.0,
        )
    plt.close(fig)


apply_neuron_style()
