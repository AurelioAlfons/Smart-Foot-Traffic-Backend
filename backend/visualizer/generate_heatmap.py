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
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn

# 🔧 Allow importing files from the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# ✅ Import logic modules
from backend.config import DB_CONFIG
from backend.forecast.temperature import assign_temperature
from backend.forecast.weather import assign_weather
from backend.visualizer.services.data_fetcher import fetch_traffic_data
from backend.visualizer.services.map_renderer import render_heatmap_map

console = Console()

# 🔎 Check if weather data already exists for date
def weather_exists(date_filter):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM weather_season_data 
            WHERE DATE(Date_ID) = %s LIMIT 1
        """, (date_filter,))
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists
    except mysql.connector.Error:
        return False

# 🔎 Check if temperature data already exists for date
def temperature_exists(date_filter):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM weather_season_data 
            WHERE DATE(Date_ID) = %s AND Temperature IS NOT NULL LIMIT 1
        """, (date_filter,))
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists
    except mysql.connector.Error:
        return False

# 🔥 Main function to generate the heatmap and save as HTML
def generate_heatmap(date_filter=None, time_filter=None, selected_type="Pedestrian Count", season_filter=None):
    label = season_filter if season_filter else date_filter

    heatmap_url = None
    existing_id = None

    # 🧱 Prepare filename early for fast checks
    filename = os.path.join(
        "heatmaps",
        f"heatmap_{label}_{(time_filter or 'all').replace(':', '-')}_{selected_type.replace(' ', '_')}.html"
    )

    # 🔍 Check database for existing entry
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

        # ✅ If file already exists, skip everything else
        if os.path.exists(filename):
            console.print(f"[green]✅ Skipping generation. File already exists: {filename}[/green]")
            return

        cursor.close()
        conn.close()

    except mysql.connector.Error as e:
        console.print(f"[red]❌ DB check failed:[/red] {e}")
        return

    console.print(f"\n📌 Generating heatmap for: [bold magenta]{selected_type}[/bold magenta] at [cyan]{label}[/cyan]")

    progress = Progress(
        TextColumn("[bold cyan]🔄 Progress"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.1f}%",
        TimeElapsedColumn(),
        console=console
    )

    with progress:
        task = progress.add_task("Fetching data...", total=3)

        # 🧠 Auto-fetch weather & temperature if not assigned yet
        console.print("🔍 Checking for missing weather or temperature...")
        if not weather_exists(date_filter):
            assign_weather(date_filter)
        else:
            console.print(f"[green]✅ Weather already assigned for {date_filter}[/green]")

        if not temperature_exists(date_filter):
            assign_temperature(date_filter)
        else:
            console.print(f"[green]✅ Temperature already assigned for {date_filter}[/green]")

        # 📊 Load and prepare the data
        df = fetch_traffic_data(date_filter=date_filter, time_filter=time_filter, selected_type=selected_type, season_filter=season_filter)

        progress.update(task, advance=1, description="Creating map...")

        # 📜 Generate folium map object
        base_map = render_heatmap_map(df, selected_type, label, time_filter)

        progress.update(task, advance=1, description="Saving file...")

        # 📁 Save the map to HTML
        os.makedirs("heatmaps", exist_ok=True)
        with open(filename, "w", encoding="utf-8", errors="ignore") as f:
            f.write(base_map.get_root().render())

        progress.update(task, advance=1)

        # 📆 Store or update metadata
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

    console.print(f"\n🚀 [bold green]Done![/bold green] Map saved as [bold]{filename}[/bold]\n")

# =====================================================
# 🧪 Placeholder: Simulating User Input for Testing
# =====================================================
# This function is used to simulate real user input (date, time,
# traffic type, and optional season) before connecting with
# the actual Flutter frontend.
# 
# Later, Flutter will POST real user selections here dynamically.
# =====================================================
def generate_from_user_input(userSelectedDate, userSelectedTime, userSelectedType, userSelectedSeason=None):
    generate_heatmap(
        date_filter=userSelectedDate,
        time_filter=userSelectedTime,
        selected_type=userSelectedType,
        season_filter=userSelectedSeason
    )

# =====================================================
# ▶️ ONLY RUN WHEN THIS FILE IS RUN DIRECTLY (NOT WHEN IMPORTED)
# =====================================================
if __name__ == "__main__":
    generate_heatmap("2025-02-27", "01:00:00", "Vehicle Count")
    generate_heatmap("2025-02-27", "01:00:00", "Pedestrian Count")
    # generate_heatmap(...)
# generate_heatmap(None, None, "Vehicle Count", "Autumn")
