# ====================================================
# Heatmap Generator for Smart Foot Traffic
# ----------------------------------------------------
# - Builds HTML heatmap based on traffic data
# - Assigns weather/temp and renders map
# - Saves map file and updates DB with metadata
# - Used by smart_generate and CLI runs
# ====================================================

from rich.console import Console
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn
import os, time
from datetime import datetime
import mysql.connector
from threading import Thread
from rich.errors import LiveError

from backend.visualizer.services.heatmap_log import log_heatmap_duration
from backend.config import DB_CONFIG
from backend.forecast.temperature import assign_temperature
from backend.forecast.weather import assign_weather
from backend.visualizer.services.data_fetcher import fetch_traffic_data
from backend.visualizer.services.map_renderer import render_heatmap_map

console = Console()

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
        return result[0] == 1, result[1] == 1
    except mysql.connector.Error:
        return False, False

def generate_heatmap(date_filter, time_filter, selected_type="Pedestrian Count", quiet=False, df=None):
    start = time.time()
    label = date_filter
    timings = {}

    def mark(name):
        timings[name] = time.time()

    filename = os.path.join(
        "heatmaps",
        f"heatmap_{label}_{(time_filter or 'all').replace(':', '-')}_{selected_type.replace(' ', '_')}.html"
    )

    if os.path.exists(filename):
        if not quiet:
            console.print(f"[green]Skipping (already exists): {filename}[/green]")
        return

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
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        if not quiet:
            console.print(f"[red]DB check failed:[/red] {e}")
        return

    if not quiet:
        console.print(f"\nGenerating: [bold magenta]{selected_type}[/bold magenta] @ [cyan]{date_filter} {time_filter}[/cyan]")

    try:
        if quiet:
            weather_ok, temp_ok = check_weather_and_temp_exists(date_filter)
            if df is None or getattr(df, "empty", True):
                df = fetch_traffic_data(date_filter, time_filter, selected_type)

            if not (weather_ok and temp_ok):
                def background_weather_temp():
                    if not weather_ok:
                        assign_weather(date_filter)
                    if not temp_ok:
                        assign_temperature(date_filter)
                    console.print(f"[green]\u2705 Weather/temp background assignment finished for {date_filter}[/green]")
                Thread(target=background_weather_temp, daemon=True).start()

            base_map = render_heatmap_map(df, selected_type, label, time_filter)
            os.makedirs("heatmaps", exist_ok=True)
            html = base_map.get_root().render()
            minified = ''.join(line.strip() for line in html.splitlines())
            with open(filename, "w", encoding="utf-8", errors="ignore") as f:
                f.write(minified)

        else:
            with Progress(
                TextColumn("[bold cyan]{task.description}"),
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task_id = progress.add_task("Generating Heatmap", total=6)

                weather_ok, temp_ok = check_weather_and_temp_exists(date_filter)

                if not (weather_ok and temp_ok):
                    def background_weather_temp():
                        if not weather_ok:
                            assign_weather(date_filter)
                        if not temp_ok:
                            assign_temperature(date_filter)
                    Thread(target=background_weather_temp, daemon=True).start()

                progress.advance(task_id, 2)
                mark("weather")
                mark("temperature")

                if df is None or getattr(df, "empty", True):
                    df = fetch_traffic_data(date_filter, time_filter, selected_type)
                progress.advance(task_id)
                mark("fetch")

                base_map = render_heatmap_map(df, selected_type, label, time_filter)
                progress.advance(task_id)
                mark("render")

                os.makedirs("heatmaps", exist_ok=True)
                html = base_map.get_root().render()
                minified = ''.join(line.strip() for line in html.splitlines())
                with open(filename, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(minified)
                progress.advance(task_id)
                mark("save")

    except LiveError:
        if not quiet:
            print("Rich LiveError: running in headless mode.")

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        base_url = os.getenv("BASE_URL", "http://localhost:5000")
        prod_url = os.getenv("PROD_URL", "https://smart-foot-traffic-backend.onrender.com")

        if "localhost" in base_url or "127.0.0.1" in base_url:
            heatmap_url = f"{base_url}/heatmaps/{filename}"
        else:
            heatmap_url = f"{prod_url}/heatmaps/{filename}"

        if existing_id:
            cursor.execute("""
                UPDATE heatmaps
                SET Generated_At = %s, Heatmap_URL = %s, Status = 'Regenerated'
                WHERE Heatmap_ID = %s
            """, (generated_at, heatmap_url, existing_id))
            if not quiet:
                console.print(f"[green]Updated heatmap ID {existing_id}[/green]")
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
            if not quiet:
                console.print(f"[green]Inserted new heatmap record[/green]")

        conn.commit()
        cursor.close()
        conn.close()

        if not quiet:
            mark("db")
            log_heatmap_duration(date_filter, time_filter, selected_type, None, timings, start)

    except mysql.connector.Error as e:
        if not quiet:
            console.print(f"[red]DB insert/update failed:[/red] {e}")

if __name__ == "__main__":
    generate_heatmap("2025-02-27", "01:00:00", "Vehicle Count")
