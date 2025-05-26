import os
import json
import mysql.connector
from datetime import datetime
import time
from pprint import pprint
from rich.console import Console

from backend.analytics.bar_chart.generate_barchart import export_bar_chart_html
from backend.config import DB_CONFIG
from backend.visualizer.map_components.sensor_locations import LOCATION_COORDINATES

console = Console()

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

def get_summary_stats(date, time_input, traffic_type):
    start_time = time.time()

    console.print("\n[bold magenta]========== SUMMARY GENERATION ==========[/bold magenta]")
    console.print(f"Date: [green]{date}[/green] | Time: [green]{time_input}[/green] | Type: [green]{traffic_type}[/green]")

    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)

    # Check cache
    cursor.execute("""
        SELECT Summary_JSON FROM summary_cache
        WHERE Date_Filter = %s AND Time_Filter = %s AND Traffic_Type = %s
    """, (date, time_input, traffic_type))

    cached = cursor.fetchone()
    if cached:
        summary_data = json.loads(cached['Summary_JSON'])

        filename = f"{date}_{time_input[:2]}-{traffic_type}.html"
        barchart_path = os.path.join("barchart", filename)

        if os.path.exists(barchart_path):
            console.print("[cyan]Summary loaded from cache[/cyan]")
            return {
                "summary": summary_data,
                "bar_chart": summary_data['selected_hour']['per_location'],
                "line_chart": {},
                "location_availability": {
                    loc: loc in summary_data['selected_hour']['per_location']
                    for loc in LOCATION_COORDINATES
                }
            }
        else:
            console.print(f"[yellow]⚠️ Cached summary found, but missing local bar chart: {barchart_path}[/yellow]")
            selected_data = summary_data['selected_hour']['per_location']
            total_data = {loc: 0 for loc in LOCATION_COORDINATES}

            # Optional: aggregate from hourly_data if stored in summary
            for hour in range(24):
                hour_label = f"{hour:02}:00"
                for loc, count in summary_data.get("hourly_data", {}).get(hour_label, {}).items():
                    total_data[loc] += count

            average_data = {
                loc: round(total_data.get(loc, 0) / 24, 2)
                for loc in LOCATION_COORDINATES
            }

            barchart_path = export_bar_chart_html(
                selected_data,
                total_data,
                average_data,
                date=date,
                time=time_input,
                traffic_type=traffic_type
            )

            if barchart_path:
                console.print(f"[green]✅ Re-generated missing bar chart: {barchart_path}[/green]")
            else:
                console.print("[red]❌ Failed to regenerate missing bar chart[/red]")

            return {
                "summary": summary_data,
                "bar_chart": selected_data,
                "line_chart": {},
                "location_availability": {
                    loc: loc in selected_data
                    for loc in LOCATION_COORDINATES
                }
            }

    # ======================
    # FULL GENERATION BELOW
    # ======================

    summary = {
        "date": date,
        "traffic_type": traffic_type,
        "time": time_input,
        "season": get_season_from_month(int(date.split("-")[1])),
        "weather": "Sunny",
        "temperature": "18°C",
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
        console.print("Querying hourly and location-based traffic data...")

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
        console.print(f"Fetched {len(rows)} rows of data.")

        location_totals = {}
        hourly_totals = [0] * 24
        hourly_data = {}

        for row in rows:
            hr = int(row['hour'])
            loc = row['Location']
            cnt = int(row['count'])

            hourly_totals[hr] += cnt
            location_totals[loc] = location_totals.get(loc, 0) + cnt
            bar_chart[loc] = bar_chart.get(loc, 0) + cnt
            time_label = f"{hr:02}:00"
            line_chart[time_label] = line_chart.get(time_label, 0) + cnt

            if time_label not in hourly_data:
                hourly_data[time_label] = {}
            hourly_data[time_label][loc] = hourly_data[time_label].get(loc, 0) + cnt

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

        summary["hourly_data"] = hourly_data

        selected_data = summary['selected_hour']['per_location']
        total_data = bar_chart
        average_data = {
            loc: round(total_data.get(loc, 0) / 24, 2)
            for loc in LOCATION_COORDINATES
        }

        console.print("[cyan]Generating bar chart...[/cyan]")
        barchart_path = export_bar_chart_html(
            selected_data,
            total_data,
            average_data,
            date=date,
            time=time_input,
            traffic_type=traffic_type
        )

        barchart_url = None
        if barchart_path:
            console.print(f"[green]Bar chart saved to:[/] {barchart_path}")
            base_url = os.getenv("BASE_URL", "http://localhost:5000")
            prod_url = os.getenv("PROD_URL", "https://smart-foot-traffic-backend.onrender.com")
            barchart_url = f"{prod_url}/{barchart_path.replace(os.sep, '/')}" if "localhost" not in base_url else f"{base_url}/{barchart_path.replace(os.sep, '/')}"

            # Update BarChart_URL in heatmaps table
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
                console.print(f"[green]Bar chart URL updated in heatmaps for ID {heatmap_id}[/green]")
            else:
                console.print("[yellow]No matching heatmap found. Bar chart URL not inserted.[/yellow]")

            connection.commit()
            cursor = connection.cursor(dictionary=True)
        else:
            console.print("[red]❌ Bar chart generation failed (returned None)[/red]")

        # Cache summary
        cursor.execute("""
            INSERT INTO summary_cache (Date_Filter, Time_Filter, Traffic_Type, Summary_JSON)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE Summary_JSON = VALUES(Summary_JSON), Generated_At = CURRENT_TIMESTAMP
        """, (
            date, time_input, traffic_type,
            json.dumps(summary)
        ))
        connection.commit()
        console.print("[green]Summary cached to database[/green]")

        included_locations = summary['selected_hour']['per_location'].keys()
        location_availability = {
            loc: loc in included_locations
            for loc in LOCATION_COORDINATES
        }

    except Exception as e:
        console.print(f"[bold red]Error in seasonal_stats:[/bold red] {e}")
        location_availability = {}

    finally:
        if cursor: cursor.close()
        if connection: connection.close()

    duration = round(time.time() - start_time, 2)
    console.print(f"[green]Summary generation complete in {duration}s[/green]\n")

    return {
        "summary": summary,
        "bar_chart": summary['selected_hour']['per_location'],
        "line_chart": line_chart,
        "location_availability": location_availability
    }

# Standalone test
if __name__ == "__main__":
    result = get_summary_stats("2024-05-05", "14:00:00", "Vehicle Count")
    pprint(result)
