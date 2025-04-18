# ========================================
# 📦 IMPORT MODULES
# ========================================
import os                 
import time               
import pandas as pd       
import mysql.connector    
from config import DB_CONFIG  
import logging            
from datetime import datetime
from collections import defaultdict  
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
TRAFFIC_TYPES = ['Pedestrian Count', 'Cyclist Count', 'Vehicle Count']
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

    # Progress tracking
    traffic_seen = set()
    file_index_tracker = {t: 0 for t in TRAFFIC_TYPES}

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

        for traffic, path in file_map:
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

            # Read and clean data
            try:
                df = pd.read_csv(path)
                if 'date' not in df.columns or 'value' not in df.columns:
                    logging.warning("⚠️ Skipping — missing 'date' or 'value'")
                    continue

                df.drop_duplicates(inplace=True)
                location = extract_location(path)

                # Convert and adjust timezone
                df['Date_Time'] = pd.to_datetime(df['date'], errors='coerce', utc=True)
                df['Date_Time'] = df['Date_Time'].dt.tz_convert('Australia/Melbourne').dt.tz_localize(None)
                df.dropna(subset=['Date_Time'], inplace=True)

                # Create date/time columns
                df['Date'] = df['Date_Time'].dt.date.astype(str)
                df['Time'] = df['Date_Time'].dt.time.astype(str)
                df['Date_Time'] = df['Date_Time'].dt.strftime('%Y-%m-%d %H:%M:%S')

                # Clean traffic count values
                df['value'] = df['value'].fillna(df['value'].median()).astype(int)
                df.sort_values(by='Date_Time', inplace=True)

                # Process each row
                inserted = 0
                failed_processed = 0
                failed_traffic = 0

                for _, row in df.iterrows():
                    try:
                        # Insert into processed_data
                        cursor.execute("""
                            INSERT INTO processed_data (Date_Time, Date, Time, Location)
                            VALUES (%s, %s, %s, %s)
                        """, (row['Date_Time'], row['Date'], row['Time'], location))
                        data_id = cursor.lastrowid

                        # CORRECTED: Using Total_Count instead of Traffic_Count
                        cursor.execute("""
                            INSERT INTO traffic_counts (Data_ID, Traffic_Type, Total_Count, Interval_Count)
                            VALUES (%s, %s, %s, %s)
                        """, (data_id, traffic, int(row['value']), int(row['Interval_Count'])))
                        inserted += 1

                    except mysql.connector.Error as e:
                        conn.rollback()
                        failed_traffic += 1
                        logging.error(f"❌ Insert failed for Data_ID {data_id}: {e}")
                        continue

                    progress.update(task, advance=1)

                # Show file results
                elapsed = round(time.time() - start_time, 2)
                console.print(f"\n[green]✅ [INSERTED][/green] {inserted} rows")
                console.print(f"⏱️ [italic]Took {elapsed} seconds[/italic]")
                if failed_processed or failed_traffic:
                    console.print(f"[red]❌ [FAILED][/red] Processed: {failed_processed}, Traffic: {failed_traffic}")
                console.print("[grey70]" + "-" * 60 + "[/grey70]")

            except Exception as e:
                logging.error(f"❌ File processing failed: {e}")
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