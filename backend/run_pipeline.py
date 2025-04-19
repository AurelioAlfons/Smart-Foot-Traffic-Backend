# backend/run_pipeline.py
import subprocess
import sys
import mysql.connector
from mysql.connector import Error

python_exec = sys.executable

def setup_database():
    # Database configuration - Update these with your actual credentials
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'smart_foot_traffic'
    }

    # SQL commands to drop tables if they exist (child tables first)
    drop_table_queries = [
        "DROP TABLE IF EXISTS traffic_counts",
        "DROP TABLE IF EXISTS weather_season_data",
        "DROP TABLE IF EXISTS heatmaps",
        "DROP TABLE IF EXISTS processed_data"
    ]

    # SQL commands to create tables (parent tables first)
    create_table_queries = [
        # Processed Data Table
        """
        CREATE TABLE processed_data (
            Data_ID INT AUTO_INCREMENT PRIMARY KEY,
            Date_Time DATETIME NOT NULL,
            Date DATE NOT NULL,
            Time TIME NOT NULL,
            Location VARCHAR(255) NOT NULL,
            INDEX idx_location (Location),
            INDEX idx_datetime (Date_Time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
        """,
        # Traffic Counts Table
        """
        CREATE TABLE traffic_counts (
            Traffic_ID INT AUTO_INCREMENT PRIMARY KEY,
            Data_ID INT NOT NULL,
            Traffic_Type ENUM('Vehicle Count', 'Pedestrian Count', 'Cyclist Count') NOT NULL,
            Total_Count INT NOT NULL,
            Interval_Count INT NOT NULL,
            FOREIGN KEY (Data_ID) REFERENCES processed_data(Data_ID),
            INDEX idx_traffic_type (Traffic_Type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
        """,
        # Weather Season Data Table
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
        """,
        # Heatmaps Table
        """
        CREATE TABLE heatmaps (
            Heatmap_ID INT AUTO_INCREMENT PRIMARY KEY,
            Generated_At DATETIME NOT NULL,
            Traffic_Type VARCHAR(50) NOT NULL,
            Date_Filter DATE NOT NULL,
            Time_Filter TIME NOT NULL,
            Status VARCHAR(50) DEFAULT 'Generated',
            Heatmap_URL VARCHAR(255) NOT NULL,
            INDEX idx_generated_at (Generated_At)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
        """
    ]

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        print("\n🗑️ Dropping existing tables...")
        for query in drop_table_queries:
            cursor.execute(query)

        print("\n🆕 Creating new tables...")
        for query in create_table_queries:
            cursor.execute(query)

        conn.commit()
        print("✅ Database tables reset successfully!")

    except Error as e:
        print(f"\n❌ Database setup error: {e}")
        sys.exit(1)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def run_pipeline():
    try:
        print("\n🚀 Starting Data Pipeline")
        
        # Database initialization
        setup_database()
        
        # Step 1: Preprocessing
        print("\n🔄 Step 1/4: Data Preprocessing")
        subprocess.run([python_exec, "backend/preprocess.py"], check=True)
        
        # Step 2: Weather/Season Assignment
        print("\n🌦️ Step 2/4: Weather Assignment")
        subprocess.run([python_exec, "backend/assign_weather_season.py"], check=True)
        
        # Step 3: ML Training
        print("\n🤖 Step 3/4: Model Training")
        subprocess.run([python_exec, "backend/model_pipeline.py"], check=True)
        
        print("\n✅ All pipeline steps completed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Pipeline failed at step: {e.cmd}")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    run_pipeline()