from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller


def descriptive_statistics(frame: pd.DataFrame, value_column: str) -> dict[str, float]:
    series = frame[value_column].dropna()
    if series.empty:
        return {}

    return {
        "count": float(series.count()),
        "mean": float(series.mean()),
        "median": float(series.median()),
        "std": float(series.std(ddof=1)),
        "min": float(series.min()),
        "max": float(series.max()),
    }


def correlation_tests(frame: pd.DataFrame, x_column: str, y_column: str) -> dict[str, float | None]:
    sample = frame[[x_column, y_column]].dropna()
    if len(sample) < 3:
        return {
            "pearson_r": None,
            "pearson_p": None,
            "spearman_rho": None,
            "spearman_p": None,
        }

    pearson_r, pearson_p = stats.pearsonr(sample[x_column], sample[y_column])
    spearman_rho, spearman_p = stats.spearmanr(sample[x_column], sample[y_column])
    return {
        "pearson_r": float(pearson_r),
        "pearson_p": float(pearson_p),
        "spearman_rho": float(spearman_rho),
        "spearman_p": float(spearman_p),
    }


def linear_trend_test(frame: pd.DataFrame, value_column: str, time_column: str = "year") -> dict[str, float | None]:
    sample = frame[[time_column, value_column]].dropna()
    if len(sample) < 3:
        return {"slope": None, "intercept": None, "r_value": None, "p_value": None}

    result = stats.linregress(sample[time_column], sample[value_column])
    return {
        "slope": float(result.slope),
        "intercept": float(result.intercept),
        "r_value": float(result.rvalue),
        "p_value": float(result.pvalue),
    }


def period_comparison(
    frame: pd.DataFrame,
    value_column: str,
    split_year: int = 2002,
    time_column: str = "year",
) -> dict[str, float | None]:
    sample = frame[[time_column, value_column]].dropna()
    early = sample[sample[time_column] <= split_year][value_column]
    late = sample[sample[time_column] > split_year][value_column]

    if len(early) < 3 or len(late) < 3:
        return {"t_stat": None, "t_p_value": None, "mann_whitney_u": None, "mann_whitney_p": None}

    t_stat, t_p_value = stats.ttest_ind(early, late, equal_var=False, nan_policy="omit")
    u_stat, u_p_value = stats.mannwhitneyu(early, late, alternative="two-sided")
    return {
        "t_stat": float(t_stat),
        "t_p_value": float(t_p_value),
        "mann_whitney_u": float(u_stat),
        "mann_whitney_p": float(u_p_value),
    }


def stationarity_test(frame: pd.DataFrame, value_column: str) -> dict[str, float | None]:
    series = frame[value_column].dropna()
    if len(series) < 8:
        return {"adf_statistic": None, "adf_p_value": None}

    adf_statistic, p_value, *_ = adfuller(series)
    return {"adf_statistic": float(adf_statistic), "adf_p_value": float(p_value)}


def safe_shapiro(frame: pd.DataFrame, value_column: str) -> dict[str, float | None]:
    series = frame[value_column].dropna()
    if len(series) < 3 or len(series) > 5000:
        return {"shapiro_w": None, "shapiro_p": None}

    statistic, p_value = stats.shapiro(series.to_numpy(dtype=np.float64))
    return {"shapiro_w": float(statistic), "shapiro_p": float(p_value)}
