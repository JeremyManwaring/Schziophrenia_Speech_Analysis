"""
Laterality Index Analysis: AVH- vs AVH+ (data only).

Computes laterality indices for bilateral ROI pairs and writes:
  - results/data/laterality.csv          (per-group means / SEM)
  - results/data/laterality_stats.csv    (t-test + Cohen's d, AVH- vs AVH+, FDR-corrected)
  - results/data/laterality_summary.json (metadata)

All plotting is handled by `poster_visualizations.py`.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).parent.parent.parent
ROI_DIR = BASE_DIR / "results" / "data" / "roi_values"
PARTICIPANTS_PATH = BASE_DIR / "participants.tsv"
OUTPUT_DIR = BASE_DIR / "results" / "data"

BILATERAL_PAIRS = {
    "STG_posterior": ("L_STG_posterior", "R_STG_posterior"),
    "STG_anterior": ("L_STG_anterior", "R_STG_anterior"),
    "MTG": ("L_MTG", "R_MTG"),
    "Heschl": ("L_Heschl", "R_Heschl"),
    "IFG": ("L_IFG_opercularis", "R_IFG"),
}

CONTRASTS = [
    "sentences_vs_reversed",
    "speech_vs_reversed",
    "words_vs_sentences",
    "words_vs_reversed",
]


def _load_roi_data(contrast: str) -> pd.DataFrame | None:
    p = ROI_DIR / f"{contrast}_roi_values.csv"
    return pd.read_csv(p) if p.exists() else None


def _laterality(left: float, right: float) -> float:
    denom = abs(left) + abs(right)
    if denom == 0 or not np.isfinite(denom):
        return np.nan
    return (left - right) / denom


def _per_subject_li(df: pd.DataFrame, pair: tuple[str, str]) -> pd.DataFrame:
    L, R = pair
    if L not in df.columns or R not in df.columns:
        return pd.DataFrame()
    out = df[["subject_id", "group"]].copy()
    out["LI"] = df.apply(lambda row: _laterality(row[L], row[R]), axis=1)
    return out


def analyze_laterality(contrast: str) -> list[dict]:
    df = _load_roi_data(contrast)
    if df is None:
        return []

    results: list[dict] = []
    for pair_name, pair in BILATERAL_PAIRS.items():
        li = _per_subject_li(df, pair)
        if li.empty:
            continue

        for group in ("HC", "AVH-", "AVH+"):
            vals = li[li["group"] == group]["LI"].dropna()
            if vals.empty:
                continue
            mean_li = float(vals.mean())
            results.append({
                "contrast": contrast,
                "roi_pair": pair_name,
                "group": group,
                "mean_LI": mean_li,
                "std_LI": float(vals.std()),
                "sem_LI": float(stats.sem(vals)),
                "n": int(len(vals)),
                "lateralization": "Left" if mean_li > 0.1 else ("Right" if mean_li < -0.1 else "Bilateral"),
            })

        a = li[li["group"] == "AVH-"]["LI"].dropna()
        b = li[li["group"] == "AVH+"]["LI"].dropna()
        if len(a) > 2 and len(b) > 2:
            t, p = stats.ttest_ind(a, b)
            pooled = np.sqrt(((len(a) - 1) * a.std() ** 2 + (len(b) - 1) * b.std() ** 2) / (len(a) + len(b) - 2))
            d = float((a.mean() - b.mean()) / pooled) if pooled > 0 else 0.0
            results.append({
                "contrast": contrast,
                "roi_pair": pair_name,
                "comparison": "AVH-_vs_AVH+",
                "t_statistic": float(t),
                "p_value": float(p),
                "cohens_d": d,
            })
    return results


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("\n" + "=" * 70)
    print("LATERALITY INDEX ANALYSIS")
    print("=" * 70)

    all_results: list[dict] = []
    for c in CONTRASTS:
        print(f"  {c}")
        all_results.extend(analyze_laterality(c))
    if not all_results:
        print("No results generated. Check ROI data.")
        return

    stat_data = [r for r in all_results if "p_value" in r]
    if stat_data:
        _, p_fdr, _, _ = multipletests([r["p_value"] for r in stat_data],
                                       alpha=0.05, method="fdr_bh")
        for r, q in zip(stat_data, p_fdr):
            r["p_fdr"] = float(q)

    df_long = pd.DataFrame([r for r in all_results if "mean_LI" in r])
    df_stats = pd.DataFrame(stat_data)

    df_long.to_csv(OUTPUT_DIR / "laterality.csv", index=False)
    df_stats.to_csv(OUTPUT_DIR / "laterality_stats.csv", index=False)

    summary = {
        "analysis": "Laterality Index Analysis",
        "comparison": "AVH- vs AVH+",
        "formula": "LI = (L - R) / (|L| + |R|)",
        "interpretation": {
            "LI > 0": "Left hemisphere dominant",
            "LI < 0": "Right hemisphere dominant",
            "LI ~ 0": "Bilateral / symmetric",
        },
        "roi_pairs_analyzed": list(BILATERAL_PAIRS.keys()),
        "contrasts_analyzed": CONTRASTS,
        "n_significant_differences": int((df_stats["p_fdr"] < 0.05).sum()) if not df_stats.empty else 0,
    }
    with open(OUTPUT_DIR / "laterality_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  -> {OUTPUT_DIR}/laterality.csv (+ stats, summary)")


if __name__ == "__main__":
    main()
