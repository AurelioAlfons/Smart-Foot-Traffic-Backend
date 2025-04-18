# ========================================
# 📦 IMPORT MODULES
# ========================================
import mysql.connector
import logging
from datetime import datetime
import random
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn
from rich.console import Console

# ========================================
# 🛠️ SETUP LOGGING AND RICH CONSOLE
# ========================================
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
console = Console()

# ========================================
# 🗄️ DATABASE CONNECTION SETTINGS
# ========================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "smart_foot_traffic"
}

# ========================================
# 🌦️ WEATHER & SEASON CONFIGURATION (ENHANCED)
# ========================================
# Meteorological seasons for Southern Hemisphere
SEASONS = {
    "Summer": (12, 1, 2),  # Dec-Feb
    "Autumn": (3, 4, 5),   # Mar-May
    "Winter": (6, 7, 8),   # Jun-Aug
    "Spring": (9, 10, 11)  # Sep-Nov
}

# Enhanced weather patterns based on Melbourne climate
WEATHER_PROBABILITY = {
    "Summer": {"Sunny": 55, "Cloudy": 25, "Rain": 15, "Storm": 5},
    "Autumn": {"Sunny": 40, "Cloudy": 35, "Rain": 20, "Fog": 5},
    "Winter": {"Sunny": 30, "Cloudy": 40, "Rain": 25, "Hail": 5},
    "Spring": {"Sunny": 50, "Cloudy": 30, "Rain": 15, "Windy": 5}
}

# More realistic temperature ranges (°C) for Melbourne
TEMPERATURE_RANGES = {
    "Summer": (22, 42),    # Hot days, occasional heat waves
    "Autumn": (12, 28),    # Mild days, cooler nights
    "Winter": (6, 16),     # Chilly but rarely freezing
    "Spring": (14, 28)     # Variable conditions
}

# ========================================
# � WEATHER GENERATION FUNCTIONS
# ========================================
def get_season(date_obj):
    """Smart season detection that handles both strings and date objects"""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
        except ValueError:
            return "Unknown"
    
    month = date_obj.month
    for season, months in SEASONS.items():
        if month in months:
            return season
    return "Unknown"

def generate_weather(season):
    """Generate realistic weather conditions with daily variation"""
    weather_options = list(WEATHER_PROBABILITY[season].keys())
    probabilities = list(WEATHER_PROBABILITY[season].values())
    return random.choices(weather_options, weights=probabilities)[0]

def generate_temperature(season):
    """Generate temperature with realistic daily fluctuations"""
    min_temp, max_temp = TEMPERATURE_RANGES[season]
    base_temp = random.uniform(min_temp, max_temp)
    
    # Add daily variation (-3° to +3° from base)
    fluctuation = random.uniform(-3, 3)
    final_temp = base_temp + fluctuation
    
    # Ensure temp stays within seasonal bounds
    final_temp = max(min_temp, min(max_temp, final_temp))
    return round(final_temp, 1)

# ========================================
# 🌤️ MAIN FUNCTION: SMART WEATHER/SEASON ASSIGNMENT
# ========================================
def assign_weather_and_season():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info("🔌 Connected to MySQL")
        
        # Create enhanced weather table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_season_data (
                Weather_ID INT AUTO_INCREMENT PRIMARY KEY,
                Data_ID INT NOT NULL,
                Weather_Condition VARCHAR(50) NOT NULL,
                Temperature FLOAT,
                Season VARCHAR(50) NOT NULL,
                FOREIGN KEY (Data_ID) REFERENCES processed_data(Data_ID),
                INDEX idx_season (Season),
                INDEX idx_weather (Weather_Condition)
            )
        """)
        
        logging.info("🌦️ Starting smart weather/season assignment...")

        # Get all records with date and location
        cursor.execute("SELECT Data_ID, Date, Location FROM processed_data")
        rows = cursor.fetchall()
        logging.info(f"📋 Retrieved {len(rows)} records for processing")

        inserted = 0
        progress = Progress(
            TextColumn("[bold green]⚙️ Processing Records"),
            BarColumn(bar_width=None, complete_style="green"),
            "[progress.percentage]{task.percentage:>3.1f}%",
            TimeElapsedColumn(),
            console=console
        )

        with progress:
            task = progress.add_task("Assigning Data...", total=len(rows))

            for data_id, date_val, location in rows:
                try:
                    # Get season (handles both date objects and strings)
                    season = get_season(date_val)
                    
                    # Generate weather data with location consideration
                    weather = generate_weather(season)
                    
                    # Slightly adjust temperatures near water
                    if "Park" in location or "Rowing" in location:
                        temp_adjustment = random.uniform(-2, 0)  # Cooler near water
                    else:
                        temp_adjustment = random.uniform(0, 2)   # Warmer in urban areas
                    
                    temperature = generate_temperature(season) + temp_adjustment
                    temperature = round(max(TEMPERATURE_RANGES[season][0], 
                                       min(TEMPERATURE_RANGES[season][1], temperature)), 1)
                    
                    # Insert into database
                    cursor.execute("""
                        INSERT INTO weather_season_data 
                            (Data_ID, Weather_Condition, Temperature, Season)
                        VALUES (%s, %s, %s, %s)
                    """, (data_id, weather, temperature, season))
                    
                    inserted += 1
                    progress.update(task, advance=1)

                except Exception as e:
                    logging.warning(f"⚠️ Skipping Data_ID {data_id} — {str(e)}")
                    progress.update(task, advance=1)
                    continue

        conn.commit()
        logging.info(f"🏁 Successfully processed {inserted}/{len(rows)} records")
        logging.info(f"💾 Added weather conditions, temperatures, and seasons")

    except mysql.connector.Error as e:
        logging.error(f"❌ Database error: {str(e)}")
        return
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ========================================
# ▶️ START THE PROGRAM
# ========================================
if __name__ == "__main__":
    assign_weather_and_season()