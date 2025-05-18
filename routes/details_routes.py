from flask import Blueprint, request, jsonify
import mysql.connector
from backend.config import DB_CONFIG

snapshot_bp = Blueprint('snapshot_bp', __name__)

@snapshot_bp.route('/api/location_snapshot', methods=['POST', 'OPTIONS'])
def location_snapshot():
    if request.method == 'OPTIONS':
        return '', 200  # ✅ Handle preflight request for CORS

    try:
        data = request.get_json()
        date = data.get("date")
        time = data.get("time")
        traffic_type = data.get("traffic_type")

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                pd.Location,
                tc.Traffic_Type,
                tc.Interval_Count,
                pd.Date_Time,
                wsd.Weather,
                wsd.Season,
                wsd.Temperature
            FROM processed_data pd
            JOIN traffic_counts tc ON pd.Data_ID = tc.Data_ID
            JOIN weather_season_data wsd ON pd.Data_ID = wsd.Data_ID
            WHERE DATE(pd.Date_Time) = %s
              AND TIME(pd.Date_Time) = %s
              AND tc.Traffic_Type = %s
        """, (date, time, traffic_type))

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        snapshot_data = [
            {
                "location": row["Location"],
                "traffic_type": row["Traffic_Type"],
                "count": row["Interval_Count"],
                "date": str(row["Date_Time"]).split()[0],
                "time": str(row["Date_Time"]).split()[1],
                "weather": row.get("Weather", "Unknown"),
                "season": row.get("Season", "Unknown"),
                "temperature": row.get("Temperature", "?")
            }
            for row in results
        ]

        return jsonify(snapshot_data), 200

    except Exception as e:
        print("🔥 Error in /api/location_snapshot:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
