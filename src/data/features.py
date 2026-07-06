from __future__ import annotations

import re
from typing import Any, Dict

import pandas as pd

from src.config.settings import (
    PROCESSED_DATA_FILE,
    FEATURED_DATA_FILE,
    PROCESSED_REQUIRED_COLUMNS,
    ensure_directories,
)


def load_processed_data() -> pd.DataFrame:
    if not PROCESSED_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at: {PROCESSED_DATA_FILE}. "
            f"Please complete preprocessing first."
        )

    df = pd.read_csv(PROCESSED_DATA_FILE)

    if df.empty:
        raise ValueError("Processed dataset is empty.")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


def validate_processed_columns(df: pd.DataFrame) -> None:
    missing_columns = [
        column for column in PROCESSED_REQUIRED_COLUMNS
        if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Missing required processed columns: {missing_columns}"
        )


def extract_start_hour(time_slot: Any) -> int:
    if pd.isna(time_slot):
        return -1

    text = str(time_slot).strip()
    match = re.match(r"^\s*(\d{1,2})\s*:\s*\d{2}\s*-\s*(\d{1,2})\s*:\s*\d{2}\s*$", text)

    if not match:
        return -1

    start_hour = int(match.group(1))
    if 0 <= start_hour <= 23:
        return start_hour

    return -1


def extract_end_hour(time_slot: Any) -> int:
    if pd.isna(time_slot):
        return -1

    text = str(time_slot).strip()
    match = re.match(r"^\s*(\d{1,2})\s*:\s*\d{2}\s*-\s*(\d{1,2})\s*:\s*\d{2}\s*$", text)

    if not match:
        return -1

    end_hour = int(match.group(2))
    if 0 <= end_hour <= 23:
        return end_hour

    return -1


def create_time_band(start_hour: int) -> str:
    if start_hour < 0:
        return "unknown"
    if 0 <= start_hour < 6:
        return "night"
    if 6 <= start_hour < 12:
        return "morning"
    if 12 <= start_hour < 18:
        return "afternoon"
    return "evening"


def create_severity_score(row: pd.Series) -> int:
    death = int(row["death"])
    serious_injury = int(row["serious_injury"])
    normal_injury = int(row["normal_injury"])

    score = (death * 5) + (serious_injury * 3) + (normal_injury * 1)
    return score


def create_total_casualties(row: pd.Series) -> int:
    return int(row["death"]) + int(row["serious_injury"]) + int(row["normal_injury"])


def classify_risk_level(row: pd.Series) -> str:
    death = int(row["death"])
    serious_injury = int(row["serious_injury"])
    normal_injury = int(row["normal_injury"])
    severity_score = int(row["severity_score"])

    if death >= 1 or serious_injury >= 2 or severity_score >= 5:
        return "High"

    if serious_injury >= 1 or normal_injury >= 2 or severity_score >= 2:
        return "Medium"

    return "Low"


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    output_df = df.copy()

    output_df["start_hour"] = output_df["time"].apply(extract_start_hour)
    output_df["end_hour"] = output_df["time"].apply(extract_end_hour)

    output_df["time_band"] = output_df["start_hour"].apply(create_time_band)

    output_df["is_night"] = output_df["time_band"].eq("night").astype(int)
    output_df["is_morning"] = output_df["time_band"].eq("morning").astype(int)
    output_df["is_afternoon"] = output_df["time_band"].eq("afternoon").astype(int)
    output_df["is_evening"] = output_df["time_band"].eq("evening").astype(int)

    return output_df


def add_severity_features(df: pd.DataFrame) -> pd.DataFrame:
    output_df = df.copy()

    output_df["total_casualties"] = output_df.apply(create_total_casualties, axis=1)
    output_df["severity_score"] = output_df.apply(create_severity_score, axis=1)
    output_df["risk_level"] = output_df.apply(classify_risk_level, axis=1)

    return output_df


def add_location_frequency_feature(df: pd.DataFrame) -> pd.DataFrame:
    output_df = df.copy()

    place_counts = output_df["locality"].value_counts().to_dict()
    output_df["place_accident_count"] = (
        output_df["locality"]
        .map(place_counts)
        .fillna(0)
        .astype(int)
    )
    output_df["place_accident_count"] = output_df["place_name"].map(place_counts).fillna(0).astype(int)

    return output_df


def build_feature_engineered_dataset(df: pd.DataFrame) -> pd.DataFrame:
    validate_processed_columns(df)

    featured_df = df.copy()

    featured_df = add_time_features(featured_df)
    featured_df = add_severity_features(featured_df)
    featured_df = add_location_frequency_feature(featured_df)

    ordered_columns = [
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
        "locality",
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

    featured_df = featured_df[ordered_columns].reset_index(drop=True)
    return featured_df


def save_feature_engineered_data(df: pd.DataFrame) -> None:
    ensure_directories()
    df.to_csv(FEATURED_DATA_FILE, index=False)


def run_feature_engineering_pipeline() -> Dict[str, Any]:
    processed_df = load_processed_data()
    featured_df = build_feature_engineered_dataset(processed_df)
    save_feature_engineered_data(featured_df)

    risk_distribution = featured_df["risk_level"].value_counts().to_dict()

    return {
        "processed_shape": processed_df.shape,
        "featured_shape": featured_df.shape,
        "featured_file": str(FEATURED_DATA_FILE),
        "columns": featured_df.columns.tolist(),
        "risk_distribution": risk_distribution,
        "preview": featured_df.head(10),
    }