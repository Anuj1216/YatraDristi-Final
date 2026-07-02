import streamlit as st

from src.config.settings import (
    KNOWN_PLACE_OPTIONS,
)

from src.services.travel_monitor import monitor_saved_trips

from src.services.alert_service import analyze_travel_plan

from src.database.travel_plan_repository import (
    save_travel_plan,
    get_all_travel_plans,
    delete_travel_plan,
    get_dashboard_statistics,
    get_latest_route_analysis,
    get_prediction_cache,
    get_notifications,
)

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


def render_summary_cards():

    stats = get_dashboard_statistics()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Saved Trips",
            stats["saved_trips"],
        )

    with c2:
        st.metric(
            "Active Alerts",
            stats["active_notifications"],
        )

    with c3:
        st.metric(
            "High Risk Alerts",
            stats["high_risk_alerts"],
        )

    with c4:
        st.metric(
            "Recommended Updates",
            stats["active_notifications"],
        )


def render_save_form():

    st.subheader("Save New Travel Plan")

    with st.form("save_trip"):

        col1, col2 = st.columns(2)

        with col1:

            from_place = st.selectbox(
                "From",
                KNOWN_PLACE_OPTIONS,
            )

            travel_date = st.date_input(
                "Travel Date",
            )

        with col2:

            to_place = st.selectbox(
                "To",
                KNOWN_PLACE_OPTIONS,
                index=2,
            )

            travel_time = st.selectbox(
                "Travel Time",
                TIME_OPTIONS,
                index=3,
            )

        vehicle = st.selectbox(
            "Vehicle",
            VEHICLE_OPTIONS,
        )

        submitted = st.form_submit_button(
            "Save Travel Plan",
            use_container_width=True,
        )

    if submitted:

        if from_place == to_place:

            st.error("Origin and destination cannot be the same.")

            return

        save_travel_plan(
            from_place,
            to_place,
            travel_date,
            travel_time,
            vehicle,
        )

        st.success("Travel plan saved successfully.")

        st.rerun()

def render_trip_header(plan):

    risk = plan.get("latest_risk") or "Not Analyzed"
    weather = plan.get("latest_weather") or "-"
    last = plan.get("last_analysis") or "Never"

    risk_class = {
        "High":"risk-high",
        "Medium":"risk-medium",
        "Low":"risk-low"
    }.get(risk,"risk-low")

    pill = {
        "High":"pill-high",
        "Medium":"pill-medium",
        "Low":"pill-low"
    }.get(risk,"pill-low")

    st.markdown(
        f"""
<div class="alert-card {risk_class}">

<div class="route-title">
📍 {plan['from_place']} → {plan['to_place']}
</div>

<div class="route-info">
🚗 {plan['vehicle']}
</div>

<div class="route-info">
📅 {plan['travel_date']}
</div>

<div class="route-info">
🕒 {plan['travel_time']}
</div>

<div class="route-info">
🌤 {weather}
</div>

<div style="margin-top:10px;">

<span class="risk-pill {pill}">
{risk} Risk
</span>

&nbsp;&nbsp;

🟢 Monitoring

</div>

<div class="last-analysis">

Last Analysis : {last}

</div>

</div>
""",
        unsafe_allow_html=True,
    )

def get_travel_status(plan):

    risk = plan.get("latest_risk")

    if risk == "Low":
        return (
            "🟢 Safe to Travel",
            "success",
        )

    if risk == "Medium":
        return (
            "🟡 Travel with Caution",
            "warning",
        )

    if risk == "High":
        return (
            "🔴 Avoid Travel",
            "error",
        )

    return (
        "⚪ Pending Analysis",
        "info",
    )

def render_saved_trips():

    st.subheader("Saved Travel Plans")

    plans = get_all_travel_plans()

    if not plans:
        st.info("No travel plans have been saved.")
        return

    for plan in plans:

        risk = plan.get("latest_risk") or "Not Analyzed"
        weather = plan.get("latest_weather") or "-"
        last_analysis = plan.get("last_analysis")

        if risk == "High":
            risk_color = "🔴"
        elif risk == "Medium":
            risk_color = "🟠"
        elif risk == "Low":
            risk_color = "🟢"
        else:
            risk_color = "⚪"

        with st.container(border=True):

            st.markdown(
                f"## 📍 {plan['from_place']} → {plan['to_place']}"
            )

            info1, info2 = st.columns(2)

            with info1:

                st.write(f"🚗 **Vehicle:** {plan['vehicle']}")
                st.write(f"📅 **Date:** {plan['travel_date']}")
                st.write(f"🕒 **Time:** {plan['travel_time']}")

            with info2:

                status_text, status_type = get_travel_status(plan)

                if status_type == "success":
                    st.success(status_text)

                elif status_type == "warning":
                    st.warning(status_text)

                elif status_type == "error":
                    st.error(status_text)

                else:
                    st.info(status_text)

                st.write(f"**Current Risk:** {risk_color} {risk}")
                st.write(f"**Weather:** {weather}")

                if last_analysis:
                    st.write(f"**Last Analysis:** {last_analysis}")
                else:
                    st.write("**Last Analysis:** Never")

            st.divider()

            b1, b2, b3, b4 = st.columns(4)

            with b1:

                analyze = st.button(
                    "Analyze",
                    key=f"analyze_{plan['id']}",
                    use_container_width=True,
                )

            with b2:

                details = st.button(
                    "View Details",
                    key=f"details_{plan['id']}",
                    use_container_width=True,
                )

            with b3:

                st.button(
                    "Edit",
                    key=f"edit_{plan['id']}",
                    use_container_width=True,
                )

            with b4:

                delete = st.button(
                    "Delete",
                    key=f"delete_{plan['id']}",
                    use_container_width=True,
                )

            if analyze:

                with st.spinner("Analyzing route..."):

                    analysis = analyze_travel_plan(plan)

                st.session_state[f"analysis_{plan['id']}"] = analysis

                st.rerun()

            if delete:

                delete_travel_plan(plan["id"])

                st.rerun()

            if details:

                st.session_state[f"show_details_{plan['id']}"] = True

            if st.session_state.get(f"show_details_{plan['id']}", False):

                prediction = get_prediction_cache(
                    plan["id"]
                )

                if prediction is None:

                    st.info(
                        "Run Analyze first to generate detailed prediction."
                    )

                else:

                    st.divider()

                    c1, c2, c3, c4 = st.columns(4)

                    with c1:
                        st.metric(
                            "Overall Risk",
                            prediction["route_risk"],
                        )

                    with c2:
                        st.metric(
                            "Distance",
                            f"{prediction['route_distance_km']:.1f} km",
                        )

                    with c3:
                        st.metric(
                            "ETA",
                            f"{prediction['route_duration_min']:.0f} min",
                        )

                    with c4:
                        st.metric(
                            "Weather",
                            prediction["highest_segment_risk"]["weather_main"],
                        )

                    st.success(
                        prediction["recommendations"]["travel_decision"]
                    )

                    latest = get_latest_route_analysis(
                        plan["id"]
                    )

                    if latest:

                        st.subheader("Latest Analysis")

                        if latest["route_risk"] == "High":
                            st.error("High accident probability detected.")

                        elif latest["route_risk"] == "Medium":
                            st.warning("Moderate accident probability detected.")

                        else:
                            st.success("Current route conditions appear safe.")


def render_notification_center():

    st.subheader("Recent Notifications")

    notifications = get_notifications()

    if not notifications:
        st.info("No notifications available.")
        return

    for notification in notifications:

        title = notification["title"]
        message = notification["message"]
        severity = notification["severity"]
        created = notification["created_at"]

        if severity == "High":
            st.error(f"**{title}**\n\n{message}\n\n{created}")

        elif severity == "Medium":
            st.warning(f"**{title}**\n\n{message}\n\n{created}")

        else:
            st.info(f"**{title}**\n\n{message}\n\n{created}")

def render_alerts_page():

    monitor_saved_trips()

    st.title("Travel Alerts")

    st.caption(
        "Save your future travel plans and let YatraDristi monitor them continuously."
    )

    render_summary_cards()

    st.divider()

    render_save_form()

    st.divider()

    render_saved_trips()

    st.divider()

    render_notification_center()