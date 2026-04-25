"""
Functional Connectivity Analysis: AVH- vs AVH+ (data only).

Computes ROI-to-ROI connectivity matrices (Fisher-z transformed Pearson r),
performs independent t-tests with FDR correction, and writes:
  - results/data/connectivity.json              (analysis summary + ROI metadata)
  - results/data/connectivity_significant.csv   (p < 0.05 connections)
  - results/data/connectivity/connectivity_AVH-.npy
  - results/data/connectivity/connectivity_AVH+.npy
  - results/data/connectivity/connectivity_difference.npy

All plotting is handled by `poster_visualizations.py`.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from nilearn.connectome import ConnectivityMeasure
from nilearn.maskers import NiftiSpheresMasker
from scipy import stats
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).parent.parent.parent
FMRIPREP_DIR = BASE_DIR / "derivatives" / "fmriprep"
PARTICIPANTS_PATH = BASE_DIR / "participants.tsv"
DATA_DIR = BASE_DIR / "results" / "data"
OUTPUT_DIR = DATA_DIR / "connectivity"

ROIS = {
    "L_STG_posterior": (-58, -32, 8),
    "L_STG_anterior": (-54, 4, -8),
    "L_MTG": (-58, -22, -10),
    "L_IFG_triangularis": (-48, 30, 8),
    "L_IFG_opercularis": (-52, 14, 16),
    "L_STS": (-54, -40, 4),
    "L_Heschl": (-42, -22, 8),
    "R_STG_posterior": (58, -32, 8),
    "R_STG_anterior": (54, 4, -8),
    "R_MTG": (58, -22, -10),
    "R_IFG": (48, 30, 8),
    "R_Heschl": (42, -22, 8),
}

SEED_RADIUS = 6  # mm


def _bold_path(sid: str) -> str | None:
    p = FMRIPREP_DIR / sid / "func" / f"{sid}_task-speech_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    return str(p) if p.exists() else None


def _confound_path(sid: str) -> str | None:
    p = FMRIPREP_DIR / sid / "func" / f"{sid}_task-speech_desc-confounds_timeseries.tsv"
    return str(p) if p.exists() else None


def _extract_timeseries(bold_path: str, confound_path: str):
    confounds_df = pd.read_csv(confound_path, sep="\t")
    cols = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"]
    if "csf" in confounds_df.columns:
        cols.append("csf")
    if "white_matter" in confounds_df.columns:
        cols.append("white_matter")
    confounds = confounds_df[cols].fillna(0).values

    masker = NiftiSpheresMasker(
        seeds=list(ROIS.values()), radius=SEED_RADIUS, allow_overlap=True,
        standardize=True, detrend=True, high_pass=0.01, low_pass=0.1, t_r=2.0,
        memory="nilearn_cache",
    )
    try:
        return masker.fit_transform(bold_path, confounds=confounds)
    except Exception as exc:
        print(f"    Error extracting timeseries: {exc}")
        return None


def _group_matrices(participants_df: pd.DataFrame, group: str):
    matrices, subs = [], []
    cm = ConnectivityMeasure(kind="correlation", vectorize=False)
    for _, row in participants_df[participants_df["group"] == group].iterrows():
        sid = row["participant_id"]
        bold = _bold_path(sid)
        conf = _confound_path(sid)
        if bold is None or conf is None:
            continue
        ts = _extract_timeseries(bold, conf)
        if ts is None:
            continue
        matrices.append(cm.fit_transform([ts])[0])
        subs.append(sid)
    if not matrices:
        return None, [], []
    return np.mean(matrices, axis=0), matrices, subs


def _fisher_z(r):
    return np.arctanh(np.clip(r, -0.999, 0.999))


def _compare(group1, group2, n_rois):
    t = np.zeros((n_rois, n_rois))
    p = np.ones((n_rois, n_rois))
    z1 = [_fisher_z(m) for m in group1]
    z2 = [_fisher_z(m) for m in group2]
    for i in range(n_rois):
        for j in range(i + 1, n_rois):
            v1 = [m[i, j] for m in z1]
            v2 = [m[i, j] for m in z2]
            if len(v1) > 2 and len(v2) > 2:
                ti, pi = stats.ttest_ind(v1, v2)
                t[i, j] = t[j, i] = ti
                p[i, j] = p[j, i] = pi
    return t, p


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("\n" + "=" * 70)
    print("FUNCTIONAL CONNECTIVITY ANALYSIS")
    print("=" * 70)

    parts = pd.read_csv(PARTICIPANTS_PATH, sep="\t")
    roi_names = list(ROIS.keys())
    n_rois = len(roi_names)

    print("\n  AVH- group ...")
    avh_minus_mean, avh_minus_mats, avh_minus_subs = _group_matrices(parts, "AVH-")
    print(f"    {len(avh_minus_subs)} subjects")
    print("\n  AVH+ group ...")
    avh_plus_mean, avh_plus_mats, avh_plus_subs = _group_matrices(parts, "AVH+")
    print(f"    {len(avh_plus_subs)} subjects")

    if avh_minus_mean is None or avh_plus_mean is None:
        print("\nError: could not compute connectivity for one or both groups.")
        return

    t_stats, p_values = _compare(avh_minus_mats, avh_plus_mats, n_rois)
    p_flat = [p_values[i, j] for i in range(n_rois) for j in range(i + 1, n_rois)]
    _, p_fdr_flat, _, _ = multipletests(p_flat, alpha=0.05, method="fdr_bh")
    p_fdr = np.ones_like(p_values)
    idx = 0
    for i in range(n_rois):
        for j in range(i + 1, n_rois):
            p_fdr[i, j] = p_fdr[j, i] = p_fdr_flat[idx]
            idx += 1

    diff = avh_minus_mean - avh_plus_mean

    sig: list[dict] = []
    for i in range(n_rois):
        for j in range(i + 1, n_rois):
            if p_values[i, j] < 0.05:
                sig.append({
                    "roi1": roi_names[i],
                    "roi2": roi_names[j],
                    "diff": float(diff[i, j]),
                    "t_stat": float(t_stats[i, j]),
                    "p_value": float(p_values[i, j]),
                    "p_fdr": float(p_fdr[i, j]),
                })

    np.save(OUTPUT_DIR / "connectivity_AVH-.npy", avh_minus_mean)
    np.save(OUTPUT_DIR / "connectivity_AVH+.npy", avh_plus_mean)
    np.save(OUTPUT_DIR / "connectivity_difference.npy", diff)
    np.save(OUTPUT_DIR / "connectivity_pvalues.npy", p_values)

    if sig:
        sig_df = pd.DataFrame(sig).sort_values("p_value")
    else:
        sig_df = pd.DataFrame(columns=["roi1", "roi2", "diff", "t_stat", "p_value", "p_fdr"])
    sig_df.to_csv(DATA_DIR / "connectivity_significant.csv", index=False)

    summary = {
        "analysis": "ROI-to-ROI Functional Connectivity",
        "comparison": "AVH- vs AVH+",
        "method": "Pearson correlation with Fisher z-transform",
        "n_rois": n_rois,
        "n_avh_minus": len(avh_minus_subs),
        "n_avh_plus": len(avh_plus_subs),
        "n_significant_connections": len(sig),
        "roi_names": roi_names,
        "roi_coordinates": {k: list(v) for k, v in ROIS.items()},
    }
    with open(DATA_DIR / "connectivity.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  -> {DATA_DIR / 'connectivity.json'}")
    print(f"  -> {DATA_DIR / 'connectivity_significant.csv'} ({len(sig)} sig)")


if __name__ == "__main__":
    main()
