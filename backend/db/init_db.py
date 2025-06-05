# ================================================================
# Database Setup for Smart Foot Traffic
# ------------------------------------------------
# - Drops and recreates all required tables
# - Includes new summary_cache table to cache summary stats
# ================================================================

import mysql.connector
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.config import DB_CONFIG

# Create database if it doesn't exist
def create_database_if_not_exists():
    db_name = 'smart_foot_traffic'
    config = DB_CONFIG.copy()
    if 'database' in config:
        del config['database']  

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Step 1: Drop old tables (drop summary_cache too)
DROP_QUERIES = [
    "DROP TABLE IF EXISTS summary_cache;",
    "DROP TABLE IF EXISTS weather_season_data;",
    "DROP TABLE IF EXISTS traffic_counts;",
    "DROP TABLE IF EXISTS processed_data;"
]

# Step 2: Create all required tables
CREATE_QUERIES = [
    # Processed Data Table
    """
    CREATE TABLE IF NOT EXISTS processed_data (
        Data_ID INT AUTO_INCREMENT PRIMARY KEY,
        Date_Time DATETIME,
        Date DATE,
        Time TIME,
        Duration VARCHAR(50),
        Location VARCHAR(255)
    );
    """,

    # Traffic Counts
    """
    CREATE TABLE IF NOT EXISTS traffic_counts (
        Traffic_ID INT AUTO_INCREMENT PRIMARY KEY,
        Data_ID INT,
        Traffic_Type VARCHAR(50),
        Interval_Count INT,
        Total_Count INT,
        FOREIGN KEY (Data_ID) REFERENCES processed_data(Data_ID)
    );
    """,

    # Weather & Season
    """
    CREATE TABLE IF NOT EXISTS weather_season_data (
        Weather_ID INT AUTO_INCREMENT PRIMARY KEY,
        Data_ID INT NOT NULL,
        Weather VARCHAR(50) NOT NULL,
        Temperature FLOAT,
        Season VARCHAR(50) NOT NULL,
        FOREIGN KEY (Data_ID) REFERENCES processed_data(Data_ID),
        INDEX idx_season (Season),
        INDEX idx_weather (Weather)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """,

    # Heatmap Table
    """
    CREATE TABLE IF NOT EXISTS heatmaps (
        Heatmap_ID INT AUTO_INCREMENT PRIMARY KEY,
        Generated_At DATETIME NOT NULL,
        Traffic_Type VARCHAR(50),
        Date_Filter DATE,
        Time_Filter TIME,
        Status VARCHAR(20) DEFAULT 'Generated',
        Heatmap_URL VARCHAR(255),
        BarChart_URL VARCHAR(255)
    );
    """,

    # Summary Cache Table
    """
    CREATE TABLE IF NOT EXISTS summary_cache (
        Summary_ID INT AUTO_INCREMENT PRIMARY KEY,
        Date_Filter DATE,
        Time_Filter TIME,
        Traffic_Type VARCHAR(50),
        Summary_JSON TEXT,
        Generated_At DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_summary (Date_Filter, Time_Filter, Traffic_Type)
    );
    """
]

def initialize_database():
    # Create the database first if it doesn't exist
    create_database_if_not_exists()

    # Use the created database for all further actions
    config_with_db = DB_CONFIG.copy()
    config_with_db['database'] = 'smart_foot_traffic'

    try:
        conn = mysql.connector.connect(**config_with_db)
        cursor = conn.cursor()

        print("\n========================================")
        print("Dropping old tables (if any)...")
        print("========================================")
        for query in DROP_QUERIES:
            cursor.execute(query)

        print("\n========================================")
        print("Creating new tables...")
        print("========================================")
        for query in CREATE_QUERIES:
            cursor.execute(query)

        conn.commit()
        print("\nTables have been dropped and recreated successfully.")

    except mysql.connector.Error as err:
        print(f"\nMySQL Error: {err}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    initialize_database()
