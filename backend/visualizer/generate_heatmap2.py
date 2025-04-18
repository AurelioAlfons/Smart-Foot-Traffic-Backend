# =====================================================
# 🌟 Updated Heatmap: Dynamic Colors & Radius + Tooltip
# =====================================================
# Shows heatmap for selected traffic type only.
# Color changes by traffic intensity (count).
# Radius scales with interval count.
# Tooltip styled like a mini table, shows date + time.
# =====================================================

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import folium
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn
from rich.console import Console

console = Console()

# ✅ Allow relative imports
from backend.config import DB_CONFIG
from backend.visualizer.utils.description_box import generate_description_box
from backend.visualizer.utils.sensor_locations import LOCATION_COORDINATES
from backend.visualizer.utils.tooltip_box import generate_tooltip_html

# 🎨 Traffic color scheme based on count thresholds
def get_color_by_count(count):
    if count > 900:
        return "#A23BEC"  # 🟣 Reddish Purple (softer)
    elif count >= 850:
        return "#C965E9"  # 🟣 Lighter Red-Purple
    elif count >= 800:
        return "#DB70E3"  # 🟣 Light Red-Purple
    elif count >= 750:
        return "#B22222"  # 🔴 Firebrick
    elif count >= 701:
        return "#C62828"  # 🔴 Strong Red
    elif count >= 660:
        return "#E53935"  # 🔴 Mid Red
    elif count >= 620:
        return "#F44336"  # 🔴 Bright Red
    elif count >= 590:
        return "#FF5252"  # 🔴 Light Red
    elif count >= 560:
        return "#FF6E6E"  # 🔴 Soft Red
    elif count >= 530:
        return "#FF7A7A"  # 🔴 Rose Red
    elif count >= 500:
        return "#FF8A65"  # 🟧 Red-Orange
    elif count >= 470:
        return "#FF7043"  # 🟧 Rich Orange
    elif count >= 440:
        return "#FF5722"  # 🟧 Deep Orange
    elif count >= 410:
        return "#FF6F00"  # 🟧 Darker Amber
    elif count >= 370:
        return "#FF8C42"  # 🟧 Dark Orange
    elif count >= 330:
        return "#FFA500"  # 🟧 Orange
    elif count >= 290:
        return "#FFB347"  # 🟧 Light Orange
    elif count >= 250:
        return "#FFD180"  # 🟧 Soft Peach
    elif count >= 210:
        return "#FFD700"  # 🟡 Dark Yellow
    elif count >= 160:
        return "#FFFF00"  # 🟡 Yellow
    elif count >= 120:
        return "#FFFF66"  # 🟡 Light Yellow
    elif count >= 70:
        return "#ADFF2F"  # 🟢 Yellow-Green
    elif count >= 40:
        return "#99FF99"  # 🟩 Light Green
    elif count >= 11:
        return "#CCFFCC"  # 🟩 Very Light Green
    elif count >= 1:
        return "#E5FFE5"  # 🟩 Faintest Green
    else:
        return "#F0F0F0"  # ⚪ No Data

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
    return pd.DataFrame(location_rows, columns=["Location", "Traffic_Type", "Interval_Count", "Time", "Date"])

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
        df["DateTime_String"] = pd.to_datetime(df["Date"].astype(str) + " " + df["Time"].astype(str), errors='coerce').dt.strftime("%Y-%m-%d %H:%M:%S")

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
            fill_color = get_color_by_count(cnt)

            tooltip_html = generate_tooltip_html(
                location=loc,
                traffic_type=selected_type.replace(' Count', ''),
                count=cnt,
                datetime_string=row['DateTime_String']
            )


            folium.CircleMarker(
                location=coords,
                radius=radius,
                color=fill_color,
                fill=True,
                fill_color=fill_color,
                fill_opacity=0.7,
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

# 🔢 Run for test case
# generate_heatmap("2025-03-03", "12:00:00", "Cyclist Count")
# generate_heatmap("2025-03-03", "12:00:00", "Pedestrian Count")
generate_heatmap("2025-03-03", "12:00:00", "Vehicle Count")