# ========================================
# 📦 IMPORT MODULES
# ========================================
import mysql.connector       # for connecting to the MySQL database
import logging               # for printing logs like success/failure
from datetime import datetime
import random                # for generating weather and temperature
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
# 🌦️ WEATHER & TEMPERATURE CONFIGURATION (Melbourne-style)
# ========================================
WEATHER_PROBABILITY = {
    "Summer": {"Sunny": 55, "Cloudy": 25, "Rain": 15, "Storm": 5},
    "Autumn": {"Sunny": 40, "Cloudy": 35, "Rain": 20, "Fog": 5},
    "Winter": {"Sunny": 30, "Cloudy": 40, "Rain": 25, "Hail": 5},
    "Spring": {"Sunny": 50, "Cloudy": 30, "Rain": 15, "Windy": 5}
}

TEMPERATURE_RANGES = {
    "Summer": (22, 42),
    "Autumn": (12, 28),
    "Winter": (6, 16),
    "Spring": (14, 28)
}

def generate_weather(season):
    options = list(WEATHER_PROBABILITY[season].keys())
    weights = list(WEATHER_PROBABILITY[season].values())
    return random.choices(options, weights=weights)[0]

def generate_temperature(season, location):
    min_temp, max_temp = TEMPERATURE_RANGES[season]
    base_temp = random.uniform(min_temp, max_temp)
    
    # Cooler near water/parks, warmer in urban
    if "Park" in location or "Rowing" in location:
        adjustment = random.uniform(-2, 0)
    else:
        adjustment = random.uniform(0, 2)
    
    temp = base_temp + adjustment
    return round(max(min_temp, min(max_temp, temp)), 1)

# ========================================
# 🌤️ MAIN FUNCTION: ASSIGN WEATHER + SEASON
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

    # --- Create table if not exists (failsafe) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_season_data (
            Weather_ID INT AUTO_INCREMENT PRIMARY KEY,
            Data_ID INT NOT NULL,
            Weather VARCHAR(50) NOT NULL,
            Temperature FLOAT,
            Season VARCHAR(50) NOT NULL,
            FOREIGN KEY (Data_ID) REFERENCES processed_data(Data_ID),
            INDEX idx_season (Season),
            INDEX idx_weather (Weather)
        )
    """)

    # --- Start processing ---
    logging.info("🌦️ Starting assignment of SEASON and WEATHER...")

    # --- Get all rows from processed_data ---
    cursor.execute("SELECT Data_ID, Date, Location FROM processed_data")
    rows = cursor.fetchall()
    logging.info(f"📋 Retrieved {len(rows)} rows from processed_data")

    inserted = 0  # track how many rows we insert

    # --- Setup a progress bar for fun ---
    progress = Progress(
        TextColumn("[bold green]📅 Assigning Season & Weather"),
        BarColumn(bar_width=None, complete_style="green"),
        "[progress.percentage]{task.percentage:>3.1f}%",
        TimeElapsedColumn(),
        console=console
    )

    # --- Loop through all rows and assign season & weather ---
    with progress:
        task = progress.add_task("Processing...", total=len(rows))

        for data_id, date, location in rows:
            try:
                # convert string date to datetime format
                if isinstance(date, str):
                    date = datetime.strptime(date, "%Y-%m-%d")

                # get season from the month
                season = get_season(date.month)

                # generate weather + temp
                weather = generate_weather(season)
                temperature = generate_temperature(season, location)

                # insert into weather_season_data table
                cursor.execute("""
                    INSERT INTO weather_season_data (Data_ID, Weather, Temperature, Season)
                    VALUES (%s, %s, %s, %s)
                """, (data_id, weather, temperature, season))

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

    logging.info(f"🏁 Finished inserting {inserted} records with season and weather data.")

# ========================================
# ▶️ START THE WHOLE PROGRAM
# ========================================
if __name__ == "__main__":
    assign_weather_and_season()
