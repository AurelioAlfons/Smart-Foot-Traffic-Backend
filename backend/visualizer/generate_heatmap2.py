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
import mysql.connector            # 🗃️ To connect to MySQL
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

# 🔍 Get traffic data for the selected date, time, and type
def fetch_traffic_data(date_filter, time_filter, selected_type, max_age_minutes=30):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    location_rows = []
    selected_time = datetime.strptime(time_filter, "%H:%M:%S")

    # 📦 SQL: Get the most recent record for each location before the selected time
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

    # 📊 Filter rows to make sure they are recent enough
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

    conn.close()
    return pd.DataFrame(location_rows, columns=["Location", "Traffic_Type", "Interval_Count", "Time", "Date"])

# 🔥 Main function to generate the heatmap and save as HTML
def generate_heatmap(date_filter, time_filter, selected_type="Pedestrian Count"):
    console.print(f"\n📌 Generating heatmap for: [bold magenta]{selected_type}[/bold magenta]")

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
        df = fetch_traffic_data(date_filter, time_filter, selected_type)
        df["DateTime_String"] = pd.to_datetime(
            df["Date"].astype(str) + " " + df["Time"].astype(str), errors='coerce'
        ).dt.strftime("%Y-%m-%d %H:%M:%S")

        progress.update(task, advance=1, description="Creating map...")

        # 🗺️ Create base map centered around Footscray
        base_map = folium.Map(location=[-37.7975, 144.8876], zoom_start=15.7, tiles='cartodbpositron')
        progress.update(task, advance=1, description="Adding markers...")

        # 📍 Loop through all sensor locations and add a circle
        for loc, coords in LOCATION_COORDINATES.items():
            row_data = df[df["Location"] == loc]

            if not row_data.empty:
                cnt = row_data.iloc[0]["Interval_Count"]
                cnt = cnt if pd.notna(cnt) else 0
                dt_string = row_data.iloc[0]["DateTime_String"]
                dt_string = dt_string if pd.notna(dt_string) else f"{date_filter} {time_filter}"
            else:
                cnt = 0
                dt_string = f"{date_filter} {time_filter}"

            # 🔵 Customize circle size and color
            radius = max(5, min(cnt * 0.3, 25))
            fill_color = get_color_by_count(cnt) if cnt > 0 else "#444444"  # dark grey if no data

            # 📝 Create tooltip with a new line for "no data"
            tooltip_html = generate_tooltip_html(
                location=loc,
                traffic_type=selected_type.replace(' Count', ''),
                count=cnt,
                datetime_string = dt_string + ("<br><span style='color: #888;'>No data available</span>" if cnt == 0 else "")
            )

            # 🟪 Add filled polygon zone instead of a circle
            folium.Polygon(
                locations=[[lat, lon] for lon, lat in LOCATION_ZONES[loc]],  # Flip (lon, lat) to (lat, lon)
                color=fill_color,
                fill=True,
                fill_color=fill_color,
                fill_opacity=0.6,
                tooltip=folium.Tooltip(tooltip_html, sticky=True)
            ).add_to(base_map)

            # 🧭 Add center marker at the original sensor point
            folium.Marker(
                location=coords,
                icon=folium.DivIcon(
                    icon_size=(40, 20),  # size of your div (adjust if needed)
                    icon_anchor=(20, 10),  # center horizontally and vertically
                    html=f"""
                        <div style="
                            font-size: 14px;
                            font-weight: 800;
                            color: white;
                            text-align: center;
                        ">
                            {cnt}
                        </div>
                    """
                )
            ).add_to(base_map)

        progress.update(task, advance=1, description="Saving file...")

        # 📋 Add floating info box on the map
        base_map.get_root().html.add_child(
            generate_description_box(date_filter, time_filter, selected_type, df["Location"].unique())
        )

        # 💾 Save map to HTML file
        os.makedirs("heatmaps", exist_ok=True)
        filename = os.path.join(
            "heatmaps",
            f"heatmap_{date_filter}_{time_filter.replace(':', '-')}_{selected_type.replace(' ', '_')}.html"
        )

        with open(filename, "w", encoding="utf-8", errors="ignore") as f:
            f.write(base_map.get_root().render())

        progress.update(task, advance=1)

    console.print(f"\n🚀 [bold green]Done![/bold green] Map saved as [bold]{filename}[/bold]\n")

# ▶️ Run example
generate_heatmap("2025-03-03", "12:00:00", "Vehicle Count")
generate_heatmap("2025-03-03", "12:00:00", "Cyclist Count")
generate_heatmap("2025-03-03", "12:00:00", "Pedestrian Count")
