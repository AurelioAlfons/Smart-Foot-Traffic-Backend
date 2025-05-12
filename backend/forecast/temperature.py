# =====================================================
# 🌡️ Optimized Accurate Temperature Assignment
# ✅ Fetches real hourly temperature from Open-Meteo
# ✅ Uses batch UPDATEs for speed
# =====================================================

import mysql.connector
import logging
import requests
from datetime import datetime
from backend.config import DB_CONFIG
from backend.visualizer.utils.sensor_locations import LOCATION_COORDINATES

def assign_temperature(target_date):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        logging.info(f"🌡️ Assigning accurate temperature for {target_date}...")

        # 🔎 Get all distinct locations with NULL temperature
        cursor.execute("""
            SELECT DISTINCT pd.Location
            FROM processed_data pd
            JOIN weather_season_data wsd ON pd.Data_ID = wsd.Data_ID
            WHERE pd.Date = %s AND wsd.Temperature IS NULL
        """, (target_date,))
        locations = [row[0] for row in cursor.fetchall()]

        total_updated = 0

        for location in locations:
            lat, lon = LOCATION_COORDINATES.get(location, (-37.798, 144.888))
            date_str = target_date

            # 🌐 Fetch hourly temperature for this location/date
            url = (
                f"https://archive-api.open-meteo.com/v1/archive?"
                f"latitude={lat}&longitude={lon}&start_date={date_str}&end_date={date_str}"
                f"&hourly=temperature_2m&timezone=Australia/Melbourne"
            )
            response = requests.get(url)
            data = response.json()

            if "hourly" not in data or "temperature_2m" not in data["hourly"]:
                logging.warning(f"⚠️ No temperature data for {location} on {date_str}")
                continue

            time_map = dict(zip(data["hourly"]["time"], data["hourly"]["temperature_2m"]))

            for hour_ts, temp in time_map.items():
                if temp is None:
                    continue

                hour = hour_ts.split("T")[1] + ":00"

                # ⚡ Bulk update all matching rows at once
                cursor.execute("""
                    UPDATE weather_season_data wsd
                    JOIN processed_data pd ON pd.Data_ID = wsd.Data_ID
                    SET wsd.Temperature = %s
                    WHERE pd.Date = %s AND pd.Time = %s AND pd.Location = %s AND wsd.Temperature IS NULL
                """, (temp, target_date, hour, location))

                total_updated += cursor.rowcount

        conn.commit()
        cursor.close()
        conn.close()

        logging.info(f"✅ Assigned temperature to {total_updated} rows on {target_date}.")

    except Exception as e:
        logging.error(f"❌ Temperature assignment failed: {e}")
