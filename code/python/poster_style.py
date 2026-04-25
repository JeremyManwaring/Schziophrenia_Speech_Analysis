"""
Shared style configuration for poster-quality visualizations.

Import once at the top of any plotting script:

    from poster_style import apply_style, PALETTE, GROUP_ORDER, format_contrast, format_roi

`apply_style()` should be called before creating any figures.
"""

from __future__ import annotations

import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Color palette (single source of truth across the codebase)
# ---------------------------------------------------------------------------
PALETTE = {
    "HC": "#7f8c8d",     # neutral gray
    "AVH-": "#3498db",   # blue
    "AVH+": "#e74c3c",   # red
}

GROUP_ORDER = ["HC", "AVH-", "AVH+"]

# Sex palette (reuse across demographic plots)
SEX_PALETTE = {"male": "#5dade2", "female": "#f1948a"}

# Significance highlight colors
SIG_COLOR = "#27ae60"      # green when significant
NS_COLOR = "#95a5a6"       # gray when non-significant


def apply_style() -> None:
    """Apply project-wide matplotlib rcParams for poster-ready figures."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 13,
        "axes.titlesize": 16,
        "axes.titleweight": "bold",
        "axes.labelsize": 14,
        "axes.labelweight": "bold",
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "legend.fontsize": 12,
        "legend.frameon": True,
        "legend.framealpha": 0.9,
        "figure.dpi": 110,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
    })


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
