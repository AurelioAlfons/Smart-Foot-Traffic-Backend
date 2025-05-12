# =====================================================
# 🍝 Updated Heatmap: Dynamic Colors & Radius + Tooltip
# =====================================================
# - Shows heatmap for selected traffic type (Pedestrian, Cyclist, Vehicle)
# - Circle color changes with count (more traffic = warmer color)
# - Radius scales with interval count
# - Tooltip shows location, type, count, and time
# =====================================================

import os
import sys
from datetime import datetime
import mysql
import time
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn

from backend.visualizer.services.heatmap_log import log_heatmap_duration

# 🔧 Allow importing files from the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# ✅ Import logic modules
from backend.config import DB_CONFIG
from backend.forecast.temperature import assign_temperature
from backend.forecast.weather import assign_weather
from backend.visualizer.services.data_fetcher import fetch_traffic_data
from backend.visualizer.services.map_renderer import render_heatmap_map

console = Console()

# 🔎 Check if weather & temp exist
def check_weather_and_temp_exists(date_filter):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                MAX(CASE WHEN Weather IS NOT NULL THEN 1 ELSE 0 END),
                MAX(CASE WHEN Temperature IS NOT NULL THEN 1 ELSE 0 END)
            FROM weather_season_data
            WHERE DATE(Date_ID) = %s
        """, (date_filter,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        weather_exists = result[0] == 1
        temperature_exists = result[1] == 1
        return weather_exists, temperature_exists

    except mysql.connector.Error:
        return False, False


# 🔥 Main function to generate the heatmap and log phase timings
def generate_heatmap(date_filter=None, time_filter=None, selected_type="Pedestrian Count", season_filter=None):
    start = time.time()
    label = season_filter if season_filter else date_filter

    timings = {}
    def mark(name):
        timings[name] = time.time()

    mark("start")

    # 🧱 Prepare filename early for fast checks
    filename = os.path.join(
        "heatmaps",
        f"heatmap_{label}_{(time_filter or 'all').replace(':', '-')}_{selected_type.replace(' ', '_')}.html"
    )

    # 🔍 Check if heatmap already exists
    existing_id = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Heatmap_ID FROM heatmaps
            WHERE Traffic_Type = %s AND Date_Filter = %s AND Time_Filter = %s
        """, (selected_type, date_filter, time_filter))
        result = cursor.fetchone()
        if result:
            existing_id = result[0]
            console.print(f"[yellow]♻️ Heatmap ID {existing_id} already exists in DB[/yellow]")
        if os.path.exists(filename):
            console.print(f"[green]✅ Skipping generation. File already exists: {filename}[/green]")
            return
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        console.print(f"[red]❌ DB check failed:[/red] {e}")
        return

    # ⏰ Build full label with time if available
    full_label = f"{label} {time_filter}" if time_filter else label

    console.print(f"\n📌 Generating heatmap for: [bold magenta]{selected_type}[/bold magenta] at [cyan]{full_label}[/cyan]")

    progress = Progress(
        TextColumn("[bold cyan]🔄 Progress"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.1f}%",
        TimeElapsedColumn(),
        console=console
    )

    with progress:
        task = progress.add_task("Fetching data...", total=3)

        # 🧠 Assign weather and temperature only if missing
        weather_ok, temp_ok = check_weather_and_temp_exists(date_filter)

        if not weather_ok:
            assign_weather(date_filter)
        else:
            console.print(f"[green]✅ Weather already assigned for {date_filter}[/green]")
        mark("weather")

        if not temp_ok:
            assign_temperature(date_filter)
        else:
            console.print(f"[green]✅ Temperature already assigned for {date_filter}[/green]")
        mark("temperature")

        # 📊 Fetch traffic data
        df = fetch_traffic_data(
            date_filter=date_filter,
            time_filter=time_filter,
            selected_type=selected_type,
            season_filter=season_filter
        )
        mark("fetch")
        progress.update(task, advance=1, description="Creating map...")

        # 🗌 Render heatmap
        base_map = render_heatmap_map(df, selected_type, label, time_filter)
        mark("render")
        progress.update(task, advance=1, description="Saving file...")

        # 📅 Save HTML
        os.makedirs("heatmaps", exist_ok=True)
        with open(filename, "w", encoding="utf-8", errors="ignore") as f:
            f.write(base_map.get_root().render())
        mark("save")

        progress.update(task, advance=1)

        # 📆 Store/update metadata
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            heatmap_url = f"http://localhost:5000/{filename.replace(os.sep, '/')}"

            if existing_id:
                cursor.execute("""
                    UPDATE heatmaps
                    SET Generated_At = %s, Heatmap_URL = %s, Status = 'Regenerated'
                    WHERE Heatmap_ID = %s
                """, (generated_at, heatmap_url, existing_id))
                console.print(f"[green]✅ Updated existing heatmap ID {existing_id}[/green]")
            else:
                cursor.execute("""
                    INSERT INTO heatmaps (Generated_At, Traffic_Type, Date_Filter, Time_Filter, Status, Heatmap_URL)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    generated_at,
                    selected_type,
                    date_filter,
                    time_filter,
                    "Generated",
                    heatmap_url
                ))
                console.print(f"[green]✅ Inserted new heatmap row[/green]")

            conn.commit()
            cursor.close()
            conn.close()
        except mysql.connector.Error as e:
            console.print(f"[red]❌ DB insert/update failed:[/red] {e}")
            return

    # ⏱️ Delegate log printing and saving
    log_heatmap_duration(date_filter, time_filter, selected_type, season_filter, timings, start)


# =====================================================
# ▶️ ONLY RUN WHEN THIS FILE IS RUN DIRECTLY (NOT WHEN IMPORTED)
# =====================================================
if __name__ == "__main__":
    generate_heatmap("2025-02-27", "01:00:00", "Vehicle Count")
    generate_heatmap("2025-02-27", "01:00:00", "Pedestrian Count")
