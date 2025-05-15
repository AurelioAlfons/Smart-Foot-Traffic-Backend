# ===========================================================
# Assign Real Weather per Hour (Step 3)
# -----------------------------------------------------------
# - Gets hourly weather from Open-Meteo API using weather codes
# - Converts weather codes to readable labels (e.g. "Clear", "Rain")
# - Updates the Weather column in weather_season_data
# - Matches by date, time, and location for accuracy
# ===========================================================

import mysql.connector
import logging
import requests
from datetime import datetime
from backend.config import DB_CONFIG
from backend.visualizer.utils.sensor_locations import LOCATION_COORDINATES

# 🧠 Convert weather code to label
WEATHER_MAP = {
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

def get_weather_label(code):
    return WEATHER_MAP.get(code, "Unknown")

def assign_weather(target_date):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        logging.info(f"🔍 Assigning accurate weather for {target_date}...")

        # 🧭 Get all distinct locations that still have undefined weather
        cursor.execute("""
            SELECT DISTINCT pd.Location
            FROM processed_data pd
            JOIN weather_season_data wsd ON pd.Data_ID = wsd.Data_ID
            WHERE pd.Date = %s AND wsd.Weather = 'Undefined'
        """, (target_date,))
        locations = [row[0] for row in cursor.fetchall()]

        total_updated = 0

        for location in locations:
            lat, lon = LOCATION_COORDINATES.get(location, (-37.798, 144.888))
            date_str = target_date

            # 🌐 Fetch hourly weather for this location/date
            url = (
                f"https://archive-api.open-meteo.com/v1/archive?"
                f"latitude={lat}&longitude={lon}&start_date={date_str}&end_date={date_str}"
                f"&hourly=weathercode&timezone=Australia/Melbourne"
            )
            response = requests.get(url)
            data = response.json()

            if "hourly" not in data or "weathercode" not in data["hourly"]:
                logging.warning(f"⚠️ No weather data for {location} on {date_str}")
                continue

            time_map = dict(zip(data["hourly"]["time"], data["hourly"]["weathercode"]))

            for hour_ts, code in time_map.items():
                weather = get_weather_label(code)
                if weather == "Unknown":
                    continue

                # Extract hour from timestamp (e.g., '2024-01-01T14:00')
                hour = hour_ts.split("T")[1] + ":00"

                # ⚡ Bulk update all matching rows at once
                cursor.execute("""
                    UPDATE weather_season_data wsd
                    JOIN processed_data pd ON pd.Data_ID = wsd.Data_ID
                    SET wsd.Weather = %s
                    WHERE pd.Date = %s AND pd.Time = %s AND pd.Location = %s AND wsd.Weather = 'Undefined'
                """, (weather, target_date, hour, location))

                total_updated += cursor.rowcount

        conn.commit()
        cursor.close()
        conn.close()

        logging.info(f"✅ Assigned weather to {total_updated} rows on {target_date}.")

    except Exception as e:
        logging.error(f"❌ Weather assignment failed: {e}")
