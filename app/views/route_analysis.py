from __future__ import annotations

from datetime import date as dt_date, datetime
import streamlit as st
from streamlit_folium import st_folium

from src.config.settings import KNOWN_PLACE_OPTIONS
from src.inference.pipeline import run_forecast_route_risk_prediction_pipeline
from src.services.hotspot_service import create_route_hotspot_map


VEHICLE_OPTIONS = [
    "Motorcycle",
    "Car",
    "Bus",
    "Truck",
    "Tempo",
]

TIME_OPTIONS = [
    "00:00 - 03:00",
    "03:00 - 06:00",
    "06:00 - 09:00",
    "09:00 - 12:00",
    "12:00 - 15:00",
    "15:00 - 18:00",
    "18:00 - 21:00",
    "21:00 - 23:59",
]


def risk_badge_html(risk: str) -> str:
    risk_class = f"risk-{risk.lower()}"
    return f'<span class="risk-badge {risk_class}">{risk} Risk</span>'


def build_dashboard_alerts_from_route(route_result: dict) -> list[dict]:
    alerts: list[dict] = []

    if route_result["route_risk"] == "High":
        alerts.append({
            "level": "red",
            "message": "High-risk accident zone detected on one or more road segments.",
        })

    highest_segment = route_result.get("highest_segment_risk")
    if highest_segment:
        weather_desc = str(highest_segment.get("weather_description", "")).lower()
        visibility = highest_segment.get("visibility_m", 0)

        if "rain" in weather_desc:
            alerts.append({
                "level": "yellow",
                "message": "Rainfall may increase road slipperiness and braking distance.",
            })

        if isinstance(visibility, (int, float)) and visibility and visibility < 4000:
            alerts.append({
                "level": "blue",
                "message": "Drive carefully in low-visibility areas.",
            })

    return alerts[:5]


def render_prediction_summary(result: dict) -> None:
    st.subheader("Prediction Summary")

    highest_segment = result.get("highest_segment_risk") or {}
    weather_main = highest_segment.get("weather_main", "Unknown")
    weather_desc = highest_segment.get("weather_description", "unknown")

    col1, col2, col3, col4, col5 = st.columns(5)

    cards = [
        ("Overall Risk", result["route_risk"], "Risk class"),
        ("Risk Score", f"{result['weighted_score'] * 30:.1f}", "Aggregated route score"),
        ("Distance", f"{result['route_distance_km']:.1f} km", "Estimated trip length"),
        ("ETA", f"{result['route_duration_min']:.0f} min", "Estimated travel time"),
        ("Weather Condition", weather_main, weather_desc),
    ]

    for col, (title, value, subtext) in zip([col1, col2, col3, col4, col5], cards):
        with col:
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

    st.subheader("Risk Badge")
    st.markdown(risk_badge_html(result["route_risk"]), unsafe_allow_html=True)


def render_segmentwise_analysis(result: dict) -> None:
    st.subheader("Segment-Wise Risk Analysis")

    segments = result.get("segment_results", [])

    if not segments:
        st.info("No segment results available.")
        return

    for idx, segment in enumerate(segments):
        col1, col2, col3, col4 = st.columns([2.2, 1.2, 1.0, 1.0])

        with col1:
            st.markdown(f"**{idx + 1}. {segment['segment_name']}**")
            visibility_km = segment.get("visibility_m", 0) / 1000 if segment.get("visibility_m", 0) else 0
            st.markdown(
                f'<div class="small-muted">Weather: {segment["weather_main"]} | '
                f'Visibility: {visibility_km:.1f} km</div>',
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(risk_badge_html(segment["adjusted_risk"]), unsafe_allow_html=True)

        with col3:
            risk_score_map = {"Low": 1, "Medium": 2, "High": 3}
            score = risk_score_map.get(segment["adjusted_risk"], 1)

            st.markdown(f"**Risk Score:** {score}")

        with col4:
            st.markdown(f"**+Weather:** {segment['weather_adjustment_points']}")

        st.markdown('<div class="segment-row"></div>', unsafe_allow_html=True)


def render_route_map(result: dict) -> None:
    st.subheader("Route Map")

    try:
        route_map = create_route_hotspot_map(route_result=result)
        st_folium(
            route_map,
            width=None,
            height=650,
            returned_objects=[],
        )
    except Exception as exc:
        st.error(f"Route map failed: {exc}")


def render_recommendations(result: dict) -> None:
    st.subheader("Recommendations")

    recommendations = result.get("recommendations")
    if not recommendations:
        st.info("No recommendations available yet.")
        return

    st.markdown(
        f"""
        <div class="recommendation-card">
            <div class="recommendation-title">Travel Decision</div>
            <div class="recommendation-item">{recommendations["travel_decision"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="recommendation-card">
            <div class="recommendation-title">Route Summary</div>
            <div class="recommendation-item">{recommendations["summary"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        advice_html = "".join(
            [f'<div class="recommendation-item">• {item}</div>' for item in recommendations["travel_advice"]]
        )
        st.markdown(
            f"""
            <div class="recommendation-card">
                <div class="recommendation-title">Travel Advice</div>
                {advice_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        precautions_html = "".join(
            [f'<div class="recommendation-item">• {item}</div>' for item in recommendations["precautions"]]
        )
        st.markdown(
            f"""
            <div class="recommendation-card">
                <div class="recommendation-title">Precautions</div>
                {precautions_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    focus_html = "".join(
        [f'<div class="recommendation-item">• {item}</div>' for item in recommendations["segment_focus"]]
    )
    st.markdown(
        f"""
        <div class="recommendation-card">
            <div class="recommendation-title">Segment Focus</div>
            {focus_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_route_analysis_page() -> None:

    from datetime import datetime

    st.title("Route Risk Prediction")
    st.caption(
        "Enter source and destination to perform accident risk prediction."
    )

    with st.form(
        "route_analysis_form",
        clear_on_submit=False
    ):

        col1, col2 = st.columns(2)

        with col1:

            from_place = st.selectbox(
                "From",
                options=KNOWN_PLACE_OPTIONS,
                index=0
            )

            travel_date = st.date_input(
                "Travel Date",
                value=dt_date.today()
            )

        with col2:

            to_place = st.selectbox(
                "To",
                options=KNOWN_PLACE_OPTIONS,
                index=2
            )

            travel_time = st.selectbox(
                "Travel Time",
                options=TIME_OPTIONS,
                index=3
            )

        vehicle = st.selectbox(
            "Travel Vehicle",
            options=VEHICLE_OPTIONS,
            index=0
        )

        submitted = st.form_submit_button(
            "Predict Risk",
            use_container_width=True
        )

    # Do nothing until button pressed
    if submitted:

        if from_place == to_place:

            st.error(
                "From and To cannot be the same."
            )

            return


        current_datetime = datetime.now()

        start_time, end_time = [
            t.strip()
            for t in travel_time.split("-")
        ]

        start_datetime = datetime.strptime(
            f"{travel_date} {start_time}",
            "%Y-%m-%d %H:%M"
        )

        end_datetime = datetime.strptime(
            f"{travel_date} {end_time}",
            "%Y-%m-%d %H:%M"
        )

        if end_time == "23:59":

            end_datetime = end_datetime.replace(
                second=59
        )

        if current_datetime > end_datetime:

            st.error(
                "Selected travel time interval has already ended."
            )

            return

        route_input = {
            "from_place": from_place,
            "to_place": to_place,
            "travel_date": str(travel_date),
            "travel_time": travel_time,
            "vehicle": vehicle,
        }

        with st.spinner(
            "Analyzing route risk..."
        ):

            try:

                result = run_forecast_route_risk_prediction_pipeline(
                    from_place=from_place,
                    to_place=to_place,
                    journey_date=travel_date,
                    journey_time=travel_time,
                    vehicle_involved=vehicle.lower(),
                    reason="normal_travel",
                    segment_count=(
                        3
                        if {from_place, to_place}
                        ==
                        {"Biratnagar", "Itahari"}
                        else 5
                    ),
                )

                st.session_state[
                    "latest_route_result"
                ] = result

                st.session_state[
                    "latest_route_input"
                ] = route_input

                st.session_state[
                    "dashboard_alerts"
                ] = build_dashboard_alerts_from_route(
                    result
                )

            except Exception as exc:

                st.error(
                    f"Route analysis failed: {exc}"
                )

                return

    result = st.session_state.get(
        "latest_route_result"
    )

    if result is None:
        return

    render_prediction_summary(result)

    st.divider()

    render_segmentwise_analysis(result)

    st.divider()

    render_route_map(result)

    st.divider()

    render_recommendations(result)