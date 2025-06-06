from flask import Blueprint, request
import os
from backend.analytics.export import export_report_html

export_bp = Blueprint('export_bp', __name__)

@export_bp.route("/api/download_report")
def download_report():
    date = request.args.get("date")
    time = request.args.get("time")
    traffic_type = request.args.get("type")

    if not date or not time or not traffic_type:
        return {"status": "error", "message": "Missing query parameters."}, 400

    base_url = "http://localhost:5000"
    safe_time = time.replace(":", "-")
    safe_type = traffic_type.replace(" ", "")
    safe_traffic = traffic_type.replace(" ", "_")
    safe_traffic_lower = traffic_type.replace(" ", "_").lower()

    # Generate URLs
    heatmap_url = f"{base_url}/heatmaps/heatmap_{date}_{safe_time}-00_{safe_traffic}.html"
    bar_chart_url = f"{base_url}/barchart/bar_{date}_{safe_time}-00_{safe_type}.html"
    line_chart_url = f"{base_url}/linecharts/line_{date}_{safe_type}.html"
    pie_chart_url = f"{base_url}/piecharts/pie_dashboard_{date}.html"
    forecast_chart_url = f"{base_url}/forecast/forecast_chart_{safe_traffic_lower}.html"

    # DEBUG: Output actual resolved filenames
    print("[DEBUG] Generated filenames:")
    print(f" - Heatmap: {heatmap_url.replace(base_url + '/heatmaps/', '')}")
    print(f" - Bar Chart: {bar_chart_url.replace(base_url + '/barchart/', '')}")
    print(f" - Line Chart: {line_chart_url.replace(base_url + '/linecharts/', '')}")
    print(f" - Pie Chart: {pie_chart_url.replace(base_url + '/piecharts/', '')}")
    print(f" - Forecast Chart: {forecast_chart_url.replace(base_url + '/forecast/', '')}")

    # Export the HTML report
    export_report_html(
        date=date,
        time=time,
        traffic_type=traffic_type,
        heatmap_url=heatmap_url,
        bar_chart_url=bar_chart_url,
        line_chart_url=line_chart_url,
        pie_chart_url=pie_chart_url,
        forecast_chart_url=forecast_chart_url
    )

    return {"status": "success", "message": f"Report saved as report_{date}.html"}, 200
