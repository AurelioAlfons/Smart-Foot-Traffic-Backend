# ==========================================
# 🛰️ Flask Server to Serve Heatmaps + API
# ==========================================
# This server allows:
# - Access generated heatmap .html files
# - API to trigger heatmap generation
# ==========================================

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
import sys
from backend.utils.get_ip import get_local_ip

# 🔧 Initialize the Flask app
app = Flask(__name__)
CORS(app) 

# 📁 Define the folder where heatmaps are saved
HEATMAP_FOLDER = os.path.join(os.getcwd(), 'heatmaps')

# 🔧 Allow importing from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ✅ Import your generate_heatmap function
from backend.visualizer.generate_heatmap import generate_heatmap

# 🏠 Home route to confirm server is running
@app.route('/')
def index():
    return "<h2>🌐 Smart Foot Traffic – Heatmaps</h2><p>Try visiting /heatmaps/filename.html or POST to /api/generate_heatmap</p>"

# 📦 Route to serve any heatmap HTML file by filename
@app.route('/heatmaps/<filename>')
def serve_heatmap(filename):
    return send_from_directory(HEATMAP_FOLDER, filename)

# 🚀 API to generate heatmap
@app.route('/api/generate_heatmap', methods=['POST'])
def api_generate_heatmap():
    try:
        data = request.get_json()

        date_filter = data.get('date')          # "2025-04-20"
        time_filter = data.get('time')           # "14:00:00"
        traffic_type = data.get('traffic_type')  # "Pedestrian Count"
        season_filter = data.get('season')       

        # Generate the heatmap using the function
        generate_heatmap(
            date_filter=date_filter,
            time_filter=time_filter,
            selected_type=traffic_type,
            season_filter=season_filter
        )

        # 📎 Build the heatmap file URL
        label = season_filter if season_filter else date_filter
        file_name = f"heatmap_{label}_{(time_filter or 'all').replace(':', '-')}_{traffic_type.replace(' ', '_')}.html"

        # ============================================================
        # 🌐 Localhost Settings & Heatmap Access URL Explanation
        # 
        # - 'localhost' refers to the current device running the server.
        # - Port 5000 is the default for Flask.
        # - Heatmaps are served as static HTML files from the '/heatmaps' route.
        #
        # 🔗 Example Heatmap URL:
        #   http://localhost:5000/heatmaps/heatmap_2025-04-20_14-00_Pedestrian_Count.html
        #
        # 💡 Note:
        # This URL is only for local access to heatmap files via the Flask server.
        # ============================================================

        # heatmap_url = f"http://localhost:5000/heatmaps/{file_name}"
        ip = get_local_ip()
        # If you use a different wifi then change the IP
        heatmap_url = f"http://{ip}:5000/heatmaps/{file_name}"

        return jsonify({"status": "success", "heatmap_url": heatmap_url}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ▶️ Run this script to start the server locally
if __name__ == '__main__':
    ip = get_local_ip()

    # Only ask the user once (on the main process)
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        print(f"\n📡 Your local Wi-Fi IP address is: http://{ip}:5000")
        proceed = input("🚀 Do you want to start the server? (y/n): ").strip().lower()
        if proceed != 'y':
            print("❌ Server not started. Exiting.")
            exit()

    # Run the server (this part runs twice, but the second time is real)
    print("✅ Starting Flask server...\n")
    app.run(host='0.0.0.0', port=5000, debug=True)

# ======================================================
# 📌 HOW TO RUN & TEST
# ======================================================
# 1. Make sure Flask is installed:
#       pip install Flask
#
# 2. From your project root, run:
#       python server.py
#
# 3. Test:
#    - Browser: http://localhost:5000/
#    - Heatmap: http://localhost:5000/heatmaps/your_file.html
#    - API: POST to http://localhost:5000/api/generate_heatmap
# ======================================================
# END OF FILE
