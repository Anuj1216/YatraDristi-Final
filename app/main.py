import streamlit as st

from src.config.settings import (
    APP_TITLE,
    APP_SUBTITLE,
    ASSETS_DIR,
    ensure_directories
)

from app.views.dashboard import render_dashboard_page
from app.views.route_analysis import render_route_analysis_page
from app.views.hotspots import render_hotspots_page
from app.views.alerts import render_alerts_page
from app.views.about import render_about_page


def load_local_css():

    css_file = ASSETS_DIR / "style.css"

    if css_file.exists():

        with open(css_file, "r", encoding="utf-8") as f:

            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )


def initialize_session_state():

    defaults = {

        "latest_route_result":None,
        "latest_route_input":None,
        "dashboard_alerts":[],
        "show_hotspot_map":True,
        "show_route_map":True,
        "hotspot_limit":200
    }

    for key,value in defaults.items():

        if key not in st.session_state:

            st.session_state[key]=value


def render_sidebar():

    with st.sidebar:

        st.markdown(
            """
            <div class='sidebar-title'>
                YatraDristi
            </div>

            <div class='sidebar-subtitle'>
                Intelligent Road Safety &
                Risk Prediction System
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("---")

        page=st.radio(
            "Navigation",

            [
                "📊 Dashboard",
                "🧭 Route Analysis",
                "🗺️ Hotspots",
                "🚨 Alerts",
                "ℹ️ About"
            ]
        )

        st.markdown("---")

        


    return page


def main():

    st.set_page_config(

        page_title=APP_TITLE,
        page_icon="🛣️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    ensure_directories()

    initialize_session_state()

    load_local_css()

    page=render_sidebar()

    if page=="📊 Dashboard":

        render_dashboard_page()

    elif page=="🧭 Route Analysis":

        render_route_analysis_page()

    elif page=="🗺️ Hotspots":

        render_hotspots_page()

    elif page=="🚨 Alerts":

        render_alerts_page()

    elif page=="ℹ️ About":

        render_about_page()


if __name__=="__main__":

    main()