# ===========================================================
# Assign Season to Each Data Row (Step 2 Alt)
# -----------------------------------------------------------
# - Reads the date from each traffic record
# - Figures out the season (Summer, Autumn, etc.) from the month
# - Updates the season in the weather_season_data table
# ===========================================================

import mysql.connector         # MySQL DB connection
import logging                 # Log info and errors
from datetime import datetime  # Handle date conversion
from backend.config import DB_CONFIG  # DB credentials

# =====================================================
# FUNCTION: Convert numeric month into season name
# =====================================================
def get_season(month):
    if month in [12, 1, 2]:
        return "Summer"
    elif month in [3, 4, 5]:
        return "Autumn"
    elif month in [6, 7, 8]:
        return "Winter"
    else:
        return "Spring"

# =====================================================
# FUNCTION: Assign season for each record in processed_data
# and update weather_season_data.Season
# =====================================================
def assign_season():
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info("Connected to MySQL")

        # Fetch all relevant data points
        cursor.execute("SELECT Data_ID, Date FROM processed_data")
        rows = cursor.fetchall()
        updated = 0

        # Loop through each row
        for data_id, date in rows:
            # Convert string to datetime if needed
            if isinstance(date, str):
                date = datetime.strptime(date, "%Y-%m-%d")

            # Determine season from the month
            season = get_season(date.month)

            # Update Season column in DB
            cursor.execute("""
                UPDATE weather_season_data
                SET Season = %s
                WHERE Data_ID = %s
            """, (season, data_id))

            updated += 1

        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"Assigned seasons to {updated} entries.")

    except Exception as e:
        logging.error(f"Error assigning seasons: {e}")
