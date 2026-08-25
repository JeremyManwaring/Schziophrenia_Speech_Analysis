"""Permutation-based whole-brain AVH- versus AVH+ inference.

The analysis uses two-sided permutation testing with a voxelwise uncorrected
cluster-forming threshold of p < .001 and maximum-cluster-size familywise-error
correction at p < .05. Corrected claims are written only after every requested
contrast completes successfully.
"""

from __future__ import annotations

import json
import platform
import time
from pathlib import Path

import nibabel as nib
import nilearn
import numpy as np
import pandas as pd
import scipy
from nilearn.glm.second_level import non_parametric_inference
from nilearn.reporting import get_clusters_table


BASE_DIR = Path(__file__).resolve().parent.parent.parent
FIRST_LEVEL_DIR = BASE_DIR / "results" / "data" / "first_level"
PARTICIPANTS_PATH = BASE_DIR / "participants.tsv"
OUTPUT_DIR = BASE_DIR / "results" / "data" / "cluster_maps"

KEY_CONTRASTS = [
    "sentences_vs_reversed",
    "speech_vs_reversed",
    "words_vs_sentences",
]

N_PERMUTATIONS = 10_000
CLUSTER_FORMING_P = 0.001
FWE_ALPHA = 0.05
RANDOM_STATE = 20260824


def load_participants() -> pd.DataFrame:
    """Load patient covariates without silently imputing missing values."""
    df = pd.read_csv(PARTICIPANTS_PATH, sep="\t")
    for col in ("age", "iq"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["sex_binary"] = df["sex"].map({"male": 0.0, "female": 1.0})
    return df


def collect_contrast_maps(
    contrast_name: str,
    participants_df: pd.DataFrame,
) -> tuple[list[str], pd.DataFrame, dict]:
    """Collect complete-case patient maps and the adjusted group design."""
    patients = participants_df[
        participants_df["group"].isin(["AVH-", "AVH+"])
    ].copy()

    missing_covariates = patients[
        patients[["age", "iq", "sex_binary"]].isna().any(axis=1)
    ]["participant_id"].tolist()
    patients = patients.dropna(subset=["age", "iq", "sex_binary"]).copy()

    maps: list[str] = []
    rows: list[dict] = []
    missing_maps: list[str] = []
    for _, row in patients.iterrows():
        subject_id = row["participant_id"]
        map_path = (
            FIRST_LEVEL_DIR
            / subject_id
            / f"{subject_id}_{contrast_name}_effect.nii.gz"
        )
        if not map_path.exists():
            missing_maps.append(subject_id)
            continue
        maps.append(str(map_path))
        rows.append(
            {
                "participant_id": subject_id,
                "group": row["group"],
                "group_effect": 1.0 if row["group"] == "AVH-" else -1.0,
                "age": float(row["age"]),
                "iq": float(row["iq"]),
                "sex": float(row["sex_binary"]),
            }
        )

    if missing_maps:
        raise FileNotFoundError(
            f"Missing first-level maps for {contrast_name}: {missing_maps}"
        )

    design_info = pd.DataFrame(rows)
    for col in ("age", "iq"):
        design_info[col] = design_info[col] - design_info[col].mean()
    design_matrix = design_info[["group_effect", "age", "iq", "sex"]].copy()

    metadata = {
        "n_subjects": int(len(design_info)),
        "n_avh_minus": int((design_info["group"] == "AVH-").sum()),
        "n_avh_plus": int((design_info["group"] == "AVH+").sum()),
        "complete_case_exclusions": missing_covariates,
        "subjects": design_info["participant_id"].tolist(),
    }
    return maps, design_matrix, metadata


def _threshold_corrected_t(
    t_img: nib.spatialimages.SpatialImage,
    logp_img: nib.spatialimages.SpatialImage,
) -> tuple[nib.Nifti1Image, np.ndarray]:
    """Keep t statistics only inside cluster-size FWER-significant clusters."""
    cutoff = -np.log10(FWE_ALPHA)
    logp = np.asarray(logp_img.get_fdata())
    significant = np.isfinite(logp) & (logp >= cutoff)
    t_data = np.asarray(t_img.get_fdata())
    corrected_t = np.where(significant, t_data, 0.0)
    return nib.Nifti1Image(corrected_t, t_img.affine, t_img.header), significant


def _cluster_table(
    corrected_t_img: nib.Nifti1Image,
    logp_img: nib.spatialimages.SpatialImage,
) -> pd.DataFrame:
    """Create a peak table and attach cluster-size FWER p-values."""
    if not np.any(corrected_t_img.get_fdata()):
        return pd.DataFrame(
            columns=[
                "Cluster ID",
                "X",
                "Y",
                "Z",
                "Peak Stat",
                "Cluster Size (mm3)",
                "cluster_size_fwer_p",
            ]
        )

    table = get_clusters_table(
        corrected_t_img,
        stat_threshold=np.finfo(float).eps,
        cluster_threshold=0,
        two_sided=True,
        min_distance=8,
    )
    inverse_affine = np.linalg.inv(logp_img.affine)
    logp_data = np.asarray(logp_img.get_fdata())
    corrected_ps = []
    for _, row in table.iterrows():
        xyz = np.array([row["X"], row["Y"], row["Z"], 1.0])
        ijk = np.rint(inverse_affine @ xyz).astype(int)[:3]
        ijk = np.clip(ijk, 0, np.array(logp_data.shape) - 1)
        logp = float(logp_data[tuple(ijk)])
        corrected_ps.append(10.0 ** (-logp))
    table["cluster_size_fwer_p"] = corrected_ps
    return table


def run_cluster_inference(
    contrast_name: str,
    participants_df: pd.DataFrame,
    n_perm: int = N_PERMUTATIONS,
) -> dict:
    """Run one complete permutation analysis and save result-backed outputs."""
    maps, design_matrix, metadata = collect_contrast_maps(
        contrast_name, participants_df
    )
    if len(maps) < 10:
        raise RuntimeError(f"Insufficient maps for {contrast_name}: {len(maps)}")

    print(
        f"\n{contrast_name}: n={metadata['n_subjects']} "
        f"(AVH-={metadata['n_avh_minus']}, AVH+={metadata['n_avh_plus']})"
    )
    print(
        f"Running {n_perm:,} two-sided permutations; "
        f"cluster-forming p < {CLUSTER_FORMING_P}"
    )
    started = time.time()
    outputs = non_parametric_inference(
        second_level_input=maps,
        design_matrix=design_matrix,
        second_level_contrast=np.array([1.0, 0.0, 0.0, 0.0]),
        model_intercept=True,
        n_perm=n_perm,
        two_sided_test=True,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=1,
        threshold=CLUSTER_FORMING_P,
    )
    required = {"t", "logp_max_t", "logp_max_size", "size"}
    missing = required.difference(outputs)
    if missing:
        raise RuntimeError(f"Nilearn omitted required outputs: {sorted(missing)}")

    prefix = f"{contrast_name}_AVH-_vs_AVH+"
    paths = {
        "t_stat": OUTPUT_DIR / f"{prefix}_tstat.nii.gz",
        "voxel_fwer_logp": OUTPUT_DIR / f"{prefix}_voxel_fwer_logp.nii.gz",
        "cluster_size_fwer_logp": OUTPUT_DIR
        / f"{prefix}_cluster_size_fwer_logp.nii.gz",
        "cluster_size": OUTPUT_DIR / f"{prefix}_cluster_size.nii.gz",
        "cluster_fwer_p05_tstat": OUTPUT_DIR
        / f"{prefix}_cluster_fwer_p05_tstat.nii.gz",
        "cluster_table": OUTPUT_DIR / f"{prefix}_cluster_table.csv",
    }
    nib.save(outputs["t"], paths["t_stat"])
    nib.save(outputs["logp_max_t"], paths["voxel_fwer_logp"])
    nib.save(outputs["logp_max_size"], paths["cluster_size_fwer_logp"])
    nib.save(outputs["size"], paths["cluster_size"])

    corrected_t, significant = _threshold_corrected_t(
        outputs["t"], outputs["logp_max_size"]
    )
    nib.save(corrected_t, paths["cluster_fwer_p05_tstat"])
    clusters = _cluster_table(corrected_t, outputs["logp_max_size"])
    clusters.to_csv(paths["cluster_table"], index=False)

    cluster_ids = {
        str(value).rstrip("abcdefghijklmnopqrstuvwxyz")
        for value in clusters.get("Cluster ID", pd.Series(dtype=str)).astype(str)
    }
    result = {
        **metadata,
        "n_permutations": int(n_perm),
        "two_sided": True,
        "cluster_forming_p_uncorrected": CLUSTER_FORMING_P,
        "cluster_size_fwer_alpha": FWE_ALPHA,
        "random_state": RANDOM_STATE,
        "n_significant_voxels": int(significant.sum()),
        "n_significant_clusters": int(len(cluster_ids - {""})),
        "runtime_seconds": float(time.time() - started),
        "outputs": {key: str(path.relative_to(BASE_DIR)) for key, path in paths.items()},
    }
    print(
        f"Completed {contrast_name}: {result['n_significant_clusters']} "
        f"cluster(s), {result['n_significant_voxels']} significant voxels"
    )
    return result


def main(n_perm: int = N_PERMUTATIONS) -> dict:
    """Run all contrasts; write the summary only after complete success."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    participants = load_participants()
    results = {
        contrast: run_cluster_inference(contrast, participants, n_perm=n_perm)
        for contrast in KEY_CONTRASTS
    }
    summary = {
        "analysis": "Two-sided permutation cluster inference",
        "comparison": "AVH- vs AVH+",
        "status": "complete",
        "inference": (
            "Maximum-cluster-size familywise-error correction at p < .05; "
            "voxelwise uncorrected cluster-forming p < .001"
        ),
        "n_permutations": int(n_perm),
        "random_state": RANDOM_STATE,
        "covariates": ["age", "iq", "sex"],
        "missing_covariate_policy": "complete case",
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "nibabel": nib.__version__,
            "nilearn": nilearn.__version__,
        },
        "results": results,
    }
    with open(OUTPUT_DIR / "analysis_summary.json", "w") as handle:
        json.dump(summary, handle, indent=2)
    print(f"\nVerified cluster-inference summary -> {OUTPUT_DIR / 'analysis_summary.json'}")
    return summary


if __name__ == "__main__":
    main()
