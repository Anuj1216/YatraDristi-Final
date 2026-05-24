from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.settings import FEATURED_DATA_FILE
from src.services.hotspot_service import get_hotspot_summary


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


@st.cache_data(show_spinner=False)
def load_dashboard_stats() -> dict:
    if not FEATURED_DATA_FILE.exists():
        return {
            "routes_analyzed": 0,
            "high_risk_routes": 0,
            "hotspots_identified": 0,
            "active_alerts": 0,
            "top_hotspots": pd.DataFrame(),
        }

    df = pd.read_csv(FEATURED_DATA_FILE)

    if df.empty:
        return {
            "routes_analyzed": 0,
            "high_risk_routes": 0,
            "hotspots_identified": 0,
            "active_alerts": 0,
            "top_hotspots": pd.DataFrame(),
        }

    hotspots_df = get_hotspot_summary(top_n=20)
    high_risk_routes_estimate = int((df["risk_level"] == "High").sum())

    return {
        "routes_analyzed": int(len(df)),
        "high_risk_routes": high_risk_routes_estimate,
        "hotspots_identified": int(len(hotspots_df)),
        "active_alerts": int(len(st.session_state.get("dashboard_alerts", []))),
        "top_hotspots": hotspots_df,
    }


def render_latest_route_analysis() -> None:
    route_result = st.session_state.get("latest_route_result")
    route_input = st.session_state.get("latest_route_input")

    st.subheader("Latest Route Analysis")

    if route_result is None or route_input is None:
        st.info("No route has been analyzed yet. Go to Route Analysis and run a prediction.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**From:** {route_input['from_place']}")
        st.markdown(f"**To:** {route_input['to_place']}")
        st.markdown(f"**Distance:** {route_result['route_distance_km']:.1f} km")

    with col2:
        st.markdown(f"**ETA:** {route_result['route_duration_min']:.0f} min")
        st.markdown(f"**Risk Score:** {route_result['weighted_score'] * 30:.1f}")

        risk = route_result["route_risk"]
        risk_class = f"risk-{risk.lower()}"
        st.markdown(
            f'<span class="risk-badge {risk_class}">{risk} Risk</span>',
            unsafe_allow_html=True,
        )


def render_current_alerts() -> None:
    st.subheader("Current Alerts")

    alerts = st.session_state.get("dashboard_alerts", [])

    if not alerts:
        st.markdown(
            '<div class="alert-box alert-blue">No active alerts right now. '
            'Alerts will appear here after route analysis.</div>',
            unsafe_allow_html=True,
        )
        return

    for alert in alerts[:5]:
        level = alert.get("level", "blue")
        message = alert.get("message", "Alert")
        st.markdown(
            f'<div class="alert-box alert-{level}">{message}</div>',
            unsafe_allow_html=True,
        )


def render_dashboard_page() -> None:
    st.title("Dashboard")

    st.subheader("System Overview")

    stats = load_dashboard_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Routes Analyzed", str(stats["routes_analyzed"]), "Accident Records in Dataset")
    with col2:
        render_metric_card("High Risk Routes", str(stats["high_risk_routes"]), "Historical Routes with High Risk")
    with col3:
        render_metric_card("Hotspots Identified", str(stats["hotspots_identified"]), "Accident Hotspots in Dataset")
    with col4:
        render_metric_card("Active Alerts", str(stats["active_alerts"]), "Current Active Travel Alerts")

    st.divider()

    left_col, right_col = st.columns([1.1, 0.9])

    with left_col:
        render_latest_route_analysis()

    with right_col:
        render_current_alerts()

    st.divider()
