from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import folium
import pandas as pd
from folium import FeatureGroup, LayerControl, Map, Marker, PolyLine

from src.config.settings import FEATURED_DATA_FILE


AREA_COORDINATES = {
    "All": None,
    "Biratnagar": (26.45505, 87.27007),
    "Itahari": (26.66225, 87.27490),
    "Urlabari": (26.66487, 87.61370),
    "Letang": (26.76571, 87.50664),
    "Nemuwa": (26.61300, 87.40200),
    "Haraicha": (26.70000, 87.43000),
    "Rangeli": (26.54360, 87.67680),
    "Belbari": (26.66310, 87.41600),
    "Pathari": (26.71400, 87.56000),
    "Sundarharaicha": (26.62100, 87.42900),
}


AREA_PLACE_GROUPS = {
    "All": None,
    "Biratnagar": ["Biratnagar"],
    "Itahari": ["Itahari", "Nemuwa"],
    "Urlabari": ["Urlabari"],
    "Letang": ["Letang"],
    "Nemuwa": ["Nemuwa"],
    "Haraicha": ["Haraicha", "Sundarharaicha"],
    "Rangeli": ["Rangeli"],
    "Belbari": ["Belbari"],
    "Pathari": ["Pathari"],
    "Sundarharaicha": ["Sundarharaicha", "Haraicha"],
}


def load_featured_dataset() -> pd.DataFrame:
    if not FEATURED_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Feature-engineered dataset not found at: {FEATURED_DATA_FILE}. "
            f"Please complete feature engineering first."
        )

    df = pd.read_csv(FEATURED_DATA_FILE)

    if df.empty:
        raise ValueError("Feature-engineered dataset is empty.")

    return df


def classify_hotspot_level(score: float) -> str:
    score = float(score)
    if score >= 15:
        return "High"
    if score >= 5:
        return "Medium"
    return "Low"


def get_hotspot_color(hotspot_level: str) -> str:
    level = str(hotspot_level).strip().lower()
    if level == "high":
        return "red"
    if level == "medium":
        return "orange"
    return "green"


def get_risk_color(risk_label: str) -> str:
    label = str(risk_label).strip().lower()
    if label == "high":
        return "red"
    if label == "medium":
        return "orange"
    return "green"


def build_hotspot_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = [
        "place_name",
        "locality",
        "latitude",
        "longitude",
        "death",
        "serious_injury",
        "normal_injury",
    ]

    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing hotspot columns: {missing_columns}")

    working_df = df.copy()

    working_df["hotspot_score_component"] = (
        working_df["death"].astype(float) * 5
        + working_df["serious_injury"].astype(float) * 3
        + working_df["normal_injury"].astype(float) * 1
    )

    grouped_df = (
    working_df.groupby(
        ["place_name", "locality", "latitude", "longitude"],
        as_index=False,
    )
        .agg(
            accident_count=("place_name", "count"),
            total_death=("death", "sum"),
            total_serious_injury=("serious_injury", "sum"),
            total_normal_injury=("normal_injury", "sum"),
            hotspot_score=("hotspot_score_component", "sum"),
        )
    )

    grouped_df["hotspot_level"] = grouped_df["hotspot_score"].apply(classify_hotspot_level)
    grouped_df = grouped_df.sort_values(
        by=["hotspot_score", "accident_count"],
        ascending=[False, False],
    ).reset_index(drop=True)

    return grouped_df


def filter_hotspots_by_area(hotspot_df: pd.DataFrame, area_name: str) -> pd.DataFrame:
    if area_name == "All":
        return hotspot_df.copy()

    allowed_places = AREA_PLACE_GROUPS.get(area_name)
    if not allowed_places:
        return hotspot_df.copy()

    filtered_df = hotspot_df[hotspot_df["place_name"].isin(allowed_places)].copy()
    return filtered_df.reset_index(drop=True)


def get_map_center(
    hotspot_df: Optional[pd.DataFrame] = None,
    route_points: Optional[List[Tuple[float, float]]] = None,
    area_filter: str = "All",
) -> List[float]:
    if route_points:
        latitudes = [point[0] for point in route_points]
        longitudes = [point[1] for point in route_points]
        return [sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)]

    if area_filter != "All" and area_filter in AREA_COORDINATES:
        coords = AREA_COORDINATES[area_filter]
        if coords is not None:
            return [coords[0], coords[1]]

    if hotspot_df is not None and not hotspot_df.empty:
        return [
            float(hotspot_df["latitude"].mean()),
            float(hotspot_df["longitude"].mean()),
        ]

    return [26.45505, 87.27007]


def add_hotspot_layer(map_object: folium.Map, hotspot_df: pd.DataFrame) -> None:
    hotspot_group = FeatureGroup(name="Accident Hotspots", show=True)

    for _, row in hotspot_df.iterrows():
        hotspot_level = row["hotspot_level"]
        color = get_hotspot_color(hotspot_level)

        popup_html = f"""
        <b>Place:</b> {row['place_name']}<br>
        <b>Locality:</b> {row['locality']}<br>
        <b>Hotspot Level:</b> {hotspot_level}<br>
        <b>Accident Count:</b> {int(row['accident_count'])}<br>
        <b>Hotspot Score:</b> {float(row['hotspot_score']):.2f}<br>
        <b>Total Death:</b> {int(row['total_death'])}<br>
        <b>Total Serious Injury:</b> {int(row['total_serious_injury'])}<br>
        <b>Total Normal Injury:</b> {int(row['total_normal_injury'])}
        """

        folium.CircleMarker(
            location=[float(row["latitude"]), float(row["longitude"])],
            radius=8 if hotspot_level == "Low" else 10 if hotspot_level == "Medium" else 12,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.70,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{row['locality']} ({hotspot_level})",
        ).add_to(hotspot_group)

    hotspot_group.add_to(map_object)


def add_route_layer(
    map_object: folium.Map,
    route_points: List[Tuple[float, float]],
    origin: Dict[str, Any],
    destination: Dict[str, Any],
) -> None:
    route_group = FeatureGroup(name="Predicted Route", show=True)

    if route_points:
        PolyLine(
            locations=route_points,
            color="blue",
            weight=5,
            opacity=0.85,
            tooltip="Route Path",
        ).add_to(route_group)

    Marker(
        location=[float(origin["latitude"]), float(origin["longitude"])],
        popup=f"Origin: {origin['display_name']}",
        tooltip="Origin",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(route_group)

    Marker(
        location=[float(destination["latitude"]), float(destination["longitude"])],
        popup=f"Destination: {destination['display_name']}",
        tooltip="Destination",
        icon=folium.Icon(color="red", icon="stop"),
    ).add_to(route_group)

    route_group.add_to(map_object)


def add_segment_layer(map_object: folium.Map, segment_results: List[Dict[str, Any]]) -> None:
    segment_group = FeatureGroup(name="Route Segments", show=True)

    for segment in segment_results:
        adjusted_risk = segment["adjusted_risk"]
        color = get_risk_color(adjusted_risk)

        popup_html = f"""
        <b>Segment:</b> {segment['segment_name']}<br>
        <b>Adjusted Risk:</b> {segment['adjusted_risk']}<br>
        <b>Distance (km):</b> {float(segment['distance_km']):.2f}<br>
        <b>Weather:</b> {segment['weather_main']} - {segment['weather_description']}<br>
        <b>Forecast Time:</b> {segment.get('forecast_time', 'N/A')}
        """

        folium.CircleMarker(
            location=[
                float(segment["midpoint_latitude"]),
                float(segment["midpoint_longitude"]),
            ],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"{segment['segment_name']} - {adjusted_risk}",
        ).add_to(segment_group)

    segment_group.add_to(map_object)


def create_hotspot_only_map(
    hotspot_limit: int = 300,
    area_filter: str = "All",
) -> folium.Map:
    featured_df = load_featured_dataset()
    hotspot_df = build_hotspot_dataframe(featured_df)
    hotspot_df = filter_hotspots_by_area(hotspot_df, area_filter)

    if hotspot_limit > 0:
        hotspot_df = hotspot_df.head(hotspot_limit).copy()

    map_center = get_map_center(hotspot_df=hotspot_df, area_filter=area_filter)

    map_object = Map(
        location=map_center,
        zoom_start=12 if area_filter != "All" else 9,
        control_scale=True,
        tiles="OpenStreetMap",
        prefer_canvas=True,
    )

    add_hotspot_layer(map_object, hotspot_df)
    LayerControl(collapsed=False).add_to(map_object)
    return map_object


def create_route_hotspot_map(
    route_result: Dict[str, Any],
) -> folium.Map:
    route_points = route_result.get("route_points", [])
    origin = route_result.get("origin", {})
    destination = route_result.get("destination", {})
    segment_results = route_result.get("segment_results", [])

    map_center = get_map_center(route_points=route_points)

    map_object = Map(
        location=map_center,
        zoom_start=10,
        control_scale=True,
        tiles="OpenStreetMap",
        prefer_canvas=True,
    )

    if route_points and origin and destination:
        add_route_layer(
            map_object=map_object,
            route_points=route_points,
            origin=origin,
            destination=destination,
        )

    if segment_results:
        add_segment_layer(map_object, segment_results)

    LayerControl(collapsed=False).add_to(map_object)
    return map_object


def get_hotspot_summary(top_n: int = 10, area_filter: str = "All") -> pd.DataFrame:
    featured_df = load_featured_dataset()
    hotspot_df = build_hotspot_dataframe(featured_df)
    hotspot_df = filter_hotspots_by_area(hotspot_df, area_filter)
    return hotspot_df.head(top_n).reset_index(drop=True)