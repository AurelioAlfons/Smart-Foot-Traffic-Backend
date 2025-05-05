# =====================================================
# 🌤️ MODULE: Assign Weather (Filtered by Date & Time)
# Purpose: Fetch hourly weather conditions (e.g. Clear, Rain)
# using Open-Meteo API and update missing weather entries
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
        45: "Fog", 48: "Rime Fog", 51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
        56: "Freezing Drizzle", 57: "Freezing Dense Drizzle",
        61: "Light Rain", 63: "Moderate Rain", 65: "Heavy Rain",
        66: "Freezing Rain", 67: "Freezing Heavy Rain",
        71: "Light Snow", 73: "Moderate Snow", 75: "Heavy Snow",
        77: "Snow Grains", 80: "Rain Showers", 81: "Heavy Showers", 82: "Violent Showers",
        85: "Snow Showers", 86: "Heavy Snow Showers",
        95: "Thunderstorm", 96: "Thunderstorm + Hail", 99: "Thunderstorm + Heavy Hail"
    }
    return weather_map.get(code, "Unknown")

# =====================================================
# 🌦️ FUNCTION: Assign weather for a specific date & time
# =====================================================
def assign_weather(target_date):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info(f"🔍 Assigning hourly weather for {target_date}...")

        # 📦 Get rows missing weather
        cursor.execute("""
            SELECT pd.Data_ID, pd.Date, pd.Time, pd.Location
            FROM processed_data pd
            JOIN weather_season_data wsd ON pd.Data_ID = wsd.Data_ID
            WHERE pd.Date = %s AND wsd.Weather = 'Undefined'
        """, (target_date,))
        
        rows = cursor.fetchall()
        updated = 0
        weather_cache = {}

        for data_id, date, time, location in rows:
            try:
                # 🗓️ Format date string
                if isinstance(date, str):
                    date = datetime.strptime(date, "%Y-%m-%d")
                date_str = date.strftime("%Y-%m-%d")

                # 🕒 Format time as HH:00 (handle str or timedelta)
                if isinstance(time, str):
                    hour_str = datetime.strptime(time, "%H:%M:%S").strftime("%H:00")
                else:
                    # ✅ Handle MySQL TIME returned as timedelta
                    hour_str = f"{int(time.total_seconds() // 3600):02d}:00"

                target_hour = f"{date_str}T{hour_str}"

                # 📍 Coordinates for location
                lat, lon = LOCATION_COORDINATES.get(location, (-37.798, 144.888))
                key = (date_str, location)

                if key not in weather_cache:
                    # 🌐 Fetch hourly weathercode data
                    url = (
                        f"https://archive-api.open-meteo.com/v1/archive?"
                        f"latitude={lat}&longitude={lon}&start_date={date_str}&end_date={date_str}"
                        f"&hourly=weathercode&timezone=Australia/Melbourne"
                    )
                    response = requests.get(url)
                    data = response.json()

                    if "hourly" in data and "weathercode" in data["hourly"]:
                        weather_cache[key] = dict(zip(data["hourly"]["time"], data["hourly"]["weathercode"]))
                    else:
                        logging.warning(f"⚠️ No hourly weather data for {location} on {date_str}")
                        weather_cache[key] = {}

                # 🎯 Match weathercode for the exact timestamp
                code = weather_cache[key].get(target_hour)
                weather = get_weather_label(code) if code is not None else "Unknown"

                if weather == "Unknown":
                    logging.warning(f"⚠️ Weather Unknown for Data_ID {data_id}, skipping...")
                    continue

                # 💾 Update the DB
                cursor.execute("""
                    UPDATE weather_season_data
                    SET Weather = %s
                    WHERE Data_ID = %s
                """, (weather, data_id))
                updated += 1

            except Exception as e:
                logging.warning(f"⚠️ Skipped Data_ID {data_id} — {e}")
                continue

        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"✅ Weather assigned for {updated} entries on {target_date}.")

    except Exception as e:
        logging.error(f"❌ Failed to assign weather — {e}")
