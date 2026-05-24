import streamlit as st


def render_about_page() -> None:
    st.title("About YatraDristi")
    st.caption("System information and project details.")

    st.markdown(
        """
## What is YatraDristi?
YatraDristi is an intelligent road safety and risk prediction system built as a B.Sc. CSIT project.

## Core Logic
- Machine learning predicts base accident risk
- Weather conditions adjust the risk dynamically
- Routes are divided into segments
- Segment risk is aggregated into final route risk
- Historical accident hotspots are visualized on map

## Main Features
- Route risk prediction
- Segment-wise analysis
- Hotspot analysis
- Forecast-aware travel planning
- Dashboard-based system overview

## Technologies Used
- Python
- Streamlit
- Pandas / NumPy
- Scikit-learn
- Folium
- OpenWeather API
- OpenStreetMap / OSRM

## Future Enhancements
- SQLite-based alert saving
- AI-generated route safety recommendations
- Better travel-time suggestion engine
- FastAPI backend migration
"""
    )