from __future__ import annotations

import math
from typing import Dict, List, Tuple

import pandas as pd


def haversine_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    radius_km = 6371.0

    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


def route_distance_km(route_points: List[Tuple[float, float]]) -> float:
    if len(route_points) < 2:
        return 0.0

    total = 0.0
    for index in range(len(route_points) - 1):
        lat1, lon1 = route_points[index]
        lat2, lon2 = route_points[index + 1]
        total += haversine_distance_km(lat1, lon1, lat2, lon2)

    return total


def split_route_into_segments(
    route_points: List[Tuple[float, float]],
    segment_count: int,
) -> List[Dict]:
    if len(route_points) < 2:
        return []

    segment_count = max(1, int(segment_count))
    total_edges = len(route_points) - 1
    edges_per_segment = max(1, total_edges // segment_count)

    segments: List[Dict] = []
    start_index = 0
    segment_id = 1

    while start_index < total_edges:
        end_index = min(start_index + edges_per_segment, total_edges)

        segment_points = route_points[start_index : end_index + 1]
        if len(segment_points) < 2:
            break

        start_point = segment_points[0]
        end_point = segment_points[-1]
        midpoint = segment_points[len(segment_points) // 2]
        distance_km = route_distance_km(segment_points)

        segments.append(
            {
                "segment_id": segment_id,
                "points": segment_points,
                "start_point": start_point,
                "end_point": end_point,
                "midpoint": midpoint,
                "distance_km": round(distance_km, 4),
            }
        )

        segment_id += 1
        start_index = end_index

    return segments


def find_nearest_historical_context(
    latitude: float,
    longitude: float,
    featured_df: pd.DataFrame,
) -> Dict:
    if featured_df.empty:
        return {
            "nearest_place_name": "Unknown",
            "nearest_vehicle_involved": "unknown",
            "nearest_reason": "unknown",
            "nearest_place_accident_count": 0,
            "nearest_distance_km": 0.0,
        }

    working_df = featured_df.copy()

    if "latitude" not in working_df.columns or "longitude" not in working_df.columns:
        raise ValueError("Featured dataset must contain latitude and longitude columns.")

    working_df["geo_distance_km"] = working_df.apply(
        lambda row: haversine_distance_km(
            latitude,
            longitude,
            row["latitude"],
            row["longitude"],
        ),
        axis=1,
    )

    nearest_row = working_df.sort_values("geo_distance_km", ascending=True).iloc[0]

    return {
        "nearest_place_name": str(nearest_row.get("place_name", "Unknown")),
        "nearest_vehicle_involved": str(nearest_row.get("vehicle_involved", "unknown")),
        "nearest_reason": str(nearest_row.get("reason", "unknown")),
        "nearest_place_accident_count": int(nearest_row.get("place_accident_count", 0)),
        "nearest_distance_km": round(float(nearest_row.get("geo_distance_km", 0.0)), 4),
    }