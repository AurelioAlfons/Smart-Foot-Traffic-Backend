# ====================================================
# Statistics API Routes for Smart Foot Traffic
# ----------------------------------------------------
# - Handles summary and seasonal stats endpoints
# - Calls analytics engine for traffic data and trends
# - Returns JSON for frontend charts and dashboard
# - Used by /api/summary_stats and /api/seasonal_stats
# ====================================================

from flask import Blueprint, request, jsonify
from backend.analytics.daily_linechart import generate_line_charts_combined
from backend.analytics.statistics import get_summary_stats

stats_bp = Blueprint('stats_bp', __name__)

@stats_bp.route('/api/summary_stats', methods=['POST'])
def api_summary_stats():
    try:
        data = request.get_json()
        return jsonify(get_summary_stats(data['date'], data['time'], data['traffic_type'])), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@stats_bp.route("/api/generate_linechart", methods=["POST"])
def api_generate_linechart():
    try:
        data = request.get_json()
        date = data["date"]
        traffic_type = data["traffic_type"]
        safe_type = traffic_type.replace(" ", "")
        filename = f"line_{date}_{safe_type}.html"
        output_path = generate_line_charts_combined(date, traffic_type)

        if output_path:
            return jsonify({
                "status": "success",
                "filename": filename,
                "url": f"http://localhost:5000/linecharts/{filename}"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "No data found to generate chart."
            }), 404

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500