from __future__ import annotations

import numpy as np
import pandas as pd

from climate_birds.config import GRID_CELL_SIZE_DEGREES


def summarize_occurrences(
    occurrences: pd.DataFrame,
    cell_size_degrees: float = GRID_CELL_SIZE_DEGREES,
) -> pd.DataFrame:
    frame = occurrences.copy()
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "year",
                "observation_records",
                "occupied_cells",
                "centroid_latitude",
                "centroid_longitude",
                "median_latitude",
                "north_edge_latitude",
            ]
        )

    frame["grid_latitude"] = np.floor(frame["decimal_latitude"] / cell_size_degrees) * cell_size_degrees
    frame["grid_longitude"] = np.floor(frame["decimal_longitude"] / cell_size_degrees) * cell_size_degrees
    frame["grid_cell_id"] = (
        frame["grid_latitude"].round(3).astype(str)
        + "_"
        + frame["grid_longitude"].round(3).astype(str)
    )

    unique_cells = frame[["year", "grid_cell_id", "grid_latitude", "grid_longitude"]].drop_duplicates()
    range_metrics = (
        unique_cells.groupby("year", as_index=False)
        .agg(
            occupied_cells=("grid_cell_id", "nunique"),
            centroid_latitude=("grid_latitude", "mean"),
            centroid_longitude=("grid_longitude", "mean"),
            median_latitude=("grid_latitude", "median"),
            north_edge_latitude=("grid_latitude", lambda values: values.quantile(0.95)),
        )
    )

    record_counts = (
        frame.groupby("year", as_index=False)
        .agg(observation_records=("gbif_id", "nunique"))
        .sort_values("year")
    )
    return record_counts.merge(range_metrics, on="year", how="left")


def assemble_species_panel(
    scientific_name: str,
    polish_name: str,
    population_indices: pd.DataFrame,
    population_trends: pd.DataFrame,
    range_metrics: pd.DataFrame,
    climate_index: pd.DataFrame,
) -> pd.DataFrame:
    species_population = population_indices[
        population_indices["scientific_name"] == scientific_name
    ].copy()
    species_trend = population_trends[
        population_trends["scientific_name"] == scientific_name
    ].copy()
    range_features = range_metrics.drop(columns=["scientific_name", "polish_name"], errors="ignore")

    panel = species_population.merge(range_features, on="year", how="left").merge(
        climate_index, on="year", how="left"
    )
    panel["polish_name"] = polish_name

    if not species_trend.empty:
        trend_row = species_trend.iloc[0].to_dict()
        for key, value in trend_row.items():
            if key != "scientific_name":
                panel[key] = value

    panel = panel.sort_values("year").reset_index(drop=True)
    panel["population_change_pct"] = panel["index_pct"].pct_change() * 100
    panel["occupied_cells_change_pct"] = panel["occupied_cells"].pct_change() * 100
    return panel


def calculate_dashboard_metrics(panel: pd.DataFrame) -> dict[str, float | None]:
    if panel.empty:
        return {
            "long_term_trend_pct": None,
            "ten_year_trend_pct": None,
            "latitude_shift_deg": None,
            "occupied_cells_delta": None,
        }

    sorted_panel = panel.sort_values("year")
    early_window = sorted_panel.head(5)
    late_window = sorted_panel.tail(5)

    latitude_shift = late_window["centroid_latitude"].mean() - early_window["centroid_latitude"].mean()
    occupied_cells_delta = late_window["occupied_cells"].mean() - early_window["occupied_cells"].mean()

    long_term = sorted_panel["trend_long_pct"].dropna()
    ten_year = sorted_panel["trend_10y_pct"].dropna()

    return {
        "long_term_trend_pct": float(long_term.iloc[0]) if not long_term.empty else None,
        "ten_year_trend_pct": float(ten_year.iloc[0]) if not ten_year.empty else None,
        "latitude_shift_deg": float(latitude_shift),
        "occupied_cells_delta": float(occupied_cells_delta),
    }
