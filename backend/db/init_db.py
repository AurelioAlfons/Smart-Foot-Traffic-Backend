import mysql.connector
import sys, os

# Add project root to import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.config import DB_CONFIG

# Drop tables in the correct order
DROP_QUERIES = [
    "DROP TABLE IF EXISTS weather_season_data;",
    "DROP TABLE IF EXISTS traffic_counts;",
    "DROP TABLE IF EXISTS processed_data;",
    "DROP TABLE IF EXISTS heatmaps;"
]

# Create tables
CREATE_QUERIES = [
    """
    CREATE TABLE processed_data (
        Data_ID INT AUTO_INCREMENT PRIMARY KEY,
        Date_Time DATETIME,
        Date DATE,
        Time TIME,
        Location VARCHAR(255)
    );
    """,
    """
    CREATE TABLE traffic_counts (
        Traffic_ID INT AUTO_INCREMENT PRIMARY KEY,
        Data_ID INT,
        Traffic_Type VARCHAR(50),
        Total_Count INT,
        Interval_Count INT,
        FOREIGN KEY (Data_ID) REFERENCES processed_data(Data_ID)
    );
    """,
    """
    CREATE TABLE weather_season_data (
        Weather_ID INT AUTO_INCREMENT PRIMARY KEY,
        Data_ID INT NOT NULL,
        Weather_Condition VARCHAR(50) NOT NULL,
        Temperature FLOAT,
        Season VARCHAR(50) NOT NULL,
        FOREIGN KEY (Data_ID) REFERENCES processed_data(Data_ID),
        INDEX idx_season (Season),
        INDEX idx_weather (Weather_Condition)
    );
    """,
    """
    CREATE TABLE heatmaps (
        Heatmap_ID INT AUTO_INCREMENT PRIMARY KEY,
        Generated_At DATETIME NOT NULL,
        Traffic_Type VARCHAR(50),
        Date_Filter DATE,
        Time_Filter TIME,
        Status VARCHAR(20) DEFAULT 'Generated',
        Heatmap_URL VARCHAR(255)
    );
    """
]

def initialize_database():
    conn = None
    cursor = None

    try:
        print("\n========================================")
        print("🔍 Checking if database exists...")
        print("========================================")

        # Strip 'database' from config to connect to server only
        db_config_without_db = {k: v for k, v in DB_CONFIG.items() if k != 'database'}

        # Step 1: Create database if it doesn't exist
        temp_conn = mysql.connector.connect(**db_config_without_db)
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("CREATE DATABASE IF NOT EXISTS smart_foot_traffic;")
        print("✅ Database 'smart_foot_traffic' checked or created.\n")
        temp_cursor.close()
        temp_conn.close()

        # Step 2: Connect with database specified
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Step 3: Drop old tables
        print("🗑️ Dropping old tables (if any)...")
        for query in DROP_QUERIES:
            try:
                cursor.execute(query)
            except mysql.connector.Error as err:
                print(f"⚠️ Error dropping table:\n{err}\nQuery:\n{query}")

        # Step 4: Create new tables
        print("🛠️ Creating new tables...")
        for i, query in enumerate(CREATE_QUERIES, start=1):
            try:
                cursor.execute(query)
                print(f"✅ Table {i} created.")
            except mysql.connector.Error as err:
                print(f"\n❌ Failed to create table {i}:\n{err}\nQuery:\n{query}\n")
                conn.rollback()
                return  # Exit early if a create fails

        # Step 5: Commit after all successful queries
        conn.commit()
        print("\n✅ All tables created and committed successfully.")

    except mysql.connector.Error as err:
        print(f"\n❌ MySQL Error: {err}")

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    initialize_database()