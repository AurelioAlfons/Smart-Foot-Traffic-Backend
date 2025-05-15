# ======================================
# 🔧 Set Up Indexes for Smart Foot Traffic DB
# ======================================
# - Makes sure useful indexes are added to speed things up
# - Only runs if index doesn’t already exist
# - Run this once when starting the app or preprocessing
# ======================================

import mysql.connector
from backend.config import DB_CONFIG

def create_indexes_if_missing():
    index_queries = [
        # ✅ Index for processed_data (Date, Time, Location)
        ("idx_processed_date_time_location", """
            CREATE INDEX idx_processed_date_time_location
            ON processed_data (Date, Time, Location)
        """),

        # ✅ Index for traffic_counts (Traffic_Type, Data_ID)
        ("idx_traffic_counts_type_dataid", """
            CREATE INDEX idx_traffic_counts_type_dataid
            ON traffic_counts (Traffic_Type, Data_ID)
        """),

        # ✅ Index for weather_season_data (Data_ID)
        ("idx_weather_dataid", """
            CREATE INDEX idx_weather_dataid
            ON weather_season_data (Data_ID)
        """)
    ]

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        for index_name, query in index_queries:
            # Check if index already exists in information_schema
            cursor.execute("""
                SELECT COUNT(1)
                FROM information_schema.statistics
                WHERE table_schema = %s AND index_name = %s
            """, (DB_CONFIG["database"], index_name))

            exists = cursor.fetchone()[0]
            if not exists:
                print(f"🔧 Creating index: {index_name}")
                cursor.execute(query)
            else:
                print(f"✅ Index already exists: {index_name}")

        conn.commit()
        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"❌ Failed to check/create indexes: {err}")

if __name__ == "__main__":
    create_indexes_if_missing()
