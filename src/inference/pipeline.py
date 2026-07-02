from __future__ import annotations

from datetime import date, datetime
from email.mime import base
from email.mime import base
from typing import Any, Dict, List, Tuple
import pandas as pd
from streamlit import context

from src.config.settings import (
    FEATURED_DATA_FILE,
    KNOWN_PLACE_OPTIONS,
    FALLBACK_ROUTE_COORDINATES,
    RISK_SCORE_MAP,
    RISK_SCORE_TO_LABEL,
)
from src.services.routing_service import geocode_and_route
from src.utils.geo_utils import haversine_distance_km, split_route_into_segments
from src.inference.predictor import predict_base_risk
from src.inference.risk_adjuster import adjust_risk_with_weather
from src.services.weather_service import get_current_weather, get_forecast_for_datetime
import src.services.weather_service as ws

from src.utils.geo_utils import (
    haversine_distance_km,
    split_route_into_segments,
    find_nearest_historical_context,
)


def _load_data() -> pd.DataFrame:
    df = pd.read_csv(FEATURED_DATA_FILE)
    if df.empty:
        raise ValueError("Feature-engineered dataset is empty.")
    return df


def _get_place_coordinates(place_name: str, df: pd.DataFrame) -> Tuple[float, float]:
    subset = df[df["place_name"] == place_name]

    if not subset.empty:
        lat = float(subset["latitude"].mean())
        lon = float(subset["longitude"].mean())
        return lat, lon

    if place_name in FALLBACK_ROUTE_COORDINATES:
        return FALLBACK_ROUTE_COORDINATES[place_name]

    available_places = sorted(df["place_name"].dropna().astype(str).unique().tolist())
    raise ValueError(
        f"No coordinates found for place: {place_name}. "
        f"Available places include: {available_places[:20]}"
    )


def _build_place_centers(df: pd.DataFrame) -> pd.DataFrame:
    centers = (
        df.groupby("place_name", as_index=False)
        .agg(
            latitude=("latitude", "mean"),
            longitude=("longitude", "mean"),
            place_accident_count=("place_name", "count"),
        )
        .reset_index(drop=True)
    )
    return centers


def _find_places_on_route(
    route_points: List[Tuple[float, float]],
    place_centers: pd.DataFrame,
    from_place: str,
    to_place: str,
) -> List[str]:
    allowed = place_centers[place_centers["place_name"].isin(KNOWN_PLACE_OPTIONS)].copy()

    candidates: List[Tuple[int, str, float]] = []

    for _, row in allowed.iterrows():
        place_name = str(row["place_name"])

        if place_name in {from_place, to_place}:
            continue

        place_lat = float(row["latitude"])
        place_lon = float(row["longitude"])

        best_idx = None
        best_dist = float("inf")

        for idx, (route_lat, route_lon) in enumerate(route_points):
            d = haversine_distance_km(place_lat, place_lon, route_lat, route_lon)
            if d < best_dist:
                best_dist = d
                best_idx = idx

        if best_idx is not None and best_dist <= 2.5:
            candidates.append((best_idx, place_name, best_dist))

    candidates.sort(key=lambda x: x[0])

    ordered_places = [from_place]
    last_idx = -10**9

    for idx, place_name, _dist in candidates:
        if idx - last_idx < 12:
            continue
        if place_name not in ordered_places:
            ordered_places.append(place_name)
            last_idx = idx

    if ordered_places[-1] != to_place:
        ordered_places.append(to_place)

    cleaned: List[str] = []
    for place in ordered_places:
        if not cleaned or cleaned[-1] != place:
            cleaned.append(place)

    return cleaned


def _assign_segment_names(
    segments: List[Dict[str, Any]],
    ordered_places: List[str],
) -> List[str]:
    if not segments:
        return []

    transitions: List[str] = []
    for i in range(len(ordered_places) - 1):
        start_name = ordered_places[i]
        end_name = ordered_places[i + 1]
        if start_name != end_name:
            transitions.append(f"{start_name} → {end_name}")

    if not transitions:
        transitions = [f"{ordered_places[0]} → {ordered_places[-1]}"]

    if len(transitions) == 1:
        return [transitions[0] for _ in segments]

    names: List[str] = []
    total_segments = len(segments)
    total_transitions = len(transitions)

    for seg_idx in range(total_segments):
        mapped_idx = min(
            int(seg_idx * total_transitions / total_segments),
            total_transitions - 1,
        )
        names.append(transitions[mapped_idx])

    return names


def _aggregate_route_risk(segment_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not segment_results:
        return {
            "route_risk": "Low",
            "route_score": 1,
            "weighted_score": 1.0,
            "total_distance_km": 0.0,
        }

    total_distance = sum(float(seg["distance_km"]) for seg in segment_results)
    if total_distance <= 0:
        total_distance = float(len(segment_results))

    weighted_sum = 0.0
    for seg in segment_results:
        seg_distance = float(seg["distance_km"])
        if seg_distance <= 0:
            seg_distance = total_distance / len(segment_results)

        weighted_sum += RISK_SCORE_MAP[seg["adjusted_risk"]] * seg_distance

    weighted_score = weighted_sum / total_distance

    if weighted_score >= 2.5:
        route_score = 3
    elif weighted_score >= 1.5:
        route_score = 2
    else:
        route_score = 1

    return {
        "route_risk": RISK_SCORE_TO_LABEL[route_score],
        "route_score": route_score,
        "weighted_score": round(weighted_score, 4),
        "total_distance_km": round(total_distance, 4),
    }


def _generate_recommendations(segment_results, route_risk: str, highest_segment: Dict[str, Any], vehicle_involved: str) -> Dict[str, Any]:
    weather_desc = str(highest_segment.get("weather_description", "")).lower()
    visibility_m = int(highest_segment.get("visibility_m", 0) or 0)
    vehicle_name = vehicle_involved.title()

    precautions: List[str] = []
    if "rain" in weather_desc or "drizzle" in weather_desc:
        precautions.append("Road surface may be slippery. Reduce speed and brake gradually.")
    if visibility_m and visibility_m < 4000:
        precautions.append("Use headlights and keep extra following distance in low visibility.")
    if vehicle_name == "Motorcycle":
        precautions.append("Wear a helmet properly and avoid sudden braking or sharp turns.")
    elif vehicle_name == "Truck":
        precautions.append("Slow early before curves and maintain wider braking distance.")
    elif vehicle_name == "Bus":
        precautions.append("Maintain stable lane discipline and smoother braking for passenger safety.")
    else:
        precautions.append("Maintain lane discipline and a safe gap from the vehicle ahead.")

    if route_risk == "High":
        travel_decision = "Delay travel if possible or proceed only with extra caution."
    elif route_risk == "Medium":
        travel_decision = "Travel is possible, but caution is strongly advised."
    else:
        travel_decision = "Travel conditions appear manageable with normal precautions."


    weather_types = []

    for seg in segment_results:
        weather = seg.get("weather_main")
        if weather and weather not in weather_types:
            weather_types.append(weather)

    weather_summary = " + ".join(weather_types) if weather_types else highest_segment.get("weather_main", "Unknown")

    return {
        "travel_decision": travel_decision,
        "summary": f"Overall route risk is {route_risk}. Weather along the route: {weather_summary}.",
        "travel_advice": [
            "Monitor weather and road conditions before departure.",
            "Stay alert near the highest-risk segment.",
        ],
        "precautions": precautions[:4],
        "segment_focus": [
            f"Pay extra attention to {highest_segment.get('segment_name', 'the highest-risk segment')}."
        ],
    }

def _calculate_hotspot_risk(
    latitude: float,
    longitude: float,
    df: pd.DataFrame,
) -> str:

    nearby_count = 0

    for _, row in df.iterrows():

        distance = haversine_distance_km(
            latitude,
            longitude,
            float(row["latitude"]),
            float(row["longitude"])
        )

        if distance <= 5:
            nearby_count += 1

    max_count = max(
        1,
        df.groupby("place_name").size().max()
    )

    normalized = nearby_count / max_count

    if normalized >= 0.70:
        return "High"

    elif normalized >= 0.35:
        return "Medium"

    return "Low"

def run_route_risk_prediction_pipeline(
    from_place,
    to_place,
    date,
    time,
    vehicle_involved,
    reason,
    segment_count=4,
):
    df = _load_data()

    from_lat, from_lon = _get_place_coordinates(from_place, df)
    to_lat, to_lon = _get_place_coordinates(to_place, df)

    route_bundle = geocode_and_route(
        from_place=from_place,
        to_place=to_place,
        from_lat=from_lat,
        from_lon=from_lon,
        to_lat=to_lat,
        to_lon=to_lon,
    )

    route = route_bundle["route"]
    segments = split_route_into_segments(route["route_points"], segment_count)

    place_centers = _build_place_centers(df)
    ordered_places = _find_places_on_route(
        route_points=route["route_points"],
        place_centers=place_centers,
        from_place=from_place,
        to_place=to_place,
    )
    segment_names = _assign_segment_names(segments, ordered_places)

    segment_results: List[Dict[str, Any]] = []

    for i, seg in enumerate(segments):
        mid_lat, mid_lon = seg["midpoint"]
    
        segment_place = segment_names[i]

        prediction_place = segment_place.split(" → ")[0]

        base = predict_base_risk(
            date=date,
            time=time,
            place_name=prediction_place,
            latitude=mid_lat,
            longitude=mid_lon,
            vehicle_involved=vehicle_involved,
            reason=reason,
        )

        from datetime import datetime
        from datetime import date as date_type
        from datetime import time as time_type

        if isinstance(date, str):
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        elif isinstance(date, date_type):
            date_obj = date
        else:
            date_obj = pd.to_datetime(date).date()

        if isinstance(time, str):

            if "-" in time:
                start_time = time.split("-")[0].strip()
            else:
                start_time = time.strip()

            time_obj = datetime.strptime(
                start_time,
                "%H:%M"
            ).time()

        else:
            time_obj = time

        travel_datetime = datetime.combine(
            date,
            time_obj,
        )

        if date_obj == datetime.now().date():

            weather = get_current_weather(
                mid_lat,
                mid_lon,
            )

        else:

            weather = get_forecast_for_datetime(
                mid_lat,
                mid_lon,
                travel_datetime,
            )

        adjusted = adjust_risk_with_weather(
            base_risk=base["predicted_risk"],
            weather=weather,
        )

        hotspot_risk = _calculate_hotspot_risk(
            mid_lat,
            mid_lon,
            df
        )

        segment_results.append({
            "segment_id": i + 1,
            "segment_name": segment_place,
            "distance_km": seg["distance_km"],
            "midpoint_latitude": round(float(mid_lat), 6),
            "midpoint_longitude": round(float(mid_lon), 6),
            "base_risk": base["predicted_risk"],
            "base_confidence": base["confidence"],
            "adjusted_risk":
                max(
                    adjusted["adjusted_risk"],
                    hotspot_risk,
                    key=lambda x: RISK_SCORE_MAP[x]
                ),
            "hotspot_risk": hotspot_risk,
            "weather_adjustment_points": adjusted["weather_adjustment_points"],
            "weather_main": weather["weather_main"],
            "weather_description": weather["weather_description"],
            "visibility_m": weather.get("visibility_m", 0),
            "segment_points": seg["points"],
        })

        merged_segments = []

        for segment in segment_results:

            if (
                merged_segments
                and merged_segments[-1]["segment_name"] == segment["segment_name"]
            ):

                previous = merged_segments[-1]

                if (
                    RISK_SCORE_MAP[segment["adjusted_risk"]]
                    >
                    RISK_SCORE_MAP[previous["adjusted_risk"]]
                ):
                    merged_segments[-1] = segment

            else:

                merged_segments.append(segment)

        segment_results = merged_segments

    route_agg = _aggregate_route_risk(segment_results)

    highest_segment = max(
        segment_results,
        key=lambda x: RISK_SCORE_MAP[x["adjusted_risk"]],
        default={
            "segment_name": f"{from_place} → {to_place}",
            "weather_main": "Unknown",
            "weather_description": "unknown",
            "visibility_m": 0,
        },
    )


    recommendations = _generate_recommendations(
        route_risk=route_agg["route_risk"],
        highest_segment=highest_segment,
        vehicle_involved=vehicle_involved,
        segment_results=segment_results,
    )

    return {
        "origin": {
            "display_name": from_place,
            "latitude": from_lat,
            "longitude": from_lon,
        },
        "destination": {
            "display_name": to_place,
            "latitude": to_lat,
            "longitude": to_lon,
        },
        "route_points": route["route_points"],
        "route_distance_km": route["distance_km"],
        "route_duration_min": route["duration_min"],
        "segment_results": segment_results,
        "route_risk": route_agg["route_risk"],
        "route_score": route_agg["route_score"],
        "weighted_score": route_agg["weighted_score"],
        "total_distance_km": route_agg["total_distance_km"],
        "highest_segment_risk": highest_segment,
        "all_segments": segment_results,
        "recommendations": recommendations,
        "ordered_route_places": ordered_places,
    }


def run_forecast_route_risk_prediction_pipeline(
    from_place,
    to_place,
    journey_date,
    journey_time,
    vehicle_involved,
    reason,
    segment_count=4,
):
    return run_route_risk_prediction_pipeline(
        from_place=from_place,
        to_place=to_place,
        date=journey_date,
        time=journey_time,
        vehicle_involved=vehicle_involved,
        reason=reason,
        segment_count=segment_count,
    )