from __future__ import annotations

import json
from typing import Any, Dict, Tuple

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

from src.config.settings import (
    FEATURED_DATA_FILE,
    FEATURED_REQUIRED_COLUMNS,
    MODEL_NUMERIC_FEATURES,
    MODEL_CATEGORICAL_FEATURES,
    MODEL_FEATURES,
    TARGET_COLUMN,
    MODEL_FILE,
    LABEL_ENCODER_FILE,
    FEATURE_COLUMNS_FILE,
    TRAINING_METRICS_FILE,
    PREPROCESSOR_FILE,
    ensure_directories,
)


def load_featured_data() -> pd.DataFrame:
    if not FEATURED_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Feature-engineered dataset not found at: {FEATURED_DATA_FILE}. "
            f"Please complete feature engineering first."
        )

    df = pd.read_csv(FEATURED_DATA_FILE)

    if df.empty:
        raise ValueError("Feature-engineered dataset is empty.")

    return df


def validate_featured_columns(df: pd.DataFrame) -> None:
    missing_columns = [
        column for column in FEATURED_REQUIRED_COLUMNS
        if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(f"Missing required featured columns: {missing_columns}")


def prepare_training_data(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.Series]:
    validate_featured_columns(df)

    training_df = df.copy()

    X = training_df[MODEL_FEATURES].copy()
    y = training_df[TARGET_COLUMN].copy()

    if X.empty:
        raise ValueError("Feature matrix is empty.")

    if y.empty:
        raise ValueError("Target column is empty.")

    return X, y


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, MODEL_NUMERIC_FEATURES),
            ("cat", categorical_pipeline, MODEL_CATEGORICAL_FEATURES),
        ]
    )

    return preprocessor


def build_model_pipeline() -> Pipeline:
    preprocessor = build_preprocessor()

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", model),
        ]
    )

    return pipeline


def encode_target(y: pd.Series) -> Tuple[pd.Series, LabelEncoder]:
    label_encoder = LabelEncoder()
    y_encoded = pd.Series(label_encoder.fit_transform(y), index=y.index)
    return y_encoded, label_encoder


def split_data(
    X: pd.DataFrame,
    y: pd.Series,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )
    return X_train, X_test, y_train, y_test


def evaluate_model(
    pipeline: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    label_encoder: LabelEncoder,
) -> Dict[str, Any]:
    y_pred = pipeline.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    confusion = confusion_matrix(y_test, y_pred).tolist()

    report_dict = classification_report(
        y_test,
        y_pred,
        target_names=label_encoder.classes_,
        output_dict=True,
        zero_division=0,
    )

    readable_predictions = label_encoder.inverse_transform(y_pred)
    readable_actuals = label_encoder.inverse_transform(y_test)

    preview_df = pd.DataFrame(
        {
            "actual": readable_actuals,
            "predicted": readable_predictions,
        }
    ).head(20)

    metrics = {
        "accuracy": float(accuracy),
        "confusion_matrix": confusion,
        "classification_report": report_dict,
        "prediction_preview": preview_df,
    }

    return metrics


def save_artifacts(
    pipeline: Pipeline,
    label_encoder: LabelEncoder,
    metrics: Dict[str, Any],
) -> None:
    ensure_directories()

    joblib.dump(pipeline, MODEL_FILE)
    joblib.dump(label_encoder, LABEL_ENCODER_FILE)
    joblib.dump(MODEL_FEATURES, FEATURE_COLUMNS_FILE)

    preprocessor = pipeline.named_steps["preprocessor"]
    joblib.dump(preprocessor, PREPROCESSOR_FILE)

    metrics_to_save = {
        "accuracy": metrics["accuracy"],
        "confusion_matrix": metrics["confusion_matrix"],
        "classification_report": metrics["classification_report"],
    }

    with open(TRAINING_METRICS_FILE, "w", encoding="utf-8") as file:
        json.dump(metrics_to_save, file, indent=4)


def run_training_pipeline() -> Dict[str, Any]:
    df = load_featured_data()
    X, y = prepare_training_data(df)
    y_encoded, label_encoder = encode_target(y)

    X_train, X_test, y_train, y_test = split_data(X, y_encoded)

    pipeline = build_model_pipeline()
    pipeline.fit(X_train, y_train)

    metrics = evaluate_model(
        pipeline=pipeline,
        X_test=X_test,
        y_test=y_test,
        label_encoder=label_encoder,
    )

    save_artifacts(
        pipeline=pipeline,
        label_encoder=label_encoder,
        metrics=metrics,
    )

    result = {
        "dataset_shape": df.shape,
        "X_train_shape": X_train.shape,
        "X_test_shape": X_test.shape,
        "accuracy": metrics["accuracy"],
        "confusion_matrix": metrics["confusion_matrix"],
        "classification_report": metrics["classification_report"],
        "prediction_preview": metrics["prediction_preview"],
        "model_file": str(MODEL_FILE),
        "label_encoder_file": str(LABEL_ENCODER_FILE),
        "feature_columns_file": str(FEATURE_COLUMNS_FILE),
        "training_metrics_file": str(TRAINING_METRICS_FILE),
        "preprocessor_file": str(PREPROCESSOR_FILE),
        "model_features": MODEL_FEATURES,
        "target_classes": list(label_encoder.classes_),
    }

    return result