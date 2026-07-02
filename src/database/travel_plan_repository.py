from src.database.connection import get_connection

import json

def save_travel_plan(
    from_place,
    to_place,
    travel_date,
    travel_time,
    vehicle,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO travel_plans
        (
            from_place,
            to_place,
            travel_date,
            travel_time,
            vehicle
        )
        VALUES (%s,%s,%s,%s,%s)
        """,
        (
            from_place,
            to_place,
            travel_date,
            travel_time,
            vehicle,
        ),
    )

    conn.commit()

    travel_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return travel_id


def get_all_travel_plans():

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM travel_plans
        ORDER BY created_at DESC
        """
    )

    plans = cursor.fetchall()

    cursor.close()
    conn.close()

    return plans


def get_travel_plan(plan_id):

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM travel_plans
        WHERE id=%s
        """,
        (plan_id,),
    )

    plan = cursor.fetchone()

    cursor.close()
    conn.close()

    return plan


def delete_travel_plan(plan_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM travel_plans
        WHERE id=%s
        """,
        (plan_id,),
    )

    conn.commit()

    cursor.close()
    conn.close()


def save_alert(
    travel_plan_id,
    alert_type,
    severity,
    message,
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO alert_logs
        (
            travel_plan_id,
            alert_type,
            severity,
            message
        )
        VALUES (%s,%s,%s,%s)
        """,
        (
            travel_plan_id,
            alert_type,
            severity,
            message,
        ),
    )

    conn.commit()

    cursor.close()
    conn.close()


def get_alerts(plan_id):

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM alert_logs
        WHERE travel_plan_id=%s
        ORDER BY generated_at DESC
        """,
        (plan_id,),
    )

    alerts = cursor.fetchall()

    cursor.close()
    conn.close()

    return alerts

def save_notification(
    travel_plan_id,
    title,
    message,
    severity,
):
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO travel_notifications
        (
            travel_plan_id,
            title,
            message,
            severity
        )
        VALUES (%s,%s,%s,%s)
        """,
        (
            travel_plan_id,
            title,
            message,
            severity,
        ),
    )

    conn.commit()

    cursor.close()
    conn.close()


def get_notifications():

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM travel_notifications
        ORDER BY created_at DESC
        """
    )

    notifications = cursor.fetchall()

    cursor.close()
    conn.close()

    return notifications


def mark_notification_read(notification_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE travel_notifications
        SET is_read=1
        WHERE id=%s
        """,
        (notification_id,),
    )

    conn.commit()

    cursor.close()
    conn.close()


def get_dashboard_statistics():

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT COUNT(*) AS total FROM travel_plans"
    )
    saved_trips = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM travel_notifications
        WHERE is_read=0
        """
    )
    active_notifications = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM alert_logs
        WHERE severity='High'
        """
    )
    high_risk_alerts = cursor.fetchone()["total"]

    cursor.close()
    conn.close()

    return {
        "saved_trips": saved_trips,
        "active_notifications": active_notifications,
        "high_risk_alerts": high_risk_alerts,
    }

def analysis_exists(travel_plan_id):

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id
        FROM route_history
        WHERE travel_plan_id=%s
        LIMIT 1
        """,
        (travel_plan_id,),
    )

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row is not None

def delete_old_analysis(travel_plan_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM route_history
        WHERE travel_plan_id=%s
        """,
        (travel_plan_id,),
    )

    conn.commit()

    cursor.close()
    conn.close()


def save_route_analysis(
    travel_plan_id,
    prediction,
):

    delete_old_analysis(travel_plan_id)

    conn = get_connection()

    cursor = conn.cursor()

    highest = prediction["highest_segment_risk"]

    cursor.execute(
        """
        INSERT INTO route_history
        (
            travel_plan_id,
            route_risk,
            risk_score,
            weather_main,
            weather_description,
            visibility_m,
            route_distance_km,
            route_duration_min,
            recommendation
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,%s,%s
        )
        """,
        (
            travel_plan_id,
            prediction["route_risk"],
            prediction["weighted_score"],
            highest["weather_main"],
            highest["weather_description"],
            highest["visibility_m"],
            prediction["route_distance_km"],
            prediction["route_duration_min"],
            prediction["recommendations"]["travel_decision"],
        ),
    )

    conn.commit()

    cursor.close()
    conn.close()


def get_latest_route_analysis(travel_plan_id):

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM route_history
        WHERE travel_plan_id=%s
        ORDER BY analyzed_at DESC
        LIMIT 1
        """,
        (travel_plan_id,),
    )

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row

def update_travel_plan_status(
    travel_plan_id,
    latest_risk,
    latest_weather,
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE travel_plans
        SET
            latest_risk=%s,
            latest_weather=%s,
            last_analysis=NOW()
        WHERE id=%s
        """,
        (
            latest_risk,
            latest_weather,
            travel_plan_id,
        ),
    )

    conn.commit()

    cursor.close()
    conn.close()

def get_latest_route_analysis(travel_plan_id):

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM route_history
        WHERE travel_plan_id=%s
        ORDER BY analyzed_at DESC
        LIMIT 1
        """,
        (travel_plan_id,),
    )

    analysis = cursor.fetchone()

    cursor.close()
    conn.close()

    return analysis


def save_prediction_cache(
    travel_plan_id,
    prediction,
):

    conn = get_connection()

    cursor = conn.cursor()

    prediction_json = json.dumps(
        prediction,
        default=str,
    )

    cursor.execute(
        """
        INSERT INTO route_prediction_cache
        (
            travel_plan_id,
            prediction_json
        )
        VALUES
        (
            %s,%s
        )
        ON DUPLICATE KEY UPDATE

        prediction_json=VALUES(prediction_json),
        updated_at=NOW()
        """,
        (
            travel_plan_id,
            prediction_json,
        ),
    )

    conn.commit()

    cursor.close()
    conn.close()

def get_prediction_cache(
    travel_plan_id,
):

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT prediction_json
        FROM route_prediction_cache
        WHERE travel_plan_id=%s
        """,
        (
            travel_plan_id,
        ),
    )

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row is None:
        return None

    return json.loads(
        row["prediction_json"]
    )

def notification_exists(
    travel_plan_id,
    title,
    message,
):

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id
        FROM travel_notifications
        WHERE
            travel_plan_id=%s
            AND title=%s
            AND message=%s
            AND DATE(created_at)=CURDATE()
        LIMIT 1
        """,
        (
            travel_plan_id,
            title,
            message,
        ),
    )

    exists = cursor.fetchone() is not None

    cursor.close()
    conn.close()

    return exists


def get_latest_dashboard_analysis():

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            tp.from_place,
            tp.to_place,
            tp.travel_date,
            tp.travel_time,
            tp.vehicle,
            rh.route_risk,
            rh.risk_score,
            rh.route_distance_km AS distance,
            rh.route_duration_min AS eta,
            rh.weather_main AS weather,
            rh.analyzed_at AS created_at
        FROM route_history rh
        JOIN travel_plans tp
            ON rh.travel_plan_id = tp.id
        ORDER BY rh.analyzed_at DESC
        LIMIT 1
        """
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result