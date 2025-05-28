# =====================================================
# Weather & Temperature Filler for Smart Foot Traffic
# -----------------------------------------------------
# - Finds dates with missing weather or temp
# - Calls weather and temperature functions for each
# - Shows progress bar and logs status
# =====================================================

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# =====================================================
# Assign weather and temperature for all missing rows
# =====================================================

import mysql.connector
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn
from rich.console import Console

from backend.forecast.weather import assign_weather
from backend.forecast.temperature import assign_temperature
from backend.config import DB_CONFIG

console = Console()

console.print("\n[bold cyan]========================================[/bold cyan]")
console.print("[bold magenta]Assigning real weather and temperature...[/bold magenta]")
console.print("[bold cyan]========================================[/bold cyan]")

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT pd.Date
        FROM processed_data pd
        JOIN weather_season_data wsd ON pd.Data_ID = wsd.Data_ID
        WHERE wsd.Weather = 'Undefined' OR wsd.Temperature IS NULL
    """)
    dates = [row[0].strftime('%Y-%m-%d') for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    if not dates:
        console.print("[bold yellow]No dates found with missing weather or temperature.[/bold yellow]")
    else:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[green]Processing dates...", total=len(dates))

            for date in dates:
                assign_weather(date)
                assign_temperature(date)
                progress.update(task, advance=1)

        console.print(f"\n[bold green]Assigned real weather and temperature for {len(dates)} date(s).[/bold green]")

except Exception as e:
    console.print(f"[bold red]Error assigning weather/temp: {e}[/bold red]")
