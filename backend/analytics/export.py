# ==============================================
# Export HTML Report Generator
# ----------------------------------------------
# - Generates analysis report based on filters
# - Outputs a formatted .html file with visuals
# ==============================================

from datetime import datetime
import os

def export_report_html(
    date,
    time,
    traffic_type,
    heatmap_url,
    bar_chart_url,
    line_chart_url,
    pie_chart_url,
    forecast_chart_url,
    save_path=None
):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if save_path is None:
        os.makedirs("downloads", exist_ok=True)
        save_path = f"downloads/report_{date}.html"
    else:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

    html_content = f"""
    <html>
    <head>
        <title>Traffic Analysis Report</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Roboto', sans-serif;
                margin: 40px;
                color: #000;
                background-color: #fdfdfd;
            }}
            h1 {{
                color: #000;
                font-size: 32px;
                border-bottom: 2px solid #ccc;
                padding-bottom: 5px;
            }}
            h2 {{
                color: #000;
                font-size: 24px;
                margin-top: 40px;
                border-left: 4px solid #000;
                padding-left: 10px;
            }}
            ul {{
                list-style: none;
                padding-left: 0;
            }}
            li {{
                padding: 4px 0;
            }}
            .section {{
                margin-top: 30px;
            }}
            iframe {{
                width: 100%;
                height: 600px;
                border: 1px solid #ccc;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <h1>Smart Foot Traffic - Analysis Report</h1>
        <p><strong>Generated on:</strong> {now}</p>

        <div class="section">
            <h2>Selected Parameters</h2>
            <ul>
                <li><strong>Date:</strong> {date}</li>
                <li><strong>Time:</strong> {time}</li>
                <li><strong>Traffic Type:</strong> {traffic_type}</li>
            </ul>
        </div>

        <div class="section">
            <h2>Heatmap</h2>
            <iframe src="{heatmap_url}"></iframe>
        </div>

        <div class="section">
            <h2>Bar Chart</h2>
            <iframe src="{bar_chart_url}"></iframe>
        </div>

        <div class="section">
            <h2>Line Chart</h2>
            <iframe src="{line_chart_url}"></iframe>
        </div>

        <div class="section">
            <h2>Pie Chart</h2>
            <iframe src="{pie_chart_url}"></iframe>
        </div>

        <div class="section">
            <h2>Forecast Chart</h2>
            <iframe src="{forecast_chart_url}"></iframe>
        </div>
    </body>
    </html>
    """

    with open(save_path, "w", encoding="utf-8") as file:
        file.write(html_content)

    return save_path
