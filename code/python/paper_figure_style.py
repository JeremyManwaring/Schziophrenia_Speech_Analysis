"""Shared visual system for the source-faithful manuscript figures."""

from __future__ import annotations

import hashlib
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from matplotlib.transforms import Bbox, ScaledTranslation

FIGURE_WIDTH = 7.2
PAPER_DPI = 600

# Core neutrals.
INK = "#17202A"
NAVY = "#17324D"
MUTED_INK = "#5E6872"
LIGHT_INK = "#89929A"
AXIS_COLOR = "#66717A"
GRID_COLOR = "#E8ECEF"
HAIRLINE = "#D8DEE3"
PAPER = "#FFFFFF"
COOL_PAPER = "#F7F9FA"
WARM_GRAY = "#8A8F91"

# Muted scientific accents. Group identity is also encoded by marker shape.
MUTED_BLUE = "#527A99"
SOFT_TEAL = "#5B958E"
CORAL = "#CB654D"
PALE_BLUE = "#DCE7ED"
PALE_TEAL = "#DCEBE8"
PALE_CORAL = "#F1DDD7"

PALETTE = {"HC": WARM_GRAY, "AVH-": MUTED_BLUE, "AVH+": CORAL}
GROUP_ORDER = ["HC", "AVH-", "AVH+"]
GROUP_MARKERS = {"HC": "o", "AVH-": "s", "AVH+": "^"}

DIVERGING_CMAP = LinearSegmentedColormap.from_list(
    "editorial_coral_navy",
    ["#B84D3A", "#E2A396", "#F7F5F1", "#AFC6D3", "#315F80"],
    N=256,
)


def lighten(color: str, amount: float = 0.72) -> tuple[float, float, float]:
    """Blend a color toward white by ``amount``."""
    rgb = np.asarray(to_rgb(color), dtype=float)
    return tuple(rgb + (1.0 - rgb) * amount)


def apply_figure_style() -> None:
    """Apply compact, vector-safe defaults for manuscript figures."""
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Helvetica Neue",
                "Helvetica",
                "Arial",
                "DejaVu Sans",
            ],
            "font.size": 7.15,
            "font.weight": "normal",
            "text.color": INK,
            "axes.titlesize": 7.8,
            "axes.titleweight": "medium",
            "axes.labelsize": 7.2,
            "axes.labelcolor": INK,
            "axes.edgecolor": AXIS_COLOR,
            "axes.linewidth": 0.55,
            "axes.facecolor": PAPER,
            "xtick.labelsize": 6.55,
            "ytick.labelsize": 6.55,
            "xtick.color": INK,
            "ytick.color": INK,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.size": 2.25,
            "ytick.major.size": 2.25,
            "xtick.major.width": 0.48,
            "ytick.major.width": 0.48,
            "legend.fontsize": 6.45,
            "legend.title_fontsize": 6.45,
            "legend.frameon": False,
            "figure.dpi": 150,
            "figure.facecolor": PAPER,
            "savefig.dpi": PAPER_DPI,
            "savefig.facecolor": PAPER,
            "savefig.transparent": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "lines.linewidth": 0.9,
            "lines.markersize": 3.7,
            "errorbar.capsize": 2.2,
            "hatch.linewidth": 0.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def style_axis(ax, *, grid_axis: str | None = "y", zero_line: bool = False) -> None:
    """Apply quiet axes and retain only comparison-relevant scaffolding."""
    if grid_axis:
        ax.grid(
            True,
            axis=grid_axis,
            color=GRID_COLOR,
            linewidth=0.38,
            alpha=0.85,
            zorder=0,
        )
        ax.set_axisbelow(True)
    if zero_line:
        if grid_axis == "x":
            ax.axvline(0, color=AXIS_COLOR, linewidth=0.62, zorder=1)
        else:
            ax.axhline(0, color=AXIS_COLOR, linewidth=0.62, zorder=1)
    ax.tick_params(pad=2.0)


def clean_axis(ax, *, keep: tuple[str, ...] = ("left", "bottom")) -> None:
    """Remove unused axis edges while preserving deliberate anchors."""
    for name, spine in ax.spines.items():
        spine.set_visible(name in keep)
        if name in keep:
            spine.set_color(AXIS_COLOR)
            spine.set_linewidth(0.55)


def panel_header(
    ax,
    label: str,
    title: str,
    subtitle: str | None = None,
    *,
    label_x: float = 0.0,
    header_y: float = 1.11,
) -> None:
    """Place a panel heading with physical, figure-independent text spacing."""
    title_transform = ax.transAxes + ScaledTranslation(
        18.0 / 72.0,
        0.0,
        ax.figure.dpi_scale_trans,
    )
    subtitle_transform = title_transform + ScaledTranslation(
        0.0,
        -11.0 / 72.0,
        ax.figure.dpi_scale_trans,
    )
    ax.text(
        label_x,
        header_y,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.5,
        fontweight="bold",
        color=NAVY,
        clip_on=False,
    )
    ax.text(
        label_x,
        header_y,
        title,
        transform=title_transform,
        ha="left",
        va="bottom",
        fontsize=7.8,
        fontweight="semibold",
        color=INK,
        clip_on=False,
    )
    if subtitle:
        ax.text(
            label_x,
            header_y,
            subtitle,
            transform=subtitle_transform,
            ha="left",
            va="bottom",
            fontsize=6.15,
            color=MUTED_INK,
            clip_on=False,
        )


def figure_title(
    fig,
    title: str,
    subtitle: str | None = None,
    *,
    x: float = 0.055,
    y: float = 0.965,
) -> None:
    """Add a concise editorial figure heading."""
    fig.text(
        x,
        y,
        title,
        ha="left",
        va="top",
        fontsize=9.0,
        fontweight="semibold",
        color=NAVY,
    )
    if subtitle:
        subtitle_transform = fig.transFigure + ScaledTranslation(
            0.0,
            -15.0 / 72.0,
            fig.dpi_scale_trans,
        )
        fig.text(
            x,
            y,
            subtitle,
            transform=subtitle_transform,
            ha="left",
            va="top",
            fontsize=6.5,
            color=MUTED_INK,
        )


def add_note(
    fig,
    text: str,
    *,
    x: float = 0.055,
    y: float = 0.018,
    width_rule: float | None = None,
) -> None:
    """Add compact caption-like information at the bottom of a figure."""
    if width_rule:
        line_count = text.count("\n") + 1
        rule_offset_points = 3.5 + line_count * 7.3
        rule_y = y + rule_offset_points / (72.0 * fig.get_figheight())
        fig.add_artist(
            plt.Line2D(
                [x, x + width_rule],
                [rule_y, rule_y],
                transform=fig.transFigure,
                color=HAIRLINE,
                linewidth=0.45,
            )
        )
    fig.text(
        x,
        y,
        text,
        ha="left",
        va="bottom",
        fontsize=5.9,
        color=MUTED_INK,
        linespacing=1.24,
    )


def stable_jitter(ids, group: str, width: float = 0.12) -> np.ndarray:
    """Return deterministic horizontal jitter without changing observed values."""
    offsets = []
    for index, value in enumerate(ids):
        token = f"{group}|{value if value is not None else index}".encode()
        digest = hashlib.sha1(token).digest()
        unit = int.from_bytes(digest[:8], "big") / float(2**64 - 1)
        offsets.append((unit * 2.0 - 1.0) * width)
    return np.asarray(offsets, dtype=float)


def vectorize_scalar_images(fig) -> None:
    """Convert nearest-neighbor scalar image layers to editable vector cells."""
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
    """Save exact-canvas 600 dpi PNG, editable SVG, and vector PDF."""
    output_stem.parent.mkdir(parents=True, exist_ok=True)
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
        svg_path = output_stem.with_suffix(".svg")
        fig.savefig(
            svg_path,
            bbox_inches=exact_canvas,
            pad_inches=0.0,
        )
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )
    plt.close(fig)


apply_figure_style()
