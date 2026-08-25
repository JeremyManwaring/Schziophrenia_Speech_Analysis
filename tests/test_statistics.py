"""Focused regression tests for the corrected statistical methods."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from scipy import stats
from statsmodels.stats.oneway import anova_oneway


CODE_DIR = Path(__file__).resolve().parents[1] / "code" / "python"
sys.path.insert(0, str(CODE_DIR))

from correlation_analysis import partial_correlation  # noqa: E402
from roi_analysis import SPEECH_ROIS, create_sphere_masker  # noqa: E402
from welch_anova import games_howell_posthoc, welch_anova  # noqa: E402


def test_welch_anova_matches_statsmodels() -> None:
    groups = [
        np.array([2.0, 3.2, 4.1, 5.0, 7.4]),
        np.array([1.1, 1.4, 1.8, 2.2, 2.5, 3.1]),
        np.array([4.2, 5.0, 5.1, 6.8, 7.0, 8.9, 9.2]),
    ]
    statistic, p_value, df_num, df_den, error = welch_anova(groups)
    values = np.concatenate(groups)
    labels = np.concatenate([[idx] * len(group) for idx, group in enumerate(groups)])
    reference = anova_oneway(values, labels, use_var="unequal", welch_correction=True)

    assert error is None
    assert np.isclose(statistic, reference.statistic, rtol=1e-12)
    assert np.isclose(p_value, reference.pvalue, rtol=1e-12)
    assert np.isclose(df_num, reference.df[0], rtol=1e-12)
    assert np.isclose(df_den, reference.df[1], rtol=1e-12)


def test_games_howell_uses_studentized_range() -> None:
    groups = [
        np.array([1.0, 1.3, 2.1, 2.8, 3.0]),
        np.array([2.2, 2.5, 2.7, 3.6, 4.4, 5.0]),
        np.array([4.0, 4.8, 5.1, 6.3, 7.2, 8.0, 9.1]),
    ]
    result = games_howell_posthoc(groups, ["A", "B", "C"])[0]

    first, second = groups[:2]
    variance_term = first.var(ddof=1) / len(first) + second.var(ddof=1) / len(second)
    t_stat = (first.mean() - second.mean()) / np.sqrt(variance_term)
    q_stat = np.sqrt(2.0) * abs(t_stat)
    df = variance_term**2 / (
        (first.var(ddof=1) / len(first)) ** 2 / (len(first) - 1)
        + (second.var(ddof=1) / len(second)) ** 2 / (len(second) - 1)
    )
    p_value = stats.studentized_range.sf(q_stat, len(groups), df)

    assert np.isclose(result["t_stat"], t_stat, rtol=1e-12)
    assert np.isclose(result["q_stat"], q_stat, rtol=1e-12)
    assert np.isclose(result["df"], df, rtol=1e-12)
    assert np.isclose(result["p_value"], p_value, rtol=1e-12)


def test_partial_correlation_uses_n_minus_k_minus_two_df() -> None:
    rng = np.random.default_rng(42)
    n = 30
    covariates = rng.normal(size=(n, 2))
    x = 0.7 * covariates[:, 0] + rng.normal(size=n)
    y = 0.5 * x + 0.8 * covariates[:, 1] + rng.normal(size=n)

    r_value, p_value, n_valid, df = partial_correlation(x, y, covariates)
    expected_df = n - 2 - 2
    expected_t = r_value * np.sqrt(expected_df / (1.0 - r_value**2))
    expected_p = 2.0 * stats.t.sf(abs(expected_t), expected_df)

    assert n_valid == n
    assert df == expected_df
    assert np.isclose(p_value, expected_p, rtol=1e-12)


def test_roi_radii_and_geometric_overlaps() -> None:
    masker_groups, _ = create_sphere_masker(SPEECH_ROIS)
    assert set(masker_groups) == {6, 8}
    assert masker_groups[6]["names"] == ["L_Heschl", "R_Heschl"]
    assert masker_groups[6]["masker"].radius == 6
    assert masker_groups[8]["masker"].radius == 8
    assert masker_groups[6]["masker"].allow_overlap is True
    assert masker_groups[8]["masker"].allow_overlap is True

    overlaps = set()
    items = list(SPEECH_ROIS.items())
    for idx, (name_a, roi_a) in enumerate(items):
        for name_b, roi_b in items[idx + 1 :]:
            if math.dist(roi_a["coords"], roi_b["coords"]) < (
                roi_a["radius"] + roi_b["radius"]
            ):
                overlaps.add((name_a, name_b))

    assert overlaps == {
        ("L_STG_posterior", "L_STS"),
        ("L_MTG", "L_STS"),
        ("L_IFG_triangularis", "L_IFG_opercularis"),
    }
