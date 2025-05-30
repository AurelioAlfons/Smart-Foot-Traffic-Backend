# ===========================================================
# Assign Real Temperature from Open-Meteo (Optimized)
# -----------------------------------------------------------
# - Gets hourly temperature from Open-Meteo API
# - Matches by date, time, and location
# - Batch updates with lock retry logic (for stability)
# ===========================================================

import mysql.connector
import requests
import time
from backend.config import DB_CONFIG
from backend.visualizer.map_components.sensor_locations import LOCATION_COORDINATES

def safe_execute_with_retry(cursor, query, params, retries=2, delay=2):
    for attempt in range(retries + 1):
        try:
            cursor.execute(query, params)
            return True
        except mysql.connector.Error as e:
            if e.errno == 1205:  # Lock wait timeout
                time.sleep(delay)
            else:
                raise
    return False

def assign_temperature(target_date):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Get all distinct locations with NULL temperature
        cursor.execute("""
            SELECT DISTINCT pd.Location
            FROM processed_data pd
            JOIN weather_season_data wsd ON pd.Data_ID = wsd.Data_ID
            WHERE pd.Date = %s AND wsd.Temperature IS NULL
        """, (target_date,))
        locations = [row[0] for row in cursor.fetchall()]

        if not locations:
            return

        total_updated = 0

        for location in locations:
            lat, lon = LOCATION_COORDINATES.get(location, (-37.798, 144.888))
            url = (
                f"https://archive-api.open-meteo.com/v1/archive?"
                f"latitude={lat}&longitude={lon}&start_date={target_date}&end_date={target_date}"
                f"&hourly=temperature_2m&timezone=Australia/Melbourne"
            )
            try:
                response = requests.get(url, timeout=10)
                data = response.json()

                if "hourly" not in data or "temperature_2m" not in data["hourly"]:
                    continue

                time_map = dict(zip(data["hourly"]["time"], data["hourly"]["temperature_2m"]))

                for hour_ts, temp in time_map.items():
                    if temp is None:
                        continue

                    hour = hour_ts.split("T")[1] + ":00"

                    safe_execute_with_retry(cursor, """
                        UPDATE weather_season_data wsd
                        JOIN processed_data pd ON pd.Data_ID = wsd.Data_ID
                        SET wsd.Temperature = %s
                        WHERE pd.Date = %s AND pd.Time = %s AND pd.Location = %s AND wsd.Temperature IS NULL
                    """, (temp, target_date, hour, location))

                    total_updated += cursor.rowcount

            except Exception:
                continue

        conn.commit()
        cursor.close()
        conn.close()

    except Exception:
        pass  # Silent fail for background use
