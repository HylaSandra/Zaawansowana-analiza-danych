from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

from climate_birds.config import PECBMS_EXCEL_URL, PECBMS_LOCAL_PATH

INDEX_SHEET = "WebPresentation_Europe_Indices"
TREND_SHEET = "WebPresentation_Europe_Trends"


def download_pecbms_excel(
    url: str = PECBMS_EXCEL_URL,
    destination: Path = PECBMS_LOCAL_PATH,
    force: bool = False,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        return destination

    response = requests.get(url, timeout=120)
    response.raise_for_status()
    destination.write_bytes(response.content)
    return destination


def _snake_case_columns(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = frame.rename(
        columns={
            "EuringCode": "euring_code",
            "PECBMS species name": "scientific_name",
            "Year": "year",
            "Index(%)": "index_pct",
            "Lower CL": "lower_cl",
            "Upper CL": "upper_cl",
            "Index_SE": "index_se",
            "TrendLong": "trend_long_pct",
            "Trend10Years": "trend_10y_pct",
            "StartYear of LongTermSlope": "long_term_start_year",
            "LongTermSlope": "long_term_slope",
            "LongTermSE": "long_term_se",
            "Trend Classification LongTermSlope": "long_term_classification",
            "StartYear of 10Years Slope": "ten_year_start_year",
            "10Years Slope": "ten_year_slope",
            "10Years Slope SE": "ten_year_slope_se",
            "Trend Classification 10Years Slope": "ten_year_classification",
            "Habitat": "habitat",
            "GraphNote": "graph_note",
        }
    )
    renamed.columns = [
        column.strip().lower().replace(" ", "_").replace("-", "_")
        for column in renamed.columns
    ]
    return renamed


def load_population_indices(
    workbook_path: Path = PECBMS_LOCAL_PATH,
    species_names: list[str] | None = None,
) -> pd.DataFrame:
    frame = pd.read_excel(workbook_path, sheet_name=INDEX_SHEET)
    frame = _snake_case_columns(frame)

    if species_names:
        frame = frame[frame["scientific_name"].isin(species_names)].copy()

    numeric_columns = ["euring_code", "year", "index_pct", "lower_cl", "upper_cl", "index_se"]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.sort_values(["scientific_name", "year"]).reset_index(drop=True)
    return frame


def load_population_trends(
    workbook_path: Path = PECBMS_LOCAL_PATH,
    species_names: list[str] | None = None,
) -> pd.DataFrame:
    frame = pd.read_excel(workbook_path, sheet_name=TREND_SHEET)
    frame = _snake_case_columns(frame)

    if species_names:
        frame = frame[frame["scientific_name"].isin(species_names)].copy()

    numeric_columns = [
        "euring_code",
        "trend_long_pct",
        "trend_10y_pct",
        "long_term_start_year",
        "long_term_slope",
        "long_term_se",
        "ten_year_start_year",
        "ten_year_slope",
        "ten_year_slope_se",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    return frame.reset_index(drop=True)
