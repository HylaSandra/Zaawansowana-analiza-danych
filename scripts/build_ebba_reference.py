from __future__ import annotations

import csv
import json
import struct
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"
GRID_OUTPUT_PATH = REFERENCE_DIR / "ebba_grid_50km.geojson"
OCCURRENCE_OUTPUT_PATH = REFERENCE_DIR / "ebba_occurrence_50km.csv"

EBBA_MVT_URL = "https://ebba2.info/maps/data/mvt/"
EBBA_GRID_SQL_URL = "https://trials.carto.com/api/v2/sql"
EBBA_GRID_QUERY = "SELECT eoagrid AS cell_id, the_geom FROM grid_50x50"

SPECIES = {
    "Ciconia ciconia": 22697691,
    "Cuculus canorus": 22683873,
    "Hirundo rustica": 22712252,
}

ATLASES = {
    "ebba1": {
        "atlas_name": "EBBA1",
        "period_label": "EBBA1 (lata 80.)",
        "period_start_year": 1980,
        "period_end_year": 1989,
        "reference_year": 1985,
    },
    "ebba2": {
        "atlas_name": "EBBA2",
        "period_label": "EBBA2 (2013-2017)",
        "period_start_year": 2013,
        "period_end_year": 2017,
        "reference_year": 2015,
    },
}


def read_varint(data: bytes, position: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        byte = data[position]
        position += 1
        result |= (byte & 0x7F) << shift
        if byte < 0x80:
            return result, position
        shift += 7


def iter_protobuf_fields(data: bytes):
    position = 0
    while position < len(data):
        key, position = read_varint(data, position)
        field_number = key >> 3
        wire_type = key & 0x07

        if wire_type == 0:
            value, position = read_varint(data, position)
        elif wire_type == 1:
            value = data[position : position + 8]
            position += 8
        elif wire_type == 2:
            length, position = read_varint(data, position)
            value = data[position : position + length]
            position += length
        elif wire_type == 5:
            value = data[position : position + 4]
            position += 4
        else:
            raise ValueError(f"Unsupported protobuf wire type: {wire_type}")

        yield field_number, wire_type, value


def decode_packed_varints(data: bytes) -> list[int]:
    values: list[int] = []
    position = 0
    while position < len(data):
        value, position = read_varint(data, position)
        values.append(value)
    return values


def decode_mvt_value(data: bytes):
    for field_number, _, value in iter_protobuf_fields(data):
        if field_number == 1:
            return value.decode("utf-8")
        if field_number == 2:
            return struct.unpack("<f", value)[0]
        if field_number == 3:
            return struct.unpack("<d", value)[0]
        if field_number in (4, 5, 7):
            return value
        if field_number == 6:
            return (value >> 1) ^ -(value & 1)
    return None


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "climate-birds-project/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "climate-birds-project/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def load_official_grid() -> dict:
    query = urllib.parse.urlencode({"format": "GeoJSON", "q": EBBA_GRID_QUERY})
    downloaded_grid = fetch_json(f"{EBBA_GRID_SQL_URL}?{query}")
    polygons_by_cell: dict[str, list] = {}
    for feature in downloaded_grid["features"]:
        cell_id = str(feature["properties"]["cell_id"]).strip()
        geometry = feature["geometry"]
        polygons = (
            [geometry["coordinates"]]
            if geometry["type"] == "Polygon"
            else geometry["coordinates"]
        )
        polygons_by_cell.setdefault(cell_id, []).extend(polygons)

    features = [
        {
            "type": "Feature",
            "id": cell_id,
            "properties": {
                "cell_id": cell_id,
                "source": "Official EBBA 50-km grid",
                "source_url": "https://mapviewer.ebba2.info/",
            },
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": polygons,
            },
        }
        for cell_id, polygons in sorted(polygons_by_cell.items())
    ]
    grid = {"type": "FeatureCollection", "features": features}
    grid["name"] = "Official EBBA 50-km grid"
    grid["metadata"] = {
        "source": "European Breeding Bird Atlas map service",
        "source_url": "https://mapviewer.ebba2.info/",
        "cell_count": len(features),
    }
    return grid


def decode_occurrence_cell_ids(data: bytes) -> set[str]:
    cell_ids: set[str] = set()

    for field_number, _, layer_data in iter_protobuf_fields(data):
        if field_number != 3:
            continue

        keys: list[str] = []
        values: list[object] = []
        features: list[bytes] = []

        for layer_field, _, value in iter_protobuf_fields(layer_data):
            if layer_field == 2:
                features.append(value)
            elif layer_field == 3:
                keys.append(value.decode("utf-8"))
            elif layer_field == 4:
                values.append(decode_mvt_value(value))

        for feature_data in features:
            tags: list[int] = []
            for feature_field, _, value in iter_protobuf_fields(feature_data):
                if feature_field == 2:
                    tags = decode_packed_varints(value)

            properties = {
                keys[tags[index]]: values[tags[index + 1]]
                for index in range(0, len(tags), 2)
            }
            cell_id = str(properties.get("cellcode", "")).strip()
            if cell_id:
                cell_ids.add(cell_id)

    return cell_ids


def load_occurrence_cell_ids(atlas_code: str, birdlife_id: int) -> set[str]:
    query = urllib.parse.urlencode(
        {
            "tile": "0/0/0",
            "map_type": "occurrence",
            "map_source": atlas_code,
            "code": birdlife_id,
        }
    )
    return decode_occurrence_cell_ids(fetch_bytes(f"{EBBA_MVT_URL}?{query}"))


def build_occurrence_rows(grid_cell_ids: set[str]) -> list[dict]:
    rows: list[dict] = []

    for scientific_name, birdlife_id in SPECIES.items():
        for atlas_code, atlas in ATLASES.items():
            occurrence_cell_ids = load_occurrence_cell_ids(atlas_code, birdlife_id)
            missing_cells = occurrence_cell_ids - grid_cell_ids
            if missing_cells:
                raise ValueError(
                    f"{scientific_name} / {atlas_code}: grid is missing "
                    f"{len(missing_cells)} occurrence cells"
                )

            print(f"{scientific_name} / {atlas_code}: {len(occurrence_cell_ids)} cells")
            for cell_id in sorted(occurrence_cell_ids):
                rows.append(
                    {
                        "scientific_name": scientific_name,
                        "birdlife_id": birdlife_id,
                        "cell_id": cell_id,
                        "atlas_code": atlas_code,
                        **atlas,
                        "source": "European Breeding Bird Atlas official occurrence map",
                        "source_url": (
                            "https://ebba2.info/maps/species/"
                            f"{scientific_name.replace(' ', '-')}/{atlas_code}/occurrence/"
                        ),
                    }
                )

    return rows


def main() -> None:
    grid = load_official_grid()
    grid_cell_ids = {
        str(feature["properties"]["cell_id"]).strip()
        for feature in grid["features"]
    }
    occurrence_rows = build_occurrence_rows(grid_cell_ids)

    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    GRID_OUTPUT_PATH.write_text(
        json.dumps(grid, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    with OCCURRENCE_OUTPUT_PATH.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(occurrence_rows[0]))
        writer.writeheader()
        writer.writerows(occurrence_rows)

    print(f"Saved {len(grid_cell_ids)} grid cells to {GRID_OUTPUT_PATH}")
    print(f"Saved {len(occurrence_rows)} occurrence records to {OCCURRENCE_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
