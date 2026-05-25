from __future__ import annotations

from typing import Any, Dict, List

from src.config.settings import RISK_SCORE_MAP, RISK_SCORE_TO_LABEL


def clamp_risk_score(score: int) -> int:
    return max(1, min(3, int(score)))


def get_weather_risk_adjustment(weather: Dict[str, Any]) -> Dict[str, Any]:
    adjustment_points = 0
    reasons: List[str] = []

    weather_main = str(weather.get("weather_main", "")).lower()
    weather_description = str(weather.get("weather_description", "")).lower()
    visibility_m = int(weather.get("visibility_m", 0))
    wind_speed_mps = float(weather.get("wind_speed_mps", 0.0))
    rain_1h_mm = float(weather.get("rain_1h_mm", 0.0))
    snow_1h_mm = float(weather.get("snow_1h_mm", 0.0))
    humidity_percent = int(weather.get("humidity_percent", 0))

    severe_weather_keywords = {
        "thunderstorm",
        "squall",
        "tornado",
        "ash",
    }

    moderate_weather_keywords = {
        "rain",
        "drizzle",
        "snow",
        "mist",
        "fog",
        "haze",
        "dust",
        "smoke",
    }

    if weather_main in severe_weather_keywords or "thunderstorm" in weather_description:
        adjustment_points += 2
        reasons.append("Severe weather condition detected.")

    elif weather_main in moderate_weather_keywords:
        adjustment_points += 1
        reasons.append("Moderate weather condition detected.")

    if rain_1h_mm >= 7:
        adjustment_points += 1
        reasons.append("Heavy rainfall reduces road grip and visibility.")
    elif rain_1h_mm > 0:
        adjustment_points += 1
        reasons.append("Rainfall may make roads slippery.")

    if snow_1h_mm > 0:
        adjustment_points += 1
        reasons.append("Snow or ice risk detected.")

    if visibility_m > 0 and visibility_m < 1000:
        adjustment_points += 1
        reasons.append("Very low visibility detected.")
    elif visibility_m >= 1000 and visibility_m < 4000:
        adjustment_points += 1
        reasons.append("Reduced visibility detected.")

    if wind_speed_mps >= 10:
        adjustment_points += 1
        reasons.append("Strong wind may affect vehicle stability.")

    if humidity_percent >= 95 and ("mist" in weather_description or "fog" in weather_description):
        adjustment_points += 1
        reasons.append("Foggy moisture-heavy conditions detected.")

    if adjustment_points > 2:
        adjustment_points = 2

    if not reasons:
        reasons.append("No major weather-based risk increase detected.")

    return {
        "adjustment_points": adjustment_points,
        "adjustment_reasons": reasons,
    }


def adjust_risk_with_weather(
    base_risk: str,
    weather: Dict[str, Any],
) -> Dict[str, Any]:
    if base_risk not in RISK_SCORE_MAP:
        raise ValueError(f"Unknown base risk label: {base_risk}")

    base_score = RISK_SCORE_MAP[base_risk]
    weather_adjustment = get_weather_risk_adjustment(weather)

    adjusted_score = clamp_risk_score(
        base_score + weather_adjustment["adjustment_points"]
    )
    adjusted_risk = RISK_SCORE_TO_LABEL[adjusted_score]

    return {
        "base_risk": base_risk,
        "base_score": base_score,
        "weather_adjustment_points": weather_adjustment["adjustment_points"],
        "weather_adjustment_reasons": weather_adjustment["adjustment_reasons"],
        "adjusted_score": adjusted_score,
        "adjusted_risk": adjusted_risk,
    }


def generate_safety_alert(
    adjusted_risk: str,
    weather: Dict[str, Any],
) -> str:
    weather_main = str(weather.get("weather_main", "Unknown"))
    visibility_m = int(weather.get("visibility_m", 0))
    wind_speed_mps = float(weather.get("wind_speed_mps", 0.0))

    if adjusted_risk == "High":
        return (
            f"High risk alert: current weather ({weather_main}) may significantly increase road danger. "
            "Drive slowly, increase braking distance, and avoid unnecessary travel if possible."
        )

    if adjusted_risk == "Medium":
        if visibility_m < 4000 or wind_speed_mps >= 10:
            return (
                f"Moderate risk alert: weather conditions ({weather_main}) require extra caution. "
                "Use headlights if needed and maintain safe following distance."
            )
        return (
            f"Moderate risk alert: stay cautious due to current weather conditions ({weather_main})."
        )

    return (
        f"Low risk alert: current weather ({weather_main}) shows no major additional danger, "
        "but normal safe driving practices still apply."
    )