# ====================================================
# Bar Chart Generator for Smart Foot Traffic System
# ----------------------------------------------------
# - Checks if chart exists and is linked in DB
# - If not, generates Plotly bar chart HTML and saves it
# - Updates heatmaps table with chart URL
# ====================================================

import os
import mysql.connector
import plotly.graph_objects as go
from rich.console import Console
from backend.config import DB_CONFIG

console = Console()

def export_bar_chart_html(
    selected_data: dict,
    total_data: dict,
    average_data: dict,
    date=None,
    time=None,
    traffic_type=None
):
    console.print("\n[bold magenta]========== Generating Bar Chart ==========[/bold magenta]")

    if not selected_data and not total_data and not average_data:
        console.print("[bold red]No bar chart data to export.[/bold red]")
        return None

    os.makedirs("barchart", exist_ok=True)

    filename = "bar_chart.html"
    if date and time and traffic_type:
        safe_type = traffic_type.replace(" ", "")
        safe_time = time.replace(":", "-")
        filename = f"bar_{date}_{safe_time}_{safe_type}.html"

    output_path = os.path.join("barchart", filename)

    # Check if file exists and it's already linked in DB
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT BarChart_URL FROM heatmaps
            WHERE Traffic_Type = %s AND Date_Filter = %s AND Time_Filter = %s
        """, (traffic_type, date, time))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result and result["BarChart_URL"] and os.path.exists(output_path):
            console.print(f"[green]Bar chart already exists and is linked in DB.[/green]")
            return result["BarChart_URL"]

    except mysql.connector.Error as e:
        console.print(f"[red]DB check failed:[/red] {e}")

    # 🔧 Generate bar chart
    locations = sorted(set(selected_data.keys()) | set(total_data.keys()) | set(average_data.keys()))
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=locations,
        y=[selected_data.get(loc, 0) for loc in locations],
        name="Selected Hour",
        text=[selected_data.get(loc, 0) for loc in locations],
        textposition="outside",
        visible=True
    ))

    fig.add_trace(go.Bar(
        x=locations,
        y=[total_data.get(loc, 0) for loc in locations],
        name="Total Count",
        text=[total_data.get(loc, 0) for loc in locations],
        textposition="outside",
        visible=False
    ))

    fig.add_trace(go.Bar(
        x=locations,
        y=[average_data.get(loc, 0) for loc in locations],
        name="Daily Average",
        text=[average_data.get(loc, 0) for loc in locations],
        textposition="outside",
        visible=False
    ))

    fig.update_layout(
        title=f"{traffic_type} Bar Chart for {date} at {time}",
        title_x=0.5,
        xaxis_title="Location",
        yaxis_title="Traffic Count",
        bargap=0.25,
        xaxis_tickangle=-30,
        plot_bgcolor='white',
        margin=dict(t=10),
        updatemenus=[{
            "buttons": [
                {"label": "Selected Hour", "method": "update", "args": [{"visible": [True, False, False]}]},
                {"label": "Total Count", "method": "update", "args": [{"visible": [False, True, False]}]},
                {"label": "Daily Average", "method": "update", "args": [{"visible": [False, False, True]}]},
            ],
            "direction": "down",
            "x": -0.35,
            "xanchor": "left",
            "y": 1.35,
            "yanchor": "top",
            "showactive": True
        }]
    )

    html_code = fig.to_html(full_html=False, include_plotlyjs='cdn')

    scrollable_html = f"""
    <html>
    <head>
        <style>
        .scroll-container {{
            height: 700px;
            overflow-y: scroll;
            padding: 10px;
            border-top: 2px solid #eee;
        }}
        body {{
            margin: 0;
            padding: 0;
        }}
        </style>
    </head>
    <body>
        <div class="scroll-container">
            {html_code}
        </div>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(scrollable_html)

    console.print("[bold magenta]" + "=" * 50 + "[/bold magenta]")
    console.print(f"Bar chart saved to: [green]{output_path}[/green]")

    # Update BarChart_URL in DB
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Use localhost or prod URL
        base_url = os.getenv("BASE_URL", "http://localhost:5000")
        prod_url = os.getenv("PROD_URL", "https://smart-foot-traffic-backend.onrender.com")

        chart_url = f"{prod_url}/barchart/{filename}" if "localhost" not in base_url else f"{base_url}/barchart/{filename}"

        cursor.execute("""
            UPDATE heatmaps
            SET BarChart_URL = %s
            WHERE Traffic_Type = %s AND Date_Filter = %s AND Time_Filter = %s
        """, (chart_url, traffic_type, date, time))
        conn.commit()
        cursor.close()
        conn.close()

    except mysql.connector.Error as e:
        console.print(f"[red]Failed to update BarChart_URL in DB:[/red] {e}")

    return chart_url
