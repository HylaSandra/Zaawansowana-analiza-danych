from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

PECBMS_EXCEL_URL = "https://pecbms.info/wp-content/uploads/2025/12/europe-indicesandtrends-till2024.xlsx"
PECBMS_LOCAL_PATH = RAW_DIR / "pecbms" / "europe_indices_and_trends_2024.xlsx"
GBIF_OCCURRENCE_API_URL = "https://api.gbif.org/v1/occurrence/search"
OPEN_METEO_ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"

BREEDING_MONTHS = (4, 5, 6, 7)
CLIMATE_BASELINE_YEARS = (1991, 2020)
GRID_CELL_SIZE_DEGREES = 1.0
EUROPE_WKT = "POLYGON((-25 34,45 34,45 72,-25 72,-25 34))"


@dataclass(frozen=True)
class SpeciesConfig:
    slug: str
    scientific_name: str
    polish_name: str
    bird_type: str
    habitat_story: str
    presentation_note: str
    image_url: str
    image_credit: str
    image_source_url: str


SELECTED_SPECIES: dict[str, SpeciesConfig] = {
    "ciconia_ciconia": SpeciesConfig(
        slug="ciconia_ciconia",
        scientific_name="Ciconia ciconia",
        polish_name="Bocian biały",
        bird_type="duży ptak mokradeł i krajobrazu rolniczego",
        habitat_story="gatunek dobrze rozpoznawalny, związany ze zmianami migracji i użytkowania krajobrazu rolniczego",
        presentation_note="Dobry przykład gatunku, który w Europie długoterminowo odbudował populację, ale nadal reaguje na zmiany siedlisk, susze i warunki migracji.",
        image_url="https://commons.wikimedia.org/wiki/Special:Redirect/file/White_Stork_Wei%C3%9Fstorch_Ciconia_ciconia.jpg",
        image_credit="Richard Bartz, Wikimedia Commons, CC BY-SA 2.5",
        image_source_url="https://commons.wikimedia.org/wiki/File:White_Stork_Wei%C3%9Fstorch_Ciconia_ciconia.jpg",
    ),
    "hirundo_rustica": SpeciesConfig(
        slug="hirundo_rustica",
        scientific_name="Hirundo rustica",
        polish_name="Jaskółka dymówka",
        bird_type="mały migrant owadożerny",
        habitat_story="migracyjny gatunek krajobrazu rolniczego, wrażliwy na zmiany sezonowe i dostępność pokarmu",
        presentation_note="Dobrze pokazuje ryzyko związane z ociepleniem, intensyfikacją rolnictwa i zmianami dostępności owadów w sezonie lęgowym.",
        image_url="https://commons.wikimedia.org/wiki/Special:Redirect/file/Barn_swallow_%28Hirundo_rustica_rustica%29.jpg",
        image_credit="Charles J. Sharp, Wikimedia Commons, CC BY-SA 4.0",
        image_source_url="https://commons.wikimedia.org/wiki/File:Barn_swallow_%28Hirundo_rustica_rustica%29.jpg",
    ),
    "cuculus_canorus": SpeciesConfig(
        slug="cuculus_canorus",
        scientific_name="Cuculus canorus",
        polish_name="Kukułka",
        bird_type="migrant i pasożyt lęgowy",
        habitat_story="gatunek migracyjny, często opisywany w kontekście niedopasowania fenologicznego",
        presentation_note="Ciekawy kontrast, bo zmiany klimatyczne mogą rozregulować synchronizację przylotu kukułki, aktywności gospodarzy i dostępności pokarmu.",
        image_url="https://commons.wikimedia.org/wiki/Special:Redirect/file/Common_cuckoo_%28Cuculus_canorus%29_image.jpg",
        image_credit="Wikimedia Commons, plik Common cuckoo (Cuculus canorus) image.jpg",
        image_source_url="https://commons.wikimedia.org/wiki/File:Common_cuckoo_%28Cuculus_canorus%29_image.jpg",
    ),
}

EUROPE_CLIMATE_POINTS = (
    {"location": "Lisbon", "latitude": 38.7223, "longitude": -9.1393},
    {"location": "Madrid", "latitude": 40.4168, "longitude": -3.7038},
    {"location": "Paris", "latitude": 48.8566, "longitude": 2.3522},
    {"location": "Rome", "latitude": 41.9028, "longitude": 12.4964},
    {"location": "Vienna", "latitude": 48.2082, "longitude": 16.3738},
    {"location": "Warsaw", "latitude": 52.2297, "longitude": 21.0122},
    {"location": "Bucharest", "latitude": 44.4268, "longitude": 26.1025},
    {"location": "Stockholm", "latitude": 59.3293, "longitude": 18.0686},
    {"location": "Helsinki", "latitude": 60.1699, "longitude": 24.9384},
    {"location": "Dublin", "latitude": 53.3498, "longitude": -6.2603},
    {"location": "Athens", "latitude": 37.9838, "longitude": 23.7275},
)


def ensure_data_directories() -> None:
    for path in (
        RAW_DIR / "pecbms",
        RAW_DIR / "gbif",
        RAW_DIR / "climate",
        PROCESSED_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
