from flask import Blueprint, request, jsonify
from backend.visualizer.generator.smart_generate import smart_generate

heatmap_bp = Blueprint('heatmap_bp', __name__)

@heatmap_bp.route('/api/generate_heatmap', methods=['POST'])
def api_generate_heatmap():
    print("🚀 /api/generate_heatmap hit")
    try:
        data = request.get_json(force=True)
        print("📥 Data received:", data)

        date_filter = data.get('date')
        time_filter = data.get('time')
        traffic_type = data.get('traffic_type')

        if not date_filter or not time_filter or not traffic_type:
            print("❌ Missing required fields.")
            return jsonify({"status": "error", "message": "Missing date, time, or traffic_type"}), 400

        print("🧠 Calling smart_generate...")
        smart_generate(date_filter, time_filter, traffic_type)
        print("✅ smart_generate completed.")

        base_url = request.host_url.rstrip('/')
        time_str = (time_filter or 'all').replace(':', '-')
        type_str = traffic_type.replace(' ', '_')

        return jsonify({
            "status": "generating",
            "heatmap_url": f"{base_url}/heatmaps/heatmap_{date_filter}_{time_str}_{type_str}.html",
            "barchart_url": f"{base_url}/barchart/barchart_{date_filter}_{time_str}_{type_str}.html"
        }), 202

    except Exception as e:
        print("🔥 ERROR in /api/generate_heatmap:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
