from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import requests

from src.config.settings import (
    OPENWEATHER_API_KEY,
    OPENWEATHER_ONECALL_CURRENT_URL,
    OPENWEATHER_ONECALL_TIMELINE_URL,
)


class WeatherServiceError(Exception):
    """Raised when weather data cannot be fetched or parsed."""

def validate_weather_api_key() -> None:
    if not OPENWEATHER_API_KEY:
        raise WeatherServiceError(
            "OpenWeather API key is missing."
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


def _normalize_weather_payload(payload):

    current = payload["data"][0]

    weather = current["weather"][0]

    return {

        "location_name": "Route Segment",

        "country_code": "",

        "weather_main": weather["main"],

        "weather_description": weather["description"],

        "temperature_c": current["temp"],

        "feels_like_c": current["feels_like"],

        "humidity_percent": current["humidity"],

        "pressure_hpa": current["pressure"],

        "visibility_m": current["visibility"],

        "wind_speed_mps": current["wind_speed"],

        "wind_deg": current["wind_deg"],

        "cloudiness_percent": current["clouds"],

        "rain_1h_mm": current.get("rain", {}).get("1h", 0),

        "snow_1h_mm": current.get("snow", {}).get("1h", 0),

        "uvi": current.get("uvi", 0),

        "dew_point": current.get("dew_point", 0),

        "has_rain": "rain" in current,

        "has_snow": "snow" in current,

    }

def fetch_current_weather(latitude: float, longitude: float):

    validate_weather_api_key()
    validate_coordinates(latitude, longitude)

    response = requests.get(
        OPENWEATHER_ONECALL_CURRENT_URL,
        params={
            "lat": latitude,
            "lon": longitude,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
        },
        timeout=20,
    )

    response.raise_for_status()

    return response.json()

def fetch_forecast_weather(latitude: float, longitude: float):


    validate_weather_api_key()
    validate_coordinates(latitude, longitude)

    response = requests.get(
        OPENWEATHER_ONECALL_TIMELINE_URL,
        params={
            "lat": latitude,
            "lon": longitude,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
        },
        timeout=20,
    )

    response.raise_for_status()

    payload = response.json()

    all_data = payload["data"]

    next_url = payload.get("next")

    while next_url:

        response = requests.get(next_url, timeout=20)
        response.raise_for_status()

        next_payload = response.json()

        all_data.extend(next_payload["data"])

        next_url = next_payload.get("next")

    return payload
    

def get_current_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    raw_payload = fetch_current_weather(latitude=latitude, longitude=longitude)
    return _normalize_weather_payload(raw_payload)


def normalize_forecast_item(item):

    weather = item["weather"][0]

    return {

        "forecast_time": pd.to_datetime(
            item["dt"],
            unit="s",
        ),

        "weather_main": weather["main"],

        "weather_description": weather["description"],

        "temperature_c": item["temp"],

        "feels_like_c": item["feels_like"],

        "humidity_percent": item["humidity"],

        "pressure_hpa": item["pressure"],

        "visibility_m": item["visibility"],

        "wind_speed_mps": item["wind_speed"],

        "wind_deg": item["wind_deg"],

        "cloudiness_percent": item["clouds"],

        "rain_1h_mm": item.get("rain", {}).get("1h", 0),

        "snow_1h_mm": item.get("snow", {}).get("1h", 0),

        "has_rain": "rain" in item,

        "has_snow": "snow" in item,

    }

def get_forecast_for_datetime(

    latitude,
    longitude,
    target_datetime,

):

    payload = fetch_forecast_weather(
        latitude,
        longitude,
    )

    forecast_items = payload["data"]

    forecasts = [
        normalize_forecast_item(item)
        for item in forecast_items
    ]

    target = pd.Timestamp(target_datetime)

    nearest = min(
        forecasts,
        key=lambda x: abs(x["forecast_time"] - target),
    )


    return nearest
