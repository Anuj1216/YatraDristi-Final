from __future__ import annotations

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.services.hotspot_service import create_hotspot_only_map, get_hotspot_summary


AREA_OPTIONS = [
    "All",
    "Biratnagar",
    "Itahari",
    "Urlabari",
    "Letang",
    "Nemuwa",
    "Haraicha",
    "Rangeli",
    "Belbari",
    "Pathari",
    "Sundarharaicha",
]


@st.cache_data(show_spinner=False)
def load_hotspot_summary(area_filter: str) -> pd.DataFrame:
    return get_hotspot_summary(top_n=500, area_filter=area_filter)


def render_metric_card(title: str, value: str, subtext: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-subtext">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hotspots_page() -> None:
    st.title("Accident Hotspot Map")

    area_filter = st.selectbox(
        "Select Area",
        options=AREA_OPTIONS,
        index=0,
    )

    hotspot_df = load_hotspot_summary(area_filter)

    if hotspot_df.empty:
        st.info("No hotspot data available for the selected area.")
        return

    total_hotspots = len(hotspot_df)
    high_risk_zones = int((hotspot_df["hotspot_level"] == "High").sum())
    medium_risk_zones = int((hotspot_df["hotspot_level"] == "Medium").sum())

    col1, col2, col3 = st.columns(3)
    with col1:
        render_metric_card("Total Hotspots", str(total_hotspots), "Current hotspot count")
    with col2:
        render_metric_card("High Risk Zones", str(high_risk_zones), "High severity locations")
    with col3:
        render_metric_card("Medium Risk Zones", str(medium_risk_zones), "Moderate severity locations")

    st.divider()

    risk_filter = st.selectbox(
        "Filter by Risk Level",
        options=["All", "High", "Medium", "Low"],
        index=0,
    )

    filtered_df = hotspot_df.copy()
    if risk_filter != "All":
        filtered_df = filtered_df[filtered_df["hotspot_level"] == risk_filter].copy()

    st.subheader("Hotspot Visualization")

    try:
        hotspot_limit = len(filtered_df) if len(filtered_df) > 0 else 50
        hotspot_map = create_hotspot_only_map(
            hotspot_limit=hotspot_limit,
            area_filter=area_filter,
        )
        st_folium(
            hotspot_map,
            width=None,
            height=650,
            returned_objects=[],
        )
    except Exception as exc:
        st.error(f"Hotspot map failed: {exc}")

    st.subheader("Hotspot Details")
    st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)