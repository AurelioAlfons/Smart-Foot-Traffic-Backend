# ======================================
# Set Up Indexes for Smart Foot Traffic DB
# ======================================
# - Adds essential indexes to speed up queries
# - Only creates indexes if they don't exist
# ======================================

import mysql.connector
from backend.config import DB_CONFIG

def create_indexes_if_missing():
    index_queries = [
        # Index to speed up WHERE Date_Time BETWEEN ... AND ...
        ("idx_processed_datetime", """
            CREATE INDEX idx_processed_datetime
            ON processed_data (Date_Time)
        """),

        # Index for foreign key join on processed_data
        ("idx_processed_dataid", """
            CREATE INDEX idx_processed_dataid
            ON processed_data (Data_ID)
        """),

        # Index for filtering and joining in traffic_counts
        ("idx_traffic_type_dataid", """
            CREATE INDEX idx_traffic_type_dataid
            ON traffic_counts (Traffic_Type, Data_ID)
        """),

        # Index for summary_cache lookup
        ("idx_summary_cache_key", """
            CREATE INDEX idx_summary_cache_key
            ON summary_cache (Date_Filter, Time_Filter, Traffic_Type)
        """),

        # Index for weather_season_data foreign key
        ("idx_weather_dataid", """
            CREATE INDEX idx_weather_dataid
            ON weather_season_data (Data_ID)
        """),
    ]

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        for index_name, query in index_queries:
            cursor.execute("""
                SELECT COUNT(1)
                FROM information_schema.statistics
                WHERE table_schema = %s AND index_name = %s
            """, (DB_CONFIG["database"], index_name))

            exists = cursor.fetchone()[0]
            if not exists:
                print(f"Creating index: {index_name}")
                try:
                    cursor.execute(query)
                except mysql.connector.Error as e:
                    print(f"Failed to create index {index_name}: {e}")
            else:
                print(f"Index already exists: {index_name}")

        conn.commit()
        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Failed to check/create indexes: {err}")

if __name__ == "__main__":
    create_indexes_if_missing()