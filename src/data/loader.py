from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import pandas as pd

from src.config.settings import (
    RAW_DATA_FILE,
    RAW_SHEET_NAME,
    REQUIRED_COLUMNS,
)


def check_file_exists(file_path: Path = RAW_DATA_FILE) -> None:
    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset file not found at: {file_path}. "
            f"Please place your Excel file there."
        )


def get_available_sheet_names(file_path: Path = RAW_DATA_FILE) -> List[str]:
    check_file_exists(file_path)
    excel_file = pd.ExcelFile(file_path)
    return excel_file.sheet_names


def validate_sheet_name(
    file_path: Path = RAW_DATA_FILE,
    sheet_name: str = RAW_SHEET_NAME,
) -> None:
    available_sheets = get_available_sheet_names(file_path)
    if sheet_name not in available_sheets:
        raise ValueError(
            f"Sheet '{sheet_name}' not found in Excel file. "
            f"Available sheets: {available_sheets}"
        )


def load_raw_excel(
    file_path: Path = RAW_DATA_FILE,
    sheet_name: str = RAW_SHEET_NAME,
) -> pd.DataFrame:
    check_file_exists(file_path)
    validate_sheet_name(file_path, sheet_name)

    df = pd.read_excel(file_path, sheet_name=sheet_name)

    if df.empty:
        raise ValueError("The Excel sheet is empty.")

    return df


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    normalized_df = df.copy()
    normalized_df.columns = [str(col).strip() for col in normalized_df.columns]
    return normalized_df


def validate_required_columns(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    normalized_df = normalize_column_names(df)

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in normalized_df.columns
    ]
    return len(missing_columns) == 0, missing_columns


def load_and_validate_raw_data() -> pd.DataFrame:
    raw_df = load_raw_excel()
    raw_df = normalize_column_names(raw_df)

    is_valid, missing_columns = validate_required_columns(raw_df)
    if not is_valid:
        raise ValueError(f"Missing required columns: {missing_columns}")

    return raw_df