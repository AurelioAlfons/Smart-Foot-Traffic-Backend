# ================================================
# 🔍 Traffic Data Fetcher (Modular Version)
# ================================================

import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
from backend.config import DB_CONFIG

def fetch_traffic_data(date_filter=None, time_filter=None, selected_type="Vehicle Count", season_filter=None, max_age_minutes=30):
    import pandas as pd
    import mysql.connector
    from backend.config import DB_CONFIG
    from datetime import datetime, timedelta

    conn = mysql.connector.connect(**DB_CONFIG)

    if season_filter:
        query = """
            SELECT pd.Location, tc.Traffic_Type, SUM(tc.Total_Count) AS Interval_Count, 
                   MAX(wsd.Weather) AS Weather, MAX(wsd.Temperature) AS Temperature
            FROM traffic_counts tc
            JOIN weather_season_data wsd ON tc.Data_ID = wsd.Data_ID
            JOIN processed_data pd ON tc.Data_ID = pd.Data_ID
            WHERE wsd.Season = %s AND tc.Traffic_Type = %s
            GROUP BY pd.Location, tc.Traffic_Type
        """
        params = (season_filter, selected_type)
        df = pd.read_sql(query, conn, params=params)
        df["Date"] = season_filter
        df["Time"] = "All"
        df["DateTime_String"] = "Unknown"
    else:
        # Calculate time window (e.g. 10:00:00 ± 30 min)
        selected_dt = datetime.strptime(f"{date_filter} {time_filter}", "%Y-%m-%d %H:%M:%S")
        time_lower = (selected_dt - timedelta(minutes=max_age_minutes)).time()
        time_upper = selected_dt.time()

        query = """
            SELECT pd.Location, tc.Traffic_Type, tc.Interval_Count,
                   pd.Time, pd.Date, wsd.Weather, wsd.Temperature
            FROM processed_data pd
            JOIN traffic_counts tc ON pd.Data_ID = tc.Data_ID
            JOIN weather_season_data wsd ON pd.Data_ID = wsd.Data_ID
            WHERE pd.Date = %s
              AND tc.Traffic_Type = %s
              AND pd.Time BETWEEN %s AND %s
        """
        params = (date_filter, selected_type, time_lower, time_upper)
        df = pd.read_sql(query, conn, params=params)

        # Construct string for display
        df["DateTime_String"] = df.apply(
            lambda row: f"{row['Date']} {row['Time']}" if pd.notna(row['Date']) and pd.notna(row['Time']) else "N/A",
            axis=1
        )

    conn.close()
    return df
