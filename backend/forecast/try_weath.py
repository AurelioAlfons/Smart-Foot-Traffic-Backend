# ===========================================================
# Optimized Real Weather Assignment per Hour
# -----------------------------------------------------------
# - Faster DB updates using executemany
# - Retry logic for weather API
# - Cleaner logging and error handling
# ===========================================================

import mysql.connector
import logging
import requests
from datetime import datetime
from backend.config import DB_CONFIG
from backend.visualizer.map_components.sensor_locations import LOCATION_COORDINATES
import time

# Convert weather code to label
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

def fetch_weather_data(lat, lon, date_str, retries=3):
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}&start_date={date_str}&end_date={date_str}"
        f"&hourly=weathercode&timezone=Australia/Melbourne"
    )
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if "hourly" in data and "weathercode" in data["hourly"]:
                return dict(zip(data["hourly"]["time"], data["hourly"]["weathercode"]))
            break
        except Exception as e:
            logging.warning(f"[Retry {attempt+1}] Weather fetch failed for {lat},{lon} on {date_str}: {e}")
            time.sleep(1)
    return {}

def assign_weather(target_date):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        logging.info(f"Assigning real weather for {target_date}...")

        cursor.execute("""
            SELECT DISTINCT pd.Location
            FROM processed_data pd
            JOIN weather_season_data wsd ON pd.Data_ID = wsd.Data_ID
            WHERE pd.Date = %s AND wsd.Weather = 'Undefined'
        """, (target_date,))
        locations = [row[0] for row in cursor.fetchall()]

        total_updates = 0

        for location in locations:
            lat, lon = LOCATION_COORDINATES.get(location, (-37.798, 144.888))
            weather_map = fetch_weather_data(lat, lon, target_date)
            updates = []

            for timestamp, code in weather_map.items():
                weather = get_weather_label(code)
                if weather == "Unknown":
                    continue
                hour = timestamp.split("T")[1] + ":00"
                updates.append((weather, target_date, hour, location))

            if updates:
                cursor.executemany("""
                    UPDATE weather_season_data wsd
                    JOIN processed_data pd ON pd.Data_ID = wsd.Data_ID
                    SET wsd.Weather = %s
                    WHERE pd.Date = %s AND pd.Time = %s AND pd.Location = %s AND wsd.Weather = 'Undefined'
                """, updates)
                total_updates += cursor.rowcount

        conn.commit()
        logging.info(f"Updated weather for {total_updates} rows on {target_date}")

    except Exception as e:
        logging.error(f"Weather assignment failed: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
