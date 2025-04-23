# =====================================================
# 🌡️ MODULE: Assign Temperature
# Purpose: Use Open-Meteo API to fetch daily max temperature
# for each record in processed_data and update it in
# weather_season_data.Temperature
# =====================================================

import mysql.connector
import logging
import requests
from datetime import datetime
from backend.config import DB_CONFIG
from backend.visualizer.utils.sensor_locations import LOCATION_COORDINATES

# =====================================================
# 🌞 FUNCTION: Fetch and assign temperature from API
# =====================================================
def assign_temperature():
    try:
        # 🔌 Connect to MySQL
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info("🔌 Connected to MySQL")

        # 📥 Get all data rows from processed_data
        cursor.execute("SELECT Data_ID, Date, Location FROM processed_data")
        rows = cursor.fetchall()
        updated = 0
        temp_cache = {}

        # 🔁 Loop through each row
        for data_id, date, location in rows:
            try:
                if isinstance(date, str):
                    date = datetime.strptime(date, "%Y-%m-%d")
                date_str = date.strftime("%Y-%m-%d")

                # 📍 Get coordinates for location
                lat, lon = LOCATION_COORDINATES.get(location, (-37.798, 144.888))

                # ⚡ Avoid duplicate API calls with caching
                key = (date_str, location)
                if key not in temp_cache:
                    url = (
                        f"https://archive-api.open-meteo.com/v1/archive?"
                        f"latitude={lat}&longitude={lon}&start_date={date_str}&end_date={date_str}"
                        f"&daily=temperature_2m_max&timezone=Australia/Melbourne"
                    )
                    response = requests.get(url)
                    data = response.json()

                    if "daily" in data:
                        max_temp = round(data["daily"]["temperature_2m_max"][0], 1)
                    else:
                        max_temp = None

                    temp_cache[key] = max_temp
                else:
                    max_temp = temp_cache[key]

                # ✏️ Update temperature in DB
                cursor.execute("""
                    UPDATE weather_season_data
                    SET Temperature = %s
                    WHERE Data_ID = %s
                """, (max_temp, data_id))
                updated += 1

            except Exception as e:
                logging.warning(f"⚠️ Skipping Data_ID {data_id} — {e}")
                continue

        # 💾 Save all changes
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"🌡️ Assigned temperatures to {updated} entries.")

    except Exception as e:
        logging.error(f"❌ Failed to assign temperature — {e}")
