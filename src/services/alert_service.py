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

    has_rain = False
    low_visibility = False

    for segment in prediction["segment_results"]:

        weather_desc = str(segment["weather_description"]).lower()

        if "rain" in weather_desc or "drizzle" in weather_desc:
            has_rain = True

        visibility = segment.get("visibility_m", 0)

        if visibility and visibility < 4000:
            low_visibility = True


    if has_rain:

        alerts.append(
            {
                "title": "Rain Expected",
                "severity": "Medium",
                "message": "Rain is expected on one or more route segments. Drive carefully.",
            }
        )


    if low_visibility:

        alerts.append(
            {
                "title": "Low Visibility",
                "severity": "High",
                "message": "Low visibility detected on one or more route segments.",
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