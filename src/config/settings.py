from pathlib import Path
from dotenv import load_dotenv
import os


load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]

APP_DIR = BASE_DIR / "app"
ASSETS_DIR = APP_DIR / "assets"

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"

MODELS_DIR = BASE_DIR / "models"
TRAINED_MODELS_DIR = MODELS_DIR / "trained"
ARTIFACTS_DIR = MODELS_DIR / "artifacts"

RAW_DATA_FILE = RAW_DATA_DIR / "accidents.xlsx"
RAW_SHEET_NAME = "data"

PROCESSED_DATA_FILE = PROCESSED_DATA_DIR / "accidents_processed.csv"
FEATURED_DATA_FILE = PROCESSED_DATA_DIR / "accidents_featured.csv"

MODEL_FILE = TRAINED_MODELS_DIR / "risk_model.pkl"
LABEL_ENCODER_FILE = TRAINED_MODELS_DIR / "label_encoder.pkl"
FEATURE_COLUMNS_FILE = TRAINED_MODELS_DIR / "feature_columns.pkl"
TRAINING_METRICS_FILE = ARTIFACTS_DIR / "training_metrics.json"
PREPROCESSOR_FILE = TRAINED_MODELS_DIR / "preprocessor.pkl"

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
OPENWEATHER_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"

APP_TITLE = "YatraDristi"
APP_SUBTITLE = "Intelligent Road Safety & Risk Prediction System"

RISK_LABELS = ["Low", "Medium", "High"]
RISK_SCORE_MAP = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}
RISK_SCORE_TO_LABEL = {
    1: "Low",
    2: "Medium",
    3: "High",
}

REQUIRED_COLUMNS = [
    "date_bs",
    "date",
    "time",
    "place_name",
    "latitude",
    "longitude",
    "vehicle_involved",
    "death",
    "serious_injury",
    "normal_injury",
    "reason",
]

PROCESSED_REQUIRED_COLUMNS = [
    "date_bs",
    "date",
    "year",
    "month",
    "day",
    "day_of_week",
    "is_weekend",
    "time",
    "place_name",
    "latitude",
    "longitude",
    "vehicle_involved",
    "death",
    "serious_injury",
    "normal_injury",
    "reason",
]

FEATURED_REQUIRED_COLUMNS = [
    "date_bs",
    "date",
    "year",
    "month",
    "day",
    "day_of_week",
    "is_weekend",
    "time",
    "start_hour",
    "end_hour",
    "time_band",
    "is_night",
    "is_morning",
    "is_afternoon",
    "is_evening",
    "place_name",
    "place_accident_count",
    "latitude",
    "longitude",
    "vehicle_involved",
    "death",
    "serious_injury",
    "normal_injury",
    "total_casualties",
    "severity_score",
    "reason",
    "risk_level",
]

MODEL_NUMERIC_FEATURES = [
    "year",
    "month",
    "day",
    "is_weekend",
    "start_hour",
    "end_hour",
    "is_night",
    "is_morning",
    "is_afternoon",
    "is_evening",
    "place_accident_count",
    "latitude",
    "longitude",
]

MODEL_CATEGORICAL_FEATURES = [
    "day_of_week",
    "time_band",
    "place_name",
    "vehicle_involved",
    "reason",
]

MODEL_FEATURES = MODEL_NUMERIC_FEATURES + MODEL_CATEGORICAL_FEATURES
TARGET_COLUMN = "risk_level"

DEFAULT_SEGMENT_COUNT = 6
DEFAULT_NOMINATIM_LIMIT = 1
APP_USER_AGENT = "YatraDristi/1.0 (BSc CSIT Academic Project)"

TOP_PLACES = {
    "Biratnagar": {"latitude": 26.45505, "longitude": 87.27007},
    "Itahari": {"latitude": 26.66225, "longitude": 87.27490},
    "Letang": {"latitude": 26.76571, "longitude": 87.50664},
}

# Controlled places used in dropdowns and geo-standardization
STANDARD_PLACE_COORDINATES = {
    "Biratnagar": {"latitude": 26.45505, "longitude": 87.27007},
    "Itahari": {"latitude": 26.66225, "longitude": 87.27490},
    "Urlabari": {"latitude": 26.66487, "longitude": 87.61370},
    "Letang": {"latitude": 26.76571, "longitude": 87.50664},
    "Nemuwa": {"latitude": 26.61300, "longitude": 87.40200},
    "Haraicha": {"latitude": 26.70000, "longitude": 87.43000},
    "Rangeli": {"latitude": 26.54360, "longitude": 87.67680},
    "Belbari": {"latitude": 26.66310, "longitude": 87.41600},
    "Pathari": {"latitude": 26.71400, "longitude": 87.56000},
    "Sundarharaicha": {"latitude": 26.62100, "longitude": 87.42900},

}

# Optional name normalization so similar spellings map to one standard place
PLACE_NAME_ALIASES = {
    "biratnagar": "Biratnagar",
    "itahari": "Itahari",
    "urlabari": "Urlabari",
    "uralabari": "Urlabari",
    "letang": "Letang",
    "nemuwa": "Nemuwa",
    "haraicha": "Haraicha",
    "haraincha": "Haraicha",
    "rangeli": "Rangeli",
    "belbari": "Belbari",
    "pathari": "Pathari",
    "pathari shanishchare": "Pathari",
    "haraicha": "Haraicha",
    "biratchowk": "Biratchowk",
    "karsiya": "Karsiya",
}

KNOWN_PLACE_OPTIONS = list(STANDARD_PLACE_COORDINATES.keys())


KNOWN_PLACE_OPTIONS = [
    "Biratnagar",
    "Itahari",
    "Urlabari",
    "Letang",
    "Nemuwa",
    "Haraicha",
    "Rangeli",
    "Belbari",
    "Pathari",
    "Sundarharaicha",
    "Karsiya",
    "Biratchowk",
]

# Use these only when a place is missing from dataset
FALLBACK_ROUTE_COORDINATES = {
    "Biratnagar": (26.45505, 87.27007),
    "Itahari": (26.66355, 87.27403),
    "Urlabari": (26.66487, 87.61370),
    "Letang": (26.76571, 87.50664),
    "Nemuwa": (26.61300, 87.40200),
    "Haraicha": (26.70000, 87.43000),
    "Sundarharaicha": (26.62100, 87.42900),
    "Rangeli": (26.54360, 87.67680),
    "Belbari": (26.66310, 87.41600),
    "Pathari": (26.71400, 87.56000),
    "Karsiya": (26.51500, 87.36000),
    "Biratchowk": (26.6725644,87.3761159),
}

def ensure_directories() -> None:
    required_dirs = [
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        EXPORTS_DIR,
        MODELS_DIR,
        TRAINED_MODELS_DIR,
        ARTIFACTS_DIR,
        APP_DIR,
        ASSETS_DIR,
    ]

    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)