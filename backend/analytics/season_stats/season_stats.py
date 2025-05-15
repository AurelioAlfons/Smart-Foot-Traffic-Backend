# backend/analytics/season_stats.py
# ------------------------------------------------------
# Optimized Seasonal Analytics with Combined Query & Logs
# ------------------------------------------------------

from backend.analytics.statistics import get_season_from_month
from backend.config import DB_CONFIG
from datetime import datetime, timedelta
import mysql.connector
import time

SEASONS = {
    "Autumn": (3, 1),
    "Winter": (6, 1),
    "Spring": (9, 1),
    "Summer": (12, 1),
}

TRAFFIC_TYPES = [
    "Pedestrian Count",
    "Vehicle Count",
    "Cyclist Count"
]

def get_first_monday(year: int, month: int) -> datetime:
    date = datetime(year, month, 1)
    while date.weekday() != 0:
        date += timedelta(days=1)
    return date

def get_seasonal_stats(year: int, time_input: str, main_traffic_type: str):
    result = {}
    season_times = {}

    for season, (month, _) in SEASONS.items():
        date_obj = get_first_monday(year, month)
        date_str = date_obj.strftime("%Y-%m-%d")

        print(f"🕒 Starting {season} analysis for {date_str}")
        start = time.time()
        seasonal_entry = analyze_day(date_str, time_input, main_traffic_type)
        duration = round(time.time() - start, 2)

        result[season] = seasonal_entry
        season_times[season] = duration

    print("\n📊 Season Summary:")
    emoji = {
        "Winter": "🧊",
        "Autumn": "🍂",
        "Spring": "🌸",
        "Summer": "☀️"
    }
    for season in SEASONS.keys():
        print(f"{emoji[season]} {season} Process → {season_times[season]}s")

    return result

def analyze_day(date: str, time_input: str, main_type: str):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    print(f"⏳ Running combined SQL query for {date}...")
    q_start = time.time()

    cursor.execute("""
        SELECT 
            tc.Traffic_Type,
            HOUR(pd.Date_Time) AS hour,
            pd.Location,
            SUM(tc.Interval_Count) AS count
        FROM processed_data pd
        JOIN Traffic_Counts tc ON pd.Data_ID = tc.Data_ID
        WHERE DATE(pd.Date_Time) = %s
          AND tc.Traffic_Type IN ('Pedestrian Count', 'Vehicle Count', 'Cyclist Count')
        GROUP BY tc.Traffic_Type, hour, pd.Location
    """, (date,))
    
    rows = cursor.fetchall()
    print(f"✅ Query complete in {round(time.time() - q_start, 2)}s with {len(rows)} rows.")

    data_by_type = {}
    totals_by_type = {}
    hourly_totals_map = {t: [0] * 24 for t in TRAFFIC_TYPES}
    location_totals_map = {t: {} for t in TRAFFIC_TYPES}

    for row in rows:
        t_type = row["Traffic_Type"]
        hr = int(row["hour"])
        loc = row["Location"]
        cnt = int(row["count"])

        hourly_totals_map[t_type][hr] += cnt
        location_totals_map[t_type][loc] = location_totals_map[t_type].get(loc, 0) + cnt

    for traffic_type in TRAFFIC_TYPES:
        h_total = hourly_totals_map[traffic_type]
        l_total = location_totals_map[traffic_type]

        total_count = sum(h_total)
        avg_hour = round(total_count / 24, 2) if total_count else 0
        top_loc = max(l_total.items(), key=lambda x: x[1], default=("-", 0))
        peak_hr = max(range(24), key=lambda h: h_total[h]) if any(h_total) else 0

        data_by_type[traffic_type] = {
            "total": total_count,
            "avg_hourly": avg_hour,
            "top_location": top_loc[0],
            "peak_hour": f"{peak_hr:02d}:00",
        }

        totals_by_type[traffic_type] = total_count

    main = data_by_type[main_type]
    highest = max(totals_by_type.items(), key=lambda x: x[1])
    lowest = min(totals_by_type.items(), key=lambda x: x[1])

    cursor.close()
    conn.close()

    return {
        "date": date,
        "season": get_season_from_month(int(date.split("-")[1])),
        "total_daily_count": main["total"],
        "average_hourly_count": main["avg_hourly"],
        "top_location": main["top_location"],
        "peak_hour": main["peak_hour"],
        "weather": "Sunny",
        "temperature": "18°C",
        "accessibility_alert": None,
        "location_availability": None,
        "highest_type": highest,
        "lowest_type": lowest
    }
