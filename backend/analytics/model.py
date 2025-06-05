# ====================================================
# Smart Traffic Forecast (Dropdown Chart)
# ----------------------------------------------------
# - Input: traffic_type only
# - Forecasts for 9 or 11 locations (based on type)
# - Uses linear regression to generate daily forecasts
# - Adds observed + linear regression
# - Single dropdown HTML with all locations
# ====================================================

import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go
from rich.console import Console
from rich.prompt import Prompt
from backend.analytics.chart_template import wrap_plotly_chart
from backend.config import DB_CONFIG

# Setup
console = Console()
RESULTS_DIR = Path("model_results")
RESULTS_DIR.mkdir(exist_ok=True)

ALL_LOCATIONS = [
    'Footscray Library Car Park', 'Footscray Market Hopkins And Irving',
    'Footscray Market Hopkins And Leeds', 'Nic St Campus',
    'Footscray Park Rowing Club', 'Footscray Park Gardens',
    'Footscray Market Irving St Train Stn', 'Nicholson Mall Clock Tower',
    'West Footscray Library', 'Snap Fitness', 'Salt Water Child Care Centre'
]
VEHICLE_EXCLUDE = {'Footscray Park Gardens', 'Footscray Park Rowing Club'}

START_DATETIME = "2024-03-04 00:00:00"
END_DATETIME = "2025-03-04 23:59:00"
FORECAST_END_DATE = datetime(2026, 12, 31).date()

conn_str = (
    f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)
engine = create_engine(conn_str)

def fetch_data(location, traffic_type):
    query = text("""
        SELECT p.Date_Time AS ds, t.Total_Count AS y
        FROM processed_data p
        JOIN traffic_counts t ON p.Data_ID = t.Data_ID
        WHERE p.Location = :location AND t.Traffic_Type = :traffic_type
          AND p.Date_Time BETWEEN :start AND :end
    """)
    df = pd.read_sql(query, engine, params={
        'location': location,
        'traffic_type': traffic_type,
        'start': START_DATETIME,
        'end': END_DATETIME
    })
    df['ds'] = pd.to_datetime(df['ds'], errors='coerce')
    df = df.dropna(subset=['ds']).drop_duplicates('ds').sort_values('ds')
    df['y'] = df['y'].clip(lower=0)
    return df[['ds', 'y']]

def create_linear_regression(df, future_dates):
    df = df.copy()
    df['timestamp'] = df['ds'].astype(np.int64) // 10 ** 9
    X = df['timestamp'].values.reshape(-1, 1)
    y = df['y'].values
    model = LinearRegression().fit(X, y)
    future_ts = (future_dates.astype(np.int64) // 10 ** 9).values.reshape(-1, 1)
    y_pred = model.predict(future_ts)
    return y_pred

def generate_forecast_chart(traffic_type: str):
    console.print(f"\n[bold cyan]Generating forecasts for: {traffic_type}[/bold cyan]")

    if traffic_type == "Vehicle Count":
        locations = [loc for loc in ALL_LOCATIONS if loc not in VEHICLE_EXCLUDE]
    else:
        locations = ALL_LOCATIONS[:]

    safe_name = traffic_type.replace(" ", "_").lower()
    output_path = RESULTS_DIR / f"forecast_chart_{safe_name}.html"

    if output_path.exists():
        console.print(f"[green]Chart already exists: {output_path}[/green]")
        return

    fig = go.Figure()
    buttons = []

    for i, location in enumerate(locations):
        console.print(f"[yellow]Forecasting: {location}[/yellow]")
        try:
            df = fetch_data(location, traffic_type)
            future_dates = pd.date_range(start=df['ds'].max() + pd.Timedelta(days=1), end=FORECAST_END_DATE, freq='D')
            linreg_y = create_linear_regression(df, future_dates)

            visibility = [False] * (2 * len(locations))
            visibility[i * 2 + 0] = True  # Observed
            visibility[i * 2 + 1] = True  # Linear

            buttons.append({
                "label": location,
                "method": "update",
                "args": [{"visible": visibility}]
            })

            fig.add_trace(go.Scatter(
                x=df['ds'], y=df['y'], mode='lines+markers',
                name="Observed", visible=(i == 0),
                line=dict(color='black')
            ))

            fig.add_trace(go.Scatter(
                x=future_dates, y=linreg_y, mode='lines',
                name="Linear Regression", visible=(i == 0),
                line=dict(color='red', dash='dash')
            ))

        except Exception as e:
            console.print(f"[red]Failed for {location}: {e}[/red]")

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Predicted Count",
        template="plotly_white",
        height=600,
        updatemenus=[{
            "buttons": buttons,
            "direction": "down",
            "x": 0.05,
            "xanchor": "left",
            "y": 1.15,
            "yanchor": "top",
            "showactive": True
        }]
    )

    fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    final_html = wrap_plotly_chart(fig_html, f"{traffic_type} — Forecast Chart")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    console.print(f"\n[green]Forecast chart saved to:[/green] {output_path}")

if __name__ == "__main__":
    with engine.connect() as conn:
        traffic_types = [row[0] for row in conn.execute(text("SELECT DISTINCT Traffic_Type FROM traffic_counts"))]

    console.print("\nAvailable Traffic Types:")
    for i, t in enumerate(traffic_types, 1):
        console.print(f"[{i}] {t}")

    selected = Prompt.ask("\nEnter traffic type", choices=traffic_types, default=traffic_types[0])
    generate_forecast_chart(selected)
