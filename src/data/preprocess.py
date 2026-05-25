from __future__ import annotations

import re
from typing import Any, Dict

import pandas as pd

from src.config.settings import (
    REQUIRED_COLUMNS,
    PROCESSED_DATA_FILE,
    ensure_directories,
    PLACE_NAME_ALIASES,
)
from src.data.loader import load_and_validate_raw_data


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return "unknown"

    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)

    if text == "":
        return "unknown"

    return text


def normalize_place_name(value: Any) -> str:
    if pd.isna(value):
        return "Unknown"

    raw_text = str(value).strip()
    raw_text = re.sub(r"\s+", " ", raw_text)

    if raw_text == "":
        return "Unknown"

    lower_text = raw_text.lower()

    if lower_text in PLACE_NAME_ALIASES:
        return PLACE_NAME_ALIASES[lower_text]

    return raw_text.title()


def clean_place_name(value: Any) -> str:
    return normalize_place_name(value)


def clean_numeric(value: Any, default: float = 0.0) -> float:
    numeric_value = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric_value):
        return default
    return float(numeric_value)


def clean_integer_count(value: Any) -> int:
    numeric_value = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric_value):
        return 0

    integer_value = int(round(float(numeric_value)))
    return max(0, integer_value)


def standardize_time_slot(value: Any) -> str:
    if pd.isna(value):
        return "unknown"

    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)

    if text == "":
        return "unknown"

    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s*-\s*", " - ", text)

    return text


def parse_english_date(value: Any) -> pd.Timestamp | pd.NaT:
    return pd.to_datetime(value, errors="coerce")


def validate_columns(df: pd.DataFrame) -> None:
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")


def add_date_features(df: pd.DataFrame) -> pd.DataFrame:
    output_df = df.copy()

    output_df["year"] = output_df["date"].dt.year
    output_df["month"] = output_df["date"].dt.month
    output_df["day"] = output_df["date"].dt.day
    output_df["day_of_week"] = output_df["date"].dt.day_name()
    output_df["is_weekend"] = output_df["day_of_week"].isin(["Saturday", "Sunday"]).astype(int)

    return output_df


def preprocess_dataset(df: pd.DataFrame) -> pd.DataFrame:
    processed_df = df.copy()
    validate_columns(processed_df)

    processed_df["date_bs"] = processed_df["date_bs"].astype(str).str.strip()
    processed_df["date"] = processed_df["date"].apply(parse_english_date)

    processed_df = processed_df.dropna(subset=["date"]).copy()

    processed_df["time"] = processed_df["time"].apply(standardize_time_slot)
    processed_df["place_name"] = processed_df["place_name"].apply(clean_place_name)
    processed_df["vehicle_involved"] = processed_df["vehicle_involved"].apply(clean_text)
    processed_df["reason"] = processed_df["reason"].apply(clean_text)

    processed_df["latitude"] = processed_df["latitude"].apply(clean_numeric)
    processed_df["longitude"] = processed_df["longitude"].apply(clean_numeric)
    processed_df["death"] = processed_df["death"].apply(clean_integer_count)
    processed_df["serious_injury"] = processed_df["serious_injury"].apply(clean_integer_count)
    processed_df["normal_injury"] = processed_df["normal_injury"].apply(clean_integer_count)

    processed_df = processed_df[
        processed_df["latitude"].between(-90, 90) &
        processed_df["longitude"].between(-180, 180)
    ].copy()

    processed_df = add_date_features(processed_df)

    ordered_columns = [
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

    processed_df = processed_df[ordered_columns].reset_index(drop=True)
    return processed_df


def save_processed_data(df: pd.DataFrame) -> None:
    ensure_directories()
    df.to_csv(PROCESSED_DATA_FILE, index=False)


def run_preprocessing_pipeline() -> Dict[str, Any]:
    raw_df = load_and_validate_raw_data()
    processed_df = preprocess_dataset(raw_df)
    save_processed_data(processed_df)

    return {
        "raw_shape": raw_df.shape,
        "processed_shape": processed_df.shape,
        "processed_file": str(PROCESSED_DATA_FILE),
        "columns": processed_df.columns.tolist(),
        "preview": processed_df.head(10),
    }