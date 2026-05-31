from __future__ import annotations

import sys
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from climate_birds.config import DATA_DIR, PROCESSED_DIR, RAW_DIR, SELECTED_SPECIES
from climate_birds.data_sources.gbif import fetch_occurrences
from climate_birds.processing import calculate_dashboard_metrics
from climate_birds.statistics import correlation_tests, linear_trend_test, period_comparison, stationarity_test

st.set_page_config(page_title="Birds and Climate Dashboard", layout="wide")

PRIMARY_BLUE = "#8FD3FF"
SECONDARY_BLUE = "#DDF2FF"
ACCENT_BLUE = "#4FA9E8"
TEXT_BLUE = "#E5E7EB"
GRID_BLUE = "rgba(143, 211, 255, 0.14)"
APP_BG = "#0B0C0F"
SIDEBAR_BG = "#111318"
PANEL_BG = "rgba(22, 24, 30, 0.94)"
CARD_BG = "rgba(27, 30, 37, 0.92)"
PLOT_BG = "rgba(14, 16, 20, 0.98)"
MUTED_TEXT = "#A7B0BA"
SUCCESS_BLUE = "#A8E6FF"

PANEL_NUMERIC_COLUMNS = [
    "year",
    "index_pct",
    "lower_cl",
    "upper_cl",
    "index_se",
    "observation_records",
    "occupied_cells",
    "centroid_latitude",
    "centroid_longitude",
    "median_latitude",
    "north_edge_latitude",
    "annual_mean_temp_c",
    "annual_precip_mm",
    "breeding_mean_temp_c",
    "breeding_precip_mm",
    "temperature_anomaly_c",
    "breeding_temperature_anomaly_c",
    "trend_long_pct",
    "trend_10y_pct",
    "population_change_pct",
    "occupied_cells_change_pct",
]

TREND_NUMERIC_COLUMNS = [
    "trend_long_pct",
    "trend_10y_pct",
    "long_term_start_year",
    "long_term_slope",
    "long_term_se",
    "ten_year_start_year",
    "ten_year_slope",
    "ten_year_slope_se",
]

CHART_OPTIONS = {
    "info": "Informacje o gatunku",
    "population": "Indeks populacji",
    "climate": "Odchylenie temperatury",
    "range": "Obszar obserwacji",
    "map": "Mapa obserwacji",
    "known_range": "Obserwacje vs zasięg",
    "centroid": "Środek zasięgu",
    "correlation": "Temperatura a populacja",
    "summary": "Podsumowanie i wnioski",
}

MAP_POINTS_PATH = PROCESSED_DIR / "occurrence_map_points.csv"
KNOWN_RANGE_CELLS_PATH = DATA_DIR / "reference" / "known_range_cells.csv"
KNOWN_RANGE_MATCH_RADIUS_KM = 36.0
KNOWN_RANGE_CELL_LAT_SPAN = 0.5
KNOWN_RANGE_CELL_LON_SPAN = 0.75
OCCURRENCE_POINT_COLUMNS = [
    "gbif_id",
    "decimal_latitude",
    "decimal_longitude",
    "country_code",
    "year",
    "month",
    "basis_of_record",
]


def inject_custom_styles() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(circle at 18% 8%, rgba(143, 211, 255, 0.10), transparent 28rem),
                linear-gradient(180deg, {APP_BG} 0%, #14161B 54%, #090A0D 100%);
            color: {TEXT_BLUE};
        }}
        header[data-testid="stHeader"] {{
            background: rgba(11, 12, 15, 0.96);
            border-bottom: 1px solid rgba(143, 211, 255, 0.10);
        }}
        div[data-testid="stToolbar"] {{
            display: flex !important;
            visibility: visible !important;
        }}
        div[data-testid="stSidebarCollapsedControl"] {{
            display: flex !important;
            visibility: visible !important;
        }}
        div[data-testid="stToolbar"] button,
        div[data-testid="stSidebarCollapsedControl"] button {{
            background: rgba(24, 27, 33, 0.96) !important;
            color: {SECONDARY_BLUE} !important;
            border: 1px solid rgba(143, 211, 255, 0.62) !important;
            border-radius: 8px !important;
            box-shadow: 0 0.35rem 1rem rgba(79, 169, 232, 0.14) !important;
            opacity: 1 !important;
        }}
        div[data-testid="stToolbar"] button:hover,
        div[data-testid="stSidebarCollapsedControl"] button:hover {{
            background: rgba(44, 50, 60, 0.98) !important;
            border-color: rgba(221, 242, 255, 0.95) !important;
            color: #F7FCFF !important;
        }}
        div[data-testid="stToolbar"] button svg,
        div[data-testid="stSidebarCollapsedControl"] button svg {{
            fill: {SECONDARY_BLUE} !important;
            color: {SECONDARY_BLUE} !important;
        }}
        .stDeployButton {{
            display: none !important;
        }}
        #MainMenu {{
            visibility: hidden;
        }}
        footer {{
            visibility: hidden;
        }}
        div[data-testid="stDecoration"] {{
            background-image: linear-gradient(90deg, transparent, rgba(143, 211, 255, 0.55), transparent);
        }}
        section[data-testid="stSidebar"] {{
            background:
                linear-gradient(180deg, rgba(24, 27, 33, 0.96) 0%, {SIDEBAR_BG} 100%);
            border-right: 1px solid rgba(143, 211, 255, 0.16);
        }}
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {{
            color: {TEXT_BLUE} !important;
        }}
        section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"] p {{
            color: {MUTED_TEXT} !important;
        }}
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color: #F7FCFF !important;
            font-weight: 800 !important;
            text-shadow: 0 0 1.1rem rgba(143, 211, 255, 0.18);
        }}
        section[data-testid="stSidebar"] h1 {{
            font-size: 1.35rem !important;
        }}
        section[data-testid="stSidebar"] h3 {{
            font-size: 1.02rem !important;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {TEXT_BLUE};
            letter-spacing: 0;
        }}
        h1 {{
            font-size: 2.45rem !important;
            line-height: 1.12 !important;
            margin-bottom: 0.55rem !important;
        }}
        div[data-testid="stMainBlockContainer"] {{
            padding-top: 3rem;
        }}
        p, li, label, span {{
            color: {TEXT_BLUE};
        }}
        div.stButton > button {{
            background: rgba(24, 27, 33, 0.92);
            color: {TEXT_BLUE};
            border: 1px solid rgba(143, 211, 255, 0.24);
            border-radius: 8px;
            font-weight: 700;
            min-height: 3rem;
            white-space: normal;
            transition: border-color 160ms ease, background 160ms ease, box-shadow 160ms ease, transform 160ms ease;
        }}
        div.stButton > button:hover {{
            background: rgba(34, 39, 47, 0.96);
            border-color: rgba(143, 211, 255, 0.75);
            color: {SECONDARY_BLUE};
            box-shadow: 0 0 0 0.12rem rgba(143, 211, 255, 0.12), 0 0.8rem 2rem rgba(79, 169, 232, 0.16);
            transform: translateY(-1px);
        }}
        div.stButton > button:focus {{
            border-color: rgba(143, 211, 255, 0.80);
            color: {SECONDARY_BLUE};
            box-shadow: 0 0 0 0.12rem rgba(143, 211, 255, 0.18);
            outline: none;
        }}
        div.stButton > button[kind="primary"] {{
            background: rgba(143, 211, 255, 0.18);
            border-color: rgba(143, 211, 255, 0.82);
            color: #F7FCFF;
            box-shadow: 0 0 0 0.08rem rgba(143, 211, 255, 0.12);
        }}
        button[kind="pillsActive"],
        button[data-testid="stBaseButton-pillsActive"] {{
            background: rgba(143, 211, 255, 0.20) !important;
            border-color: rgba(143, 211, 255, 0.82) !important;
            color: #F7FCFF !important;
            box-shadow: 0 0 0 0.08rem rgba(143, 211, 255, 0.12) !important;
        }}
        button[kind="pills"],
        button[data-testid="stBaseButton-pills"] {{
            background: rgba(24, 27, 33, 0.92) !important;
            border-color: rgba(143, 211, 255, 0.24) !important;
            color: {TEXT_BLUE} !important;
        }}
        button[kind="pills"]:hover,
        button[data-testid="stBaseButton-pills"]:hover {{
            background: rgba(34, 39, 47, 0.96) !important;
            border-color: rgba(143, 211, 255, 0.70) !important;
        }}
        div[role="radiogroup"]:has(button[kind^="pills"]),
        div[role="radiogroup"]:has(button[data-testid^="stBaseButton-pills"]) {{
            display: flex !important;
            flex-wrap: wrap !important;
            justify-content: center !important;
            align-items: stretch !important;
            gap: 0.55rem !important;
        }}
        div[role="radiogroup"] > button[kind^="pills"],
        div[role="radiogroup"] > button[data-testid^="stBaseButton-pills"],
        div[role="radiogroup"] > div:has(button[kind^="pills"]),
        div[role="radiogroup"] > div:has(button[data-testid^="stBaseButton-pills"]),
        div[role="radiogroup"] > label:has(button[kind^="pills"]),
        div[role="radiogroup"] > label:has(button[data-testid^="stBaseButton-pills"]) {{
            flex: 0 1 13.5rem !important;
            max-width: min(13.5rem, 100%) !important;
            min-width: min(9.5rem, 100%) !important;
        }}
        div[role="radiogroup"] > div:has(button[kind^="pills"]) button,
        div[role="radiogroup"] > div:has(button[data-testid^="stBaseButton-pills"]) button,
        div[role="radiogroup"] > label:has(button[kind^="pills"]) button,
        div[role="radiogroup"] > label:has(button[data-testid^="stBaseButton-pills"]) button {{
            width: 100% !important;
        }}
        div[role="radiogroup"] button[kind^="pills"],
        div[role="radiogroup"] button[data-testid^="stBaseButton-pills"] {{
            justify-content: center !important;
            min-height: 2.75rem !important;
            padding: 0.55rem 0.85rem !important;
            text-align: center !important;
            white-space: normal !important;
        }}
        div[role="radiogroup"] button[kind^="pills"] p,
        div[role="radiogroup"] button[data-testid^="stBaseButton-pills"] p {{
            margin: 0 !important;
            max-width: 100% !important;
            overflow-wrap: anywhere !important;
            text-align: center !important;
            white-space: normal !important;
        }}
        div.stButton > button p {{
            color: {TEXT_BLUE} !important;
            font-weight: 700;
            margin: 0;
        }}
        button[aria-pressed="true"],
        button[aria-selected="true"] {{
            background: rgba(143, 211, 255, 0.20) !important;
            border-color: rgba(143, 211, 255, 0.82) !important;
            color: #F7FCFF !important;
            box-shadow: 0 0 0 0.08rem rgba(143, 211, 255, 0.12) !important;
        }}
        button:focus,
        button:focus-visible {{
            outline: none !important;
            border-color: rgba(143, 211, 255, 0.82) !important;
            box-shadow: 0 0 0 0.12rem rgba(143, 211, 255, 0.16) !important;
        }}
        div[data-testid="stForm"] {{
            margin: 0.75rem 0 1rem 0;
            padding: 1rem 1rem 0.9rem 1rem;
            border: 1px solid rgba(143, 211, 255, 0.22);
            border-radius: 8px;
            background: linear-gradient(135deg, rgba(27, 30, 37, 0.94), rgba(14, 16, 20, 0.92));
            box-shadow: 0 1rem 2.3rem rgba(0, 0, 0, 0.14);
        }}
        div[data-testid="stForm"] label p {{
            color: {SECONDARY_BLUE} !important;
            font-weight: 800 !important;
        }}
        div[data-testid="stForm"] div[data-baseweb="select"] > div {{
            background: rgba(19, 22, 27, 0.96) !important;
            border: 1px solid rgba(143, 211, 255, 0.26) !important;
            border-radius: 8px !important;
            color: {TEXT_BLUE} !important;
        }}
        div[data-testid="stForm"] div[data-baseweb="select"] input,
        div[data-testid="stForm"] div[data-baseweb="select"] span {{
            color: {TEXT_BLUE} !important;
        }}
        div[data-testid="stForm"] div[data-baseweb="tag"],
        div[data-testid="stForm"] span[data-baseweb="tag"] {{
            background: rgba(143, 211, 255, 0.16) !important;
            border: 1px solid rgba(143, 211, 255, 0.30) !important;
            border-radius: 6px !important;
            color: {TEXT_BLUE} !important;
        }}
        div[data-testid="stFormSubmitButton"] button {{
            width: 100% !important;
            min-height: 2.85rem !important;
            background: rgba(143, 211, 255, 0.16) !important;
            color: {TEXT_BLUE} !important;
            border: 1px solid rgba(143, 211, 255, 0.72) !important;
            border-radius: 8px !important;
            box-shadow: 0 0 0 0.08rem rgba(143, 211, 255, 0.10) !important;
            font-weight: 800 !important;
        }}
        div[data-testid="stFormSubmitButton"] button:hover {{
            background: rgba(143, 211, 255, 0.24) !important;
            border-color: rgba(221, 242, 255, 0.94) !important;
            transform: translateY(-1px);
        }}
        .comparison-panel {{
            margin-top: 0.85rem;
            padding: 1rem;
            border: 1px solid rgba(143, 211, 255, 0.20);
            border-radius: 8px;
            background: linear-gradient(135deg, rgba(27, 30, 37, 0.94), rgba(14, 16, 20, 0.92));
        }}
        .comparison-kicker {{
            color: {PRIMARY_BLUE};
            font-size: 0.82rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }}
        .comparison-title {{
            color: {SECONDARY_BLUE};
            font-size: 1.22rem;
            font-weight: 850;
            margin-bottom: 0.45rem;
        }}
        .comparison-panel p {{
            color: {TEXT_BLUE};
            margin: 0 0 0.7rem 0;
            line-height: 1.55;
        }}
        .comparison-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin-top: 0.9rem;
        }}
        .comparison-stat {{
            border: 1px solid rgba(143, 211, 255, 0.16);
            border-radius: 8px;
            background: rgba(19, 22, 27, 0.78);
            padding: 0.75rem 0.85rem;
        }}
        .comparison-stat-label {{
            color: {MUTED_TEXT};
            font-size: 0.8rem;
            line-height: 1.25;
        }}
        .comparison-stat-value {{
            color: {SUCCESS_BLUE};
            font-size: 1.5rem;
            font-weight: 800;
            line-height: 1.05;
            margin-top: 0.35rem;
        }}
        div[data-testid="stMetric"] {{
            background: {CARD_BG};
            border: 1px solid rgba(143, 211, 255, 0.20);
            border-radius: 8px;
            padding: 0.8rem;
        }}
        div[data-testid="stMetricValue"], div[data-testid="stMetricDelta"] {{
            color: {SUCCESS_BLUE};
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.8rem 0 1rem 0;
        }}
        .metric-card {{
            background: {CARD_BG};
            border: 1px solid rgba(143, 211, 255, 0.20);
            border-radius: 8px;
            padding: 0.75rem 0.85rem;
            min-height: 5rem;
        }}
        .metric-label {{
            color: {MUTED_TEXT};
            font-size: 0.82rem;
            line-height: 1.25;
            margin-bottom: 0.45rem;
        }}
        .metric-value {{
            color: {SUCCESS_BLUE};
            font-size: 1.65rem;
            line-height: 1;
            font-weight: 750;
        }}
        .selected-species-banner {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin: 1.45rem 0 0.85rem 0;
            padding: 0.9rem 1rem;
            border: 1px solid rgba(143, 211, 255, 0.18);
            border-radius: 8px;
            background: linear-gradient(135deg, rgba(27, 30, 37, 0.94), rgba(14, 16, 20, 0.92));
            box-shadow: 0 1rem 2.5rem rgba(0, 0, 0, 0.16);
        }}
        .selected-thumb {{
            width: 4.25rem;
            height: 4.25rem;
            flex: 0 0 4.25rem;
            border-radius: 8px;
            object-fit: cover;
            border: 1px solid rgba(143, 211, 255, 0.28);
            background: rgba(143, 211, 255, 0.08);
        }}
        .selected-title {{
            color: {SECONDARY_BLUE};
            font-size: 1.55rem;
            font-weight: 800;
            line-height: 1.15;
            margin-bottom: 0.2rem;
        }}
        .selected-meta {{
            color: {MUTED_TEXT};
            font-size: 0.95rem;
            line-height: 1.35;
        }}
        .selected-tag-mini {{
            display: inline-block;
            margin-top: 0.35rem;
            color: {PRIMARY_BLUE};
            font-size: 0.86rem;
        }}
        .species-hero {{
            background: {PANEL_BG};
            border: 1px solid rgba(143, 211, 255, 0.18);
            border-radius: 8px;
            padding: 1.1rem 1.2rem;
            min-height: 100%;
        }}
        .species-name {{
            color: {PRIMARY_BLUE};
            font-size: 1.55rem;
            font-weight: 750;
            line-height: 1.2;
            margin-bottom: 0.25rem;
        }}
        .species-latin {{
            color: {MUTED_TEXT};
            font-style: italic;
            margin-bottom: 0.9rem;
        }}
        .species-tag {{
            display: inline-block;
            background: rgba(143, 211, 255, 0.14);
            border: 1px solid rgba(143, 211, 255, 0.28);
            border-radius: 6px;
            color: {SECONDARY_BLUE};
            padding: 0.25rem 0.65rem;
            font-size: 0.82rem;
            margin-bottom: 0.75rem;
        }}
        .bird-photo {{
            width: 100%;
            aspect-ratio: 4 / 3.35;
            object-fit: cover;
            border-radius: 8px;
            border: 1px solid rgba(143, 211, 255, 0.20);
            background: rgba(143, 211, 255, 0.08);
        }}
        .photo-card {{
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(143, 211, 255, 0.20);
            border-radius: 8px;
            background: rgba(19, 22, 27, 0.95);
            box-shadow: 0 1rem 2.6rem rgba(0, 0, 0, 0.26);
        }}
        .photo-card .bird-photo {{
            border: 0;
            border-radius: 0;
            display: block;
            filter: saturate(1.06) contrast(1.04);
        }}
        .photo-card::after {{
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(180deg, transparent 42%, rgba(11, 12, 15, 0.88) 100%);
            pointer-events: none;
        }}
        .photo-meta {{
            position: absolute;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 1;
            padding: 0.85rem 0.9rem;
        }}
        .photo-label {{
            color: {SECONDARY_BLUE};
            font-size: 0.9rem;
            font-weight: 750;
            margin-bottom: 0.1rem;
        }}
        .photo-caption {{
            color: {MUTED_TEXT};
            font-size: 0.78rem;
            line-height: 1.35;
            margin-top: 0.15rem;
        }}
        .photo-caption a {{
            color: {PRIMARY_BLUE};
        }}
        .insight-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 0.85rem;
        }}
        .insight-card {{
            background: {CARD_BG};
            border: 1px solid rgba(143, 211, 255, 0.20);
            border-radius: 8px;
            padding: 0.9rem 1rem;
            min-height: 8.3rem;
        }}
        .insight-title {{
            color: {PRIMARY_BLUE};
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }}
        .insight-card p {{
            color: {TEXT_BLUE};
            margin: 0;
            line-height: 1.48;
        }}
        .takeaway-panel {{
            margin: 1rem 0 1.2rem 0;
            padding: 1rem 1.1rem;
            border: 1px solid rgba(143, 211, 255, 0.22);
            border-left: 4px solid {PRIMARY_BLUE};
            border-radius: 8px;
            background: linear-gradient(135deg, rgba(27, 30, 37, 0.95), rgba(14, 16, 20, 0.95));
            box-shadow: 0 1rem 2.5rem rgba(0, 0, 0, 0.18);
        }}
        .takeaway-kicker {{
            color: {PRIMARY_BLUE};
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }}
        .takeaway-panel p {{
            margin: 0.25rem 0;
            color: {TEXT_BLUE};
            line-height: 1.48;
        }}
        .takeaway-muted {{
            color: {MUTED_TEXT} !important;
            font-size: 0.9rem;
        }}
        .chart-description {{
            margin: 0.9rem 0 0.7rem 0;
            padding: 0.85rem 1rem;
            border: 1px solid rgba(143, 211, 255, 0.16);
            border-radius: 8px;
            background: rgba(27, 30, 37, 0.78);
        }}
        .chart-description-title {{
            color: {PRIMARY_BLUE};
            font-weight: 800;
            font-size: 0.88rem;
            margin-bottom: 0.3rem;
        }}
        .chart-description p {{
            margin: 0;
            color: {TEXT_BLUE};
            line-height: 1.45;
        }}
        .muted-note {{
            color: {MUTED_TEXT};
            font-size: 0.88rem;
            line-height: 1.45;
        }}
        .dark-table-wrap {{
            overflow-x: auto;
            border: 1px solid rgba(143, 211, 255, 0.16);
            border-radius: 8px;
            background: rgba(14, 16, 20, 0.84);
            box-shadow: inset 0 1px 0 rgba(221, 242, 255, 0.04);
        }}
        table.dark-table {{
            width: 100%;
            border-collapse: collapse;
            color: {TEXT_BLUE};
            font-size: 0.88rem;
        }}
        table.dark-table thead th {{
            position: sticky;
            top: 0;
            background: rgba(27, 30, 37, 0.98);
            color: {PRIMARY_BLUE};
            border-bottom: 1px solid rgba(143, 211, 255, 0.20);
            font-weight: 750;
            text-align: left;
            padding: 0.72rem 0.8rem;
            white-space: nowrap;
        }}
        table.dark-table tbody td {{
            border-bottom: 1px solid rgba(143, 211, 255, 0.09);
            color: {TEXT_BLUE};
            padding: 0.62rem 0.8rem;
            vertical-align: top;
        }}
        table.dark-table tbody tr:nth-child(even) {{
            background: rgba(143, 211, 255, 0.035);
        }}
        table.dark-table tbody tr:hover {{
            background: rgba(79, 169, 232, 0.12);
        }}
        .sidebar-note {{
            margin-top: 1rem;
            padding: 0.9rem;
            border: 1px solid rgba(143, 211, 255, 0.16);
            border-radius: 8px;
            background: rgba(27, 30, 37, 0.72);
            color: {TEXT_BLUE};
            font-size: 0.84rem;
            line-height: 1.45;
        }}
        .sidebar-note strong {{
            color: {PRIMARY_BLUE};
        }}
        div[data-testid="stAlert"] {{
            background: rgba(13, 31, 49, 0.90);
            border: 1px solid rgba(143, 211, 255, 0.24);
            color: {TEXT_BLUE};
        }}
        a {{
            color: {PRIMARY_BLUE};
        }}
        @media (max-width: 900px) {{
            .insight-grid {{
                grid-template-columns: 1fr;
            }}
            .metric-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
            .comparison-grid {{
                grid-template-columns: 1fr;
            }}
            h1 {{
                font-size: 2rem !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_species_background(species) -> None:
    image_url = escape(species.image_url, quote=True)
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                linear-gradient(90deg, rgba(11, 12, 15, 0.98) 0%, rgba(11, 12, 15, 0.94) 42%, rgba(11, 12, 15, 0.88) 100%),
                linear-gradient(180deg, rgba(11, 12, 15, 0.88), rgba(11, 12, 15, 0.98)),
                url("{image_url}") center center / cover fixed !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    panel_path = PROCESSED_DIR / "analysis_panel.csv"
    trends_path = PROCESSED_DIR / "population_trends.csv"
    if not panel_path.exists() or not trends_path.exists():
        return pd.DataFrame(), pd.DataFrame()
    panel = pd.read_csv(panel_path)
    trends = pd.read_csv(trends_path)

    for column in PANEL_NUMERIC_COLUMNS:
        if column in panel.columns:
            panel[column] = pd.to_numeric(panel[column], errors="coerce")

    for column in TREND_NUMERIC_COLUMNS:
        if column in trends.columns:
            trends[column] = pd.to_numeric(trends[column], errors="coerce")

    for frame in (panel, trends):
        if "scientific_name" in frame.columns:
            frame["scientific_name"] = frame["scientific_name"].astype(str).str.strip()

    polish_names = {
        species.scientific_name: species.polish_name
        for species in SELECTED_SPECIES.values()
    }
    for frame in (panel, trends):
        if "scientific_name" in frame.columns:
            frame["polish_name"] = frame["scientific_name"].map(polish_names).fillna(
                frame.get("polish_name", "")
            )

    return panel, trends


def format_metric(value: float | None, suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return "brak danych"
    return f"{value:.2f}".replace(".", ",") + suffix


def format_decimal(value: float | None, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "brak danych"
    return f"{value:.{digits}f}".replace(".", ",")


def format_signed(value: float | None, suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return "brak danych"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}".replace(".", ",") + suffix


def format_p_value(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "brak danych"
    if value < 0.001:
        return "< 0,001"
    return f"{value:.3f}".replace(".", ",")


def format_p_statement(value: float | None) -> str:
    formatted = format_p_value(value)
    if formatted.startswith("<"):
        return f"p {formatted}"
    return f"p = {formatted}"


def selected_species_config(scientific_name: str):
    return next(
        species for species in SELECTED_SPECIES.values() if species.scientific_name == scientific_name
    )


def empty_occurrence_points() -> pd.DataFrame:
    return pd.DataFrame(columns=OCCURRENCE_POINT_COLUMNS)


def normalize_occurrence_points(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return empty_occurrence_points()

    normalized = frame.copy()
    for column in OCCURRENCE_POINT_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = pd.NA

    normalized = normalized[OCCURRENCE_POINT_COLUMNS].copy()
    for column in ("year", "month", "decimal_latitude", "decimal_longitude"):
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    normalized = normalized.dropna(subset=["year", "decimal_latitude", "decimal_longitude"]).copy()
    if normalized.empty:
        return empty_occurrence_points()

    normalized["year"] = normalized["year"].astype(int)
    normalized["country_code"] = normalized["country_code"].fillna("brak danych").astype(str)
    return normalized.sort_values("year").reset_index(drop=True)


def load_raw_occurrence_points(scientific_name: str) -> pd.DataFrame:
    species = selected_species_config(scientific_name)
    occurrence_path = RAW_DIR / "gbif" / f"{species.slug}_occurrences.csv"
    if not occurrence_path.exists():
        return empty_occurrence_points()

    frame = pd.read_csv(occurrence_path, usecols=lambda column: column in OCCURRENCE_POINT_COLUMNS)
    return normalize_occurrence_points(frame)


def load_processed_map_points(scientific_name: str) -> pd.DataFrame:
    if not MAP_POINTS_PATH.exists():
        return empty_occurrence_points()

    columns = set(OCCURRENCE_POINT_COLUMNS) | {"scientific_name", "period_label"}
    frame = pd.read_csv(MAP_POINTS_PATH, usecols=lambda column: column in columns)

    if "scientific_name" in frame.columns:
        frame = frame[frame["scientific_name"].astype(str).str.strip() == scientific_name].copy()

    return normalize_occurrence_points(frame)


def fetch_live_occurrence_points(scientific_name: str, years: list[int]) -> pd.DataFrame:
    if not years:
        return empty_occurrence_points()
    try:
        frame = fetch_occurrences(
            scientific_name=scientific_name,
            years=years,
        )
    except Exception:
        return empty_occurrence_points()

    return normalize_occurrence_points(frame)


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
@st.cache_data(show_spinner=False)
def load_stored_occurrence_points(scientific_name: str) -> pd.DataFrame:
    raw_points = load_raw_occurrence_points(scientific_name)
    if not raw_points.empty:
        return raw_points

    processed_points = load_processed_map_points(scientific_name)
    if not processed_points.empty:
        return processed_points

    return empty_occurrence_points()


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def load_occurrence_points(scientific_name: str, years: tuple[int, ...]) -> pd.DataFrame:
    selected_years = list(years)
    stored_points = load_stored_occurrence_points(scientific_name)
    if not stored_points.empty:
        return filter_occurrences_by_years(stored_points, selected_years)

    return fetch_live_occurrence_points(scientific_name, selected_years)


def filter_occurrences_by_years(points: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    if not years:
        return points.iloc[0:0].copy()
    return points[points["year"].isin(years)].sort_values("year").copy()


def filter_frame_by_years(frame: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    if not years:
        return frame.iloc[0:0].copy()
    return frame[frame["year"].isin(years)].sort_values("year").copy()


def available_years(frame: pd.DataFrame) -> list[int]:
    return sorted(int(year) for year in frame["year"].dropna().unique())


def format_year_selection(years: list[int], all_years: list[int]) -> str:
    if not years:
        return "brak wybranych lat"
    if years == all_years:
        return f"wszystkie lata ({years[0]}-{years[-1]})"
    if len(years) == 1:
        return f"rok {years[0]}"
    if len(years) <= 8:
        return "lata " + ", ".join(str(year) for year in years)
    return f"wybrane lata: {len(years)} roczników ({years[0]}-{years[-1]})"


def empty_known_range_cells() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["scientific_name", "cell_id", "center_latitude", "center_longitude", "source"]
    )


def pick_first_column(frame: pd.DataFrame, candidates: list[str]) -> str | None:
    columns = {column.lower(): column for column in frame.columns}
    for candidate in candidates:
        if candidate.lower() in columns:
            return columns[candidate.lower()]
    return None


@st.cache_data(show_spinner=False)
def load_known_range_cells(scientific_name: str) -> pd.DataFrame:
    if not KNOWN_RANGE_CELLS_PATH.exists():
        return empty_known_range_cells()

    frame = pd.read_csv(KNOWN_RANGE_CELLS_PATH)
    if frame.empty:
        return empty_known_range_cells()

    species_column = pick_first_column(frame, ["scientific_name", "species", "taxon", "sci_name", "binomial"])
    latitude_column = pick_first_column(frame, ["center_latitude", "latitude", "lat", "decimal_latitude"])
    longitude_column = pick_first_column(frame, ["center_longitude", "longitude", "lon", "lng", "decimal_longitude"])
    cell_column = pick_first_column(frame, ["cell_id", "square_id", "square", "utm_square", "grid_cell_id"])
    source_column = pick_first_column(frame, ["source", "data_source"])

    if latitude_column is None or longitude_column is None:
        return empty_known_range_cells()

    normalized = pd.DataFrame(
        {
            "scientific_name": frame[species_column] if species_column else scientific_name,
            "cell_id": frame[cell_column] if cell_column else "",
            "center_latitude": pd.to_numeric(frame[latitude_column], errors="coerce"),
            "center_longitude": pd.to_numeric(frame[longitude_column], errors="coerce"),
            "source": frame[source_column] if source_column else "EBBA2 50-km occurrence",
        }
    )
    normalized["scientific_name"] = normalized["scientific_name"].astype(str).str.strip()
    normalized = normalized[normalized["scientific_name"] == scientific_name].copy()
    normalized = normalized.dropna(subset=["center_latitude", "center_longitude"])
    return normalized.reset_index(drop=True)


def haversine_distance_km(
    latitude: float,
    longitude: float,
    candidate_latitudes: np.ndarray,
    candidate_longitudes: np.ndarray,
) -> np.ndarray:
    earth_radius_km = 6371.0088
    lat1 = np.radians(latitude)
    lon1 = np.radians(longitude)
    lat2 = np.radians(candidate_latitudes)
    lon2 = np.radians(candidate_longitudes)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = np.sin(delta_lat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(delta_lon / 2) ** 2
    return earth_radius_km * 2 * np.arcsin(np.sqrt(a))


def classify_points_against_known_range(
    points: pd.DataFrame,
    known_range_cells: pd.DataFrame,
    radius_km: float = KNOWN_RANGE_MATCH_RADIUS_KM,
) -> pd.DataFrame:
    classified = points.copy()
    classified["known_range_match"] = False
    classified["nearest_known_range_km"] = pd.NA
    classified["nearest_known_range_cell"] = pd.NA

    if classified.empty or known_range_cells.empty:
        return classified

    bin_size = 1.0
    spatial_index: dict[tuple[int, int], list[tuple[float, float, str]]] = {}
    for row in known_range_cells.itertuples(index=False):
        lat_bin = int(np.floor(float(row.center_latitude) / bin_size))
        lon_bin = int(np.floor(float(row.center_longitude) / bin_size))
        spatial_index.setdefault((lat_bin, lon_bin), []).append(
            (float(row.center_latitude), float(row.center_longitude), str(row.cell_id))
        )

    matches: list[bool] = []
    distances: list[float | None] = []
    nearest_cells: list[str | None] = []

    for point in classified.itertuples(index=False):
        latitude = float(point.decimal_latitude)
        longitude = float(point.decimal_longitude)
        lat_bin = int(np.floor(latitude / bin_size))
        lon_bin = int(np.floor(longitude / bin_size))
        candidates: list[tuple[float, float, str]] = []
        for lat_offset in range(-1, 2):
            for lon_offset in range(-2, 3):
                candidates.extend(spatial_index.get((lat_bin + lat_offset, lon_bin + lon_offset), []))

        if not candidates:
            matches.append(False)
            distances.append(None)
            nearest_cells.append(None)
            continue

        candidate_latitudes = np.array([candidate[0] for candidate in candidates], dtype=float)
        candidate_longitudes = np.array([candidate[1] for candidate in candidates], dtype=float)
        candidate_distances = haversine_distance_km(latitude, longitude, candidate_latitudes, candidate_longitudes)
        nearest_index = int(candidate_distances.argmin())
        nearest_distance = float(candidate_distances[nearest_index])
        matches.append(nearest_distance <= radius_km)
        distances.append(nearest_distance)
        nearest_cells.append(candidates[nearest_index][2])

    classified["known_range_match"] = matches
    classified["nearest_known_range_km"] = distances
    classified["nearest_known_range_cell"] = nearest_cells
    return classified


@st.cache_data(show_spinner=False)
def load_known_range_comparison_data(
    scientific_name: str,
    years: tuple[int, ...],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    year_points = load_occurrence_points(scientific_name, years)
    known_range_cells = load_known_range_cells(scientific_name)
    classified_points = classify_points_against_known_range(year_points, known_range_cells)
    return classified_points, known_range_cells


@st.cache_data(show_spinner=False)
def build_known_range_geojson(known_range_cells: pd.DataFrame) -> dict:
    features = []
    lat_half = KNOWN_RANGE_CELL_LAT_SPAN / 2
    lon_half = KNOWN_RANGE_CELL_LON_SPAN / 2

    for row in known_range_cells.itertuples(index=False):
        center_latitude = float(row.center_latitude)
        center_longitude = float(row.center_longitude)
        west = center_longitude - lon_half
        east = center_longitude + lon_half
        south = center_latitude - lat_half
        north = center_latitude + lat_half
        cell_id = str(row.cell_id)
        source = str(row.source)
        features.append(
            {
                "type": "Feature",
                "id": cell_id,
                "properties": {
                    "cell_id": cell_id,
                    "source": source,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [west, south],
                            [east, south],
                            [east, north],
                            [west, north],
                            [west, south],
                        ]
                    ],
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}


def translate_trend_classification(value: str | None) -> str:
    if value is None or pd.isna(value):
        return "brak klasyfikacji"

    translations = {
        "Moderate increase (p<0.01)": "umiarkowany wzrost (p < 0,01)",
        "Moderate increase": "umiarkowany wzrost",
        "Stable": "stabilny",
        "Moderate decline (p<0.01)": "umiarkowany spadek (p < 0,01)",
        "Moderate decline": "umiarkowany spadek",
        "Steep decline": "silny spadek",
        "Uncertain": "trend niepewny",
    }
    return translations.get(str(value), str(value))


def first_last_index_text(frame: pd.DataFrame) -> tuple[str, float | None]:
    first_year = int(frame["year"].min())
    last_year = int(frame["year"].max())
    first_index = frame.loc[frame["year"] == first_year, "index_pct"].dropna()
    last_index = frame.loc[frame["year"] == last_year, "index_pct"].dropna()
    if first_index.empty or last_index.empty:
        return "Brak danych do porównania pierwszego i ostatniego roku.", None

    first_value = float(first_index.iloc[0])
    last_value = float(last_index.iloc[0])
    delta = last_value - first_value
    text = (
        f"Między {first_year} a {last_year} indeks zmienił się z "
        f"{first_value:.1f} do {last_value:.1f}, czyli o {format_signed(delta, ' pkt')}."
    )
    return text, delta


def render_dark_table(frame: pd.DataFrame, max_rows: int | None = None) -> None:
    display_frame = frame.copy()
    if max_rows is not None:
        display_frame = display_frame.head(max_rows)

    for column in display_frame.select_dtypes(include=[np.number]).columns:
        display_frame[column] = display_frame[column].map(
            lambda value: "" if pd.isna(value) else f"{value:.4f}".rstrip("0").rstrip(".").replace(".", ",")
        )

    display_frame = display_frame.fillna("")
    html_table = display_frame.to_html(
        index=False,
        classes="dark-table",
        border=0,
        justify="left",
        escape=True,
    )
    st.markdown(f'<div class="dark-table-wrap">{html_table}</div>', unsafe_allow_html=True)


def build_trend_summary_table(species, species_trend: pd.DataFrame) -> pd.DataFrame:
    if species_trend.empty:
        return pd.DataFrame()

    row = species_trend.iloc[0]
    return pd.DataFrame(
        [
            {
                "Gatunek": species.polish_name,
                "Nazwa łacińska": species.scientific_name,
                "Trend długoterminowy": format_signed(row.get("trend_long_pct"), "%"),
                "Ocena trendu długoterminowego": translate_trend_classification(row.get("long_term_classification")),
                "Trend z ostatnich 10 lat": format_signed(row.get("trend_10y_pct"), "%"),
                "Ocena trendu 10-letniego": translate_trend_classification(row.get("ten_year_classification")),
            }
        ]
    )


def render_metric_grid(metrics: dict[str, float | None]) -> None:
    items = [
        ("Trend długoterminowy", format_metric(metrics["long_term_trend_pct"], "%")),
        ("Trend 10-letni", format_metric(metrics["ten_year_trend_pct"], "%")),
        ("Przesunięcie środka zasięgu", format_metric(metrics["latitude_shift_deg"], "°")),
        ("Zmiana pól siatki", format_metric(metrics["occupied_cells_delta"])),
    ]
    cards = "\n".join(
        f'<div class="metric-card"><div class="metric-label">{escape(label)}</div>'
        f'<div class="metric-value">{escape(value)}</div></div>'
        for label, value in items
    )
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)


def render_selected_species_banner(species) -> None:
    st.markdown(
        f"""
        <div class="selected-species-banner">
            <img class="selected-thumb" src="{escape(species.image_url, quote=True)}" alt="{escape(species.polish_name)}">
            <div>
                <div class="selected-title">{escape(species.polish_name)}</div>
                <div class="selected-meta"><em>{escape(species.scientific_name)}</em></div>
                <div class="selected-tag-mini">{escape(species.bird_type)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_population_figure(frame: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=frame["year"],
            y=frame["upper_cl"],
            mode="lines",
            line={"width": 0, "color": SECONDARY_BLUE},
            showlegend=False,
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=frame["year"],
            y=frame["lower_cl"],
            mode="lines",
            fill="tonexty",
            line={"width": 0, "color": SECONDARY_BLUE},
            fillcolor="rgba(143, 211, 255, 0.35)",
            name="Przedział ufności",
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=frame["year"],
            y=frame["index_pct"],
            mode="lines+markers",
            line={"color": ACCENT_BLUE, "width": 3},
            marker={"color": TEXT_BLUE, "size": 7},
            name="Indeks populacji",
        )
    )
    figure.add_hline(y=100, line_dash="dash", line_color=TEXT_BLUE, opacity=0.5)
    figure.update_layout(
        title="Indeks populacji według Europejskiego Monitoringu Ptaków",
        xaxis_title="Rok",
        yaxis_title="Indeks populacji (100 = poziom odniesienia)",
        template="plotly_dark",
        legend_title="Seria",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BG,
        font={"color": TEXT_BLUE},
        title_font={"color": SECONDARY_BLUE},
    )
    figure.update_xaxes(showgrid=True, gridcolor=GRID_BLUE)
    figure.update_yaxes(showgrid=True, gridcolor=GRID_BLUE)
    return figure


def build_temperature_population_figure(frame: pd.DataFrame) -> go.Figure:
    sample = frame[["breeding_temperature_anomaly_c", "index_pct", "year"]].dropna().copy()
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=sample["year"],
            y=sample["index_pct"],
            mode="lines+markers",
            marker={
                "size": 9,
                "color": sample["breeding_temperature_anomaly_c"],
                "colorscale": [[0, SECONDARY_BLUE], [0.5, PRIMARY_BLUE], [1, ACCENT_BLUE]],
                "line": {"color": TEXT_BLUE, "width": 1},
                "colorbar": {"title": "Odchylenie temperatury [C]", "tickfont": {"color": TEXT_BLUE}},
            },
            line={"color": "rgba(221, 242, 255, 0.48)", "width": 2},
            customdata=sample[["breeding_temperature_anomaly_c"]].to_numpy(),
            name="Indeks populacji",
            hovertemplate=(
                "Rok: %{x}<br>"
                "Indeks populacji: %{y:.2f}<br>"
                "Odchylenie temperatury: %{customdata[0]:.2f} C<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title="Indeks populacji w czasie z informacją o temperaturze sezonu lęgowego",
        xaxis_title="Rok",
        yaxis_title="Indeks populacji (%)",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BG,
        font={"color": TEXT_BLUE},
        title_font={"color": SECONDARY_BLUE},
    )
    figure.update_xaxes(showgrid=True, gridcolor=GRID_BLUE)
    figure.update_yaxes(showgrid=True, gridcolor=GRID_BLUE)
    return figure


def build_climate_figure(frame: pd.DataFrame) -> go.Figure:
    figure = px.line(
        frame,
        x="year",
        y="breeding_temperature_anomaly_c",
        markers=True,
        title="Odchylenie temperatury sezonu lęgowego od średniej",
        labels={"year": "Rok", "breeding_temperature_anomaly_c": "Odchylenie temperatury [C]"},
    )
    figure.update_traces(line={"color": ACCENT_BLUE, "width": 3}, marker={"color": TEXT_BLUE, "size": 7})
    figure.add_hline(y=0, line_dash="dash", line_color=TEXT_BLUE, opacity=0.5)
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BG,
        font={"color": TEXT_BLUE},
        title_font={"color": SECONDARY_BLUE},
    )
    figure.update_xaxes(showgrid=True, gridcolor=GRID_BLUE)
    figure.update_yaxes(showgrid=True, gridcolor=GRID_BLUE)
    return figure


def build_range_figure(frame: pd.DataFrame) -> go.Figure:
    figure = px.line(
        frame,
        x="year",
        y="occupied_cells",
        markers=True,
        title="Obszar obserwacji mierzony liczbą zajętych pól siatki",
        labels={"year": "Rok", "occupied_cells": "Liczba pól siatki"},
    )
    figure.update_traces(line={"color": ACCENT_BLUE, "width": 3}, marker={"color": TEXT_BLUE, "size": 7})
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BG,
        font={"color": TEXT_BLUE},
        title_font={"color": SECONDARY_BLUE},
    )
    figure.update_xaxes(showgrid=True, gridcolor=GRID_BLUE)
    figure.update_yaxes(showgrid=True, gridcolor=GRID_BLUE)
    return figure


def build_centroid_figure(frame: pd.DataFrame) -> go.Figure:
    figure = px.line(
        frame,
        x="year",
        y="centroid_latitude",
        markers=True,
        title="Przesunięcie środka zasięgu obserwacji",
        labels={"year": "Rok", "centroid_latitude": "Szerokość geograficzna"},
    )
    figure.update_traces(line={"color": ACCENT_BLUE, "width": 3}, marker={"color": TEXT_BLUE, "size": 7})
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BG,
        font={"color": TEXT_BLUE},
        title_font={"color": SECONDARY_BLUE},
    )
    figure.update_xaxes(showgrid=True, gridcolor=GRID_BLUE)
    figure.update_yaxes(showgrid=True, gridcolor=GRID_BLUE)
    return figure


def build_observation_map_figure(points: pd.DataFrame, species, years_label: str) -> go.Figure:
    figure = go.Figure()
    if points.empty:
        figure.add_annotation(
            text="Brak punktów obserwacji dla wybranych lat.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"color": TEXT_BLUE, "size": 18},
        )
    else:
        display_points = points.sort_values("year")
        hover_data = display_points[["year", "country_code", "month"]].fillna("").astype(str).to_numpy()
        figure.add_trace(
            go.Scattergeo(
                lon=display_points["decimal_longitude"],
                lat=display_points["decimal_latitude"],
                mode="markers",
                customdata=hover_data,
                marker={
                    "size": 5,
                    "opacity": 0.72,
                    "color": display_points["year"],
                    "colorscale": [[0, SECONDARY_BLUE], [0.55, PRIMARY_BLUE], [1, ACCENT_BLUE]],
                    "line": {"width": 0},
                    "colorbar": {"title": "Rok", "tickfont": {"color": TEXT_BLUE}},
                },
                hovertemplate=(
                    "Rok: %{customdata[0]}<br>"
                    "Kraj: %{customdata[1]}<br>"
                    "Miesiąc: %{customdata[2]}<br>"
                    "Szerokość: %{lat:.2f}<br>"
                    "Długość: %{lon:.2f}<extra></extra>"
                ),
                name="Punkty obserwacji",
            )
        )

    figure.update_geos(
        projection_type="natural earth",
        lataxis_range=[34, 72],
        lonaxis_range=[-25, 45],
        showland=True,
        landcolor="rgba(24, 27, 33, 0.96)",
        showocean=True,
        oceancolor="rgba(11, 12, 15, 0.98)",
        showcountries=True,
        countrycolor="rgba(143, 211, 255, 0.26)",
        coastlinecolor="rgba(221, 242, 255, 0.28)",
        showlakes=True,
        lakecolor="rgba(4, 16, 30, 0.94)",
        bgcolor="rgba(0,0,0,0)",
        showframe=False,
    )
    figure.update_layout(
        title=f"Mapa punktów obserwacji: {species.polish_name}, {years_label}",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BG,
        font={"color": TEXT_BLUE},
        title_font={"color": SECONDARY_BLUE},
        height=620,
        margin={"l": 0, "r": 0, "t": 56, "b": 0},
    )
    return figure


def build_known_range_comparison_figure(
    points: pd.DataFrame,
    known_range_cells: pd.DataFrame,
    species,
    years_label: str,
) -> go.Figure:
    figure = go.Figure()
    has_known_range = not known_range_cells.empty
    range_source = (
        str(known_range_cells["source"].dropna().iloc[0])
        if has_known_range and "source" in known_range_cells.columns and not known_range_cells["source"].dropna().empty
        else "warstwa referencyjna"
    )
    display_frame = points.copy()
    if not display_frame.empty and "known_range_match" not in display_frame.columns:
        display_frame["known_range_match"] = False
    for column in ("nearest_known_range_km", "nearest_known_range_cell"):
        if not display_frame.empty and column not in display_frame.columns:
            display_frame[column] = pd.NA

    if has_known_range:
        known_range_hover = known_range_cells[["cell_id", "source"]].fillna("").astype(str).to_numpy()
        figure.add_trace(
            go.Scattergeo(
                lon=known_range_cells["center_longitude"],
                lat=known_range_cells["center_latitude"],
                mode="markers",
                customdata=known_range_hover,
                marker={
                    "symbol": "square",
                    "size": 9,
                    "opacity": 0.18,
                    "color": PRIMARY_BLUE,
                    "line": {"width": 0.4, "color": "rgba(221, 242, 255, 0.20)"},
                },
                name="Znany zasięg",
                hovertemplate=(
                    "Komórka: %{customdata[0]}<br>"
                    "Źródło: %{customdata[1]}<br>"
                    "Warstwa zasięgu<br>"
                    "Szerokość: %{lat:.2f}<br>"
                    "Długość: %{lon:.2f}<extra></extra>"
                ),
            )
        )

    if not display_frame.empty:
        if has_known_range:
            point_layers = (
                (display_frame[~display_frame["known_range_match"]].copy(), "Poza zasięgiem", "#A7B0BA", 0.72),
                (display_frame[display_frame["known_range_match"]].copy(), "W zasięgu", ACCENT_BLUE, 0.78),
            )
        else:
            point_layers = (
                (display_frame, "Punkty GBIF (brak warstwy zasięgu)", ACCENT_BLUE, 0.72),
            )

        for display_points, name, color, opacity in point_layers:
            if display_points.empty:
                continue
            hover_data = display_points[
                ["year", "country_code", "month", "nearest_known_range_km", "nearest_known_range_cell"]
            ].fillna("").astype(str).to_numpy()
            figure.add_trace(
                go.Scattergeo(
                    lon=display_points["decimal_longitude"],
                    lat=display_points["decimal_latitude"],
                    mode="markers",
                    customdata=hover_data,
                    marker={
                        "size": 4,
                        "opacity": opacity,
                        "color": color,
                        "line": {"width": 0},
                    },
                    hovertemplate=(
                        "Rok: %{customdata[0]}<br>"
                        "Kraj: %{customdata[1]}<br>"
                        "Miesiąc: %{customdata[2]}<br>"
                        "Najbliższa komórka zasięgu: %{customdata[4]}<br>"
                        "Odległość do komórki: %{customdata[3]} km<br>"
                        "Szerokość: %{lat:.2f}<br>"
                        "Długość: %{lon:.2f}<extra></extra>"
                    ),
                    name=name,
                )
            )
    else:
        figure.add_annotation(
            text="Brak punktów GBIF dla wybranych lat.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"color": TEXT_BLUE, "size": 18},
        )

    figure.update_geos(
        projection_type="natural earth",
        lataxis_range=[34, 72],
        lonaxis_range=[-25, 45],
        showland=True,
        landcolor="rgba(24, 27, 33, 0.96)",
        showocean=True,
        oceancolor="rgba(11, 12, 15, 0.98)",
        showcountries=True,
        countrycolor="rgba(143, 211, 255, 0.24)",
        coastlinecolor="rgba(221, 242, 255, 0.26)",
        showlakes=True,
        lakecolor="rgba(14, 16, 20, 0.94)",
        bgcolor="rgba(0,0,0,0)",
        showframe=False,
    )
    figure.update_layout(
        title=f"Obserwacje GBIF vs znany zasięg: {species.polish_name}, {years_label}",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BG,
        font={"color": TEXT_BLUE},
        title_font={"color": SECONDARY_BLUE},
        legend={"orientation": "h", "y": -0.05, "x": 0.5, "xanchor": "center", "yanchor": "top"},
        legend_title="",
        height=620,
        margin={"l": 0, "r": 0, "t": 56, "b": 54},
    )
    return figure


def initialize_state() -> None:
    default_species = next(iter(SELECTED_SPECIES.values())).scientific_name
    st.session_state.setdefault("selected_species", default_species)
    st.session_state.setdefault("selected_chart", "population")


def set_selected_species(scientific_name: str) -> None:
    st.session_state["selected_species"] = scientific_name


def set_selected_chart(chart_key: str) -> None:
    st.session_state["selected_chart"] = chart_key


def render_species_buttons() -> str:
    selected_species = st.session_state["selected_species"]

    for species in SELECTED_SPECIES.values():
        is_selected = selected_species == species.scientific_name
        button_label = f"{species.polish_name} ({species.scientific_name})"
        if st.sidebar.button(
            button_label,
            key=f"species_{species.slug}",
            type="primary" if is_selected else "secondary",
            width="stretch",
        ):
            set_selected_species(species.scientific_name)
            st.rerun()

    return st.session_state["selected_species"]


def render_chart_buttons() -> str:
    st.subheader("Wybierz wykres")
    st.caption("Przyciski zmieniają widok analizy dla aktualnie wybranego gatunku.")
    chart_keys = list(CHART_OPTIONS)
    selected_chart = st.pills(
        "Widok analizy",
        chart_keys,
        default=st.session_state["selected_chart"],
        format_func=lambda key: CHART_OPTIONS[key],
        key="chart_selector",
        label_visibility="collapsed",
        width="stretch",
    )
    if selected_chart is not None:
        st.session_state["selected_chart"] = selected_chart
    return st.session_state["selected_chart"]


def render_year_filter(frame: pd.DataFrame) -> list[int]:
    years = available_years(frame)
    current_years = st.session_state.get("applied_years")
    if current_years is None:
        st.session_state["applied_years"] = years
    else:
        valid_years = [int(year) for year in current_years if int(year) in years]
        if valid_years or not current_years:
            st.session_state["applied_years"] = valid_years
        else:
            st.session_state["applied_years"] = years

    draft_key = "draft_selected_years"
    draft_years = st.session_state.get(draft_key)
    if st.session_state.get("sync_year_filter_draft", False):
        st.session_state["sync_year_filter_draft"] = False
        st.session_state[draft_key] = st.session_state["applied_years"]
    elif draft_years is None:
        st.session_state[draft_key] = st.session_state["applied_years"]
    else:
        st.session_state[draft_key] = [int(year) for year in draft_years if int(year) in years]

    st.caption("Zmień wybór lat, a potem kliknij „Zastosuj lata”. Dzięki temu wykresy nie przeładowują się po każdym kliknięciu.")
    with st.form("year_filter_form"):
        draft_selection = st.multiselect(
            "Lata analizy",
            years,
            key=draft_key,
            placeholder="Wybierz dowolne lata",
        )
        apply_column, all_column = st.columns([1, 1])
        apply_clicked = apply_column.form_submit_button("Zastosuj lata", type="primary")
        all_clicked = all_column.form_submit_button("Wszystkie lata", type="primary")

    if all_clicked:
        st.session_state["applied_years"] = years
        st.session_state["sync_year_filter_draft"] = True
        st.rerun()

    if apply_clicked:
        st.session_state["applied_years"] = sorted(int(year) for year in draft_selection)

    selected_years = sorted(int(year) for year in st.session_state["applied_years"])

    if selected_years:
        st.caption(f"Filtr aktywny: {format_year_selection(selected_years, years)}.")
    else:
        st.warning("Wybierz co najmniej jeden rok i kliknij „Zastosuj lata”, żeby wyświetlić wykres lub mapę.")

    return selected_years


def render_sidebar_glossary() -> None:
    st.sidebar.markdown(
        """
        <div class="sidebar-note">
            <strong>PECBMS</strong> - Europejski Monitoring Ptaków, źródło trendów populacji.<br>
            <strong>GBIF</strong> - globalna baza obserwacji organizmów, tutaj używana do analizy zasięgu.<br>
            <strong>Wartość p</strong> - informacja, czy wynik testu statystycznego jest istotny.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_species_profile(species, species_panel: pd.DataFrame, species_trend: pd.DataFrame) -> None:
    latest_year = int(species_panel["year"].max())
    latest_row = species_panel.sort_values("year").tail(1).iloc[0]
    trend_row = species_trend.iloc[0] if not species_trend.empty else latest_row
    long_term = pd.to_numeric(pd.Series([trend_row.get("trend_long_pct")]), errors="coerce").iloc[0]
    ten_year = pd.to_numeric(pd.Series([trend_row.get("trend_10y_pct")]), errors="coerce").iloc[0]
    long_class = translate_trend_classification(trend_row.get("long_term_classification"))
    ten_class = translate_trend_classification(trend_row.get("ten_year_classification"))

    image_column, story_column, note_column = st.columns([1.05, 1.75, 1.25])
    with image_column:
        st.markdown(
            f"""
            <div class="photo-card">
                <img class="bird-photo" src="{escape(species.image_url)}" alt="{escape(species.polish_name)}">
                <div class="photo-meta">
                    <div class="photo-label">{escape(species.polish_name)}</div>
                    <div class="photo-caption">
                        {escape(species.image_credit)}<br>
                        <a href="{escape(species.image_source_url)}" target="_blank">Źródło zdjęcia</a>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with story_column:
        st.markdown(
            f"""
            <div class="species-hero">
                <div class="species-name">{escape(species.polish_name)}</div>
                <div class="species-latin">{escape(species.scientific_name)}</div>
                <div class="species-tag">{escape(species.bird_type)}</div>
                <p>{escape(species.habitat_story)}.</p>
                <p class="muted-note">{escape(species.presentation_note)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with note_column:
        st.markdown(
            f"""
            <div class="species-hero">
                <div class="insight-title">Szybki kontekst</div>
                <p><strong>Europejski Monitoring Ptaków (PECBMS), trend długoterminowy:</strong> {format_signed(long_term, "%")} ({escape(long_class)}).</p>
                <p><strong>Ostatnie 10 lat:</strong> {format_signed(ten_year, "%")} ({escape(ten_class)}).</p>
                <p><strong>Najnowszy rok w panelu:</strong> {latest_year}, indeks {format_decimal(float(latest_row["index_pct"]), 1)}.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _recent_direction_text(frame: pd.DataFrame, column: str, higher_text: str, lower_text: str) -> str:
    early_mean = frame.head(5)[column].mean()
    late_mean = frame.tail(5)[column].mean()
    if pd.isna(early_mean) or pd.isna(late_mean):
        return "Brak wystarczających danych do porównania początku i końca szeregu."
    if late_mean > early_mean:
        return higher_text
    if late_mean < early_mean:
        return lower_text
    return "Na początku i na końcu szeregu wartości są zbliżone."


def relationship_strength(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "brak wystarczających danych"
    absolute_value = abs(value)
    if absolute_value < 0.2:
        return "bardzo słaby"
    if absolute_value < 0.4:
        return "słaby"
    if absolute_value < 0.6:
        return "umiarkowany"
    if absolute_value < 0.8:
        return "silny"
    return "bardzo silny"


def correlation_story(species, stats: dict[str, float | None]) -> tuple[str, str]:
    pearson = stats["pearson_r"]
    pearson_p = stats["pearson_p"]
    if pearson is None:
        return (
            "Brak wystarczającej liczby obserwacji do zbudowania wiarygodnej interpretacji korelacji.",
            "Wniosek jest niepewny, dlatego ten wynik warto traktować jako miejsce na dalszą analizę.",
        )

    direction = "dodatni" if pearson > 0 else "ujemny"
    strength = relationship_strength(pearson)
    significance = "statystycznie istotny" if pearson_p is not None and pearson_p < 0.05 else "nie jest statystycznie istotny"

    if species.scientific_name == "Ciconia ciconia":
        interpretation = (
            "W cieplejszych sezonach lęgowych indeks populacji bociana był zwykle wyższy. "
            "To daje ciekawy kontrast wobec pozostałych gatunków, ale nie oznacza automatycznie, że sama temperatura zwiększa populację."
        )
        context_line = (
            "Bocian biały pokazuje, że reakcja gatunku na ocieplenie może wyglądać pozytywnie, "
            "ale wynik trzeba zestawić z ochroną gatunku, zmianami rolnictwa i dostępnością siedlisk."
        )
    elif species.scientific_name == "Hirundo rustica":
        interpretation = (
            "Dla jaskółki dymówki cieplejsze sezony lęgowe współwystępowały z niższym indeksem populacji. "
            "Zależność jest słabsza niż u kukułki, ale pasuje do pytania o owady, suszę i zmiany krajobrazu rolniczego."
        )
        context_line = (
            "Jaskółka dymówka jest dobrym przykładem gatunku, u którego cieplejsze lata nie muszą oznaczać lepszych warunków życia."
        )
    else:
        interpretation = (
            "Dla kukułki cieplejsze sezony lęgowe wyraźnie współwystępowały z niższym indeksem populacji. "
            "To jest najmocniejszy sygnał w tej części analizy i dobrze łączy się z hipotezą niedopasowania sezonowego."
        )
        context_line = (
            "Kukułka może być najmocniejszym przykładem ryzyka: jeśli klimat zmienia terminy aktywności gospodarzy i dostępność pokarmu, "
            "gatunek migracyjny może tracić synchronizację z sezonem lęgowym."
        )

    summary = (
        f"Korelacja Pearsona wskazuje na {strength} związek {direction} "
        f"(r = {format_signed(pearson)}, {format_p_statement(pearson_p)}). Wynik jest {significance}. "
        f"{interpretation}"
    )
    return summary, context_line


def render_correlation_takeaway(species, frame: pd.DataFrame) -> None:
    stats = correlation_tests(
        frame,
        x_column="breeding_temperature_anomaly_c",
        y_column="index_pct",
    )
    summary, context_line = correlation_story(species, stats)
    st.markdown(
        f"""
        <div class="takeaway-panel">
            <div class="takeaway-kicker">Najważniejszy wniosek z korelacji</div>
            <p>{escape(summary)}</p>
            <p class="takeaway-muted">{escape(context_line)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_science_context() -> None:
    st.subheader("Kontekst naukowy")
    st.caption(
        "Ta sekcja pomaga porównać wyniki z dashboardu z tym, co pokazuje literatura i raporty europejskie."
    )
    st.markdown(
        """
        **Co jest zgodne z literaturą?**

        - W Europie populacje wielu pospolitych ptaków spadają. Według EEA między 1990 a 2023 r. wspólny indeks 168 gatunków spadł o 15%, a dla ptaków krajobrazu rolniczego o 42%.
        - EEA podaje też, że w europejskim wskaźniku wpływu klimatu na ptaki liczba gatunków reagujących negatywnie na ocieplenie jest około trzy razy większa niż liczba gatunków reagujących pozytywnie.
        - BirdLife wskazuje, że ptaki próbują odpowiadać na ocieplenie przez przesuwanie zasięgów ku wyższym szerokościom i wysokościom lub przez zmianę terminów migracji i lęgów, ale nie zawsze nadążają za tempem zmian.
        - Badanie opublikowane w *Nature Communications* dla 378 europejskich gatunków wykazało średnie przesuwanie centrum zasięgu o około 2,4 km rocznie, ale jednocześnie pokazało, że sam klimat nie wyjaśnia całego wzorca zmian.
        """
    )
    st.markdown(
        """
        **Źródła**

        - [EEA: Common bird index in Europe](https://www.eea.europa.eu/en/analysis/indicators/common-bird-index-in-europe)
        - [EEA: Climate change impact indicator for European birds](https://www.eea.europa.eu/en/analysis/maps-and-charts/climate-change-impact-indicator-for-european-birds)
        - [EBBA2: European Breeding Bird Atlas 2](https://ebba2.info/faq/)
        - [BirdLife DataZone: Climate change](https://datazone.birdlife.org/topics/climate-change)
        - [Nature Communications 2023: Local colonisations and extinctions of European birds are poorly explained by changes in climate suitability](https://www.nature.com/articles/s41467-023-39093-1)
        """
    )


def render_chart_description(chart_key: str) -> None:
    descriptions = {
        "population": (
            "Co pokazuje ten wykres?",
            "Linia przedstawia indeks populacji w kolejnych latach. Wartość 100 oznacza poziom odniesienia, "
            "więc wartości powyżej 100 sugerują wzrost, a wartości poniżej 100 spadek względem początku szeregu. "
            "Jasnoniebieskie pole pokazuje niepewność oszacowania."
        ),
        "climate": (
            "Co pokazuje ten wykres?",
            "Wykres pokazuje, czy sezon lęgowy był cieplejszy lub chłodniejszy od średniej z lat 1991-2020. "
            "Wartości dodatnie oznaczają cieplejsze lata, a ujemne lata chłodniejsze od normy."
        ),
        "range": (
            "Co pokazuje ten wykres?",
            "Wykres pokazuje, w ilu polach siatki 1° x 1° pojawiły się obserwacje gatunku z bazy GBIF. "
            "To przybliżenie zasięgu obserwacji, a nie bezpośredni pomiar liczebności populacji."
        ),
        "map": (
            "Co pokazuje ta mapa?",
            "Każdy punkt oznacza pojedynczy rekord obserwacji GBIF z datą i współrzędnymi. "
            "Filtr lat pozwala zobaczyć, gdzie gatunek był notowany w dowolnie wybranych rocznikach. "
            "Punkty nie oznaczają liczby osobników, tylko miejsca zapisanych obserwacji."
        ),
        "known_range": (
            "Co pokazuje to porównanie?",
            "Ten widok sprawdza, czy w projekcie jest niezależny zasięg referencyjny gatunku, "
            "z którym można porównać punkty obserwacji GBIF. Same punkty GBIF nie są takim zasięgiem, "
            "bo zależą od aktywności obserwatorów."
        ),
        "centroid": (
            "Co pokazuje ten wykres?",
            "Wykres pokazuje średnią szerokość geograficzną zajętych pól siatki w danym roku. "
            "Jeśli linia przesuwa się ku wyższym szerokościom geograficznym, może to sugerować przesuwanie obserwacji w stronę północy."
        ),
        "correlation": (
            "Co pokazuje ten wykres?",
            "Każdy punkt oznacza jeden rok. Oś pozioma pokazuje rok, oś pionowa indeks populacji, "
            "a kolor punktu pokazuje odchylenie temperatury sezonu lęgowego."
        ),
    }
    if chart_key not in descriptions:
        return
    title, body = descriptions[chart_key]
    st.markdown(
        f"""
        <div class="chart-description">
            <div class="chart-description-title">{escape(title)}</div>
            <p>{escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight_grid(_how_to_read: str, evidence: str, presentation_line: str) -> None:
    st.markdown(
        f"""
        <div class="insight-grid">
            <div class="insight-card">
                <div class="insight-title">Co wynika z danych</div>
                <p>{escape(evidence)}</p>
            </div>
            <div class="insight-card">
                <div class="insight-title">Wniosek</div>
                <p>{escape(presentation_line)}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_map_insights(species, year_points: pd.DataFrame, years_label: str) -> None:
    if year_points.empty:
        render_insight_grid(
            "Mapa korzysta z punktów obserwacji GBIF zapisanych ze współrzędnymi geograficznymi.",
            f"Dla wyboru: {years_label} nie ma punktów obserwacji dla gatunku {species.polish_name} w używanym zbiorze GBIF.",
            "W takim przypadku warto wybrać inne lata albo potraktować brak punktów jako ograniczenie danych, a nie dowód braku gatunku.",
        )
        return

    records_count = len(year_points)
    countries_count = year_points["country_code"].nunique() if "country_code" in year_points.columns else 0
    north = year_points["decimal_latitude"].max()
    south = year_points["decimal_latitude"].min()
    render_insight_grid(
        "Punkt na mapie oznacza rekord obserwacji, czyli informację, że ktoś zanotował gatunek w danym miejscu i czasie. To nie jest liczba osobników.",
        (
            f"Dla wyboru: {years_label} używany zbiór GBIF zawiera {records_count} rekordów z {countries_count} krajów. "
            f"Na mapie pokazano wszystkie te punkty. Rozpiętość północ-południe wynosi od {format_decimal(south, 2)}° "
            f"do {format_decimal(north, 2)}° szerokości geograficznej."
        ),
        (
            "Mapa pomaga pokazać, czy obserwacje są skupione w części Europy, czy rozproszone szerzej. "
            "Przy interpretacji trzeba pamiętać, że liczba punktów zależy także od liczby obserwatorów i popularności zgłaszania danych."
        ),
    )


def render_chart_insights(chart_key: str, frame: pd.DataFrame) -> None:
    if frame.empty:
        render_insight_grid(
            "Filtr lat ogranicza dane używane w aktualnym widoku.",
            "Nie wybrano żadnego roku, więc nie ma danych do podsumowania.",
            "Wybierz przynajmniej jeden rok w filtrze, żeby odtworzyć wykres i wniosek.",
        )
        return

    trend_label = "brak klasyfikacji trendu"
    if "long_term_classification" in frame.columns and not frame["long_term_classification"].dropna().empty:
        trend_label = translate_trend_classification(frame["long_term_classification"].dropna().iloc[0])
    stats = correlation_tests(frame, x_column="breeding_temperature_anomaly_c", y_column="index_pct")

    if chart_key == "population":
        index_text, delta = first_last_index_text(frame)
        direction = "wzrost" if delta is not None and delta > 0 else "spadek" if delta is not None and delta < 0 else "zmianę"
        render_insight_grid(
            "Indeks 100 oznacza poziom odniesienia. Wartość powyżej 100 sugeruje wzrost względem początku szeregu, a poniżej 100 spadek.",
            f"{index_text} Klasyfikacja długoterminowa Europejskiego Monitoringu Ptaków: {trend_label}.",
            f"Ten gatunek pokazuje {direction} populacji, dlatego porównujemy go z klimatem, ale nie traktujemy samej korelacji jako dowodu przyczynowości.",
        )
        return

    if chart_key == "climate":
        early_mean = frame.head(5)["breeding_temperature_anomaly_c"].mean()
        late_mean = frame.tail(5)["breeding_temperature_anomaly_c"].mean()
        delta = late_mean - early_mean
        warmest = frame.dropna(subset=["breeding_temperature_anomaly_c"]).sort_values(
            "breeding_temperature_anomaly_c"
        ).tail(1)
        warmest_text = "Brak danych o najcieplejszym roku."
        if not warmest.empty:
            row = warmest.iloc[0]
            warmest_text = f"Najwyższe odchylenie temperatury wystąpiło w {int(row['year'])}: {format_decimal(row['breeding_temperature_anomaly_c'], 2)} C."
        render_insight_grid(
            "Odchylenie temperatury pokazuje różnicę względem średniej z lat 1991-2020. Wynik dodatni oznacza cieplejszy sezon lęgowy.",
            f"Średnia z ostatnich 5 lat różni się od pierwszych 5 lat o {format_signed(delta, ' C')}. {warmest_text}",
            "To jest klimatyczne tło analizy: najpierw pokazujemy zmianę warunków w sezonie lęgowym, a potem pytamy, czy gatunek zmienia populację lub zasięg.",
        )
        return

    if chart_key == "range":
        early_cells = frame.head(5)["occupied_cells"].mean()
        late_cells = frame.tail(5)["occupied_cells"].mean()
        cells_delta = late_cells - early_cells
        record_delta = frame.tail(5)["observation_records"].mean() - frame.head(5)["observation_records"].mean()
        render_insight_grid(
            "Jedno pole siatki ma 1° szerokości i 1° długości geograficznej. Jeśli w danym roku pojawi się w nim co najmniej jedna obserwacja, pole liczy się jako zajęte.",
            f"Średnia liczba pól siatki zmieniła się o {format_signed(cells_delta)}; średnia liczba rekordów obserwacji zmieniła się o {format_signed(record_delta)}.",
            "Ten wykres warto komentować ostrożnie: wzrost obserwacji może wynikać ze zmiany zasięgu, ale też z większej aktywności obserwatorów.",
        )
        return

    if chart_key == "centroid":
        latitude_shift = frame.tail(5)["centroid_latitude"].mean() - frame.head(5)["centroid_latitude"].mean()
        if pd.isna(latitude_shift):
            shift_text = "Brak wystarczających danych do oceny przesunięcia."
        elif latitude_shift > 0:
            shift_text = f"Środek zasięgu obserwacji przesunął się średnio o {format_decimal(latitude_shift, 2)} stopnia na północ."
        elif latitude_shift < 0:
            shift_text = f"Środek zasięgu obserwacji przesunął się średnio o {format_decimal(abs(latitude_shift), 2)} stopnia na południe."
        else:
            shift_text = "Środek zasięgu obserwacji pozostawał zbliżony."
        render_insight_grid(
            "Środek zasięgu to średnia pozycja zajętych pól siatki, a nie średnia wszystkich pojedynczych rekordów. Rosnąca szerokość geograficzna oznacza przesunięcie obserwacji ku północy.",
            shift_text,
            "To prosty sposób pokazania, czy w danych obserwacyjnych widać przestrzenne przesunięcie potencjalnego zasięgu.",
        )
        return

    if stats["pearson_r"] is None:
        evidence = "Brak wystarczającej liczby punktów do oceny związku między temperaturą a populacją."
        presentation_line = "Przy tym gatunku trzeba uzupełnić dane albo pokazać ten wykres jako miejsce na dalszą analizę."
    else:
        direction = "dodatni" if stats["pearson_r"] > 0 else "ujemny"
        strength = relationship_strength(stats["pearson_r"])
        evidence = (
            f"Współczynnik korelacji Pearsona = {format_signed(stats['pearson_r'])}, {format_p_statement(stats['pearson_p'])}; "
            f"związek jest {direction} i {strength}."
        )
        presentation_line = (
            "Kolor punktów pokazuje temperaturę sezonu lęgowego, ale wynik trzeba zestawić z biologią gatunku "
            "i ograniczeniami danych obserwacyjnych."
        )
    render_insight_grid(
        "Każdy punkt to jeden rok. Oś X pokazuje rok, oś Y indeks populacji, a kolor punktu pokazuje odchylenie temperatury sezonu lęgowego.",
        evidence,
        presentation_line,
    )


def render_known_range_comparison(species, selected_years: list[int], all_years: list[int]) -> None:
    years_label = format_year_selection(selected_years, all_years)
    classified_points, known_range_cells = load_known_range_comparison_data(
        species.scientific_name,
        tuple(selected_years),
    )
    records_count = len(classified_points)
    years_count = classified_points["year"].nunique() if not classified_points.empty and "year" in classified_points.columns else 0
    countries_count = (
        classified_points["country_code"].nunique()
        if not classified_points.empty and "country_code" in classified_points.columns
        else 0
    )
    records_label = f"{records_count:,}".replace(",", " ")

    if known_range_cells.empty:
        st.plotly_chart(
            build_known_range_comparison_figure(classified_points, known_range_cells, species, years_label),
            width="stretch",
        )
        st.markdown(
            f"""
            <div class="comparison-panel">
                <div class="comparison-kicker">Porównanie zasięgu</div>
                <div class="comparison-title">Brakuje warstwy referencyjnej dla: {escape(species.polish_name)}</div>
                <p>
                    Mapa pokazuje punkty GBIF dla wyboru: <strong>{escape(years_label)}</strong>.
                    Warstwa zasięgu pojawi się po dodaniu komórek referencyjnych do
                    <strong>data/reference/known_range_cells.csv</strong>.
                </p>
                <div class="comparison-grid">
                    <div class="comparison-stat">
                        <div class="comparison-stat-label">Punkty GBIF w wybranych latach</div>
                        <div class="comparison-stat-value">{records_label}</div>
                    </div>
                    <div class="comparison-stat">
                        <div class="comparison-stat-label">Lata z punktami GBIF</div>
                        <div class="comparison-stat-value">{years_count}</div>
                    </div>
                    <div class="comparison-stat">
                        <div class="comparison-stat-label">Kraje w punktach GBIF</div>
                        <div class="comparison-stat-value">{countries_count}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_insight_grid(
            "Punkty GBIF pokazują miejsca zgłoszonych obserwacji, a nie kompletny zasięg biologiczny gatunku.",
            "Porównanie jest przygotowane technicznie, ale wymaga dodania referencyjnej siatki EBBA2 do pliku known_range_cells.csv.",
            "Po dodaniu komórek EBBA2 dashboard pokaże realny udział punktów obserwacji wewnątrz i poza znanym zasięgiem lęgowym.",
        )
        return

    range_source = (
        str(known_range_cells["source"].dropna().iloc[0])
        if "source" in known_range_cells.columns and not known_range_cells["source"].dropna().empty
        else "warstwa referencyjna"
    )
    matched_count = int(classified_points["known_range_match"].sum()) if not classified_points.empty else 0
    outside_count = records_count - matched_count
    matched_pct = (matched_count / records_count * 100) if records_count else 0
    outside_pct = (outside_count / records_count * 100) if records_count else 0
    range_cells_count = len(known_range_cells)
    matched_label = f"{matched_count:,}".replace(",", " ")
    outside_label = f"{outside_count:,}".replace(",", " ")

    st.plotly_chart(
        build_known_range_comparison_figure(classified_points, known_range_cells, species, years_label),
        width="stretch",
    )
    st.markdown(
        f"""
        <div class="comparison-panel">
            <div class="comparison-kicker">Porównanie zasięgu</div>
            <div class="comparison-title">Obserwacje GBIF vs znany zasięg: {escape(species.polish_name)}</div>
            <p>
                Źródło warstwy: <strong>{escape(range_source)}</strong>. Jasnoniebieskie kwadraty pokazują komórki
                znanego/przybliżonego zasięgu. Punkt uznaję za zgodny, jeśli leży do
                {format_decimal(KNOWN_RANGE_MATCH_RADIUS_KM, 0)} km od środka komórki.
            </p>
            <div class="comparison-grid">
                <div class="comparison-stat">
                    <div class="comparison-stat-label">Punkty w znanym zasięgu</div>
                    <div class="comparison-stat-value">{matched_label} ({format_decimal(matched_pct, 1)}%)</div>
                </div>
                <div class="comparison-stat">
                    <div class="comparison-stat-label">Punkty poza znanym zasięgiem</div>
                    <div class="comparison-stat-value">{outside_label} ({format_decimal(outside_pct, 1)}%)</div>
                </div>
                <div class="comparison-stat">
                    <div class="comparison-stat-label">Komórki zasięgu referencyjnego</div>
                    <div class="comparison-stat-value">{range_cells_count}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_insight_grid(
        "Komórki referencyjne oznaczają znany lub przybliżony zasięg lęgowy, a punkty GBIF pokazują pojedyncze zgłoszone obserwacje.",
        (
            f"W wybranych latach {format_decimal(matched_pct, 1)}% punktów GBIF leży w pobliżu komórek znanego zasięgu, "
            f"a {format_decimal(outside_pct, 1)}% poza nimi."
        ),
        "Punkty poza zasięgiem warto interpretować ostrożnie: mogą oznaczać migrację, obserwacje poza sezonem lęgowym, błąd geolokalizacji albo realną rozbieżność z atlasem.",
    )


def render_summary_view(species, species_panel: pd.DataFrame, species_trend: pd.DataFrame) -> None:
    st.subheader("Podsumowanie i wnioski")
    st.write(
        "Dane populacyjne pochodzą z Europejskiego Monitoringu Ptaków (PECBMS), natomiast dane GBIF "
        "służą tutaj jako przybliżenie zmian zasięgu obserwacji. Najlepiej interpretować je razem, a nie osobno."
    )

    st.subheader("Najważniejsze miary")
    render_metric_grid(calculate_dashboard_metrics(species_panel))

    render_correlation_takeaway(species, species_panel)

    correlation_result = correlation_tests(
        species_panel,
        x_column="breeding_temperature_anomaly_c",
        y_column="index_pct",
    )
    trend_result = linear_trend_test(species_panel, value_column="index_pct")
    range_comparison = period_comparison(species_panel, value_column="occupied_cells")
    stationarity_result = stationarity_test(species_panel, value_column="index_pct")

    result_table = pd.DataFrame(
        [
            {
                "Miara statystyczna": "Korelacja Pearsona",
                "Wartość": correlation_result["pearson_r"],
                "Istotność statystyczna (p)": format_p_value(correlation_result["pearson_p"]),
            },
            {
                "Miara statystyczna": "Korelacja rang Spearmana",
                "Wartość": correlation_result["spearman_rho"],
                "Istotność statystyczna (p)": format_p_value(correlation_result["spearman_p"]),
            },
            {
                "Miara statystyczna": "Trend liniowy indeksu populacji",
                "Wartość": trend_result["slope"],
                "Istotność statystyczna (p)": format_p_value(trend_result["p_value"]),
            },
            {
                "Miara statystyczna": "Porównanie wcześniejszych i późniejszych lat (test t)",
                "Wartość": range_comparison["t_stat"],
                "Istotność statystyczna (p)": format_p_value(range_comparison["t_p_value"]),
            },
            {
                "Miara statystyczna": "Test stabilności szeregu czasowego (ADF)",
                "Wartość": stationarity_result["adf_statistic"],
                "Istotność statystyczna (p)": format_p_value(stationarity_result["adf_p_value"]),
            },
        ]
    )

    st.subheader("Wyniki statystyczne")
    st.caption(
        "Wartość p pokazuje, czy zależność jest statystycznie istotna. Im mniejsza wartość p, "
        "tym silniejsza podstawa do odrzucenia przypadku."
    )
    render_dark_table(result_table)

    if not species_trend.empty:
        st.subheader("Podsumowanie trendu z Europejskiego Monitoringu Ptaków")
        st.caption(
            "Ta tabela tłumaczy surowe dane PECBMS na krótkie podsumowanie przydatne podczas prezentacji."
        )
        render_dark_table(build_trend_summary_table(species, species_trend))

    render_science_context()


def render_selected_chart(
    chart_key: str,
    frame: pd.DataFrame,
    species,
    species_trend: pd.DataFrame,
    selected_years: list[int],
    all_years: list[int],
) -> None:
    if chart_key == "info":
        render_species_profile(species, frame, species_trend)
        return

    if frame.empty:
        render_chart_description(chart_key)
        st.warning("Brak danych dla wybranych lat. Zaznacz co najmniej jeden rok w filtrze.")
        return

    if chart_key == "summary":
        render_summary_view(species, frame, species_trend)
        return

    if chart_key == "population":
        render_chart_description(chart_key)
        st.plotly_chart(build_population_figure(frame), width="stretch")
        render_chart_insights(chart_key, frame)
        return

    if chart_key == "climate":
        render_chart_description(chart_key)
        st.plotly_chart(build_climate_figure(frame), width="stretch")
        render_chart_insights(chart_key, frame)
        return

    if chart_key == "range":
        render_chart_description(chart_key)
        st.plotly_chart(build_range_figure(frame), width="stretch")
        render_chart_insights(chart_key, frame)
        return

    if chart_key == "known_range":
        render_chart_description(chart_key)
        render_known_range_comparison(species, selected_years, all_years)
        return

    if chart_key == "map":
        render_chart_description(chart_key)
        years_label = format_year_selection(selected_years, all_years)
        year_points = load_occurrence_points(species.scientific_name, tuple(selected_years))
        st.markdown(
            (
                f'<p class="muted-note">Dane punktowe: GBIF, obserwacje ze współrzędnymi w miesiącach lęgowych '
                f'(kwiecień-lipiec). Wybrane lata: {escape(years_label)}; punktów widocznych na mapie: {len(year_points)}.</p>'
            ),
            unsafe_allow_html=True,
        )
        st.plotly_chart(build_observation_map_figure(year_points, species, years_label), width="stretch")
        render_map_insights(species, year_points, years_label)
        return

    if chart_key == "centroid":
        render_chart_description(chart_key)
        st.plotly_chart(build_centroid_figure(frame), width="stretch")
        render_chart_insights(chart_key, frame)
        return

    render_chart_description(chart_key)
    st.plotly_chart(build_temperature_population_figure(frame), width="stretch")
    render_chart_insights(chart_key, frame)


def main() -> None:
    st.title("Wpływ zmian klimatycznych na zasięg i populacje ptaków")
    st.caption(
        "Dashboard łączy dane Europejskiego Monitoringu Ptaków (PECBMS), obserwacje z bazy GBIF "
        "oraz historyczne dane klimatyczne."
    )
    inject_custom_styles()
    initialize_state()

    panel, trends = load_data()
    if panel.empty:
        st.warning("Brak danych przetworzonych. Najpierw uruchom `python scripts/build_dataset.py`.")
        st.stop()

    scientific_name = render_species_buttons()
    render_sidebar_glossary()
    selected_config = selected_species_config(scientific_name)
    inject_species_background(selected_config)

    species_panel = panel[panel["scientific_name"] == scientific_name].copy()
    species_trend = trends[trends["scientific_name"] == scientific_name].copy()

    if species_panel.empty:
        st.error(
            "Dla wybranego gatunku nie znaleziono danych w analysis_panel.csv. "
            "Spróbuj odświeżyć aplikację albo ponownie uruchomić pipeline."
        )
        st.stop()

    render_selected_species_banner(selected_config)

    selected_chart = render_chart_buttons()
    all_years = available_years(species_panel)
    if selected_chart == "info":
        selected_years = all_years
        filtered_species_panel = species_panel
    else:
        selected_years = render_year_filter(species_panel)
        filtered_species_panel = filter_frame_by_years(species_panel, selected_years)

    render_selected_chart(
        selected_chart,
        filtered_species_panel,
        selected_config,
        species_trend,
        selected_years,
        all_years,
    )
if __name__ == "__main__":
    main()
