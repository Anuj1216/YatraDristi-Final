import streamlit as st


def render_alerts_page() -> None:
    st.title("Alerts")
    st.caption("Saved travel alerts and route warning management.")

    st.info(
        "This page will store saved travel details and generate risk alerts such as "
        "High Risk, Caution, and Better Travel Time."
    )

    st.markdown(
        """
Planned next logic:
- save travel details in SQLite
- compare saved trip with forecast route risk
- show active travel alerts
- suggest better travel windows
"""
    )