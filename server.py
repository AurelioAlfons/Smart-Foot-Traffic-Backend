# ====================================================
# Main Server for Smart Foot Traffic System
# ----------------------------------------------------
# - Hosts Flask app and registers all API routes
# - Serves heatmap and bar chart HTML files
# - Auto-generates default map on first request
# - Adds CORS and basic security headers
# ====================================================

import time
from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import logging
from rich.console import Console

# Console setup
console = Console()

# App Setup
app = Flask(__name__)
CORS(app)

# Import Blueprints
from routes.heatmap_routes import heatmap_bp
from routes.statistics_routes import stats_bp
from routes.details_routes import snapshot_bp

# Suppress Werkzeug's default logs
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Register Blueprints
app.register_blueprint(heatmap_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(snapshot_bp)

# Folder Paths
HEATMAP_FOLDER = os.path.join(os.getcwd(), 'heatmaps')
BARCHART_FOLDER = os.path.join(os.getcwd(), 'barchart')
default_map_generated = False

# Serve Heatmap HTML
@app.route('/heatmaps/<path:filename>')
def serve_heatmap(filename):
    console.print("\n[bold magenta]========== Serving Heatmap ==========[/bold magenta]")
    start = time.time()
    
    console.print(f"Requested heatmap file: [green]{filename}[/green]")
    response = send_from_directory(HEATMAP_FOLDER, filename)
    
    duration = time.time() - start
    console.print(f"[cyan]Time taken: {duration:.2f} seconds[/cyan]")
    return response

# Serve Bar Chart HTML
@app.route('/barchart/<path:filename>')
def serve_barchart(filename):
    console.print("\n[bold magenta]========== Serving Bar Chart ==========[/bold magenta]")
    start = time.time()
    
    console.print(f"Requested bar chart file: [green]{filename}[/green]")
    response = send_from_directory(BARCHART_FOLDER, filename)
    
    duration = time.time() - start
    console.print(f"[cyan]Time taken: {duration:.2f} seconds[/cyan]")
    return response

# Health Check
@app.route('/healthz')
def health_check():
    console.print("[green]Health check OK[/green]")
    return "OK", 200

# Default Heatmap Preload
@app.before_request
def ensure_default_map():
    global default_map_generated
    path = os.path.join(HEATMAP_FOLDER, 'default_map.html')
    if not os.path.exists(path) or not default_map_generated:
        from backend.visualizer.generator.generate_default import generate_default_map
        try:
            generate_default_map()
            default_map_generated = True
        except Exception as e:
            console.print(f"[bold red]Failed to generate default map:[/bold red] {e}")

# CORS & Security Headers
@app.after_request
def apply_cors_headers(response):
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

# Run the Server
if __name__ == '__main__':
    console.print("[bold magenta]=== Starting Smart Foot Traffic Server ===[/bold magenta]")
    console.print("[cyan]Listening on http://localhost:5000[/cyan]\n")
    app.run(host='0.0.0.0', port=5000)
