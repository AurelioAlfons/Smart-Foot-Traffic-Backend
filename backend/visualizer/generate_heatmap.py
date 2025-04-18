# =====================================================
# 🌟 Updated Heatmap: Dynamic Colors & Radius + Tooltip
# =====================================================
# - Shows heatmap for selected traffic type (Pedestrian, Cyclist, Vehicle)
# - Circle color changes with count (more traffic = warmer color)
# - Radius scales with interval count
# - Tooltip shows location, type, count, and time
# =====================================================

import os
import sys

# 🔧 Allow importing files from the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import folium                      # 📍 For map creation
import mysql.connector            # 🗓️ To connect to MySQL
import pandas as pd               # 📊 For working with data tables
from datetime import datetime, timedelta
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn
from rich.console import Console

console = Console()

# ✅ Import helper functions and settings
from backend.config import DB_CONFIG
from backend.visualizer.utils.description_box import generate_description_box
from backend.visualizer.utils.sensor_locations import LOCATION_COORDINATES, LOCATION_ZONES
from backend.visualizer.utils.tooltip_box import generate_tooltip_html
from backend.visualizer.utils.heatmap_colors import get_color_by_count
from backend.visualizer.utils.marker_helpers import add_center_marker
from backend.visualizer.utils.map_shapes import add_zone_polygon

# 🔍 Get traffic data for the selected date, time, and type (or by season)
def fetch_traffic_data(date_filter=None, time_filter=None, selected_type="Vehicle Count", season_filter=None, max_age_minutes=30):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    if season_filter:
        cursor.execute("""
            SELECT pd.Location, tc.Traffic_Type, SUM(tc.Total_Count) AS Interval_Count
            FROM traffic_counts tc
            JOIN weather_season_data wsd ON tc.Data_ID = wsd.Data_ID
            JOIN processed_data pd ON tc.Data_ID = pd.Data_ID
            WHERE wsd.Season = %s AND tc.Traffic_Type = %s
            GROUP BY pd.Location, tc.Traffic_Type
        """, (season_filter, selected_type))

        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=["Location", "Traffic_Type", "Interval_Count"])
        df["Date"] = season_filter
        df["Time"] = "All"
        df["DateTime_String"] = "Unknown"
    else:
        location_rows = []
        selected_time = datetime.strptime(time_filter, "%H:%M:%S")

        cursor.execute("""
            SELECT pd.Location, tc.Traffic_Type, tc.Interval_Count, pd.Time, pd.Date
            FROM processed_data pd
            JOIN traffic_counts tc ON pd.Data_ID = tc.Data_ID
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

        df = pd.DataFrame(location_rows, columns=["Location", "Traffic_Type", "Interval_Count", "Time", "Date"])
        df["DateTime_String"] = df.apply(
            lambda row: f"{row['Date']} {row['Time']}" if pd.notna(row['Date']) and pd.notna(row['Time']) else "N/A",
            axis=1
        )

    conn.close()
    return df

# 🔥 Main function to generate the heatmap and save as HTML
def generate_heatmap(date_filter=None, time_filter=None, selected_type="Pedestrian Count", season_filter=None):
    label = season_filter if season_filter else date_filter
    console.print(f"\n📌 Generating heatmap for: [bold magenta]{selected_type}[/bold magenta] at [cyan]{label}[/cyan]")

    progress = Progress(
        TextColumn("[bold cyan]🔄 Progress"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.1f}%",
        TimeElapsedColumn(),
        console=console
    )

    with progress:
        task = progress.add_task("Fetching data...", total=4)

        # 📊 Load and prepare the data
        df = fetch_traffic_data(date_filter=date_filter, time_filter=time_filter, selected_type=selected_type, season_filter=season_filter)

        progress.update(task, advance=1, description="Creating map...")

        # 📜 Base map around Footscray
        base_map = folium.Map(location=[-37.7975, 144.8876], zoom_start=15.7, tiles='cartodbpositron')
        progress.update(task, advance=1, description="Adding markers...")

        for loc, coords in LOCATION_COORDINATES.items():
            row_data = df[df["Location"] == loc]

            if not row_data.empty:
                cnt = row_data.iloc[0]["Interval_Count"]
                cnt = cnt if pd.notna(cnt) else 0
                dt_string = row_data.iloc[0]["DateTime_String"]
            else:
                cnt = 0
                dt_string = "Unknown"

            fill_color = get_color_by_count(cnt) if cnt > 0 else "#444444"

            # 📅 Build tooltip with proper logic
            tooltip_html = generate_tooltip_html(
                location=loc,
                traffic_type=selected_type.replace(' Count', ''),
                count=cnt,
                datetime_string="Unknown" if season_filter else dt_string,
                season=season_filter if season_filter else "Unknown",
                weather="Unknown"
            )

            add_zone_polygon(base_map, loc, fill_color, tooltip_html, LOCATION_ZONES)
            add_center_marker(base_map, coords, cnt, fill_color)

        progress.update(task, advance=1, description="Saving file...")

        base_map.get_root().html.add_child(
            generate_description_box(label, time_filter or "All", selected_type, df["Location"].unique())
        )

        os.makedirs("heatmaps", exist_ok=True)
        filename = os.path.join(
            "heatmaps",
            f"heatmap_{label}_{(time_filter or 'all').replace(':', '-')}_{selected_type.replace(' ', '_')}.html"
        )

        with open(filename, "w", encoding="utf-8", errors="ignore") as f:
            f.write(base_map.get_root().render())

        progress.update(task, advance=1)

    console.print(f"\n🚀 [bold green]Done![/bold green] Map saved as [bold]{filename}[/bold]\n")

# ▶️ Run example
generate_heatmap("2025-03-03", "12:00:00", "Vehicle Count")
# generate_heatmap("2024-04-11", "20:00:00", "Vehicle Count")
# generate_heatmap("2025-03-03", "12:00:00", "Cyclist Count")
# generate_heatmap("2025-03-03", "12:00:00", "Pedestrian Count")
generate_heatmap(None, None, "Vehicle Count", "Autumn")
