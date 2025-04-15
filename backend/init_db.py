import mysql.connector  # Used to connect to MySQL database

# 🔌 Database login details
DB_CONFIG = {
    "host": "localhost",      # Database is on your computer
    "user": "root",           # Default MySQL username
    "password": "",           # Use your own password here if you set one
    "database": "smart_foot_traffic"  # The database you're using
}

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
        cursor = conn.cursor()

        # Step A: Drop old tables if they exist
        print("🗑️ Dropping old tables (if any)...")
        for query in DROP_QUERIES:
            cursor.execute(query)

        # Step B: Create new tables fresh
        print("🛠️ Creating new tables...")
        for query in CREATE_QUERIES:
            cursor.execute(query)

        # Save all changes to the database
        conn.commit()
        print("✅ Tables have been dropped and recreated successfully.")

    # If something goes wrong, print the error
    except mysql.connector.Error as err:
        print(f"❌ MySQL Error: {err}")

    # Step C: Close the connection when done
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# 🏁 Only run this if the file is executed directly
if __name__ == "__main__":
    initialize_database()
