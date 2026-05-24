from __future__ import annotations

import re
from typing import Any, Dict, List

import joblib
import pandas as pd

from src.config.settings import (
    MODEL_FILE,
    LABEL_ENCODER_FILE,
    FEATURE_COLUMNS_FILE,
    FEATURED_DATA_FILE,
    MODEL_FEATURES,
)


def load_model_artifacts() -> Dict[str, Any]:
    """
    Load trained pipeline, label encoder, feature list, and featured dataset.
    """
    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Trained model not found at: {MODEL_FILE}. Please complete training first."
        )

    if not LABEL_ENCODER_FILE.exists():
        raise FileNotFoundError(
            f"Label encoder not found at: {LABEL_ENCODER_FILE}. Please complete training first."
        )

    if not FEATURE_COLUMNS_FILE.exists():
        raise FileNotFoundError(
            f"Feature columns file not found at: {FEATURE_COLUMNS_FILE}. Please complete training first."
        )

    if not FEATURED_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Feature-engineered dataset not found at: {FEATURED_DATA_FILE}. "
            f"Please complete feature engineering first."
        )

    pipeline = joblib.load(MODEL_FILE)
    label_encoder = joblib.load(LABEL_ENCODER_FILE)
    feature_columns = joblib.load(FEATURE_COLUMNS_FILE)
    featured_df = pd.read_csv(FEATURED_DATA_FILE)

    return {
        "pipeline": pipeline,
        "label_encoder": label_encoder,
        "feature_columns": feature_columns,
        "featured_df": featured_df,
    }


def clean_text(value: Any) -> str:
    """
    Normalize text values for inference consistency.
    """
    if value is None or pd.isna(value):
        return "unknown"

    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)

    if text == "":
        return "unknown"

    return text


def clean_place_name(value: Any) -> str:
    """
    Normalize place names.
    """
    if value is None or pd.isna(value):
        return "unknown"

    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)

    if text == "":
        return "unknown"

    return text.title()


def parse_prediction_date(date_value: Any) -> pd.Timestamp:
    """
    Parse prediction date input.
    """
    parsed = pd.to_datetime(date_value, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"Invalid date value: {date_value}")
    return parsed


def extract_start_hour(time_slot: Any) -> int:
    """
    Extract start hour from time slot string.
    """
    if time_slot is None or pd.isna(time_slot):
        return -1

    text = str(time_slot).strip()
    text = text.replace("–", "-").replace("—", "-")

    match = re.match(r"^\s*(\d{1,2})\s*:\s*\d{2}\s*-\s*(\d{1,2})\s*:\s*\d{2}\s*$", text)
    if not match:
        return -1

    start_hour = int(match.group(1))
    if 0 <= start_hour <= 23:
        return start_hour

    return -1


def extract_end_hour(time_slot: Any) -> int:
    """
    Extract end hour from time slot string.
    """
    if time_slot is None or pd.isna(time_slot):
        return -1

    text = str(time_slot).strip()
    text = text.replace("–", "-").replace("—", "-")

    match = re.match(r"^\s*(\d{1,2})\s*:\s*\d{2}\s*-\s*(\d{1,2})\s*:\s*\d{2}\s*$", text)
    if not match:
        return -1

    end_hour = int(match.group(2))
    if 0 <= end_hour <= 23:
        return end_hour

    return -1


def create_time_band(start_hour: int) -> str:
    """
    Convert start hour into time band.
    """
    if start_hour < 0:
        return "unknown"
    if 0 <= start_hour < 6:
        return "night"
    if 6 <= start_hour < 12:
        return "morning"
    if 12 <= start_hour < 18:
        return "afternoon"
    return "evening"


def estimate_place_accident_count(place_name: str, featured_df: pd.DataFrame) -> int:
    """
    Estimate historical accident frequency for the selected place.
    If not found, return 0.
    """
    if "place_name" not in featured_df.columns:
        return 0

    normalized_place = clean_place_name(place_name)
    matching_rows = featured_df[featured_df["place_name"].astype(str).str.strip() == normalized_place]

    if matching_rows.empty:
        return 0

    if "place_accident_count" in matching_rows.columns:
        return int(matching_rows["place_accident_count"].iloc[0])

    return int(len(matching_rows))


def build_prediction_record(
    *,
    date: Any,
    time: str,
    place_name: str,
    latitude: float,
    longitude: float,
    vehicle_involved: str,
    reason: str,
    featured_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build a single prediction record matching model feature columns.
    """
    parsed_date = parse_prediction_date(date)

    start_hour = extract_start_hour(time)
    end_hour = extract_end_hour(time)
    time_band = create_time_band(start_hour)

    cleaned_place_name = clean_place_name(place_name)
    cleaned_vehicle = clean_text(vehicle_involved)
    cleaned_reason = clean_text(reason)

    place_accident_count = estimate_place_accident_count(
        place_name=cleaned_place_name,
        featured_df=featured_df,
    )

    prediction_data = {
        "year": int(parsed_date.year),
        "month": int(parsed_date.month),
        "day": int(parsed_date.day),
        "is_weekend": int(parsed_date.day_name() in ["Saturday", "Sunday"]),
        "start_hour": int(start_hour),
        "end_hour": int(end_hour),
        "is_night": int(time_band == "night"),
        "is_morning": int(time_band == "morning"),
        "is_afternoon": int(time_band == "afternoon"),
        "is_evening": int(time_band == "evening"),
        "place_accident_count": int(place_accident_count),
        "latitude": float(latitude),
        "longitude": float(longitude),
        "day_of_week": str(parsed_date.day_name()),
        "time_band": str(time_band),
        "place_name": cleaned_place_name,
        "vehicle_involved": cleaned_vehicle,
        "reason": cleaned_reason,
    }

    input_df = pd.DataFrame([prediction_data])

    for column in MODEL_FEATURES:
        if column not in input_df.columns:
            input_df[column] = None

    input_df = input_df[MODEL_FEATURES]
    return input_df


def predict_base_risk(
    *,
    date: Any,
    time: str,
    place_name: str,
    latitude: float,
    longitude: float,
    vehicle_involved: str,
    reason: str,
) -> Dict[str, Any]:
    """
    Predict base accident risk and return class probabilities.
    """
    artifacts = load_model_artifacts()
    pipeline = artifacts["pipeline"]
    label_encoder = artifacts["label_encoder"]
    featured_df = artifacts["featured_df"]

    input_df = build_prediction_record(
        date=date,
        time=time,
        place_name=place_name,
        latitude=latitude,
        longitude=longitude,
        vehicle_involved=vehicle_involved,
        reason=reason,
        featured_df=featured_df,
    )

    predicted_encoded = pipeline.predict(input_df)[0]
    predicted_label = label_encoder.inverse_transform([predicted_encoded])[0]

    probabilities = pipeline.predict_proba(input_df)[0]
    class_names: List[str] = list(label_encoder.classes_)

    probability_map = {
        class_name: round(float(probability), 4)
        for class_name, probability in zip(class_names, probabilities)
    }

    max_confidence = max(probability_map.values()) if probability_map else 0.0

    return {
        "predicted_risk": predicted_label,
        "confidence": round(max_confidence, 4),
        "probabilities": probability_map,
        "input_record": input_df,
    }