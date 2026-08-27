"""
Shared style configuration for publication-quality visualizations.

Import once at the top of any plotting script:

    from poster_style import apply_style, PALETTE, GROUP_ORDER, format_contrast, format_roi

`apply_style()` should be called before creating any figures.
"""

from __future__ import annotations

import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Color palette (single source of truth across the codebase)
# ---------------------------------------------------------------------------
# Okabe-Ito-derived colors keep the three groups distinguishable for readers
# with common color-vision deficiencies and when printed in grayscale.
PALETTE = {
    "HC": "#7A7A7A",     # neutral gray
    "AVH-": "#0072B2",   # blue
    "AVH+": "#D55E00",   # vermillion
}

GROUP_ORDER = ["HC", "AVH-", "AVH+"]

# Sex palette (reuse across demographic plots)
SEX_PALETTE = {"male": "#0072B2", "female": "#CC79A7"}

# Significance highlight colors
SIG_COLOR = "#009E73"      # blue-green when significant
NS_COLOR = "#9CA3AF"       # gray when non-significant

INK = "#202124"
MUTED_INK = "#5F6368"
GRID_COLOR = "#D9DDE3"
OUTLINE_COLOR = "#30343B"
POSITIVE_COLOR = "#D55E00"
NEGATIVE_COLOR = "#0072B2"
PAPER_DPI = 600


def apply_style() -> None:
    """Apply journal-oriented Matplotlib defaults.

    Font sizes are specified for figures placed at roughly 7.2 inches (a
    typical two-column journal width). Individual poster composites may still
    opt into larger type explicitly.
    """
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 8.5,
        "font.weight": "normal",
        "text.color": INK,
        "axes.titlesize": 10,
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.labelsize": 9,
        "axes.labelweight": "normal",
        "axes.labelcolor": INK,
        "axes.edgecolor": OUTLINE_COLOR,
        "axes.linewidth": 0.8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "legend.fontsize": 8,
        "legend.title_fontsize": 8,
        "legend.frameon": False,
        "figure.dpi": 140,
        "figure.facecolor": "white",
        "savefig.dpi": PAPER_DPI,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.04,
        "savefig.facecolor": "white",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "lines.linewidth": 1.2,
        "lines.markersize": 4.5,
        "errorbar.capsize": 2.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


def style_axis(ax, *, grid_axis: str | None = "y") -> None:
    """Apply quiet scaffolding to an existing axis."""
    if grid_axis:
        ax.grid(True, axis=grid_axis, color=GRID_COLOR, linewidth=0.55, alpha=0.75)
        ax.set_axisbelow(True)
    ax.tick_params(length=3, width=0.7)


# ---------------------------------------------------------------------------
# Title / label formatters
# ---------------------------------------------------------------------------
_CONTRAST_OVERRIDES = {
    "vs": "vs",
    "psyrats": "PSYRATS",
    "avh": "AVH",
    "hc": "HC",
    "iq": "IQ",
    "fd": "FD",
    "stg": "STG",
    "mtg": "MTG",
    "sts": "STS",
    "ifg": "IFG",
    "heschl": "Heschl",
    "roi": "ROI",
}


def format_contrast(name: str) -> str:
    """Convert a contrast key like 'sentences_vs_reversed' to 'Sentences vs Reversed'."""
    if not name:
        return ""
    parts = name.replace("-", " ").split("_")
    out = []
    for p in parts:
        low = p.lower()
        if low in _CONTRAST_OVERRIDES:
            out.append(_CONTRAST_OVERRIDES[low])
        else:
            out.append(p.capitalize())
    return " ".join(out)


def format_roi(name: str) -> str:
    """Convert an ROI key like 'L_STG_posterior' to 'L STG posterior'."""
    if not name:
        return ""
    parts = name.split("_")
    out = []
    for p in parts:
        low = p.lower()
        if p in ("L", "R"):
            out.append(p)
        elif low in _CONTRAST_OVERRIDES:
            out.append(_CONTRAST_OVERRIDES[low])
        else:
            out.append(p.capitalize())
    return " ".join(out)
