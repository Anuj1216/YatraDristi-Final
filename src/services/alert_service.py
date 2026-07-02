from src.database.travel_plan_repository import (
    save_alert,
    save_notification,
    save_route_analysis,
    save_prediction_cache,
    update_travel_plan_status,
    notification_exists,
)

from src.inference.pipeline import (
    run_forecast_route_risk_prediction_pipeline,
)


def analyze_travel_plan(plan):

    prediction = run_forecast_route_risk_prediction_pipeline(
        from_place=plan["from_place"],
        to_place=plan["to_place"],
        journey_date=plan["travel_date"],
        journey_time=plan["travel_time"],
        vehicle_involved=plan["vehicle"].lower(),
        reason="saved_trip",
    )

    save_route_analysis(
        travel_plan_id=plan["id"],
        prediction=prediction,
    )

    save_prediction_cache(
        travel_plan_id=plan["id"],
        prediction=prediction,
    )

    highest = prediction["highest_segment_risk"]

    update_travel_plan_status(
        travel_plan_id=plan["id"],
        latest_risk=prediction["route_risk"],
        latest_weather=highest["weather_main"],
    )

    alerts = []

    if prediction["route_risk"] == "High":

        alerts.append(
            {
                "title": "High Route Risk",
                "severity": "High",
                "message": "This route currently has a high accident probability.",
            }
        )

    elif prediction["route_risk"] == "Medium":

        alerts.append(
            {
                "title": "Moderate Route Risk",
                "severity": "Medium",
                "message": "Drive carefully because the accident probability is moderate.",
            }
        )

    weather_desc = highest["weather_description"].lower()

    if "rain" in weather_desc or "drizzle" in weather_desc:

        alerts.append(
            {
                "title": "Rain Expected",
                "severity": "Medium",
                "message": "Rain may reduce road grip and increase braking distance.",
            }
        )

    visibility = highest["visibility_m"]

    if visibility and visibility < 4000:

        alerts.append(
            {
                "title": "Low Visibility",
                "severity": "High",
                "message": "Low visibility detected on this route.",
            }
        )

    recommendation = prediction["recommendations"]["travel_decision"]

    for alert in alerts:

        save_alert(
            travel_plan_id=plan["id"],
            alert_type=alert["title"],
            severity=alert["severity"],
            message=alert["message"],
        )

        if not notification_exists(
            plan["id"],
            alert["title"],
            alert["message"],
        ):

            save_notification(
                travel_plan_id=plan["id"],
                title=alert["title"],
                message=alert["message"],
                severity=alert["severity"],
            )

    return {
        "prediction": prediction,
        "alerts": alerts,
        "recommendation": recommendation,
    }