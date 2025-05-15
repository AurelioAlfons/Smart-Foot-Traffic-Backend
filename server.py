# ================================================
# Flask Backend API for Smart Foot Traffic System
# --------------------------------
# - Serves heatmap and bar chart HTML files
# - Provides API to generate heatmaps and summary stats
# - Stores and returns URLs to frontend
# - Used by Flutter client for heatmap + analytics display
# ================================================

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
import sys
import traceback

# 🔧 Initialize the Flask app
app = Flask(__name__)
CORS(app)

# 📁 Define folders
HEATMAP_FOLDER = os.path.join(os.getcwd(), 'heatmaps')
BARCHART_FOLDER = os.path.join(os.getcwd(), 'barchart')

# 🔧 Allow importing from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ✅ Import core logic
from backend.analytics.seasonal_stats import get_summary_stats
from backend.visualizer.generate_heatmap import generate_heatmap

# ✅ Health check route for Render or local testing
@app.route('/healthz')
def health_check():
    return "OK", 200

# 🏠 Root route
@app.route('/')
def index():
    return """
    <h2>🌐 Smart Foot Traffic – Server</h2>
    <ul>
        <li>✅ POST to <code>/api/generate_heatmap</code></li>
        <li>✅ POST to <code>/api/summary_stats</code></li>
        <li>🗺️ Access heatmaps at <code>/heatmaps/&lt;filename&gt;</code></li>
        <li>📊 Access bar charts at <code>/barchart/&lt;filename&gt;</code></li>
    </ul>
    """

# 📦 Serve heatmap HTML file
@app.route('/heatmaps/<filename>')
def serve_heatmap(filename):
    return send_from_directory(HEATMAP_FOLDER, filename)

# 📦 Serve bar chart HTML file
@app.route('/barchart/<path:filename>')
def serve_barchart(filename):
    return send_from_directory(BARCHART_FOLDER, filename)

# 🚀 Generate heatmap and barchart, return both URLs
@app.route('/api/generate_heatmap', methods=['POST'])
def api_generate_heatmap():
    try:
        data = request.get_json()
        date_filter = data.get('date')
        time_filter = data.get('time')
        traffic_type = data.get('traffic_type')

        # 🔁 Generate heatmap (this already saves to DB)
        generate_heatmap(
            date_filter=date_filter,
            time_filter=time_filter,
            selected_type=traffic_type,
        )

        # 🌐 Base URL handling (localhost or production)
        base_url = request.host_url.rstrip('/')
        if "localhost" in base_url or "127.0.0.1" in base_url:
            heatmap_url = f"{base_url}/heatmaps/heatmap_{date_filter}_{(time_filter or 'all').replace(':', '-')}_{traffic_type.replace(' ', '_')}.html"
            barchart_url = f"{base_url}/barchart/barchart_{date_filter}_{(time_filter or 'all').replace(':', '-')}_{traffic_type.replace(' ', '_')}.html"
        else:
            heatmap_url = f"https://smart-foot-traffic-backend.onrender.com/heatmaps/heatmap_{date_filter}_{(time_filter or 'all').replace(':', '-')}_{traffic_type.replace(' ', '_')}.html"
            barchart_url = f"https://smart-foot-traffic-backend.onrender.com/barchart/barchart_{date_filter}_{(time_filter or 'all').replace(':', '-')}_{traffic_type.replace(' ', '_')}.html"

        return jsonify({
            "status": "success",
            "heatmap_url": heatmap_url,
            "barchart_url": barchart_url
        }), 200

    except Exception as e:
        print("❌ Error generating heatmap:")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# 📊 Return summary stats and generate charts
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
        print("❌ Error in summary_stats API:")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# 🧩 Allow iframe embedding (for Flutter Web)
@app.after_request
def allow_iframe(response):
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    return response

# ▶️ Start the server
if __name__ == '__main__':
    print("✅ Starting Smart Foot Traffic server on http://localhost:5000\n")
    app.run(host='0.0.0.0', port=5000)
