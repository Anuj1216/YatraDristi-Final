import streamlit as st


def render_about_page() -> None:

    st.title("About YatraDristi")

    st.caption(
        "An Intelligent Road Safety and Accident Risk Prediction System"
    )

    st.divider()

    st.header("Project Overview")

    st.write(
        """
YatraDristi is an AI-powered road safety application developed as a B.Sc. CSIT
7th Semester Major Project. The system predicts accident risk for travel routes
by combining historical accident records, live weather conditions, and
route information. It assists travelers in making safer travel decisions by
providing route risk analysis, hotspot visualization, and intelligent travel
recommendations.
        """
    )

    st.divider()

    st.header("Objectives")

    st.markdown(
        """
- Predict accident risk for selected travel routes.
- Visualize accident hotspot locations.
- Analyze segment-wise route risk.
- Integrate real-time weather information.
- Recommend safer travel decisions.
- Monitor saved travel plans and generate alerts.
        """
    )

    st.divider()

    st.header("Major Features")

    col1, col2 = st.columns(2)

    with col1:

        st.success("Route Risk Prediction")

        st.success("Accident Hotspot Mapping")

        st.success("Live Weather Integration")

        st.success("Segment-wise Risk Analysis")

    with col2:

        st.success("Travel Monitoring")

        st.success("AI Travel Recommendations")

        st.success("Saved Travel Alerts")

        st.success("Interactive Route Maps")

    st.divider()

    st.header("Technology Stack")

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            """
**Frontend**
- Streamlit

**Backend**
- Python

**Database**
- MySQL
            """
        )

    with c2:

        st.markdown(
            """
**Machine Learning**
- XGBoost Classifier

**Maps**
- Folium
- OpenRouteService

**Weather**
- OpenWeather API
            """
        )

    st.divider()

    st.header("Dataset")

    st.write(
        """
The prediction model is trained using Nepal road accident data enriched through
feature engineering. Important attributes include:

• Location

• Date and Time

• Vehicle Type

• Accident Cause

• Weather Information

• Latitude & Longitude

The trained model predicts the base accident risk, which is further adjusted
using current weather conditions to estimate the final travel risk.
        """
    )

    st.divider()

    st.header("System Workflow")

    st.markdown(
        """
1. User selects origin and destination.

2. Route is generated.

3. Route is divided into segments.

4. Weather data is collected for each segment.

5. Machine learning predicts accident risk.

6. Weather adjustment is applied.

7. Overall route risk is calculated.

8. Recommendations and alerts are generated.
        """
    )

    st.divider()

    st.header("Project Information")

    c1, c2 = st.columns(2)

    with c1:

        st.metric(
            "Version",
            "1.0"
        )

        st.metric(
            "Project Type",
            "Major Project"
        )

    with c2:

        st.metric(
            "Degree",
            "B.Sc. CSIT"
        )

        st.metric(
            "Semester",
            "7th Semester"
        )

    st.divider()

    st.info(
        "YatraDristi is developed for educational and research purposes to support safer travel through data-driven accident risk prediction."
    )