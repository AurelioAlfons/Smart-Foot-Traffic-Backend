# =====================================================
# 🌤️ MODULE: Assign Weather
# Purpose: Fetch historical weather conditions (e.g. Clear, Rain)
# using Open-Meteo's API and update the Weather column
# in weather_season_data table.
# =====================================================

import mysql.connector
import logging
import requests
from datetime import datetime
from backend.config import DB_CONFIG
from backend.visualizer.utils.sensor_locations import LOCATION_COORDINATES

# =====================================================
# 🗺️ FUNCTION: Get readable weather label from weather code
# =====================================================
def get_weather_label(code):
    weather_map = {
        0: "Clear", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
        45: "Fog", 48: "Rime Fog", 51: "Light Drizzle", 61: "Light Rain",
        71: "Light Snow", 80: "Rain Showers", 95: "Thunderstorm"
    }
    return weather_map.get(code, "Unknown")

# =====================================================
# 🌦️ FUNCTION: Fetch and assign weather to each data point
# =====================================================
def assign_weather():
    try:
        # 🔌 Connect to DB
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info("🔌 Connected to MySQL")

        # 📥 Get all data points
        cursor.execute("SELECT Data_ID, Date, Location FROM processed_data")
        rows = cursor.fetchall()
        updated = 0
        weather_cache = {}

        # 🔁 Process each row
        for data_id, date, location in rows:
            try:
                if isinstance(date, str):
                    date = datetime.strptime(date, "%Y-%m-%d")
                date_str = date.strftime("%Y-%m-%d")

                # 📍 Get lat/lon from known sensor locations
                lat, lon = LOCATION_COORDINATES.get(location, (-37.798, 144.888))

                # ⚡ Cache API calls per date-location combo
                key = (date_str, location)
                if key not in weather_cache:
                    url = (
                        f"https://archive-api.open-meteo.com/v1/archive?"
                        f"latitude={lat}&longitude={lon}&start_date={date_str}&end_date={date_str}"
                        f"&daily=weathercode&timezone=Australia/Melbourne"
                    )
                    response = requests.get(url)
                    data = response.json()

                    if "daily" in data:
                        code = data["daily"]["weathercode"][0]
                        weather = get_weather_label(code)
                    else:
                        weather = "Unknown"

                    weather_cache[key] = weather
                else:
                    weather = weather_cache[key]

                # ✏️ Update weather in DB
                cursor.execute("""
                    UPDATE weather_season_data
                    SET Weather = %s
                    WHERE Data_ID = %s
                """, (weather, data_id))
                updated += 1

            except Exception as e:
                logging.warning(f"⚠️ Skipped Data_ID {data_id} — {e}")
                continue

        # 💾 Save changes
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"✅ Weather assigned for {updated} entries.")

    except Exception as e:
        logging.error(f"❌ Failed to assign weather — {e}")
