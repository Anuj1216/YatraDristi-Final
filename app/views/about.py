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
- RandomForestClassifier

**Maps**
- Folium
- OpenRouteService

**Weather**
- OpenWeather API
            """
        )

    st.divider()

    st.header("Project Supervisor & Team")

    col1, col2 = st.columns(2)

    with col1:
        st.info(
            """
### 👨‍🏫 Project Supervisor

**Er. Sushant Bhattarai**

Department of Computer Science and Information Technology
(Mahendra Morang Adarsha Multiple Campus, Biratnagar)
            """
        )

    with col2:
        st.info(
            """
### 👥 Project Team

**Team Members:**

1. Anuj Acharya
2. Suchana Chapagain
            """
        )


