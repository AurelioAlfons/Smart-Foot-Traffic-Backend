from flask import Flask, send_from_directory
from flask_cors import CORS
import os

# 🔧 App Setup
app = Flask(__name__)
CORS(app)

# 🔁 Import Blueprints
from routes.heatmap_routes import heatmap_bp
from routes.statistics_routes import stats_bp

# 🔗 Register Blueprints
app.register_blueprint(heatmap_bp)
app.register_blueprint(stats_bp)

# 📁 Folder Paths
HEATMAP_FOLDER = os.path.join(os.getcwd(), 'heatmaps')
BARCHART_FOLDER = os.path.join(os.getcwd(), 'barchart')
default_map_generated = False

# 🗺️ Serve Heatmap HTML
@app.route('/heatmaps/<path:filename>')
def serve_heatmap(filename):
    return send_from_directory(HEATMAP_FOLDER, filename)

# 📊 Serve Bar Chart HTML
@app.route('/barchart/<path:filename>')
def serve_barchart(filename):
    return send_from_directory(BARCHART_FOLDER, filename)

# ✅ Health Check
@app.route('/healthz')
def health_check():
    return "OK", 200

# 🌍 Default Heatmap Preload
@app.before_request
def ensure_default_map():
    global default_map_generated
    path = os.path.join(HEATMAP_FOLDER, 'default_map.html')
    if not os.path.exists(path) or not default_map_generated:
        from backend.visualizer.generator.generate_default import generate_default_map
        generate_default_map()
        default_map_generated = True

# 🧰 CORS & Security Headers
@app.after_request
def apply_cors_headers(response):
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

# ▶️ Run the Server
if __name__ == '__main__':
    print("✅ Starting Smart Foot Traffic server on http://localhost:5000\n")
    app.run(host='0.0.0.0', port=5000)
