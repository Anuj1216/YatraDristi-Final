from src.database.connection import get_connection


def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS travel_plans (

        id INT AUTO_INCREMENT PRIMARY KEY,

        from_place VARCHAR(100),

        to_place VARCHAR(100),

        travel_date DATE,

        travel_time VARCHAR(30),

        vehicle VARCHAR(30),

        monitoring_status VARCHAR(30) DEFAULT 'Monitoring',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alert_logs (

        id INT AUTO_INCREMENT PRIMARY KEY,

        travel_plan_id INT,

        alert_type VARCHAR(100),

        severity VARCHAR(20),

        message TEXT,

        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(travel_plan_id)
        REFERENCES travel_plans(id)
        ON DELETE CASCADE

    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS route_history (

        id INT AUTO_INCREMENT PRIMARY KEY,

        from_place VARCHAR(100),

        to_place VARCHAR(100),

        travel_date DATE,

        travel_time VARCHAR(30),

        vehicle VARCHAR(30),

        route_risk VARCHAR(20),

        risk_score FLOAT,

        distance FLOAT,

        eta FLOAT,

        weather VARCHAR(100),

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    conn.commit()

    cursor.close()

    conn.close()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")