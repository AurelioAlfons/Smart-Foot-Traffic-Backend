# =====================================================
# 🌟 Updated Heatmap: Reusable Description Box + Table Tooltip
# =====================================================
# Shows heatmap for selected traffic type only.
# Circle marker radius scales with count.
# Tooltip styled like a mini table, shows date + time.
# =====================================================

import os
import sys
import folium
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn
from rich.console import Console

console = Console()

# Allow relative imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.config import DB_CONFIG
from backend.visualizer.utils.description_box import generate_description_box
from backend.visualizer.utils.sensor_locations import LOCATION_COORDINATES

# 🔍 FETCH TRAFFIC DATA (Recent)
def fetch_traffic_data(date_filter, time_filter, selected_type, max_age_minutes=30):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

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

    conn.close()
    return pd.DataFrame(location_rows)

# 🔥 MAIN FUNCTION: GENERATE HEATMAP
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

        df = fetch_traffic_data(date_filter, time_filter, selected_type)
        df["Time"] = pd.to_datetime(df["Time"], errors='coerce').dt.strftime("%H:%M:%S")
        df["DateTime_String"] = df["Date"].astype(str) + " " + df["Time"].astype(str)

        progress.update(task, advance=1, description="Creating map...")

        base_map = folium.Map(location=[-37.7975, 144.8876], zoom_start=15.7, tiles='cartodbpositron')
        progress.update(task, advance=1, description="Adding markers...")

        for _, row in df.iterrows():
            loc = row["Location"]
            cnt = row["Interval_Count"]
            coords = LOCATION_COORDINATES.get(loc)

            if not coords or cnt == 0:
                continue

            radius = max(5, min(cnt * 0.3, 25))
            tooltip_html = f"""
                <div style="
                    font-size: 14px;
                    font-weight: normal;
                    line-height: 1.5;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    padding: 10px 12px;
                    background-color: white;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                    width: 280px;
                ">
                    <div style="font-weight: bold; margin-bottom: 6px;">{loc}</div>
                    <hr style="margin: 6px 0;">
                    <div style="display: flex; justify-content: space-between;">
                        <span><b>Type:</b></span> <span>{selected_type.replace(' Count', '')}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span><b>Count:</b></span> <span>{cnt}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span><b>Time:</b></span> <span>{row['DateTime_String']}</span>
                    </div>
                </div>
            """

            folium.CircleMarker(
                location=coords,
                radius=radius,
                color='#3bffc1',
                fill=True,
                fill_color='#3bffc1',
                fill_opacity=0.6,
                tooltip=folium.Tooltip(tooltip_html, sticky=True)
            ).add_to(base_map)

        progress.update(task, advance=1, description="Saving file...")

        base_map.get_root().html.add_child(
            generate_description_box(date_filter, time_filter, selected_type, df["Location"].unique())
        )

        os.makedirs("heatmaps", exist_ok=True)
        filename = os.path.join("heatmaps", f"heatmap_{date_filter}_{time_filter.replace(':', '-')}_{selected_type.replace(' ', '_')}.html")

        with open(filename, "w", encoding="utf-8", errors="ignore") as f:
            f.write(base_map.get_root().render())

        progress.update(task, advance=1)

    console.print(f"\n🚀 [bold green]Done![/bold green] Map saved as [bold]{filename}[/bold]\n")

# 🔢 Run test
generate_heatmap("2025-03-03", "12:55:00", "Pedestrian Count")
