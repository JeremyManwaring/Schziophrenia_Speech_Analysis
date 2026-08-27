"""Release checks for dataset grain, stored results, and figure artifacts."""

from __future__ import annotations

import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "results" / "data"
FIGURE_DIR = ROOT / "results" / "paper_figures"

CONTRASTS = {
    "reversed_vs_baseline",
    "sentences_vs_baseline",
    "sentences_vs_reversed",
    "speech_vs_reversed",
    "words_vs_baseline",
    "words_vs_reversed",
    "words_vs_sentences",
}

FIGURES = {
    "Figure_1_core_results",
    "Figure_2_effect_size_landscape",
    "Figure_3_ROI_definitions",
    "Supplement_Figure_1_whole_brain_inference",
    "Supplement_Figure_2_MVPA",
    "Supplement_Figure_3_sample_and_QC",
    "Supplement_Figure_4_exploratory_network",
}


def test_participant_grain_and_bids_paths() -> None:
    participants = pd.read_csv(ROOT / "participants.tsv", sep="\t")

    assert len(participants) == 71
    assert participants["participant_id"].is_unique
    assert participants["group"].value_counts().to_dict() == {
        "HC": 25,
        "AVH-": 23,
        "AVH+": 23,
    }
    assert participants["iq"].isna().sum() == 2
    assert participants["psyrats"].isna().sum() == 25

    subject_dirs = {path.name for path in ROOT.glob("sub-*") if path.is_dir()}
    assert subject_dirs == set(participants["participant_id"])

    for subject in participants["participant_id"]:
        assert (ROOT / subject / "anat" / f"{subject}_T1w.nii.gz").is_symlink()
        assert (
            ROOT / subject / "func" / f"{subject}_task-speech_bold.nii.gz"
        ).is_symlink()

    events = pd.read_csv(ROOT / "task-speech_events.tsv", sep="\t")
    assert list(events.columns) == ["onset", "duration", "condition"]
    assert len(events) == 24
    assert events["condition"].value_counts().to_dict() == {
        "white_noise": 6,
        "sentences": 6,
        "words": 6,
        "reversed": 6,
    }
    assert (events["onset"] >= 0).all()
    assert (events["duration"] > 0).all()


def test_stored_tables_and_json_parse_cleanly() -> None:
    for path in sorted(DATA_DIR.rglob("*.json")):
        with path.open(encoding="utf-8") as stream:
            json.load(stream)

    for path in sorted(DATA_DIR.rglob("*.csv")):
        table = pd.read_csv(path)
        assert not table.duplicated().any(), path


def test_roi_families_have_expected_coverage() -> None:
    roi_dir = DATA_DIR / "roi_values"
    value_files = {
        path.name.removesuffix("_roi_values.csv"): path
        for path in roi_dir.glob("*_roi_values.csv")
    }
    anova_files = {
        path.name.removesuffix("_roi_anova.csv"): path
        for path in roi_dir.glob("*_roi_anova.csv")
    }

    assert set(value_files) == CONTRASTS
    assert set(anova_files) == CONTRASTS

    for path in value_files.values():
        values = pd.read_csv(path)
        assert len(values) == 71
        assert values["subject_id"].is_unique
        assert values["group"].value_counts().to_dict() == {
            "HC": 25,
            "AVH-": 23,
            "AVH+": 23,
        }

    for path in anova_files.values():
        anova = pd.read_csv(path)
        assert len(anova) == 12
        assert (anova["p_fdr"] >= 0.05).all()


def test_confirmatory_metadata_and_primary_correlation() -> None:
    with (DATA_DIR / "cluster_maps" / "analysis_summary.json").open() as stream:
        cluster_summary = json.load(stream)

    assert cluster_summary["status"] == "complete"
    assert cluster_summary["n_permutations"] == 10_000
    assert cluster_summary["random_state"] == 20260824
    assert set(cluster_summary["results"]) == {
        "sentences_vs_reversed",
        "speech_vs_reversed",
        "words_vs_sentences",
    }
    for result in cluster_summary["results"].values():
        assert result["n_subjects"] == 45
        assert result["n_avh_minus"] == 22
        assert result["n_avh_plus"] == 23
        assert result["n_permutations"] == 10_000
        assert result["n_significant_clusters"] == 0
        assert result["complete_case_exclusions"] == ["sub-28"]
        for output in result["outputs"].values():
            assert (ROOT / output).exists()

    primary = pd.read_csv(DATA_DIR / "correlations" / "primary_psyrats.csv")
    significant = primary[primary["partial_p_fdr_within_contrast"] < 0.05]
    assert len(significant) == 1
    hit = significant.iloc[0]
    assert hit["contrast"] == "speech_vs_reversed"
    assert hit["roi"] == "R_STG_posterior"
    assert hit["n"] == 23
    assert hit["df"] == 19


def test_exploratory_outputs_report_multiplicity_corrections() -> None:
    edges = pd.read_csv(DATA_DIR / "connectivity_uncorrected_edges.csv")
    assert list(edges.columns) == [
        "roi1",
        "roi2",
        "diff",
        "t_stat",
        "p_value",
        "p_fdr",
    ]
    assert len(edges) == 2
    assert (edges["p_value"] < 0.05).all()
    assert (edges["p_fdr"] >= 0.05).all()

    with (DATA_DIR / "connectivity.json").open() as stream:
        connectivity = json.load(stream)
    assert connectivity["n_uncorrected_edges"] == len(edges)
    assert connectivity["n_fdr_significant_edges"] == 0

    matrix_dir = DATA_DIR / "connectivity"
    for name in (
        "connectivity_AVH-.npy",
        "connectivity_AVH+.npy",
        "connectivity_difference.npy",
        "connectivity_pvalues.npy",
    ):
        matrix = np.load(matrix_dir / name)
        assert matrix.shape == (12, 12)
        assert np.isfinite(matrix).all()
        assert np.allclose(matrix, matrix.T)

    laterality = pd.read_csv(DATA_DIR / "laterality.csv")
    laterality_stats = pd.read_csv(DATA_DIR / "laterality_stats.csv")
    assert len(laterality) == 60
    assert len(laterality_stats) == 20
    assert set(laterality_stats["comparison"]) == {"AVH-_vs_AVH+"}
    assert (laterality_stats["p_fdr"] >= 0.05).all()


def test_quality_control_has_one_canonical_record() -> None:
    qc = pd.read_csv(DATA_DIR / "qc.csv")
    assert len(qc) == 71
    assert qc["subject_id"].is_unique
    assert not (ROOT / "results" / "qc").exists()

    exclusions = (DATA_DIR / "motion_exclusions.txt").read_text()
    assert "Mean FD > 0.5 mm" in exclusions
    assert "sub-02" in exclusions
    assert "sub-22" in exclusions
    assert "sub-34" in exclusions
    assert "sub-45" in exclusions


def test_canonical_figure_package_is_complete_and_unambiguous() -> None:
    expected = {"README.md"}
    for stem in FIGURES:
        expected.update({f"{stem}.png", f"{stem}.svg", f"{stem}.pdf"})

    actual = {path.name for path in FIGURE_DIR.iterdir() if path.is_file()}
    assert actual == expected
    assert not (ROOT / "results" / "paper_figures_nature").exists()
    assert not (ROOT / "results" / "paper_figures_neuron").exists()
    assert not (ROOT / "results" / "poster" / "paper_visualizations").exists()

    for stem in FIGURES:
        png = FIGURE_DIR / f"{stem}.png"
        with png.open("rb") as stream:
            assert stream.read(8) == b"\x89PNG\r\n\x1a\n"
            assert stream.read(4) == b"\x00\x00\x00\r"
            assert stream.read(4) == b"IHDR"
            width, height = struct.unpack(">II", stream.read(8))
        assert width == 4320
        assert height >= 1800

        ET.parse(FIGURE_DIR / f"{stem}.svg")
        assert (FIGURE_DIR / f"{stem}.pdf").read_bytes().startswith(b"%PDF-")
