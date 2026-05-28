from __future__ import annotations

from pathlib import Path
import time

import pandas as pd
import requests

from climate_birds.config import (
    BREEDING_MONTHS,
    CLIMATE_BASELINE_YEARS,
    EUROPE_CLIMATE_POINTS,
    OPEN_METEO_ARCHIVE_API_URL,
)

OPEN_METEO_DAILY_VARIABLES = "temperature_2m_mean,precipitation_sum"
OPEN_METEO_MODEL = "era5"
MAX_RETRIES = 5


def _parse_retry_after_seconds(raw_value: str | None, attempt: int) -> float:
    if raw_value:
        try:
            return max(float(raw_value), 1.0)
        except ValueError:
            pass
    return min(60.0, 2.0**attempt)


def _open_meteo_get(
    params: dict[str, str],
    session: requests.Session | None = None,
) -> requests.Response:
    http = session or requests.Session()
    headers = {"User-Agent": "climate-birds-project/0.1"}

    for attempt in range(MAX_RETRIES):
        response = http.get(
            OPEN_METEO_ARCHIVE_API_URL,
            params=params,
            headers=headers,
            timeout=120,
        )

        if response.ok:
            return response

        if response.status_code == 429 or 500 <= response.status_code < 600:
            if attempt == MAX_RETRIES - 1:
                response.raise_for_status()
            wait_seconds = _parse_retry_after_seconds(response.headers.get("Retry-After"), attempt)
            time.sleep(wait_seconds)
            continue

        response.raise_for_status()

    raise RuntimeError("Open-Meteo request failed after retries.")


def _normalize_daily_climate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce")
    normalized["temperature_2m_mean"] = pd.to_numeric(normalized["temperature_2m_mean"], errors="coerce")
    normalized["precipitation_sum"] = pd.to_numeric(normalized["precipitation_sum"], errors="coerce")
    normalized["latitude"] = pd.to_numeric(normalized["latitude"], errors="coerce")
    normalized["longitude"] = pd.to_numeric(normalized["longitude"], errors="coerce")
    normalized = normalized.dropna(subset=["date"]).reset_index(drop=True)
    normalized["year"] = normalized["date"].dt.year
    normalized["month"] = normalized["date"].dt.month
    return normalized


def fetch_locations_daily_weather(
    locations: tuple[dict[str, float | str], ...] = EUROPE_CLIMATE_POINTS,
    start_date: str = "1980-01-01",
    end_date: str = "2024-12-31",
    session: requests.Session | None = None,
) -> pd.DataFrame:
    params = {
        "latitude": ",".join(str(point["latitude"]) for point in locations),
        "longitude": ",".join(str(point["longitude"]) for point in locations),
        "start_date": start_date,
        "end_date": end_date,
        "daily": OPEN_METEO_DAILY_VARIABLES,
        "timezone": "UTC",
        "models": OPEN_METEO_MODEL,
    }
    response = _open_meteo_get(params=params, session=session)
    payload = response.json()

    response_items = payload if isinstance(payload, list) else [payload]
    frames: list[pd.DataFrame] = []

    for index, item in enumerate(response_items):
        daily = item.get("daily", {})
        source_point = locations[index]
        frame = pd.DataFrame(
            {
                "date": daily.get("time", []),
                "temperature_2m_mean": daily.get("temperature_2m_mean", []),
                "precipitation_sum": daily.get("precipitation_sum", []),
            }
        )
        frame["location"] = str(source_point["location"])
        frame["latitude"] = item.get("latitude", source_point["latitude"])
        frame["longitude"] = item.get("longitude", source_point["longitude"])
        frames.append(frame)

    if not frames:
        return pd.DataFrame(
            columns=[
                "date",
                "temperature_2m_mean",
                "precipitation_sum",
                "location",
                "latitude",
                "longitude",
                "year",
                "month",
            ]
        )

    return _normalize_daily_climate_frame(pd.concat(frames, ignore_index=True))


def build_europe_climate_index(
    raw_output_path: Path | None = None,
    session: requests.Session | None = None,
    use_cache: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if raw_output_path is not None and use_cache and raw_output_path.exists():
        daily_frame = pd.read_csv(raw_output_path)
        daily_frame = _normalize_daily_climate_frame(daily_frame)
    else:
        daily_frame = fetch_locations_daily_weather(session=session)
        if raw_output_path is not None:
            raw_output_path.parent.mkdir(parents=True, exist_ok=True)
            daily_frame.to_csv(raw_output_path, index=False)

    annual_frame = (
        daily_frame.groupby(["location", "year"], as_index=False)
        .agg(
            annual_mean_temp_c=("temperature_2m_mean", "mean"),
            annual_precip_mm=("precipitation_sum", "sum"),
            breeding_mean_temp_c=(
                "temperature_2m_mean",
                lambda values: values[
                    daily_frame.loc[values.index, "month"].isin(BREEDING_MONTHS)
                ].mean(),
            ),
            breeding_precip_mm=(
                "precipitation_sum",
                lambda values: values[
                    daily_frame.loc[values.index, "month"].isin(BREEDING_MONTHS)
                ].sum(),
            ),
        )
    )

    europe_index = (
        annual_frame.groupby("year", as_index=False)
        .agg(
            annual_mean_temp_c=("annual_mean_temp_c", "mean"),
            annual_precip_mm=("annual_precip_mm", "mean"),
            breeding_mean_temp_c=("breeding_mean_temp_c", "mean"),
            breeding_precip_mm=("breeding_precip_mm", "mean"),
        )
        .sort_values("year")
        .reset_index(drop=True)
    )

    baseline_start, baseline_end = CLIMATE_BASELINE_YEARS
    baseline_slice = europe_index["year"].between(baseline_start, baseline_end)

    annual_baseline = europe_index.loc[baseline_slice, "annual_mean_temp_c"].mean()
    breeding_baseline = europe_index.loc[baseline_slice, "breeding_mean_temp_c"].mean()

    europe_index["temperature_anomaly_c"] = europe_index["annual_mean_temp_c"] - annual_baseline
    europe_index["breeding_temperature_anomaly_c"] = (
        europe_index["breeding_mean_temp_c"] - breeding_baseline
    )
    return daily_frame, europe_index
