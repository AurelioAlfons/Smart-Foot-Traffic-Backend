# =====================================================
# 🌡️ MODULE: Assign Temperature (Filtered by Date)
# Purpose: Use Open-Meteo API to fetch max temp for
# specific date entries where temp is NULL
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
        # 🔌 Connect to DB
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info(f"🌡️ Assigning temperature for {target_date}...")

        # 📥 Fetch only records for the target date where temp is missing
        cursor.execute("""
            SELECT pd.Data_ID, pd.Date, pd.Location
            FROM processed_data pd
            JOIN weather_season_data wsd ON pd.Data_ID = wsd.Data_ID
            WHERE pd.Date = %s AND wsd.Temperature IS NULL
        """, (target_date,))
        
        rows = cursor.fetchall()
        updated = 0
        temp_cache = {}

        for data_id, date, location in rows:
            try:
                if isinstance(date, str):
                    date = datetime.strptime(date, "%Y-%m-%d")
                date_str = date.strftime("%Y-%m-%d")

                # 📍 Get lat/lon for the location
                lat, lon = LOCATION_COORDINATES.get(location, (-37.798, 144.888))

                # ⚡ Cache to avoid duplicate API calls
                key = (date_str, location)
                if key not in temp_cache:
                    url = (
                        f"https://archive-api.open-meteo.com/v1/archive?"
                        f"latitude={lat}&longitude={lon}&start_date={date_str}&end_date={date_str}"
                        f"&daily=temperature_2m_max&timezone=Australia/Melbourne"
                    )
                    response = requests.get(url)
                    data = response.json()

                    if "daily" in data and data["daily"].get("temperature_2m_max"):
                        max_temp = round(data["daily"]["temperature_2m_max"][0], 1)
                    else:
                        max_temp = None

                    temp_cache[key] = max_temp
                else:
                    max_temp = temp_cache[key]

                # 📝 Update the DB
                cursor.execute("""
                    UPDATE weather_season_data
                    SET Temperature = %s
                    WHERE Data_ID = %s
                """, (max_temp, data_id))
                updated += 1

            except Exception as e:
                logging.warning(f"⚠️ Skipping Data_ID {data_id} — {e}")
                continue

        # 💾 Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"✅ Temperature assigned for {updated} rows on {target_date}.")

    except Exception as e:
        logging.error(f"❌ Failed to assign temperature — {e}")
