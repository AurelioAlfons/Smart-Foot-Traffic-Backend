# ===========================================================
# Step 2: Set Default Weather & Season Values in Database
# -----------------------------------------------------------
# - Loops through all cleaned traffic data rows
# - Resets weather to 'Undefined' and temperature to NULL
# - Detects and assigns season based on the month
# - Saves or updates each record in weather_season_data table
# ===========================================================

import mysql.connector         # 💾 MySQL DB connection
import logging                 # 📋 For logging process & warnings
from datetime import datetime  # 🕒 To parse/convert dates
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn  # 📊 Progress bar
from rich.console import Console
from backend.config import DB_CONFIG
from backend.forecast.season import get_season

console = Console()

# =====================================================
# 🧹 FUNCTION: Reset all rows in weather_season_data
# Sets default values for weather + temperature,
# and assigns season based on the timestamp month.
# =====================================================
def reset_weather_season_values():
    try:
        # 🔌 Connect to MySQL
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info("🔌 Connected to MySQL")

        # 📥 Grab all Data_IDs and Dates from processed_data
        cursor.execute("SELECT Data_ID, Date FROM processed_data")
        rows = cursor.fetchall()

        updated = 0

        # 🟩 Setup progress bar
        progress = Progress(
            TextColumn("[bold green]📅 Assigning Season"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            TimeElapsedColumn(),
            console=console
        )

        with progress:
            task = progress.add_task("Processing...", total=len(rows))

            # 🔁 Loop through each entry in processed_data
            for data_id, date in rows:
                try:
                    # ⏱️ Convert string to datetime if not already
                    if isinstance(date, str):
                        date = datetime.strptime(date, "%Y-%m-%d")

                    # 🍁 Get the season name using external logic
                    season = get_season(date.month)

                    # 📦 Insert new record or update existing one
                    cursor.execute("""
                        INSERT INTO weather_season_data (Data_ID, Weather, Temperature, Season)
                        VALUES (%s, 'Undefined', NULL, %s)
                        ON DUPLICATE KEY UPDATE
                            Weather = 'Undefined',
                            Temperature = NULL,
                            Season = VALUES(Season)
                    """, (data_id, season))

                    updated += 1
                except Exception as e:
                    logging.warning(f"⚠️ Skipping Data_ID {data_id} — {e}")
                finally:
                    progress.update(task, advance=1)

        # 💾 Save changes to DB
        conn.commit()
        logging.info(f"✅ Reset {updated} rows in weather_season_data with season assigned.")

        # 🔒 Close DB connection
        cursor.close()
        conn.close()

    except Exception as e:
        logging.error(f"❌ Error resetting values in weather_season_data: {e}")

# =====================================================
# ▶️ ENTRY POINT: Only runs if called directly
# =====================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    reset_weather_season_values()
