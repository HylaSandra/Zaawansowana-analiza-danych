from __future__ import annotations

from pathlib import Path
import time
from typing import Iterable
import warnings

import pandas as pd
import requests

from climate_birds.config import BREEDING_MONTHS, EUROPE_WKT, GBIF_OCCURRENCE_API_URL

PAGE_SIZE = 300
MAX_RECORDS_PER_YEAR = 5000
MIN_PAGE_SIZE = 75
MAX_RETRIES = 5


def _build_params(
    scientific_name: str,
    year: int,
    months: Iterable[int],
    offset: int,
    page_size: int,
) -> list[tuple[str, str]]:
    params: list[tuple[str, str]] = [
        ("scientificName", scientific_name),
        ("geometry", EUROPE_WKT),
        ("year", str(year)),
        ("limit", str(page_size)),
        ("offset", str(offset)),
        ("occurrenceStatus", "PRESENT"),
        ("hasCoordinate", "true"),
        ("hasGeospatialIssue", "false"),
    ]
    params.extend(("month", str(month)) for month in months)
    return params


def _normalize_occurrence_records(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(
            columns=[
                "gbif_id",
                "scientific_name",
                "decimal_latitude",
                "decimal_longitude",
                "country_code",
                "year",
                "month",
                "basis_of_record",
                "event_date",
            ]
        )

    frame = pd.json_normalize(records)
    frame = frame.rename(
        columns={
            "gbifID": "gbif_id",
            "scientificName": "scientific_name",
            "decimalLatitude": "decimal_latitude",
            "decimalLongitude": "decimal_longitude",
            "countryCode": "country_code",
            "basisOfRecord": "basis_of_record",
            "eventDate": "event_date",
        }
    )

    expected_columns = [
        "gbif_id",
        "scientific_name",
        "decimal_latitude",
        "decimal_longitude",
        "country_code",
        "year",
        "month",
        "basis_of_record",
        "event_date",
    ]
    for column in expected_columns:
        if column not in frame:
            frame[column] = pd.NA

    frame = frame[expected_columns].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["month"] = pd.to_numeric(frame["month"], errors="coerce")
    frame["decimal_latitude"] = pd.to_numeric(frame["decimal_latitude"], errors="coerce")
    frame["decimal_longitude"] = pd.to_numeric(frame["decimal_longitude"], errors="coerce")

    accepted_basis = {"HUMAN_OBSERVATION", "OBSERVATION", "MACHINE_OBSERVATION"}
    frame = frame[frame["basis_of_record"].fillna("").isin(accepted_basis)].copy()
    frame = frame.dropna(subset=["year", "decimal_latitude", "decimal_longitude"])
    return frame.reset_index(drop=True)


def load_occurrences(source: Path) -> pd.DataFrame:
    frame = pd.read_csv(source)
    for column in ("year", "month", "decimal_latitude", "decimal_longitude"):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def _retry_wait_seconds(response: requests.Response | None, attempt: int) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(float(retry_after), 1.0)
            except ValueError:
                pass
    return min(45.0, 2.0**attempt)


def _fetch_page_payload(
    http: requests.Session,
    scientific_name: str,
    year: int,
    months: Iterable[int],
    offset: int,
    page_size: int,
) -> dict:
    headers = {"User-Agent": "climate-birds-project/0.1"}
    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES):
        response: requests.Response | None = None
        try:
            response = http.get(
                GBIF_OCCURRENCE_API_URL,
                params=_build_params(scientific_name, year, months, offset, page_size),
                headers=headers,
                timeout=120,
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as error:
            last_error = error
            status_code = error.response.status_code if error.response is not None else None
            if status_code in {429, 500, 502, 503, 504}:
                if attempt == MAX_RETRIES - 1:
                    break
                time.sleep(_retry_wait_seconds(error.response, attempt))
                continue
            raise
        except requests.RequestException as error:
            last_error = error
            if attempt == MAX_RETRIES - 1:
                break
            time.sleep(2.0**attempt)

    if last_error is not None:
        raise last_error
    raise RuntimeError("GBIF request failed without a captured exception.")


def fetch_occurrences(
    scientific_name: str,
    years: Iterable[int],
    months: Iterable[int] = BREEDING_MONTHS,
    page_size: int = PAGE_SIZE,
    max_records_per_year: int = MAX_RECORDS_PER_YEAR,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    http = session or requests.Session()
    yearly_frames: list[pd.DataFrame] = []

    for year in years:
        offset = 0
        current_page_size = page_size
        year_records: list[dict] = []

        while offset < max_records_per_year:
            try:
                payload = _fetch_page_payload(
                    http=http,
                    scientific_name=scientific_name,
                    year=year,
                    months=months,
                    offset=offset,
                    page_size=current_page_size,
                )
            except Exception:
                if current_page_size > MIN_PAGE_SIZE:
                    current_page_size = max(MIN_PAGE_SIZE, current_page_size // 2)
                    continue

                warnings.warn(
                    (
                        f"GBIF returned repeated errors for {scientific_name} in {year} "
                        f"at offset {offset}. Using partial year data collected so far."
                    ),
                    stacklevel=2,
                )
                break

            results = payload.get("results", [])
            year_records.extend(results)

            end_of_records = payload.get("endOfRecords", True)
            if end_of_records or len(results) < current_page_size:
                break

            offset += current_page_size

        yearly_frames.append(_normalize_occurrence_records(year_records))

    if not yearly_frames:
        return _normalize_occurrence_records([])

    combined = pd.concat(yearly_frames, ignore_index=True)
    combined["scientific_name"] = scientific_name
    return combined.sort_values(["year", "month", "gbif_id"]).reset_index(drop=True)


def save_occurrences(frame: pd.DataFrame, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False)
    return destination
