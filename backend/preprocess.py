# ========================================
# 📦 IMPORT MODULES
# ========================================
import os
import time
import pandas as pd
import mysql.connector
from config import DB_CONFIG
import logging
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn

# ========================================
# 🛠️ SETUP LOGGING AND VISUAL TOOLS
# ========================================
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
console = Console()

# ========================================
# 🛑 TYPES OF TRAFFIC WE CARE ABOUT
# ========================================
# Map folder names to database enum values
TRAFFIC_TYPES = {
    'Pedestrian Count': 'Pedestrian_Count',
    'Cyclist Count': 'Cyclist_Count',
    'Vehicle Count': 'Vehicle_Count'
}
FOLDER_ICONS = {
    'Pedestrian Count': '🚶‍♂️',
    'Cyclist Count': '🚴‍♀️',
    'Vehicle Count': '🚗'
}

# ========================================
# 🔍 Extract location name from file name
# ========================================
def extract_location(filename):
    name = filename.lower().split('---')[-1]
    location = name.split('__')[0].replace('-', ' ').strip()
    return location.title()

# ========================================
# 🚀 MAIN PROCESSING FUNCTION
# ========================================
def preprocess_data():
    base_path = os.path.join(os.path.dirname(__file__), 'data')

    # 🔌 Database connection
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info("🔌 Connected to MySQL")
    except mysql.connector.Error as e:
        logging.error(f"❌ Connection failed: {e}")
        return

    # File processing setup
    total_rows = 0
    file_map = []
    max_files = {
        'Pedestrian Count': 11,
        'Cyclist Count': 11,
        'Vehicle Count': 9
    }

    # 📂 Count total rows
    for traffic_folder, traffic_db in TRAFFIC_TYPES.items():
        folder = os.path.join(base_path, traffic_folder)
        if not os.path.exists(folder):
            continue

        files = sorted([f for f in os.listdir(folder) if f.endswith('.csv')])[:max_files[traffic_folder]]
        for file in files:
            path = os.path.join(folder, file)
            try:
                df = pd.read_csv(path)
                total_rows += len(df)
                file_map.append((traffic_folder, path))
            except:
                continue

    # Progress tracking
    traffic_seen = set()
    file_index_tracker = {t: 0 for t in TRAFFIC_TYPES.keys()}

    # 🎯 Progress bar setup
    progress = Progress(
        TextColumn("[bold green]📈 Preprocessing Progress"),
        BarColumn(bar_width=None, complete_style="green"),
        "[progress.percentage]{task.percentage:>3.1f}%",
        TimeElapsedColumn(),
        console=console
    )

    # ========================================
    # 🔄 PROCESS ALL FILES
    # ========================================
    with progress:
        task = progress.add_task("Processing...", total=total_rows)

        for traffic_folder, path in file_map:
            if traffic_folder not in traffic_seen:
                traffic_seen.add(traffic_folder)
                console.print(f"\n[bold yellow]{FOLDER_ICONS[traffic_folder]} Starting {traffic_folder}[/bold yellow]\n")

            file_index_tracker[traffic_folder] += 1
            index = file_index_tracker[traffic_folder]
            max_count = max_files[traffic_folder]

            file_name = os.path.basename(path)
            console.print(f"\n[cyan]📂 [PROCESSING #{index}/{max_count}][/cyan] {file_name}")
            console.print("=" * 60)
            start_time = time.time()

            # Read and clean data
            try:
                df = pd.read_csv(path)
                df.columns = df.columns.str.strip().str.lower()  # Standardize column names

                # Handle missing Interval_Count
                if 'interval_count' not in df.columns:
                    df['interval_count'] = 1  # Default value

                # Validate required columns
                required_columns = ['date', 'value']
                if not all(col in df.columns for col in required_columns):
                    logging.warning(f"⚠️ Skipping {file_name} — missing required columns")
                    continue

                # Clean data
                df = df.drop_duplicates().dropna(subset=['date'])
                location = extract_location(file_name)

                # Convert datetime
                df['date_time'] = pd.to_datetime(df['date'], errors='coerce', utc=True)
                df['date_time'] = df['date_time'].dt.tz_convert('Australia/Melbourne').dt.tz_localize(None)
                df = df.dropna(subset=['date_time'])

                # Extract date/time components
                df['date'] = df['date_time'].dt.date.astype(str)
                df['time'] = df['date_time'].dt.time.astype(str)
                df['date_time'] = df['date_time'].dt.strftime('%Y-%m-%d %H:%M:%S')

                # Clean numerical values
                df['value'] = pd.to_numeric(df['value'], errors='coerce').fillna(0).astype(int)
                df['interval_count'] = pd.to_numeric(df['interval_count'], errors='coerce').fillna(1).astype(int)

                # Process each row
                inserted = 0
                failed_rows = 0

                for _, row in df.iterrows():
                    try:
                        # Insert into processed_data
                        cursor.execute("""
                            INSERT INTO processed_data (Date_Time, Date, Time, Location)
                            VALUES (%s, %s, %s, %s)
                        """, (row['date_time'], row['date'], row['time'], location))
                        data_id = cursor.lastrowid

                        # Map traffic type to database enum
                        traffic_db = TRAFFIC_TYPES[traffic_folder]

                        # Insert into traffic_counts
                        cursor.execute("""
                            INSERT INTO traffic_counts (Data_ID, Traffic_Type, Total_Count, Interval_Count)
                            VALUES (%s, %s, %s, %s)
                        """, (data_id, traffic_db, row['value'], row['interval_count']))
                        inserted += 1

                    except mysql.connector.Error as e:
                        conn.rollback()
                        failed_rows += 1
                        logging.error(f"❌ Insert failed: {e}")
                        continue

                    progress.update(task, advance=1)

                # Show file results
                elapsed = round(time.time() - start_time, 2)
                console.print(f"\n[green]✅ [INSERTED][/green] {inserted} rows")
                console.print(f"[red]❌ [FAILED][/red] {failed_rows} rows")
                console.print(f"⏱️ [italic]Took {elapsed} seconds[/italic]")
                console.print("[grey70]" + "-" * 60 + "[/grey70]")

            except Exception as e:
                logging.error(f"❌ File processing failed: {str(e)}")
                continue

    # Final commit and cleanup
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("🌟 All data saved successfully!")

# ========================================
# ▶️ ENTRY POINT
# ========================================
if __name__ == "__main__":
    preprocess_data()