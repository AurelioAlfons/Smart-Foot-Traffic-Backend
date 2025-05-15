import os
import mysql.connector
from datetime import datetime
import time
from pprint import pprint

from backend.analytics.bar_chart.generate_barchart import export_bar_chart_html
from backend.config import DB_CONFIG
from backend.visualizer.utils.sensor_locations import LOCATION_COORDINATES


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

    bar_chart = {}
    line_chart = {}

    try:
        # 🔹 Determine season
        month = int(date.split("-")[1])
        summary["season"] = get_season_from_month(month)

        print("📊 Querying hourly and location-based traffic data...")
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

        location_totals = {}
        hourly_totals = [0] * 24

        for row in rows:
            hr = int(row['hour'])
            loc = row['Location']
            cnt = int(row['count'])

            hourly_totals[hr] += cnt
            location_totals[loc] = location_totals.get(loc, 0) + cnt
            bar_chart[loc] = bar_chart.get(loc, 0) + cnt
            time_label = f"{hr:02d}:00"
            line_chart[time_label] = line_chart.get(time_label, 0) + cnt

            if time_input and hr == int(time_input[:2]):
                summary['selected_hour']['total_count'] += cnt
                summary['selected_hour']['per_location'][loc] = cnt

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

        # 🔹 Static placeholders
        summary['weather'] = "Sunny"
        summary['temperature'] = "18°C"

        # 🔁 Generate and get path to bar chart
        barchart_path = export_bar_chart_html(
            summary['selected_hour']['per_location'],
            date=date,
            time=time_input,
            traffic_type=traffic_type
        )

        barchart_url = None
        if barchart_path:
            barchart_url = f"http://localhost:5000/{barchart_path.replace(os.sep, '/')}"

        # 🔁 Update BarChart_URL in heatmaps table
        if barchart_url:
            cursor.close()
            connection.close()
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()

            cursor.execute("""
                SELECT Heatmap_ID FROM heatmaps
                WHERE Traffic_Type = %s AND Date_Filter = %s AND Time_Filter = %s
            """, (traffic_type, date, time_input))
            result = cursor.fetchone()

            if result:
                heatmap_id = result[0]
                cursor.execute("""
                    UPDATE heatmaps
                    SET BarChart_URL = %s
                    WHERE Heatmap_ID = %s
                """, (barchart_url, heatmap_id))
                print(f"🟩 Bar chart URL updated in heatmaps for ID {heatmap_id}")
            else:
                print("⚠️ No matching heatmap found. Bar chart URL not inserted.")

            connection.commit()

        # ✅ Build location availability map
        included_locations = summary['selected_hour']['per_location'].keys()
        location_availability = {
            loc: loc in included_locations
            for loc in LOCATION_COORDINATES.keys()
        }

    except Exception as e:
        print("❌ Error in seasonal_stats:", e)

    finally:
        if cursor: cursor.close()
        if connection: connection.close()

    duration = round(time.time() - start_time, 2)
    print(f"\n✅ Summary generation complete in {duration}s\n")

    return {
        "summary": summary,
        "bar_chart": summary['selected_hour']['per_location'],
        "line_chart": line_chart,
        "location_availability": location_availability
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
