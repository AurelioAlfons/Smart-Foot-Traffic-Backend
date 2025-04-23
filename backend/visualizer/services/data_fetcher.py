# ================================================
# 🔍 Traffic Data Fetcher (Modular Version)
# ================================================

import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
from backend.config import DB_CONFIG

def fetch_traffic_data(date_filter=None, time_filter=None, selected_type="Vehicle Count", season_filter=None, max_age_minutes=30):
    """
    Fetch traffic data from the MySQL database.
    Supports optional filtering by date, time, and season.
    Returns a pandas DataFrame with relevant fields.
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    if season_filter:
        cursor.execute("""
            SELECT pd.Location, tc.Traffic_Type, SUM(tc.Total_Count) AS Interval_Count, 
                   MAX(wsd.Weather) AS Weather, MAX(wsd.Temperature) AS Temperature
            FROM traffic_counts tc
            JOIN weather_season_data wsd ON tc.Data_ID = wsd.Data_ID
            JOIN processed_data pd ON tc.Data_ID = pd.Data_ID
            WHERE wsd.Season = %s AND tc.Traffic_Type = %s
            GROUP BY pd.Location, tc.Traffic_Type
        """, (season_filter, selected_type))

        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=["Location", "Traffic_Type", "Interval_Count", "Weather", "Temperature"])
        df["Date"] = season_filter
        df["Time"] = "All"
        df["DateTime_String"] = "Unknown"
    else:
        location_rows = []
        selected_time = datetime.strptime(time_filter, "%H:%M:%S")

        cursor.execute("""
            SELECT pd.Location, tc.Traffic_Type, tc.Interval_Count, pd.Time, pd.Date, 
                   wsd.Weather, wsd.Temperature
            FROM processed_data pd
            JOIN traffic_counts tc ON pd.Data_ID = tc.Data_ID
            JOIN weather_season_data wsd ON pd.Data_ID = wsd.Data_ID
            WHERE pd.Date = %s AND tc.Traffic_Type = %s AND pd.Time <= %s
              AND pd.Time = (
                  SELECT MAX(pd2.Time)
                  FROM processed_data pd2
                  JOIN traffic_counts tc2 ON pd2.Data_ID = tc2.Data_ID
                  WHERE pd2.Date = %s AND pd2.Location = pd.Location AND tc2.Traffic_Type = %s AND pd2.Time <= %s
              )
        """, (date_filter, selected_type, time_filter, date_filter, selected_type, time_filter))

        for row in cursor.fetchall():
            parsed_time = row["Time"]
            if isinstance(parsed_time, timedelta):
                total_minutes = parsed_time.total_seconds() // 60
            elif isinstance(parsed_time, str):
                parsed_time_obj = datetime.strptime(parsed_time, "%H:%M:%S")
                total_minutes = parsed_time_obj.hour * 60 + parsed_time_obj.minute
            elif isinstance(parsed_time, datetime):
                total_minutes = parsed_time.hour * 60 + parsed_time.minute
            else:
                total_minutes = parsed_time.hour * 60 + parsed_time.minute

            age_minutes = selected_time.hour * 60 + selected_time.minute - total_minutes
            if age_minutes <= max_age_minutes:
                location_rows.append(row)

        df = pd.DataFrame(location_rows, columns=["Location", "Traffic_Type", "Interval_Count", "Time", "Date", "Weather", "Temperature"])
        df["DateTime_String"] = df.apply(
            lambda row: f"{row['Date']} {row['Time']}" if pd.notna(row['Date']) and pd.notna(row['Time']) else "N/A",
            axis=1
        )

    conn.close()
    return df
