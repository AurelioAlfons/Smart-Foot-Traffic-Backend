# ===========================================================
# Helper Functions for Smart Foot Traffic Preprocessing
# -----------------------------------------------------------
# - Defines traffic types and folder icons
# - Extracts clean location names from filenames
# - Checks for missing hourly data across all locations/types
# - Used in preprocessing pipeline scripts
# ===========================================================

import logging
from datetime import datetime
from collections import defaultdict

# =====================================================
# TYPES OF TRAFFIC USED IN PROJECT
# These labels match folder names and DB values
# =====================================================
TRAFFIC_TYPES = ['Pedestrian Count', 'Cyclist Count', 'Vehicle Count']

# =====================================================
# EMOJIS FOR LOGGING / VISUAL SECTIONS
# The traffic type folders emojis
# =====================================================
FOLDER_ICONS = {
    'Pedestrian Count': '🪅',
    'Cyclist Count': '🚲',
    'Vehicle Count': '🚗'
}

# =====================================================
# EXTRACT LOCATION FROM FILE NAME
# Converts: vehicle-count---footscray-market__2022.csv
# Into: Footscray Market
# =====================================================
def extract_location(filename):
    # Get the part after the last '---'
    # [-1] means the last part after splitting by '---'
    name = filename.lower().split('---')[-1]

    # Remove everything after '__' and replace dashes with spaces
    location = name.split('__')[0].replace('-', ' ').strip()

    # Capitalize first letter of each word
    return location.title()

# =====================================================
# CHECK FOR MISSING HOURS PER DAY
# Used to make sure each day has 24 full hours of data
# for one specific location (editable inside query)
# =====================================================
from rich.console import Console
from collections import defaultdict
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn

console = Console()

def check_missing_hours(cursor):
    # Get all unique locations and traffic types from the database
    cursor.execute("SELECT DISTINCT Location FROM processed_data")
    locations = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT Traffic_Type FROM traffic_counts")
    traffic_types = [row[0] for row in cursor.fetchall()]

    # Data structures to track full vs missing hours
    missing_summary = defaultdict(list)
    full_coverage = []

    # Setup the rich progress bar UI
    with Progress(
        TextColumn("[bold cyan]Checking:[/bold cyan] {task.fields[desc]}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Checking...", total=len(locations) * len(traffic_types), desc="")

        for location in locations:
            for traffic in traffic_types:
                desc = f"{location} ({traffic})"
                progress.update(task, desc=desc)

                # Get all rows for this location and traffic type
                cursor.execute("""
                    SELECT pd.Date, pd.Time
                    FROM processed_data pd
                    JOIN traffic_counts tc ON pd.Data_ID = tc.Data_ID
                    WHERE pd.Location = %s AND tc.Traffic_Type = %s
                    ORDER BY pd.Date, pd.Time
                """, (location, traffic))
                rows = cursor.fetchall()

                # Group time entries by date
                time_data = defaultdict(list)
                for date, time in rows:
                    full_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
                    time_data[date].append(full_dt.hour)

                # Check for missing hours (0–23)
                any_missing = False
                for date, hours in time_data.items():
                    missing_hours = sorted(set(range(24)) - set(hours))
                    if missing_hours:
                        any_missing = True
                        key = f"{location} ({traffic})"
                        missing_summary[key].append((date, missing_hours))

                if not any_missing:
                    full_coverage.append(f"{location} ({traffic})")

                progress.advance(task)

    # Display locations with full coverage
    if full_coverage:
        console.print("\n[green]Locations with full 24-hour coverage:[/green]")
        for entry in sorted(full_coverage):
            console.print(f" - {entry}")

    # Grouped report for locations with missing data
    if missing_summary:
        console.print("\n[bold red]Missing Hour Report (Grouped by Location):[/bold red]\n")

        # Group missing data by location and traffic type
        grouped_by_location = defaultdict(lambda: defaultdict(list))
        for full_key, date_hours in missing_summary.items():
            location, traffic_type = full_key.rsplit(" (", 1)
            traffic_type = traffic_type.rstrip(")")
            grouped_by_location[location][traffic_type].extend(date_hours)

        for location in sorted(grouped_by_location.keys()):
            console.print(f"[bold]📍 -- {location} --[/bold]")

            for i, (traffic_type, missing_list) in enumerate(sorted(grouped_by_location[location].items()), start=1):
                label = chr(64 + i)  # A, B, C...
                console.print(f"[yellow]{label}. {traffic_type}:[/yellow]")

                for date, hours in missing_list:
                    console.print(f"    • [blue]{date}[/blue] → missing hours: {hours}")

                console.print()  # spacing

            console.print("[grey70]" + "=" * 50 + "[/grey70]")

    else:
        console.print("\n[green]No missing hours detected across all traffic types and locations![/green]")
