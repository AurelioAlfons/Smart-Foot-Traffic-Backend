# ========================================
# 📦 IMPORT MODULES
# ========================================
import os
import time
import pandas as pd
import mysql.connector
import logging
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn

# 🔧 Enable importing helpers and DB config
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.config import DB_CONFIG
from backend.pipeline.helpers.helpers import (
    extract_location, check_missing_hours,
    TRAFFIC_TYPES, FOLDER_ICONS
)

# ========================================
# 🛠️ SETUP LOGGING AND CONSOLE
# ========================================
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
console = Console()

# ========================================
# 🚀 MAIN FUNCTION TO PROCESS ALL DATA
# ========================================
def preprocess_data():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))

    # 🔌 Connect to MySQL
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info("🔌 Connected to MySQL")
    except mysql.connector.Error as e:
        logging.error(f"❌ Connection failed: {e}")
        return

    total_rows = 0
    file_map = []
    max_files = {
        'Pedestrian Count': 11,
        'Cyclist Count': 11,
        'Vehicle Count': 9
    }

    # 🔍 Read and count rows from selected CSVs
    for traffic in TRAFFIC_TYPES:
        folder = os.path.join(base_path, traffic)
        if not os.path.exists(folder):
            continue

        files = sorted([f for f in os.listdir(folder) if f.endswith('.csv')])[:max_files[traffic]]
        for file in files:
            path = os.path.join(folder, file)
            try:
                df = pd.read_csv(path)
                total_rows += len(df)
                file_map.append((traffic, path))
            except:
                continue

    traffic_seen = set()
    file_index_tracker = {t: 0 for t in TRAFFIC_TYPES}

    progress = Progress(
        TextColumn("[bold green]📈 Preprocessing Progress"),
        BarColumn(bar_width=None, complete_style="green"),
        "[progress.percentage]{task.percentage:>3.1f}%",
        TimeElapsedColumn(),
        console=console
    )

    with progress:
        task = progress.add_task("Processing...", total=total_rows)

        for traffic, path in file_map:
            if traffic not in traffic_seen:
                traffic_seen.add(traffic)
                console.print(f"\n[bold yellow]{FOLDER_ICONS[traffic]} Starting {traffic}[/bold yellow]")

            file_index_tracker[traffic] += 1
            file_name = os.path.basename(path)
            index = file_index_tracker[traffic]
            max_count = max_files[traffic]
            console.print(f"\n[cyan]📂 [PROCESSING {index}/{max_count}][/cyan]: {file_name}")
            start_time = time.time()

            try:
                df = pd.read_csv(path)
            except Exception as e:
                logging.error(f"❌ Couldn't read file: {e}")
                continue

            if 'date' not in df.columns or 'value' not in df.columns:
                logging.warning("⚠️ Skipping — missing 'date' or 'value'")
                continue

            df.drop_duplicates(inplace=True)
            location = extract_location(path)

            # 🕒 Convert to Melbourne time and round to nearest hour
            df['Date_Time'] = pd.to_datetime(df['date'], errors='coerce', utc=True)
            df.dropna(subset=['Date_Time'], inplace=True)

            # Convert from UTC to Australia/Melbourne
            df['Date_Time'] = df['Date_Time'].dt.tz_convert('Australia/Melbourne')

            # 🧠 Floor to the start of the hour safely
            # ➕ Avoid DST ambiguity by setting ambiguous='infer'
            df['Date_Time'] = df['Date_Time'].dt.floor('h', ambiguous='infer')

            # Remove timezone info (naive datetime) before storing in MySQL
            df['Date_Time'] = df['Date_Time'].dt.tz_localize(None)

            # 🧮 Group by hour and sum traffic values
            df = df.groupby('Date_Time', as_index=False)['value'].sum()

            # ⏱ Extract date and time fields
            df['Date'] = df['Date_Time'].dt.date.astype(str)
            df['Time'] = df['Date_Time'].dt.time.astype(str)
            df['Date_Time'] = df['Date_Time'].dt.strftime('%Y-%m-%d %H:%M:%S')

            df['value'] = df['value'].fillna(df['value'].median())
            df.sort_values(by='Date_Time', inplace=True)

            # 🧠 Reset interval count logic grouped by date
            df['Date_Only'] = pd.to_datetime(df['Date_Time']).dt.date
            interval_list = []

            for _, group in df.groupby('Date_Only'):
                group = group.sort_values(by='Date_Time')
                last_total = None
                for _, row in group.iterrows():
                    current_total = row['value']
                    if last_total is None:
                        interval = int(current_total)
                    else:
                        interval = max(0, int(current_total - last_total))
                    interval_list.append(interval)
                    last_total = current_total

            # ✅ Assign interval counts
            df['Interval_Count'] = interval_list
            df.drop(columns=['Date_Only'], inplace=True)

            inserted = 0
            failed_processed = 0
            failed_traffic = 0

            for _, row in df.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO processed_data (Date_Time, Date, Time, Location)
                        VALUES (%s, %s, %s, %s)
                    """, (row['Date_Time'], row['Date'], row['Time'], location))
                    data_id = cursor.lastrowid

                    try:
                        cursor.execute("""
                            INSERT INTO traffic_counts (Data_ID, Traffic_Type, Total_Count, Interval_Count)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            data_id, traffic,
                            int(row['value']),
                            int(row['Interval_Count'])
                        ))
                        inserted += 1

                    except mysql.connector.Error as e:
                        conn.rollback()
                        failed_traffic += 1
                        logging.error(f"❌ traffic_counts error for ID {data_id}: {e}")

                except mysql.connector.Error as e:
                    failed_processed += 1
                    logging.error(f"❌ processed_data error: {e}")
                    continue

                progress.update(task, advance=1)

            elapsed = round(time.time() - start_time, 2)
            console.print(f"\n[green]✅ Inserted:[/green] {inserted} rows from: {file_name}")
            console.print(f"⏱️ Took {elapsed} seconds")

            if failed_processed or failed_traffic:
                console.print(f"[red]❌ Failed[/red] Processed: {failed_processed}, Traffic: {failed_traffic}")
            console.print("[grey70]" + "-" * 60 + "[/grey70]")

    conn.commit()
    logging.info("📦 All CSVs committed to MySQL.")
    logging.info("🔍 Checking missing hours...")
    check_missing_hours(cursor)

    cursor.close()
    conn.close()
    logging.info("🌟 All done!")

# ▶️ RUN SCRIPT
if __name__ == "__main__":
    preprocess_data()
