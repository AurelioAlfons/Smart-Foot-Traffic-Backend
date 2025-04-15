# =====================================================
# 0. Initialize Database Tables
# This file is used to create the database table from scratch
# So it checks if the database already has the tables or not
# Helps automate the process of setting up the database
# Instead of manually running SQL query in MySQL all the time when re run
# =====================================================
import mysql.connector  # Used to connect to MySQL database
import sys, os  # Needed to fix import path for subprocess runs

# 🛠️ Makes sure we can import stuff from the main project folder wherever we are in the directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 🔌 Database login details
from backend.config import DB_CONFIG

# 🗑️ Step 1: List of SQL commands to delete old tables (clean reset)
# ⚠️ Order matters because some tables depend on others
DROP_QUERIES = [
    "DROP TABLE IF EXISTS weather_season_data;",  # Delete weather table
    "DROP TABLE IF EXISTS traffic_counts;",       # Delete traffic table
    "DROP TABLE IF EXISTS processed_data;",       # Delete main data table
    "DROP TABLE IF EXISTS heatmaps;"              # Delete heatmap records
]

# 🧱 Step 2: SQL commands to create tables from scratch
CREATE_QUERIES = [
    # Table to store cleaned data from CSV
    """
    CREATE TABLE processed_data (
        Data_ID INT AUTO_INCREMENT PRIMARY KEY,  -- Unique ID
        Date_Time DATETIME,                      -- Full timestamp
        Date DATE,                               -- Date only
        Time TIME,                               -- Time only
        Location VARCHAR(255)                    -- Sensor location
    );
    """,

    # Table for traffic counts linked to processed_data
    """
    CREATE TABLE traffic_counts (
        Traffic_ID INT AUTO_INCREMENT PRIMARY KEY,  -- Unique ID
        Data_ID INT,                                -- Link to processed_data
        Traffic_Type VARCHAR(50),                   -- Pedestrian, Vehicle, etc.
        Total_Count INT,                            -- Cumulative count
        Interval_Count INT,                         -- Count in specific time window
        FOREIGN KEY (Data_ID) REFERENCES processed_data(Data_ID)
    );
    """,

    # Table to store weather and season info
    """
    CREATE TABLE weather_season_data (
        Forecast_ID INT AUTO_INCREMENT PRIMARY KEY, -- Unique ID
        Data_ID INT,                                -- Link to processed_data
        Weather VARCHAR(50),                        -- e.g. Sunny, Rainy
        Season VARCHAR(20),                         -- e.g. Summer, Winter
        FOREIGN KEY (Data_ID) REFERENCES processed_data(Data_ID)
    );
    """,

    # Table to store saved heatmaps
    """
    CREATE TABLE heatmaps (
        Heatmap_ID INT AUTO_INCREMENT PRIMARY KEY,  -- Unique ID
        Generated_At DATETIME NOT NULL,             -- When the map was made
        Traffic_Type VARCHAR(50),                   -- Type of traffic shown
        Date_Filter DATE,                           -- Filter used for date
        Time_Filter TIME,                           -- Filter used for time
        Status VARCHAR(20) DEFAULT 'Generated',     -- Status info (optional)
        Heatmap_URL VARCHAR(255)                    -- Where the map is saved
    );
    """
]

# 🔁 This function connects to the database and runs the queries
def initialize_database():
    try:
        # Connect to the MySQL server
        conn = mysql.connector.connect(**DB_CONFIG)
        # This acts as a cursor to execute SQL commands
        # It allows us to run SQL queries and fetch results
        # Cursor is like a pointer to the current position in the database
        cursor = conn.cursor()

        # =====================================================
        # 🗑️ Step A: Drop old tables if they exist
        # =====================================================
        print("\n========================================")
        print("🗑️ Dropping old tables (if any)...")
        print("========================================")
        # Loop through each query in the DROP_QUERIES list
        # Remember it has the drop (4) tables 
        for query in DROP_QUERIES:
            # Execute using the cursor, query == DROP_QUERIES contents
            cursor.execute(query)

        # =====================================================
        # 🛠️ Step B: Create new tables fresh
        # =====================================================
        print("\n========================================")
        print("🛠️ Creating new tables...")
        print("========================================")
        # Loop through each query in the CREATE_QUERIES list - same like DROP_QUERIES
        # This time it will create (4) tables
        for query in CREATE_QUERIES:
            # Execute using the cursor, query == CREATE_QUERIES contents
            cursor.execute(query)

        # Save all changes to the database
        # This is important because without it, nothing will be saved
        conn.commit()
        # Log success message
        print("\n✅ Tables have been dropped and recreated successfully.")
    
    # Error handling so it won't crash if something goes wrong
    # This will catch any MySQL errors that occur during the process
    # It will print the error message to the console
    except mysql.connector.Error as err:
        print(f"\n❌ MySQL Error: {err}")
    
    # This runs wherever, it program succeeds or fail (both)
    finally:
        # Always close connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 🏁 Only run this if the file is executed directly
if __name__ == "__main__":
    initialize_database()
