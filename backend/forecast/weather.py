# =====================================================
# 🌤️ MODULE: Assign Weather (Filtered by Date)
# Purpose: Fetch historical weather (e.g. Clear, Rain)
# using Open-Meteo API, and update only records from
# a specific date where Weather = 'Undefined'
# =====================================================

import mysql.connector
import logging
import requests
from datetime import datetime
from backend.config import DB_CONFIG
from backend.visualizer.utils.sensor_locations import LOCATION_COORDINATES

# =====================================================
# 🗺️ FUNCTION: Convert weather code to readable label
# =====================================================
def get_weather_label(code):
    weather_map = {
        0: "Clear", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
        45: "Fog", 48: "Rime Fog", 51: "Light Drizzle", 61: "Light Rain",
        71: "Light Snow", 80: "Rain Showers", 95: "Thunderstorm"
    }
    return weather_map.get(code, "Unknown")

# =====================================================
# 🌦️ FUNCTION: Assign weather for a specific date only
# =====================================================
def assign_weather(target_date):
    try:
        # 🔌 Connect to DB
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info(f"🔍 Assigning weather for {target_date}...")

        # 🗃️ Only select rows with undefined weather for that date
        cursor.execute("""
            SELECT pd.Data_ID, pd.Date, pd.Location
            FROM processed_data pd
            JOIN weather_season_data wsd ON pd.Data_ID = wsd.Data_ID
            WHERE pd.Date = %s AND wsd.Weather = 'Undefined'
        """, (target_date,))
        
        rows = cursor.fetchall()
        updated = 0
        weather_cache = {}

        for data_id, date, location in rows:
            try:
                # ⏱️ Normalize date format
                if isinstance(date, str):
                    date = datetime.strptime(date, "%Y-%m-%d")
                date_str = date.strftime("%Y-%m-%d")

                # 📍 Get lat/lon for location
                lat, lon = LOCATION_COORDINATES.get(location, (-37.798, 144.888))

                # 🚀 Avoid duplicate API calls
                key = (date_str, location)
                if key not in weather_cache:
                    url = (
                        f"https://archive-api.open-meteo.com/v1/archive?"
                        f"latitude={lat}&longitude={lon}&start_date={date_str}&end_date={date_str}"
                        f"&daily=weathercode&timezone=Australia/Melbourne"
                    )
                    response = requests.get(url)
                    data = response.json()

                    if "daily" in data and data["daily"].get("weathercode"):
                        code = data["daily"]["weathercode"][0]
                        weather = get_weather_label(code)
                    else:
                        weather = "Unknown"

                    weather_cache[key] = weather
                else:
                    weather = weather_cache[key]

                # ✏️ Update the weather in DB
                cursor.execute("""
                    UPDATE weather_season_data
                    SET Weather = %s
                    WHERE Data_ID = %s
                """, (weather, data_id))
                updated += 1

            except Exception as e:
                logging.warning(f"⚠️ Skipped Data_ID {data_id} — {e}")
                continue

        # 💾 Commit and cleanup
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"✅ Weather assigned for {updated} entries on {target_date}.")

    except Exception as e:
        logging.error(f"❌ Failed to assign weather — {e}")
