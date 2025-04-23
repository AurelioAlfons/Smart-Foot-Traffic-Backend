# ==========================================
# 🛰️ Flask Server to Serve Heatmaps Locally
# ==========================================
# This server allows you to access generated
# heatmap .html files from your browser via
# localhost URLs (e.g. http://localhost:5000)

from flask import Flask, send_from_directory
import os

# 🔧 Initialize the Flask app
app = Flask(__name__)

# 📁 Define the folder where heatmaps are saved
HEATMAP_FOLDER = os.path.join(os.getcwd(), 'heatmaps')

# 🏠 Home route to confirm server is running
@app.route('/')
def index():
    return "<h2>🌐 Smart Foot Traffic – Heatmaps</h2><p>Try visiting /heatmaps/filename.html</p>"

# 📦 Route to serve any heatmap HTML file by filename
@app.route('/heatmaps/<filename>')
def serve_heatmap(filename):
    return send_from_directory(HEATMAP_FOLDER, filename)

# ▶️ Run this script to start the server locally
if __name__ == '__main__':
    app.run(debug=True)

# ======================================================
# 📌 HOW TO RUN & TEST
# ======================================================
# 1. Make sure Flask is installed:
#       pip install Flask
#
# 2. From your project root, run:
#       python server.py
#
# 3. Visit in your browser:
#       http://localhost:5000/
#       http://localhost:5000/heatmaps/heatmap_2025-02-27_12-00-00_Vehicle_Count.html
#
# 4. Make sure the .html file exists in the heatmaps/ folder!
# ======================================================
# END OF FILE