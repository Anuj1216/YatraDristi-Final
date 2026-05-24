from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import requests

from src.config.settings import (
    OPENWEATHER_API_KEY,
    OPENWEATHER_CURRENT_URL,
    OPENWEATHER_FORECAST_URL,
)


class WeatherServiceError(Exception):
    """Raised when weather data cannot be fetched or parsed."""


def validate_weather_api_key() -> None:
    if not OPENWEATHER_API_KEY:
        raise WeatherServiceError(
            "OpenWeather API key is missing. Please set OPENWEATHER_API_KEY in your .env file."
        )


def validate_coordinates(latitude: float, longitude: float) -> None:
    if not (-90 <= float(latitude) <= 90):
        raise WeatherServiceError(f"Invalid latitude: {latitude}")

    if not (-180 <= float(longitude) <= 180):
        raise WeatherServiceError(f"Invalid longitude: {longitude}")


def _safe_nested_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


def _normalize_weather_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    weather_list = payload.get("weather", [])
    primary_weather = weather_list[0] if isinstance(weather_list, list) and weather_list else {}

    normalized = {
        "location_name": payload.get("name", "Unknown"),
        "country_code": _safe_nested_get(payload, "sys", "country", default=""),
        "weather_main": primary_weather.get("main", "Unknown"),
        "weather_description": primary_weather.get("description", "unknown"),
        "temperature_c": float(_safe_nested_get(payload, "main", "temp", default=0.0) or 0.0),
        "feels_like_c": float(_safe_nested_get(payload, "main", "feels_like", default=0.0) or 0.0),
        "humidity_percent": int(_safe_nested_get(payload, "main", "humidity", default=0) or 0),
        "pressure_hpa": int(_safe_nested_get(payload, "main", "pressure", default=0) or 0),
        "visibility_m": int(payload.get("visibility", 0) or 0),
        "wind_speed_mps": float(_safe_nested_get(payload, "wind", "speed", default=0.0) or 0.0),
        "wind_deg": int(_safe_nested_get(payload, "wind", "deg", default=0) or 0),
        "cloudiness_percent": int(_safe_nested_get(payload, "clouds", "all", default=0) or 0),
        "rain_1h_mm": float(_safe_nested_get(payload, "rain", "1h", default=0.0) or 0.0),
        "snow_1h_mm": float(_safe_nested_get(payload, "snow", "1h", default=0.0) or 0.0),
    }

    normalized["has_rain"] = normalized["rain_1h_mm"] > 0
    normalized["has_snow"] = normalized["snow_1h_mm"] > 0

    return normalized


def fetch_current_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    validate_weather_api_key()
    validate_coordinates(latitude, longitude)

    params = {
        "lat": float(latitude),
        "lon": float(longitude),
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(
            OPENWEATHER_CURRENT_URL,
            params=params,
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise WeatherServiceError(f"Weather API request failed: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise WeatherServiceError("Weather API returned invalid JSON.") from exc

    if not isinstance(payload, dict):
        raise WeatherServiceError("Unexpected weather API response format.")

    if str(payload.get("cod")) not in {"200", "200.0"} and payload.get("cod") != 200:
        message = payload.get("message", "Unknown weather API error")
        raise WeatherServiceError(f"Weather API error: {message}")

    return payload


def get_current_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    raw_payload = fetch_current_weather(latitude=latitude, longitude=longitude)
    return _normalize_weather_payload(raw_payload)


def fetch_forecast_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Fetch 5-day / 3-hour forecast data from OpenWeather.
    """
    validate_weather_api_key()
    validate_coordinates(latitude, longitude)

    params = {
        "lat": float(latitude),
        "lon": float(longitude),
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(
            OPENWEATHER_FORECAST_URL,
            params=params,
            timeout=20,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise WeatherServiceError(f"Forecast API request failed: {exc}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise WeatherServiceError("Forecast API returned invalid JSON.") from exc

    if not isinstance(payload, dict):
        raise WeatherServiceError("Unexpected forecast API response format.")

    if str(payload.get("cod")) not in {"200", "200.0"} and payload.get("cod") != "200":
        message = payload.get("message", "Unknown forecast API error")
        raise WeatherServiceError(f"Forecast API error: {message}")

    return payload


def normalize_forecast_item(item: Dict[str, Any], city_name: str = "Unknown") -> Dict[str, Any]:
    weather_list = item.get("weather", [])
    primary_weather = weather_list[0] if isinstance(weather_list, list) and weather_list else {}

    forecast_time_raw = item.get("dt_txt")
    forecast_time = pd.to_datetime(forecast_time_raw, errors="coerce")

    normalized = {
        "location_name": city_name,
        "forecast_time": forecast_time,
        "forecast_time_str": str(forecast_time_raw),
        "weather_main": primary_weather.get("main", "Unknown"),
        "weather_description": primary_weather.get("description", "unknown"),
        "temperature_c": float(_safe_nested_get(item, "main", "temp", default=0.0) or 0.0),
        "feels_like_c": float(_safe_nested_get(item, "main", "feels_like", default=0.0) or 0.0),
        "humidity_percent": int(_safe_nested_get(item, "main", "humidity", default=0) or 0),
        "pressure_hpa": int(_safe_nested_get(item, "main", "pressure", default=0) or 0),
        "visibility_m": int(item.get("visibility", 0) or 0),
        "wind_speed_mps": float(_safe_nested_get(item, "wind", "speed", default=0.0) or 0.0),
        "wind_deg": int(_safe_nested_get(item, "wind", "deg", default=0) or 0),
        "cloudiness_percent": int(_safe_nested_get(item, "clouds", "all", default=0) or 0),
        "rain_3h_mm": float(_safe_nested_get(item, "rain", "3h", default=0.0) or 0.0),
        "snow_3h_mm": float(_safe_nested_get(item, "snow", "3h", default=0.0) or 0.0),
    }

    normalized["rain_1h_mm"] = normalized["rain_3h_mm"] / 3 if normalized["rain_3h_mm"] else 0.0
    normalized["snow_1h_mm"] = normalized["snow_3h_mm"] / 3 if normalized["snow_3h_mm"] else 0.0
    normalized["has_rain"] = normalized["rain_3h_mm"] > 0
    normalized["has_snow"] = normalized["snow_3h_mm"] > 0

    return normalized


def get_forecast_for_datetime(
    latitude: float,
    longitude: float,
    target_datetime: datetime,
) -> Dict[str, Any]:
    """
    Return the nearest available forecast item for the requested datetime.
    """
    payload = fetch_forecast_weather(latitude=latitude, longitude=longitude)

    forecast_list = payload.get("list", [])
    city_name = _safe_nested_get(payload, "city", "name", default="Unknown")

    if not forecast_list:
        raise WeatherServiceError("Forecast list is empty.")

    normalized_items: List[Dict[str, Any]] = [
        normalize_forecast_item(item, city_name=city_name)
        for item in forecast_list
    ]

    valid_items = [
        item for item in normalized_items
        if pd.notna(item["forecast_time"])
    ]

    if not valid_items:
        raise WeatherServiceError("Forecast data contains no valid timestamps.")

    target_ts = pd.to_datetime(target_datetime)

    nearest_item = min(
        valid_items,
        key=lambda item: abs(item["forecast_time"] - target_ts),
    )

    nearest_item["hours_from_target"] = round(
        abs((nearest_item["forecast_time"] - target_ts).total_seconds()) / 3600.0,
        2,
    )

    return nearest_item