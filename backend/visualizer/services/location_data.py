# backend/routes/location_data.py

from flask import Blueprint, request, jsonify
import mysql.connector
from backend.config import DB_CONFIG

location_data_bp = Blueprint('location_data', __name__)

@location_data_bp.route('/api/location_data', methods=['GET'])
def get_location_data():
    location = request.args.get('location')
    if not location:
        return jsonify({"error": "Missing location parameter"}), 400

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                pd.Location,
                MAX(pd.Date_Time) AS latest_timestamp,
                MAX(wsd.Weather) AS weather,
                MAX(wsd.Temperature) AS temperature,
                MAX(wsd.Season) AS season,
                SUM(CASE WHEN tc.Traffic_Type = 'Pedestrian Count' THEN tc.Total_Count ELSE 0 END) AS pedestrian_total,
                SUM(CASE WHEN tc.Traffic_Type = 'Vehicle Count' THEN tc.Total_Count ELSE 0 END) AS vehicle_total,
                SUM(CASE WHEN tc.Traffic_Type = 'Cyclist Count' THEN tc.Total_Count ELSE 0 END) AS cyclist_total
            FROM processed_data pd
            JOIN traffic_counts tc ON pd.Data_ID = tc.Data_ID
            JOIN weather_season_data wsd ON pd.Data_ID = wsd.Data_ID
            WHERE pd.Location = %s
            GROUP BY pd.Location;
        """, (location,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            return jsonify(result)
        else:
            return jsonify({"error": "No data found"}), 404

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500
