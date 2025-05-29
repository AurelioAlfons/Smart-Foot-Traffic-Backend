# ====================================================
# Statistics API Routes for Smart Foot Traffic
# ----------------------------------------------------
# - Handles summary and seasonal stats endpoints
# - Calls analytics engine for traffic data and trends
# - Returns JSON for frontend charts and dashboard
# - Used by /api/summary_stats and /api/seasonal_stats
# ====================================================

import os
from flask import Blueprint, request, jsonify
from backend.analytics.daily_linechart import generate_line_charts_combined
from backend.analytics.distribution_pie import generate_combined_pie_dashboard
from backend.analytics.statistics import get_summary_stats
from backend.analytics.weather_distribution import generate_interactive_weather_chart

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
                "url": f"/linecharts/{filename}"
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

@stats_bp.route("/api/generate_piechart", methods=["POST"])
def api_generate_piechart():
    try:
        data = request.get_json()
        date = data.get("date")
        if not date:
            return jsonify({"status": "error", "message": "Missing date parameter."}), 400

        filename = f"pie_dashboard_{date}.html"
        output_path = generate_combined_pie_dashboard(date)

        if output_path:
            return jsonify({
                "status": "success",
                "filename": filename,
                "url": f"/piecharts/{filename}"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "No data found to generate pie chart."
            }), 404

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@stats_bp.route("/api/generate_weather_chart", methods=["POST"])
def api_generate_weather_chart():
    try:
        data = request.get_json()
        traffic_type = data.get("traffic_type")
        weather_filter = data.get("weather_filter")  # optional list of codes

        if not traffic_type:
            return jsonify({"status": "error", "message": "Missing traffic_type."}), 400

        # Generate safe filename based on traffic type
        safe_type = traffic_type.replace(" ", "")
        filename = f"weather_bar_{safe_type}.html"
        output_path = f"weather_chart/{filename}"

        # If chart already exists, return it directly
        if os.path.exists(output_path):
            return jsonify({
                "status": "exists",
                "filename": filename,
                "url": f"/weather_chart/{filename}"
            }), 200

        # Otherwise, generate new chart
        generate_interactive_weather_chart(
            traffic_type=traffic_type,
            weather_filter=weather_filter,
            output_path=output_path
        )

        return jsonify({
            "status": "generated",
            "filename": filename,
            "url": f"/weather_chart/{filename}"
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
