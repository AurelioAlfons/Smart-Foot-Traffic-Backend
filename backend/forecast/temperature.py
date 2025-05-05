# =====================================================
# 🌡️ MODULE: Assign Temperature (Filtered by Date)
# Purpose: Fetch hourly temperature using Open-Meteo API
# and assign it based on exact hour for rows with NULL temp
# =====================================================

import mysql.connector
import logging
import requests
from datetime import datetime
from backend.config import DB_CONFIG
from backend.visualizer.utils.sensor_locations import LOCATION_COORDINATES

# =====================================================
# 🌞 FUNCTION: Assign temperature for a specific date only
# =====================================================
def assign_temperature(target_date):
    try:
        # 🔌 Connect to the MySQL database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info(f"🌡️ Assigning hourly temperature for {target_date}...")

        # 📥 Fetch records on the selected date where temperature is missing
        cursor.execute("""
            SELECT pd.Data_ID, pd.Date, pd.Time, pd.Location
            FROM processed_data pd
            JOIN weather_season_data wsd ON pd.Data_ID = wsd.Data_ID
            WHERE pd.Date = %s AND wsd.Temperature IS NULL
        """, (target_date,))
        
        rows = cursor.fetchall()
        updated = 0
        temp_cache = {}

        for data_id, date, time, location in rows:
            try:
                # 🗓️ Format date
                if isinstance(date, str):
                    date = datetime.strptime(date, "%Y-%m-%d")
                date_str = date.strftime("%Y-%m-%d")

                # 🕒 Format time into HH:00
                if isinstance(time, str):
                    hour_str = datetime.strptime(time, "%H:%M:%S").strftime("%H:00")
                else:
                    # ✅ Handle MySQL TIME returned as timedelta
                    hour_str = f"{int(time.total_seconds() // 3600):02d}:00"

                target_timestamp = f"{date_str}T{hour_str}"  # e.g., 2025-03-03T21:00

                # 📍 Get coordinates for the location
                lat, lon = LOCATION_COORDINATES.get(location, (-37.798, 144.888))
                key = (date_str, location)

                # 🌐 Fetch API data if not cached
                if key not in temp_cache:
                    url = (
                        f"https://archive-api.open-meteo.com/v1/archive?"
                        f"latitude={lat}&longitude={lon}&start_date={date_str}&end_date={date_str}"
                        f"&hourly=temperature_2m&timezone=Australia/Melbourne"
                    )
                    response = requests.get(url)
                    data = response.json()

                    if "hourly" in data and "temperature_2m" in data["hourly"]:
                        times = data["hourly"]["time"]
                        temps = data["hourly"]["temperature_2m"]
                        temp_cache[key] = dict(zip(times, temps))
                    else:
                        logging.warning(f"⚠️ No hourly temperature data for {location} on {date_str}")
                        temp_cache[key] = {}

                # 🌡️ Get temperature for this hour
                hourly_temp = temp_cache[key].get(target_timestamp)

                # 💾 Update the DB
                cursor.execute("""
                    UPDATE weather_season_data
                    SET Temperature = %s
                    WHERE Data_ID = %s
                """, (hourly_temp, data_id))
                updated += 1

            except Exception as e:
                logging.warning(f"⚠️ Skipping Data_ID {data_id} — {e}")
                continue

        # ✅ Save changes and close
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"✅ Temperature assigned for {updated} rows on {target_date}.")

    except Exception as e:
        logging.error(f"❌ Failed to assign temperature — {e}")
