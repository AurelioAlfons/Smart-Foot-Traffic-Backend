# ========================================
# 📦 IMPORT MODULES
# ========================================
import mysql.connector       # for connecting to the MySQL database
import logging               # for printing logs like success/failure
from datetime import datetime
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn
from rich.console import Console

# 🔧 Fix for running as subprocess (enables importing backend.config)
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# ========================================
# 🛠️ SETUP LOGGING AND RICH CONSOLE
# ========================================
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
console = Console()

# ========================================
# 🗄️ DATABASE CONNECTION SETTINGS
# ========================================
from backend.config import DB_CONFIG

# ========================================
# 🍁 FUNCTION TO DETERMINE SEASON FROM MONTH
# ========================================
def get_season(month):
    if month in [12, 1, 2]:
        return "Summer"
    elif month in [3, 4, 5]:
        return "Autumn"
    elif month in [6, 7, 8]:
        return "Winter"
    else:
        return "Spring"

# ========================================
# 🌤️ MAIN FUNCTION: ASSIGN SEASON (Weather is 'Unknown')
# ========================================
def assign_weather_and_season():
    # --- Try to connect to the database ---
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info("🔌 Connected to MySQL")
    except mysql.connector.Error as e:
        logging.error(f"❌ Connection failed: {e}")
        return

    # --- Start processing ---
    logging.info("🌦️ Starting assignment of SEASON only (weather='Unknown')...")

    # --- Get all rows from processed_data ---
    cursor.execute("SELECT Data_ID, Date FROM processed_data")
    rows = cursor.fetchall()
    logging.info(f"📋 Retrieved {len(rows)} rows from processed_data")

    inserted = 0  # track how many rows we insert

    # --- Setup a progress bar for fun ---
    progress = Progress(
        TextColumn("[bold green]📅 Assigning Season"),
        BarColumn(bar_width=None, complete_style="green"),
        "[progress.percentage]{task.percentage:>3.1f}%",
        TimeElapsedColumn(),
        console=console
    )

    # --- Loop through all rows and assign season ---
    with progress:
        task = progress.add_task("Processing...", total=len(rows))

        for data_id, date in rows:
            try:
                # convert string date to datetime format
                if isinstance(date, str):
                    date = datetime.strptime(date, "%Y-%m-%d")

                # get season from the month
                season = get_season(date.month)

                # insert into weather_season_data table
                cursor.execute("""
                    INSERT INTO weather_season_data (Data_ID, Weather, Season)
                    VALUES (%s, %s, %s)
                """, (data_id, "Unknown", season))

                inserted += 1
                progress.update(task, advance=1)

            except Exception as e:
                logging.warning(f"⚠️ Skipping Data_ID {data_id} — {e}")
                progress.update(task, advance=1)
                continue

    # --- Save to DB and close everything ---
    conn.commit()
    cursor.close()
    conn.close()

    logging.info(f"🏁 Finished inserting {inserted} records with season (weather='Unknown').")

# ========================================
# ▶️ START THE WHOLE PROGRAM
# ========================================
if __name__ == "__main__":
    assign_weather_and_season()
