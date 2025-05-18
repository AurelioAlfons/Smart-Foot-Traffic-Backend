from flask import Blueprint, request, jsonify
from backend.analytics.statistics import get_summary_stats
from backend.analytics.season_stats.season_stats import get_seasonal_stats

stats_bp = Blueprint('stats_bp', __name__)

@stats_bp.route('/api/summary_stats', methods=['POST'])
def api_summary_stats():
    try:
        data = request.get_json()
        return jsonify(get_summary_stats(data['date'], data['time'], data['traffic_type'])), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@stats_bp.route('/api/seasonal_stats', methods=['POST'])
def api_seasonal_stats():
    try:
        data = request.get_json()
        return jsonify(get_seasonal_stats(int(data['year']), data['time'], data['traffic_type'])), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
