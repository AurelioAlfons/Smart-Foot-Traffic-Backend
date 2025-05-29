# ===========================================================
# Heatmap Database Logger
# -----------------------------------------------------------
# - Inserts metadata about generated heatmaps into the database
# - Stores generation time, type, filters, and URL
# - Used to track and retrieve heatmap outputs via API or UI
# ===========================================================

import mysql.connector
from datetime import datetime
from backend.config import DB_CONFIG
import os

def log_heatmap_to_db(filename, selected_type, date_filter, time_filter):
    """
    Insert heatmap metadata into the `heatmaps` table.
    - filename: full path to the saved HTML file
    - selected_type: traffic type (Pedestrian Count, etc.)
    - date_filter: filter used to generate map
    - time_filter: time used to generate map
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # heatmap_url = f"http://localhost:5000/{filename.replace(os.sep, '/')}"
        heatmap_url = f"https://smart-foot-traffic-backend.onrender.com/{filename.replace(os.sep, '/')}"
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO heatmaps (Generated_At, Traffic_Type, Date_Filter, Time_Filter, Status, Heatmap_URL)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            generated_at,
            selected_type,
            date_filter,
            time_filter,
            "Generated",
            heatmap_url
        ))

        conn.commit()
        cursor.close()
        conn.close()
        return True

    except mysql.connector.Error as e:
        print(f"DB INSERT FAILED: {e}")
        return False
