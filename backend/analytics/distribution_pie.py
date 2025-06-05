import os
import mysql.connector
import plotly.graph_objects as go
from rich.console import Console
from backend.config import DB_CONFIG
from backend.analytics.chart_template import wrap_plotly_chart

console = Console()

# Normalize DB traffic types to short labels
normalize_type = {
    "Pedestrian Count": "Pedestrian",
    "Cyclist Count": "Cyclist",
    "Vehicle Count": "Vehicle"
}

# Set consistent colors
type_color_map = {
    "Pedestrian": "#3bffc1",
    "Cyclist": "#ffe53b",
    "Vehicle": "#8b4dff"
}

def generate_combined_pie_dashboard(date: str) -> str:
    console.print(f"\n[bold magenta]========== Generating Pie Chart Dashboard ==========[/bold magenta]")
    console.print(f"Date: [green]{date}[/green]")

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                pd.Location,
                tc.Traffic_Type,
                SUM(tc.Interval_Count) AS Total_Count
            FROM processed_data pd
            JOIN traffic_counts tc ON pd.Data_ID = tc.Data_ID
            WHERE DATE(pd.Date_Time) = %s
            GROUP BY pd.Location, tc.Traffic_Type
            ORDER BY pd.Location;
        """, (date,))

        rows = cursor.fetchall()
        console.print(f"Fetched [cyan]{len(rows)}[/cyan] rows from database.")

        if not rows:
            console.print("[yellow]No data available for this date.[/yellow]")
            return ""

        # Organize counts per location
        data_by_location = {}
        for row in rows:
            loc = row["Location"]
            raw_type = row["Traffic_Type"]
            ttype = normalize_type.get(raw_type, raw_type)
            count = row["Total_Count"]
            if loc not in data_by_location:
                data_by_location[loc] = {}
            data_by_location[loc][ttype] = count

        traffic_types = ["Pedestrian", "Cyclist", "Vehicle"]
        fig = go.Figure()
        valid_locations = []

        # Add all pie chart traces
        for loc, counts in data_by_location.items():
            labels = []
            values = []
            colors = []

            for t in traffic_types:
                labels.append(t)
                values.append(counts.get(t, 0))
                colors.append(type_color_map[t])

            if sum(values) == 0:
                console.print(f"[yellow]Skipping {loc} — all values are 0[/yellow]")
                continue

            fig.add_trace(go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                name=loc,
                visible=False,
                marker=dict(colors=colors),
                text=[loc] * len(labels),
                textinfo='label+percent+value+text',
                textposition='outside',
                automargin=True
            ))

            valid_locations.append(loc)

        if not valid_locations:
            console.print("[red]No non-zero traffic data found for any location.[/red]")
            return ""

        # Show only the first location by default
        fig.data[0].visible = True

        # Fix visibility toggling with correctly sized arrays
        buttons = []
        for i, loc in enumerate(valid_locations):
            visible_array = [j == i for j in range(len(valid_locations))]
            buttons.append({
                "label": loc,
                "method": "update",
                "args": [
                    {"visible": visible_array},
                    {"title": f"Traffic Distribution — {loc} ({date})"}
                ]
            })

        fig.update_layout(
            showlegend=True,
            uniformtext_minsize=10,
            uniformtext_mode='hide',
            updatemenus=[{
                "buttons": buttons,
                "direction": "down",
                "x": 0.5,
                "xanchor": "center",
                "y": 1.35,
                "yanchor": "top",
                "showactive": True
            }],
            margin=dict(t=30, b=30),
            height=500
        )

        # Create folder and set path
        os.makedirs("piecharts", exist_ok=True)
        filename = f"pie_dashboard_{date}.html"
        output_path = os.path.join("piecharts", filename)

        # Use cached file if already exists
        if os.path.exists(output_path):
            console.print(f"[green]Chart already exists:[/] {output_path}")
            return output_path

        fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        full_html = wrap_plotly_chart(fig_html, f"Traffic Distribution Dashboard — {date}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_html)

        console.print(f"[green]Dashboard saved to:[/] {output_path}")
        return output_path

    except Exception as e:
        console.print(f"[bold red]Error generating dashboard:[/bold red] {e}")
        return ""

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Run directly for testing
if __name__ == "__main__":
    test_date = "2024-06-27"  # Change as needed
    generate_combined_pie_dashboard(test_date)
