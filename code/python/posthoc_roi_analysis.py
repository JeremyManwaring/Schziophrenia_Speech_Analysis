"""
Post hoc targeted ROI ANCOVA for the AVH replication rework.

Reads pre-computed ROI activation values from results/data/roi_values/ and
adds the analyses needed to defend the inference against the original
limitations (small N, multiple comparisons, age imbalance, motion):

1. ANCOVA per (contrast, ROI):  activation ~ group + age + iq + sex + mean_fd
   with FDR correction within each contrast (12 ROIs).
2. Post hoc targeted family (Bonferroni m=2):
       sentences_vs_reversed x {L_MTG, L_STS}, AVH- vs AVH+
3. Motion-sensitivity rerun of (1) and (2), excluding the 4 high-motion
   subjects in results/data/motion_exclusions.txt (the source cohort drops
   from 71 to 67; complete-case model n drops from 69 to 65).
4. Adjusted Cohen's d (from the partialled residuals) + bootstrap 95% CI for
   the targeted ROIs, so the poster forest plot uses covariate-adjusted
   effects rather than raw two-sample d.

All outputs are written to results/data/posthoc/.  No GLM re-run.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PARTICIPANTS_PATH = BASE_DIR / "participants.tsv"
QC_PATH = BASE_DIR / "results" / "data" / "qc.csv"
ROI_DIR = BASE_DIR / "results" / "data" / "roi_values"
MOTION_EXCL_PATH = BASE_DIR / "results" / "data" / "motion_exclusions.txt"
OUTPUT_DIR = BASE_DIR / "results" / "data" / "posthoc"

CONTRASTS = [
    "words_vs_baseline",
    "sentences_vs_baseline",
    "reversed_vs_baseline",
    "words_vs_reversed",
    "sentences_vs_reversed",
    "speech_vs_reversed",
    "words_vs_sentences",
]

ROI_COLS = [
    "L_STG_posterior", "L_STG_anterior", "L_MTG", "L_IFG_triangularis",
    "L_IFG_opercularis", "L_STS", "R_STG_posterior", "R_STG_anterior",
    "R_MTG", "R_IFG", "L_Heschl", "R_Heschl",
]

# Targeted post hoc family selected after inspecting the omnibus ROI results.
TARGET_CONTRAST = "sentences_vs_reversed"
TARGET_ROIS = ["L_MTG", "L_STS"]
TARGET_M = len(TARGET_ROIS)  # Bonferroni denominator

N_BOOT = 2000  # used only for the small targeted post hoc family
RNG = np.random.default_rng(20260608)


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
def load_covariates() -> pd.DataFrame:
    """Build a per-subject covariate table (group, age, iq, sex, mean_fd)."""
    parts = pd.read_csv(PARTICIPANTS_PATH, sep="\t")
    for col in ("age", "iq", "psyrats"):
        parts[col] = pd.to_numeric(parts[col], errors="coerce")
    parts["sex"] = parts["sex"].map({"male": 0, "female": 1}).astype(float)

    qc = pd.read_csv(QC_PATH)[["subject_id", "mean_fd"]]
    qc = qc.rename(columns={"subject_id": "participant_id"})

    cov = parts.merge(qc, on="participant_id", how="left")
    return cov


def load_excluded_subjects() -> list[str]:
    """Parse results/data/motion_exclusions.txt for flagged subject IDs."""
    if not MOTION_EXCL_PATH.exists():
        return []
    flagged: list[str] = []
    for line in MOTION_EXCL_PATH.read_text().splitlines():
        line = line.strip()
        if line.startswith("sub-") and ":" in line:
            flagged.append(line.split(":")[0].strip())
    return flagged


def build_design(contrast: str, covariates: pd.DataFrame) -> pd.DataFrame:
    """Merge ROI activations with covariates for one contrast."""
    roi_path = ROI_DIR / f"{contrast}_roi_values.csv"
    roi = pd.read_csv(roi_path)
    roi = roi.rename(columns={"subject_id": "participant_id"})
    if "group" in roi.columns:
        roi = roi.drop(columns=["group"])
    merged = roi.merge(
        covariates[["participant_id", "group", "age", "iq", "sex", "mean_fd"]],
        on="participant_id", how="left",
    )
    return merged


# --------------------------------------------------------------------------
# ANCOVA: activation ~ group + age + iq + sex + mean_fd
# --------------------------------------------------------------------------
def _fit_ancova(df: pd.DataFrame, roi: str, bootstrap: bool = False) -> dict:
    """Fit the AVH-vs-AVH+ contrast inside a 3-group ANCOVA.

    The model uses both patient groups (and HC) and recovers the AVH- vs AVH+
    contrast directly from the fitted coefficients.  HC are kept so the
    variance estimate uses all available complete cases across the three groups.

    A bootstrap CI on the adjusted Cohen's d is only computed when
    ``bootstrap`` is True (used for the small targeted family); otherwise
    a fast closed-form CI is derived from the contrast t-statistic.
    """
    sub = df.dropna(subset=[roi, "age", "iq", "sex", "mean_fd", "group"]).copy()
    sub["group"] = pd.Categorical(sub["group"], categories=["HC", "AVH-", "AVH+"])
    formula = f"Q('{roi}') ~ C(group, Treatment(reference='HC')) + age + iq + sex + mean_fd"
    model = smf.ols(formula, data=sub).fit()

    # Group coefficients are vs HC; AVH- vs AVH+ = beta_AVH- - beta_AVH+
    avh_minus = "C(group, Treatment(reference='HC'))[T.AVH-]"
    avh_plus = "C(group, Treatment(reference='HC'))[T.AVH+]"
    contrast = np.zeros(len(model.params))
    idx = {name: i for i, name in enumerate(model.params.index)}
    contrast[idx[avh_minus]] = 1.0
    contrast[idx[avh_plus]] = -1.0
    t_test = model.t_test(contrast)

    # Adjusted Cohen's d from residual SD (covariate-adjusted)
    resid_sd = float(np.sqrt(model.mse_resid))
    diff = float(np.atleast_1d(t_test.effect).ravel()[0])
    se = float(np.atleast_1d(t_test.sd).ravel()[0])
    d_adj = diff / resid_sd if resid_sd > 0 else np.nan

    if bootstrap:
        # Bootstrap CI for d_adj (resample within group to keep balance)
        boots: list[float] = []
        g_a = sub[sub["group"] == "AVH-"]
        g_b = sub[sub["group"] == "AVH+"]
        g_h = sub[sub["group"] == "HC"]
        if len(g_a) >= 3 and len(g_b) >= 3 and len(g_h) >= 3:
            for _ in range(N_BOOT):
                try:
                    b = pd.concat([
                        g_h.iloc[RNG.integers(0, len(g_h), len(g_h))],
                        g_a.iloc[RNG.integers(0, len(g_a), len(g_a))],
                        g_b.iloc[RNG.integers(0, len(g_b), len(g_b))],
                    ], ignore_index=True)
                    m = smf.ols(formula, data=b).fit()
                    idx_b = {n: i for i, n in enumerate(m.params.index)}
                    if avh_minus not in idx_b or avh_plus not in idx_b:
                        continue
                    d_b = (m.params.iloc[idx_b[avh_minus]] - m.params.iloc[idx_b[avh_plus]])
                    rsd = float(np.sqrt(m.mse_resid))
                    if rsd > 0:
                        boots.append(d_b / rsd)
                except Exception:
                    continue
        if boots:
            d_lo, d_hi = float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))
        else:
            d_lo = d_hi = np.nan
    else:
        # Closed-form CI: scale the difference CI by residual SD
        if resid_sd > 0 and se > 0:
            crit = 1.96
            d_lo = (diff - crit * se) / resid_sd
            d_hi = (diff + crit * se) / resid_sd
        else:
            d_lo = d_hi = np.nan

    return {
        "roi": roi,
        "n": int(len(sub)),
        "n_HC": int((sub["group"] == "HC").sum()),
        "n_AVH-": int((sub["group"] == "AVH-").sum()),
        "n_AVH+": int((sub["group"] == "AVH+").sum()),
        "diff_AVHneg_minus_AVHpos": diff,
        "se": float(np.atleast_1d(t_test.sd).ravel()[0]),
        "t_stat": float(np.atleast_1d(t_test.tvalue).ravel()[0]),
        "df": float(model.df_resid),
        "p_value": float(np.atleast_1d(t_test.pvalue).ravel()[0]),
        "d_adj": d_adj,
        "d_adj_ci_lo": d_lo,
        "d_adj_ci_hi": d_hi,
    }


def run_ancova_for_subjects(covariates: pd.DataFrame, label: str) -> pd.DataFrame:
    """ANCOVA across all contrasts x ROIs for the given covariate set."""
    rows: list[dict] = []
    for contrast in CONTRASTS:
        merged = build_design(contrast, covariates)
        contrast_rows: list[dict] = []
        for roi in ROI_COLS:
            if roi not in merged.columns:
                continue
            boot = (contrast == TARGET_CONTRAST) and (roi in TARGET_ROIS)
            r = _fit_ancova(merged, roi, bootstrap=boot)
            r["contrast"] = contrast
            r["sample"] = label
            contrast_rows.append(r)
        # FDR within this contrast (12 ROIs)
        pvals = [r["p_value"] for r in contrast_rows]
        if pvals:
            _, p_fdr, _, _ = multipletests(pvals, alpha=0.05, method="fdr_bh")
            for r, q in zip(contrast_rows, p_fdr):
                r["p_fdr_within_contrast"] = float(q)
        rows.extend(contrast_rows)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Targeted post hoc family
# --------------------------------------------------------------------------
def run_targeted_family(ancova_df: pd.DataFrame, sample: str) -> pd.DataFrame:
    """Extract the post hoc targeted ROIs and apply Bonferroni m=2."""
    sub = ancova_df[
        (ancova_df["contrast"] == TARGET_CONTRAST)
        & (ancova_df["roi"].isin(TARGET_ROIS))
        & (ancova_df["sample"] == sample)
    ].copy()
    sub["bonferroni_threshold"] = 0.05 / TARGET_M
    sub["p_bonferroni"] = (sub["p_value"] * TARGET_M).clip(upper=1.0)
    sub["survives_bonferroni"] = sub["p_value"] < (0.05 / TARGET_M)
    return sub.sort_values("roi").reset_index(drop=True)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("POST HOC TARGETED ROI ANCOVA")
    print("=" * 70)

    cov_full = load_covariates()
    excluded = load_excluded_subjects()
    cov_clean = cov_full[~cov_full["participant_id"].isin(excluded)].copy()

    n_full = cov_full["participant_id"].nunique()
    n_clean = cov_clean["participant_id"].nunique()
    print(f"\nFull sample : n = {n_full}")
    print(f"Motion-clean: n = {n_clean}  (excluded: {', '.join(excluded) if excluded else 'none'})")

    print("\n[1/2] ANCOVA on full sample ...")
    ancova_full = run_ancova_for_subjects(cov_full, label="full")
    model_ns_full = sorted(ancova_full["n"].unique())
    if len(model_ns_full) != 1:
        raise RuntimeError(f"Inconsistent full-sample model sizes: {model_ns_full}")
    n_model_full = int(model_ns_full[0])
    full_label = f"full_n{n_model_full}"
    ancova_full["sample"] = full_label
    ancova_full.to_csv(OUTPUT_DIR / "roi_ancova_full.csv", index=False)

    print("[2/2] ANCOVA on motion-clean sample ...")
    ancova_clean = run_ancova_for_subjects(cov_clean, label="motion_clean")
    model_ns_clean = sorted(ancova_clean["n"].unique())
    if len(model_ns_clean) != 1:
        raise RuntimeError(f"Inconsistent motion-clean model sizes: {model_ns_clean}")
    n_model_clean = int(model_ns_clean[0])
    clean_label = f"motion_clean_n{n_model_clean}"
    ancova_clean["sample"] = clean_label
    ancova_clean.to_csv(OUTPUT_DIR / "roi_ancova_motion_clean.csv", index=False)

    ancova_all = pd.concat([ancova_full, ancova_clean], ignore_index=True)
    ancova_all.to_csv(OUTPUT_DIR / "roi_ancova.csv", index=False)

    targeted_full = run_targeted_family(ancova_full, sample=full_label)
    targeted_clean = run_targeted_family(ancova_clean, sample=clean_label)
    targeted = pd.concat([targeted_full, targeted_clean], ignore_index=True)
    targeted.to_csv(OUTPUT_DIR / "posthoc_targeted.csv", index=False)

    sensitivity = targeted[["sample", "roi", "p_value", "p_bonferroni",
                           "survives_bonferroni", "d_adj",
                           "d_adj_ci_lo", "d_adj_ci_hi"]].copy()
    sensitivity.to_csv(OUTPUT_DIR / "motion_sensitivity.csv", index=False)

    # FDR summary across full ANCOVA (any contrast x ROI surviving FDR)
    fdr_hits = ancova_full[ancova_full["p_fdr_within_contrast"] < 0.05][
        ["contrast", "roi", "diff_AVHneg_minus_AVHpos", "t_stat",
         "p_value", "p_fdr_within_contrast", "d_adj"]
    ].sort_values(["contrast", "p_fdr_within_contrast"]).reset_index(drop=True)
    fdr_hits.to_csv(OUTPUT_DIR / "roi_ancova_fdr_hits.csv", index=False)

    summary = {
        "analysis": "ANCOVA: activation ~ group + age + iq + sex + mean_fd",
        "interpretation": "Post hoc targeted ANCOVA selected after omnibus ROI review",
        "target_contrast": TARGET_CONTRAST,
        "target_rois": TARGET_ROIS,
        "targeted_correction": f"Bonferroni m={TARGET_M} (alpha = 0.05)",
        "exploratory_correction": "FDR (Benjamini-Hochberg) within each contrast (12 ROIs)",
        "cohort_n_full": int(n_full),
        "cohort_n_motion_clean": int(n_clean),
        "model_n_full": n_model_full,
        "model_n_motion_clean": n_model_clean,
        "excluded_motion_subjects": excluded,
        "targeted_full": targeted_full.to_dict(orient="records"),
        "targeted_motion_clean": targeted_clean.to_dict(orient="records"),
        "n_fdr_hits_full": int(len(fdr_hits)),
    }
    with open(OUTPUT_DIR / "posthoc_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)

    # Console report --------------------------------------------------------
    print("\n----------------- POST HOC TARGETED ANCOVA -------------------")
    for _, r in targeted.iterrows():
        flag = "PASS" if r["survives_bonferroni"] else "fail"
        print(f"  [{r['sample']:>12}] {r['roi']:>6}  t={r['t_stat']:+.2f}  "
              f"p={r['p_value']:.4f}  p_bonf={r['p_bonferroni']:.4f}  "
              f"d_adj={r['d_adj']:+.2f} [{r['d_adj_ci_lo']:+.2f}, {r['d_adj_ci_hi']:+.2f}]  -> {flag}")
    print("\n----------------- EXPLORATORY FDR HITS -----------------------")
    if fdr_hits.empty:
        print("  (none survive within-contrast FDR)")
    else:
        for _, r in fdr_hits.iterrows():
            print(f"  {r['contrast']:>25}  {r['roi']:>18}  "
                  f"p={r['p_value']:.4f}  p_fdr={r['p_fdr_within_contrast']:.4f}  "
                  f"d_adj={r['d_adj']:+.2f}")
    print("\nOutputs -> " + str(OUTPUT_DIR))


if __name__ == "__main__":
    main()
