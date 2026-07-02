from datetime import datetime, date, timedelta

from src.database.travel_plan_repository import (
    get_all_travel_plans,
    update_travel_plan_status,
)

from src.services.alert_service import analyze_travel_plan


def monitor_saved_trips():

    plans = get_all_travel_plans()

    today = date.today()
    tomorrow = today + timedelta(days=1)

    for plan in plans:

        travel_date = plan["travel_date"]

        if travel_date not in [today, tomorrow]:
            continue

        last_analysis = plan["last_analysis"]

        if last_analysis is not None:
            hours = (datetime.now() - last_analysis).total_seconds() / 3600

            if hours < 3:
                continue

        analysis = analyze_travel_plan(plan)

        prediction = analysis["prediction"]

        update_travel_plan_status(
            travel_plan_id=plan["id"],
            latest_risk=prediction["route_risk"],
            latest_weather=prediction["highest_segment_risk"]["weather_main"],
        )