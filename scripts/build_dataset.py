from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from climate_birds.config import PECBMS_LOCAL_PATH, PROCESSED_DIR, RAW_DIR, SELECTED_SPECIES, ensure_data_directories
from climate_birds.data_sources.climate import build_europe_climate_index
from climate_birds.data_sources.gbif import fetch_occurrences, load_occurrences, save_occurrences
from climate_birds.data_sources.pecbms import download_pecbms_excel, load_population_indices, load_population_trends
from climate_birds.processing import assemble_species_panel, summarize_occurrences

MAP_POINT_COLUMNS = [
    "gbif_id",
    "decimal_latitude",
    "decimal_longitude",
    "country_code",
    "year",
    "month",
    "basis_of_record",
]


def build_map_points(occurrences: pd.DataFrame, scientific_name: str) -> pd.DataFrame:
    if occurrences.empty:
        return pd.DataFrame(columns=["scientific_name", *MAP_POINT_COLUMNS])

    frame = occurrences.copy()
    for column in MAP_POINT_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA

    for column in ("year", "month", "decimal_latitude", "decimal_longitude"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.dropna(subset=["year", "decimal_latitude", "decimal_longitude"]).copy()
    if frame.empty:
        return pd.DataFrame(columns=["scientific_name", *MAP_POINT_COLUMNS])

    frame["year"] = frame["year"].astype(int)
    map_points = frame.sort_values("year")[MAP_POINT_COLUMNS].copy()
    map_points.insert(0, "scientific_name", scientific_name)
    return map_points


def main() -> None:
    ensure_data_directories()
    species_names = [species.scientific_name for species in SELECTED_SPECIES.values()]

    if not PECBMS_LOCAL_PATH.exists():
        download_pecbms_excel()

    population_indices = load_population_indices(species_names=species_names)
    population_trends = load_population_trends(species_names=species_names)

    climate_daily, climate_index = build_europe_climate_index(
        raw_output_path=RAW_DIR / "climate" / "europe_daily_climate.csv"
    )

    population_indices.to_csv(PROCESSED_DIR / "population_indices.csv", index=False)
    population_trends.to_csv(PROCESSED_DIR / "population_trends.csv", index=False)
    climate_daily.to_csv(RAW_DIR / "climate" / "europe_daily_climate.csv", index=False)
    climate_index.to_csv(PROCESSED_DIR / "climate_index.csv", index=False)

    http = requests.Session()
    range_frames: list[pd.DataFrame] = []
    panel_frames: list[pd.DataFrame] = []
    map_point_frames: list[pd.DataFrame] = []

    for species in SELECTED_SPECIES.values():
        occurrence_path = RAW_DIR / "gbif" / f"{species.slug}_occurrences.csv"
        if occurrence_path.exists():
            occurrences = load_occurrences(occurrence_path)
        else:
            occurrences = fetch_occurrences(
                scientific_name=species.scientific_name,
                years=range(1980, 2025),
                session=http,
            )
            save_occurrences(occurrences, occurrence_path)

        range_metrics = summarize_occurrences(occurrences)
        map_point_frames.append(build_map_points(occurrences, species.scientific_name))

        panel = assemble_species_panel(
            scientific_name=species.scientific_name,
            polish_name=species.polish_name,
            population_indices=population_indices,
            population_trends=population_trends,
            range_metrics=range_metrics,
            climate_index=climate_index,
        )
        panel_frames.append(panel)

        range_export = range_metrics.copy()
        range_export["scientific_name"] = species.scientific_name
        range_export["polish_name"] = species.polish_name
        range_frames.append(range_export)

    all_ranges = pd.concat(range_frames, ignore_index=True)
    analysis_panel = pd.concat(panel_frames, ignore_index=True)
    map_points = (
        pd.concat(map_point_frames, ignore_index=True)
        if map_point_frames
        else pd.DataFrame(columns=["scientific_name", *MAP_POINT_COLUMNS])
    )

    all_ranges.to_csv(PROCESSED_DIR / "range_metrics.csv", index=False)
    analysis_panel.to_csv(PROCESSED_DIR / "analysis_panel.csv", index=False)
    map_points.to_csv(PROCESSED_DIR / "occurrence_map_points.csv", index=False)

    print("Saved processed data to:", PROCESSED_DIR)


if __name__ == "__main__":
    main()
