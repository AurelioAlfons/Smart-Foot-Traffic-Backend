# ============================================================
# Interactive Weather-Based Traffic Chart by Location
# ------------------------------------------------------------
# - One chart displayed at a time
# - Users can select location from a dropdown menu
# - Chart updates dynamically using JavaScript
# - Uses plotly and shared HTML template for consistent layout
# ============================================================

import pandas as pd
import plotly.graph_objects as go
import os
import json

from backend.analytics.chart_template import wrap_plotly_chart

# Weather label mapping
WEATHER_MAP = {
    0: "Clear", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime Fog", 51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
    56: "Freezing Drizzle", 57: "Freezing Dense Drizzle",
    61: "Light Rain", 63: "Moderate Rain", 65: "Heavy Rain",
    66: "Freezing Rain", 67: "Freezing Heavy Rain",
    71: "Light Snow", 73: "Moderate Snow", 75: "Heavy Snow",
    77: "Snow Grains", 80: "Rain Showers", 81: "Heavy Showers", 82: "Violent Showers",
    85: "Snow Showers", 86: "Heavy Snow Showers",
    95: "Thunderstorm", 96: "Thunderstorm + Hail", 99: "Thunderstorm + Heavy Hail"
}

# List of known traffic sensor locations
LOCATIONS = [
    "Footscray Library Car Park", "Footscray Market Hopkins And Irving", "Footscray Market Hopkins And Leeds",
    "Nic St Campus", "Footscray Park Rowing Club", "Footscray Park Gardens",
    "Footscray Market Irving St Train Stn", "Nicholson Mall Clock Tower", "West Footscray Library",
    "Snap Fitness", "Salt Water Child Care Centre"
]

# Simulated data for demo (replace with MySQL query in production)
def simulate_data():
    data = []
    for loc in LOCATIONS:
        for weather in WEATHER_MAP.keys():
            avg_count = 100 + hash((loc, weather)) % 200
            data.append({
                "Location": loc,
                "Weather": weather,
                "Avg_Count": avg_count
            })
    return pd.DataFrame(data)

# Main chart generator
def generate_interactive_weather_chart(
    traffic_type="Vehicle Count",
    weather_filter=None,
    output_path="weather_chart/weather_bar_charts.html"
):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df = simulate_data()
    df["Weather_Label"] = df["Weather"].map(WEATHER_MAP)

    if weather_filter:
        df = df[df["Weather"].isin(weather_filter)]

    chart_data = {}
    for location in LOCATIONS:
        loc_df = df[df['Location'] == location]
        if loc_df.empty:
            continue

        fig = go.Figure()
        for _, row in loc_df.iterrows():
            fig.add_trace(go.Bar(
                x=[row['Weather_Label']],
                y=[row['Avg_Count']],
                name=row['Weather_Label'],
                text=[row['Avg_Count']],
                textposition="auto"
            ))

        fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.25,            # simulate "outside top"
            xanchor="center",
            x=0.5,
            font=dict(size=10)
        ),
        xaxis_title="Weather Condition",
        yaxis_title="Average Traffic Count",
        template="plotly_white",
        height=600,
        margin=dict(t=240, b=80, l=40, r=40)
    )

        chart_data[location] = json.loads(fig.to_json())

    # Create dropdown and chart HTML using template
    dropdown_html = f"""
    <div style="margin-top: 40px;">  
        <label for="locationSelect" style="font-weight:bold; margin-right:10px;">Choose Location:</label>
        <select id="locationSelect" onchange="updateChart()" style="padding:8px 12px; border-radius:6px; font-size:14px;">
            {''.join(f'<option value="{loc}">{loc}</option>' for loc in chart_data)}
        </select>
    </div>
    <div id="chart"></div>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        const chartData = {json.dumps(chart_data)};
        function updateChart() {{
            const selected = document.getElementById("locationSelect").value;
            Plotly.newPlot("chart", chartData[selected].data, chartData[selected].layout);
        }}
        updateChart();
    </script>
    """


    # Wrap in shared HTML template
    full_html = wrap_plotly_chart(dropdown_html, f"{traffic_type} – Weather Chart")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)

# Example usage
if __name__ == "__main__":
    generate_interactive_weather_chart(
        traffic_type="Vehicle Count",
        weather_filter=None,  # Show all weather conditions
        output_path="weather_chart/weather_bar_charts.html"
    )
