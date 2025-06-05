import os
import mysql.connector
import plotly.graph_objects as go
from rich.console import Console
from backend.analytics.chart_template import wrap_plotly_chart
from backend.config import DB_CONFIG

console = Console()

def generate_line_charts_combined(date: str, traffic_type: str) -> str:
    console.print(f"\n[bold magenta]========== Generating Combined Line Chart ==========[/bold magenta]")
    console.print(f"Traffic Type: {traffic_type} | Date: {date}")

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                pd.Location,
                DATE_FORMAT(pd.Date_Time, '%H:%i') AS time_label,
                tc.Interval_Count
            FROM processed_data pd
            JOIN traffic_counts tc ON pd.Data_ID = tc.Data_ID
            WHERE DATE(pd.Date_Time) = %s AND tc.Traffic_Type = %s
            ORDER BY pd.Location, pd.Date_Time
        """, (date, traffic_type))

        rows = cursor.fetchall()
        console.print(f"Fetched {len(rows)} rows from database.")

        if not rows:
            console.print("No data found for the given date and type.")
            return ""

        location_data = {}
        for row in rows:
            loc = row['Location']
            time_label = row['time_label']
            count = row['Interval_Count']
            if loc not in location_data:
                location_data[loc] = {"time": [], "count": []}
            location_data[loc]["time"].append(time_label)
            location_data[loc]["count"].append(count)

        os.makedirs("linecharts", exist_ok=True)

        fig = go.Figure()
        buttons = []
        all_locations = list(location_data.keys())

        for i, loc in enumerate(all_locations):
            data = location_data[loc]
            visible_array = [False] * len(all_locations)
            visible_array[i] = True

            fig.add_trace(go.Scatter(
                x=data["time"],
                y=data["count"],
                mode='lines+markers',
                name=loc,
                line=dict(color='#FBC02D'),
                marker=dict(color='#FBC02D'),
                visible=(i == 0)
            ))

            buttons.append(dict(
                label=loc,
                method="update",
                args=[{"visible": visible_array},
                      {"title": f"{traffic_type} - {loc} on {date}"}]
            ))

        fig.update_layout(
            title_x=0.5,
            xaxis_title="Time of Day",
            yaxis_title="Interval Count",
            plot_bgcolor='white',
            margin=dict(t=10),
            height=500,
            updatemenus=[{
                "buttons": buttons,
                "direction": "down",
                "x": -0.05,
                "xanchor": "left",
                "y": 1.15,
                "yanchor": "top",
                "showactive": True
            }]
        )

        safe_type = traffic_type.replace(" ", "")
        filename = f"line_{date}_{safe_type}.html"
        output_path = os.path.join("linecharts", filename)

        fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        full_html = wrap_plotly_chart(fig_html, f"{traffic_type} — {date}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_html)

        console.print(f"Chart saved to: {output_path}")
        return output_path

    except Exception as e:
        console.print(f"Error generating line chart: {e}")
        return ""

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
