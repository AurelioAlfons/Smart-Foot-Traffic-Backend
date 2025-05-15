# ================================================
# Flask Backend API for Smart Foot Traffic System
# --------------------------------
# - Serves heatmap and bar chart HTML files
# - Provides API to generate heatmaps and summary stats
# - NEW: Serves real-time location data for sidebar
# ================================================

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
import sys
import traceback
import mysql.connector

from backend.visualizer.generate_default import generate_default_map
from backend.config import DB_CONFIG
from backend.analytics.statistics import get_summary_stats
from backend.visualizer.generate_heatmap import generate_heatmap

# 🔧 Initialize the Flask app
app = Flask(__name__)
CORS(app)

default_map_generated = False

# 📁 Define folders
HEATMAP_FOLDER = os.path.join(os.getcwd(), 'heatmaps')
BARCHART_FOLDER = os.path.join(os.getcwd(), 'barchart')

# 🔧 Allow importing from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ✅ Health check
@app.route('/healthz')
def health_check():
    return "OK", 200

# 🏠 Home
@app.route('/')
def index():
    return """
    <h2>🌐 Smart Foot Traffic – Server</h2>
    <ul>
        <li>✅ POST to <code>/api/generate_heatmap</code></li>
        <li>✅ POST to <code>/api/summary_stats</code></li>
        <li>✅ GET from <code>/api/location_data?location=Footscray Station</code></li>
        <li>🗺️ Access heatmaps at <code>/heatmaps/&lt;filename&gt;</code></li>
        <li>📊 Access bar charts at <code>/barchart/&lt;filename&gt;</code></li>
    </ul>
    """

# 📦 Serve heatmap HTML
@app.route('/heatmaps/<path:filename>')
def serve_heatmap(filename):
    return send_from_directory(HEATMAP_FOLDER, filename)

# 📦 Serve bar chart HTML
@app.route('/barchart/<path:filename>')
def serve_barchart(filename):
    return send_from_directory(BARCHART_FOLDER, filename)

# 🚀 Generate heatmap + bar chart
@app.route('/api/generate_heatmap', methods=['POST'])
def api_generate_heatmap():
    try:
        data = request.get_json()
        date_filter = data.get('date')
        time_filter = data.get('time')
        traffic_type = data.get('traffic_type')

        generate_heatmap(date_filter, time_filter, traffic_type)

        base_url = request.host_url.rstrip('/')
        heatmap_url = f"{base_url}/heatmaps/heatmap_{date_filter}_{(time_filter or 'all').replace(':', '-')}_{traffic_type.replace(' ', '_')}.html"
        barchart_url = f"{base_url}/barchart/barchart_{date_filter}_{(time_filter or 'all').replace(':', '-')}_{traffic_type.replace(' ', '_')}.html"

        return jsonify({
            "status": "success",
            "heatmap_url": heatmap_url,
            "barchart_url": barchart_url
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# 📊 Summary stats
@app.route('/api/summary_stats', methods=['POST'])
def api_summary_stats():
    try:
        data = request.get_json()
        date = data.get("date")
        time = data.get("time")
        traffic_type = data.get("traffic_type")

        result = get_summary_stats(date, time, traffic_type)
        return jsonify(result), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# 📈 Seasonal stats
@app.route('/api/seasonal_stats', methods=['POST'])
def api_seasonal_stats():
    try:
        from backend.analytics.season_stats.season_stats import get_seasonal_stats
        data = request.get_json()
        year = int(data.get("year"))
        time = data.get("time")
        traffic_type = data.get("traffic_type")

        result = get_seasonal_stats(year, time, traffic_type)
        return jsonify(result), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# 🧠 Location sidebar data
@app.route('/api/location_data', methods=['GET'])
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

# 🧰 Global CORS and frame policy
@app.after_request
def apply_cors_headers(response):
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

# 🌍 Preload default map
@app.before_request
def ensure_default_map():
    global default_map_generated
    if not default_map_generated:
        path = os.path.join(HEATMAP_FOLDER, 'default_map.html')
        if not os.path.exists(path):
            print("🛠 Generating default_map.html...")
            generate_default_map()
        else:
            print("✅ default_map.html already exists.")
        default_map_generated = True

# ▶️ Launch server
if __name__ == '__main__':
    print("✅ Starting Smart Foot Traffic server on http://localhost:5000\n")
    app.run(host='0.0.0.0', port=5000)
