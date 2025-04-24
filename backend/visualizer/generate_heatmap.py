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
from backend.visualizer.services.db_logger import log_heatmap_to_db

console = Console()

# 🔥 Main function to generate the heatmap and save as HTML
def generate_heatmap(date_filter=None, time_filter=None, selected_type="Pedestrian Count", season_filter=None):
    label = season_filter if season_filter else date_filter

    # 🚫 Check for duplicate filter in DB
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM heatmaps
            WHERE Traffic_Type = %s AND Date_Filter = %s AND Time_Filter = %s
        """, (selected_type, date_filter, time_filter))

        (count,) = cursor.fetchone()
        cursor.close()
        conn.close()

        if count > 0:
            console.print(f"[yellow]⚠️ Heatmap already exists for {selected_type} on {date_filter} at {time_filter}. Skipping generation.[/yellow]")
            return

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
        assign_weather(date_filter)
        assign_temperature(date_filter)

        # 📊 Load and prepare the data
        df = fetch_traffic_data(date_filter=date_filter, time_filter=time_filter, selected_type=selected_type, season_filter=season_filter)

        progress.update(task, advance=1, description="Creating map...")

        # 📜 Generate folium map object
        base_map = render_heatmap_map(df, selected_type, label, time_filter)

        progress.update(task, advance=1, description="Saving file...")

        # 📁 Save the map as an HTML file
        os.makedirs("heatmaps", exist_ok=True)
        filename = os.path.join(
            "heatmaps",
            f"heatmap_{label}_{(time_filter or 'all').replace(':', '-')}_{selected_type.replace(' ', '_')}.html"
        )

        with open(filename, "w", encoding="utf-8", errors="ignore") as f:
            f.write(base_map.get_root().render())

        progress.update(task, advance=1)

        # 📆 Store heatmap metadata in the database
        success = log_heatmap_to_db(filename, selected_type, date_filter, time_filter)
        if success:
            console.print(f"[green]✅ Heatmap metadata inserted into heatmaps table.[/green]")
        else:
            console.print(f"[red]❌ Failed to insert heatmap into DB.[/red]")

    console.print(f"\n🚀 [bold green]Done![/bold green] Map saved as [bold]{filename}[/bold]\n")

# ▶️ Run example
generate_heatmap("2025-02-27", "12:00:00", "Pedestrian Count")
generate_heatmap("2025-02-27", "12:00:00", "Vehicle Count")
# generate_heatmap("2025-02-28", "12:00:00", "Pedestrian Count")
# generate_heatmap("2025-02-28", "12:00:00", "Vehicle Count")
# generate_heatmap("2025-03-03", "12:00:00", "Pedestrian Count")
# generate_heatmap("2025-03-03", "01:00:00", "Vehicle Count")
# generate_heatmap("2024-04-11", "20:00:00", "Vehicle Count")
# generate_heatmap("2025-03-03", "12:00:00", "Cyclist Count")
# generate_heatmap("2025-03-03", "12:00:00", "Pedestrian Count")
# generate_heatmap(None, None, "Vehicle Count", "Autumn")
