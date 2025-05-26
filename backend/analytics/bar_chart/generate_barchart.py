# ====================================================
# Bar Chart Generator for Smart Foot Traffic System
# ----------------------------------------------------
# - Creates a Plotly bar chart by location and time
# - Includes 3 chart modes: Selected Hour, Total Day, Daily Average
# - Dropdown menu toggles chart visibility
# - Saves chart as HTML to local barchart/ folder
# - Returns full path to use in database or API
# - Called from statistics.py
# ====================================================

import os
import plotly.graph_objects as go

def export_bar_chart_html(
    selected_data: dict,
    total_data: dict,
    average_data: dict,
    date=None,
    time=None,
    traffic_type=None
):
    if not selected_data and not total_data and not average_data:
        print("⚠️ No bar chart data to export.")
        return None

    os.makedirs("barchart", exist_ok=True)

    filename = "bar_chart.html"
    if date and time and traffic_type:
        safe_type = traffic_type.replace(" ", "")
        safe_time = time.replace(":", "-")
        filename = f"bar_{date}_{safe_time}_{safe_type}.html"

    output_path = os.path.join("barchart", filename)

    # Prepare location axis
    locations = sorted(set(selected_data.keys()) | set(total_data.keys()) | set(average_data.keys()))

    # Create the figure
    fig = go.Figure()

    # Trace 1: Selected Hour
    fig.add_trace(go.Bar(
        x=locations,
        y=[selected_data.get(loc, 0) for loc in locations],
        name="Selected Hour",
        text=[selected_data.get(loc, 0) for loc in locations],
        textposition="outside",
        visible=True
    ))

    # Trace 2: Total Count
    fig.add_trace(go.Bar(
        x=locations,
        y=[total_data.get(loc, 0) for loc in locations],
        name="Total Count",
        text=[total_data.get(loc, 0) for loc in locations],
        textposition="outside",
        visible=False
    ))

    # Trace 3: Daily Average
    fig.add_trace(go.Bar(
        x=locations,
        y=[average_data.get(loc, 0) for loc in locations],
        name="Daily Average",
        text=[average_data.get(loc, 0) for loc in locations],
        textposition="outside",
        visible=False
    ))

    # Add dropdown menu
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

    print(f"✅ Combined bar chart saved to {output_path}\n")

    return output_path
