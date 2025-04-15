# ========================================
# 📦 IMPORT MODULES
# ========================================
import os                 # for working with folders and file paths
import time               # to track how long each file takes
import pandas as pd       # to load and clean CSV files
import mysql.connector    # to connect and insert into MySQL

# 🔧 Fix for running as subprocess (enables importing backend.config)
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.config import DB_CONFIG  # your database login config

import logging            # to show logs in the terminal
from datetime import datetime
from collections import defaultdict  # for tracking missing hours
from rich.console import Console     # to print colored progress
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn

# ========================================
# 🛠️ SETUP LOGGING AND VISUAL TOOLS
# ========================================
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
console = Console()

# ========================================
# 🛑 TYPES OF TRAFFIC WE CARE ABOUT
# ========================================
TRAFFIC_TYPES = ['Pedestrian Count', 'Cyclist Count', 'Vehicle Count']

# Add emojis for fun and clarity in logs
FOLDER_ICONS = {
    'Pedestrian Count': '🚶‍♂️',
    'Cyclist Count': '🚴‍♀️',
    'Vehicle Count': '🚗'
}

# ========================================
# 🔍 Extract location name from file name
# ========================================
# vehicle-count---footscray-library-car-park__2022.csv
def extract_location(filename):
    name = filename.lower().split('---')[-1]
    location = name.split('__')[0].replace('-', ' ').strip()
    # Result -> Footscray Library Car Park
    return location.title()

# ========================================
# 🚀 MAIN FUNCTION TO PROCESS ALL DATA
# ========================================
def preprocess_data():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))

    # 🔌 Connect to the database
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info("🔌 Connected to MySQL")
    except mysql.connector.Error as e:
        logging.error(f"❌ Connection failed: {e}")
        return

    # Prepare to track all files and rows
    total_rows = 0
    file_map = []

    # Limit max files per traffic type
    max_files = {
        'Pedestrian Count': 11,
        'Cyclist Count': 11,
        'Vehicle Count': 9
    }

    # 📂 Find all CSVs and count total rows
    # TRAFFIC_TYPES is declared on top
    for traffic in TRAFFIC_TYPES:
        # Combine base path with traffic type folder
        # e.g. data/Pedestrian Count
        # e.g. data/Cyclist Count
        # e.g. data/Vehicle Count
        # e.g. data/Vehicle Count/vehicle-count---footscray-library-car-park__2022.csv
        folder = os.path.join(base_path, traffic)
        if not os.path.exists(folder):
            continue

        # Grab the first N files only
        files = sorted([f for f in os.listdir(folder) if f.endswith('.csv')])[:max_files[traffic]]
        for file in files:
            path = os.path.join(folder, file)
            try:
                df = pd.read_csv(path)
                total_rows += len(df)
                file_map.append((traffic, path))
            except:
                continue

    # For keeping track of how many files we processed
    traffic_seen = set()
    file_index_tracker = {t: 0 for t in TRAFFIC_TYPES}

    # 🎯 Setup progress bar with Rich
    progress = Progress(
        TextColumn("[bold green]📈 Preprocessing Progress"),
        BarColumn(bar_width=None, complete_style="green"),
        "[progress.percentage]{task.percentage:>3.1f}%",
        TimeElapsedColumn(),
        console=console
    )

    # ========================================
    # 🔄 LOOP THROUGH ALL FILES AND INSERT DATA
    # ========================================
    with progress:
        task = progress.add_task("Processing...", total=total_rows)

        for traffic, path in file_map:
            # Show section header per traffic type
            if traffic not in traffic_seen:
                traffic_seen.add(traffic)
                console.print(f"\n[bold yellow]{FOLDER_ICONS[traffic]} Starting {traffic}[/bold yellow]\n")

            file_index_tracker[traffic] += 1
            index = file_index_tracker[traffic]
            max_count = max_files[traffic]

            file_name = os.path.basename(path)
            console.print(f"\n[cyan]📂 [PROCESSING #{index}/{max_count}][/cyan] {file_name}")
            console.print("=" * 60)
            start_time = time.time()

            # Try reading the CSV
            try:
                df = pd.read_csv(path)
            except Exception as e:
                logging.error(f"❌ Couldn't read file: {e}")
                continue

            # Check required columns exist
            if 'date' not in df.columns or 'value' not in df.columns:
                logging.warning("⚠️ Skipping — missing 'date' or 'value'")
                continue

            df.drop_duplicates(inplace=True)  # Remove repeated rows
            location = extract_location(path)  # Get location name

            # Convert date to datetime and adjust to Melbourne timezone
            df['Date_Time'] = pd.to_datetime(df['date'], errors='coerce', utc=True)
            df['Date_Time'] = df['Date_Time'].dt.tz_convert('Australia/Melbourne').dt.tz_localize(None)
            df.dropna(subset=['Date_Time'], inplace=True)

            # Split into Date and Time columns
            df['Date'] = df['Date_Time'].dt.date.astype(str)
            df['Time'] = df['Date_Time'].dt.time.astype(str)
            df['Date_Time'] = df['Date_Time'].dt.strftime('%Y-%m-%d %H:%M:%S')

            # Fill missing value with median
            df['value'] = df['value'].fillna(df['value'].median())

            # Sort by time and calculate interval count
            df.sort_values(by='Date_Time', inplace=True)
            df['Interval_Count'] = df.groupby('Date')['value'].diff().fillna(df['value']).clip(lower=0).astype(int)

            inserted = 0
            failed_processed = 0
            failed_traffic = 0

            # 🧾 Insert each row into MySQL
            for _, row in df.iterrows():
                try:
                    # Insert into processed_data table
                    cursor.execute("""
                        INSERT INTO processed_data (Date_Time, Date, Time, Location)
                        VALUES (%s, %s, %s, %s)
                    """, (row['Date_Time'], row['Date'], row['Time'], location))
                    data_id = cursor.lastrowid  # Get ID for traffic_counts

                    try:
                        # Insert into traffic_counts table
                        cursor.execute("""
                            INSERT INTO traffic_counts (Data_ID, Traffic_Type, Total_Count, Interval_Count)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            data_id,
                            traffic,
                            int(row['value']),
                            int(row['Interval_Count'])
                        ))
                        inserted += 1

                    except mysql.connector.Error as e:
                        conn.rollback()  # Cancel the last insert if traffic_counts fails
                        failed_traffic += 1
                        logging.error(f"❌ Insert failed for traffic_counts → Data_ID {data_id}: {e}")

                except mysql.connector.Error as e:
                    failed_processed += 1
                    logging.error(f"❌ Insert failed for processed_data: {e}")
                    continue

                # Update progress bar
                progress.update(task, advance=1)

            # Show final status per file
            elapsed = round(time.time() - start_time, 2)
            console.print(f"\n[green]✅ [INSERTED][/green] {inserted} rows from: {file_name}")
            console.print(f"⏱️ [italic]Took {elapsed} seconds[/italic]")

            if failed_processed or failed_traffic:
                console.print(f"[red]❌ [FAILED][/red] Processed: {failed_processed}, Traffic: {failed_traffic}")

            console.print("[grey70]" + "-" * 60 + "[/grey70]")

    # ✅ Commit everything at the end
    conn.commit()
    logging.info("📦 Finished inserting all CSV data.")

    # ✅ Run check to see if we have full hour data
    logging.info("🔎 Checking for missing hours by day/location...")
    check_missing_hours(cursor)

    # Close the connection
    cursor.close()
    conn.close()
    logging.info("🌟 All data saved to MySQL successfully!")

# ========================================
# 🕒 CHECK IF WE HAVE MISSING HOURS PER DAY
# ========================================
def check_missing_hours(cursor):
    query = """
    SELECT Date, Time, Location
    FROM processed_data
    WHERE Location = 'Footscray Library Car Park'
    ORDER BY Date, Time
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    time_data = defaultdict(list)

    for date, time, _ in rows:
        full_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
        time_data[date].append(full_dt.hour)

    for date, hours in time_data.items():
        missing_hours = sorted(set(range(24)) - set(hours))
        if missing_hours:
            logging.warning(f"🕒 {date} is missing hours: {missing_hours}")
        else:
            logging.info(f"✅ {date} has full 24-hour coverage")

# ========================================
# ▶️ START THE WHOLE PROGRAM
# ========================================
if __name__ == "__main__":
    preprocess_data()
