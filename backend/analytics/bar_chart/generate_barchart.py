# ====================================================
# Bar Chart Generator for Smart Foot Traffic System
# ----------------------------------------------------
# - Creates a Plotly bar chart by location and time
# - Saves chart as HTML to local barchart/ folder
# - Returns full path to use in database or API
# - Called from seasonal_stats.py
# ====================================================

import os
import plotly.express as px

def export_bar_chart_html(bar_data: dict, date=None, time=None, traffic_type=None):
    if not bar_data:
        print("⚠️ No bar chart data to export.")
        return None  # Explicitly return None if no data

    # 🛡️ Ensure the output folder exists
    os.makedirs("barchart", exist_ok=True)

    # 🧠 Generate dynamic filename with consistent format
    filename = "bar_chart.html"
    if date and time and traffic_type:
        safe_type = traffic_type.replace(" ", "")
        safe_time = time.replace(":", "-")
        filename = f"bar_{date}_{safe_time}_{safe_type}.html"

    output_path = os.path.join("barchart", filename)

    # 📊 Create and save bar chart
    fig = px.bar(
        x=list(bar_data.keys()),
        y=list(bar_data.values()),
        labels={'x': 'Location', 'y': 'Traffic Count'},
        title=f"📊 {traffic_type} by Location at {time} on {date}",
    )
    fig.update_layout(
        bargap=0.25,
        title_x=0.5,
        xaxis_tickangle=-30,
        plot_bgcolor='white'
    )
    fig.write_html(output_path)
    print(f"✅ Plotly bar chart saved to {output_path}")

    return output_path  # ✅ Return the full path to use in URL or DB
