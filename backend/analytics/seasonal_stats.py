# analytics/seasonal_stats.py

import mysql.connector
from datetime import datetime
import time
from pprint import pprint

from backend.analytics.bar_chart.generate_barchart import export_bar_chart_html
from backend.config import DB_CONFIG


def get_summary_stats(date, time_input, traffic_type):
    start_time = time.time()
    print("\n🚦 Starting summary generation...")
    print(f"📅 Date: {date} | 🕒 Time: {time_input} | 🚸 Type: {traffic_type}\n")

    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)

    summary = {
        "date": date,
        "traffic_type": traffic_type,
        "time": time_input,
        "season": None,
        "weather": None,
        "temperature": None,
        "total_daily_count": 0,
        "average_hourly_count": 0,
        "top_location": {},
        "peak_hour": {},
        "selected_hour": {
            "time": time_input,
            "total_count": 0,
            "per_location": {}
        }
    }

    bar_chart = {}     # full-day total per location (unused now)
    line_chart = {}    # total count per hour

    try:
        # 🔹 Determine season (based on month)
        month = int(date.split("-")[1])
        summary["season"] = get_season_from_month(month)

        print("📊 Querying hourly and location-based traffic data...")
        # 🔹 Get full-day counts by location/hour
        cursor.execute("""
            SELECT 
                HOUR(pd.Date_Time) AS hour,
                pd.Location,
                SUM(tc.Interval_Count) AS count
            FROM processed_data pd
            JOIN Traffic_Counts tc ON pd.Data_ID = tc.Data_ID
            WHERE DATE(pd.Date_Time) = %s AND tc.Traffic_Type = %s
            GROUP BY hour, pd.Location
        """, (date, traffic_type))

        rows = cursor.fetchall()
        print(f"✅ Fetched {len(rows)} rows of data.")

        # 🔹 Structure for calculations
        location_totals = {}
        hourly_totals = [0] * 24

        for row in rows:
            hr = int(row['hour'])
            loc = row['Location']
            cnt = int(row['count'])

            # Total per hour
            hourly_totals[hr] += cnt

            # Total per location
            location_totals[loc] = location_totals.get(loc, 0) + cnt

            # Full-day bar chart (optional)
            bar_chart[loc] = bar_chart.get(loc, 0) + cnt

            # Line chart
            time_label = f"{hr:02d}:00"
            line_chart[time_label] = line_chart.get(time_label, 0) + cnt

            # Selected hour bar chart
            if time_input and hr == int(time_input[:2]):
                summary['selected_hour']['total_count'] += cnt
                summary['selected_hour']['per_location'][loc] = cnt

        # 🔹 Summary values
        summary['total_daily_count'] = sum(hourly_totals)
        summary['average_hourly_count'] = round(summary['total_daily_count'] / 24, 2)

        if location_totals:
            summary['top_location'] = max(location_totals.items(), key=lambda x: x[1])

        if any(hourly_totals):
            peak_hr = max(range(24), key=lambda h: hourly_totals[h])
            summary['peak_hour'] = {
                "time": f"{peak_hr:02d}:00:00",
                "count": hourly_totals[peak_hr]
            }

        # 🔹 Static weather placeholder
        summary['weather'] = "Sunny"
        summary['temperature'] = "18°C"

        export_bar_chart_html(
            summary['selected_hour']['per_location'],
            date=date,
            time=time_input,
            traffic_type=traffic_type
        )

    except Exception as e:
        print("❌ Error in seasonal_stats:", e)

    finally:
        cursor.close()
        connection.close()

    duration = round(time.time() - start_time, 2)
    print(f"\n✅ Summary generation complete in {duration}s\n")

    return {
        "summary": summary,
        "bar_chart": summary['selected_hour']['per_location'],  # ✅ Matches chart output
        "line_chart": line_chart
    }


def get_season_from_month(month):
    if month in [12, 1, 2]:
        return "Summer"
    elif month in [3, 4, 5]:
        return "Autumn"
    elif month in [6, 7, 8]:
        return "Winter"
    elif month in [9, 10, 11]:
        return "Spring"
    return "Unknown"


# 🎯 Standalone test
if __name__ == "__main__":
    result = get_summary_stats("2024-05-05", "14:00:00", "Vehicle Count")
    pprint(result)
