# ====================================================
# Heatmap API Route for Smart Foot Traffic
# ----------------------------------------------------
# - Accepts date, time, and type from frontend
# - Calls smart_generate to build heatmap + bar chart
# - Returns URLs to generated HTML files
# - Used by /api/generate_heatmap endpoint
# ====================================================

from flask import Blueprint, request, jsonify
from backend.visualizer.generator.smart_generate import smart_generate
from rich.console import Console

# Blueprint setup
heatmap_bp = Blueprint('heatmap_bp', __name__)
console = Console()

@heatmap_bp.route('/api/generate_heatmap', methods=['POST'])
def api_generate_heatmap():
    console.print("\n[bold magenta]========== /api/generate_heatmap ==========[/bold magenta]")

    try:
        # Extract request data
        data = request.get_json(force=True)
        console.print(f"Data received: [green]{data}[/green]")

        date_filter = data.get('date')
        time_filter = data.get('time')
        traffic_type = data.get('traffic_type')

        # Validate required fields
        if not date_filter or not time_filter or not traffic_type:
            console.print("[bold red]Missing required fields: date, time, or traffic_type[/bold red]")
            return jsonify({"status": "error", "message": "Missing date, time, or traffic_type"}), 400

        # Call backend generator
        console.print("[yellow]Calling smart_generate...[/yellow]")
        smart_generate(date_filter, time_filter, traffic_type)
        console.print("[green]smart_generate completed successfully.[/green]")
        console.print("[bold magenta]" + "=" * 50 + "[/bold magenta]\n")

        # Build URLs
        base_url = request.host_url.rstrip('/')
        time_str = (time_filter or 'all').replace(':', '-')
        type_str = traffic_type.replace(' ', '_')

        return jsonify({
            "status": "generating",
            "heatmap_url": f"{base_url}/heatmaps/heatmap_{date_filter}_{time_str}_{type_str}.html",
            "barchart_url": f"{base_url}/barchart/bar_{date_filter}_{time_str}_{type_str}.html"
        }), 202

    except Exception as e:
        console.print(f"[bold red]ERROR in /api/generate_heatmap:[/bold red] {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
