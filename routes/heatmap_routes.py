from flask import Blueprint, request, jsonify
from backend.visualizer.generator import smart_generate

heatmap_bp = Blueprint('heatmap_bp', __name__)

@heatmap_bp.route('/api/generate_heatmap', methods=['POST'])
def api_generate_heatmap():
    try:
        data = request.get_json()
        date_filter = data.get('date')
        time_filter = data.get('time')
        traffic_type = data.get('traffic_type')

        smart_generate(date_filter, time_filter, traffic_type)

        base_url = request.host_url.rstrip('/')
        time_str = (time_filter or 'all').replace(':', '-')
        type_str = traffic_type.replace(' ', '_')

        return jsonify({
            "status": "generating",
            "heatmap_url": f"{base_url}/heatmaps/heatmap_{date_filter}_{time_str}_{type_str}.html",
            "barchart_url": f"{base_url}/barchart/barchart_{date_filter}_{time_str}_{type_str}.html"
        }), 202
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
