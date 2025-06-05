# ====================================================
# Smart Traffic Forecast (Dropdown Chart)
# ----------------------------------------------------
# - Input: traffic_type only
# - Forecasts for 9 or 11 locations (based on type)
# - Uses Prophet to generate daily forecasts
# - Adds observed + linear regression
# - Single dropdown HTML with all locations
# ====================================================

import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from prophet import Prophet
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

# Default time range
START_DATETIME = "2024-03-04 00:00:00"
END_DATETIME = "2025-03-04 23:59:00"
FORECAST_END_DATE = datetime(2026, 12, 31).date()

# DB Connection
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


def create_prophet_forecast(df):
    df = df.set_index('ds').asfreq('D').ffill().reset_index()
    model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)
    model.fit(df)
    future = model.make_future_dataframe(periods=(FORECAST_END_DATE - df['ds'].max().date()).days)
    forecast = model.predict(future)
    return forecast[['ds', 'yhat']]


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

    # Skip if file already exists
    if output_path.exists():
        console.print(f"[green]Chart already exists: {output_path}[/green]")
        return

    fig = go.Figure()
    buttons = []

    for i, location in enumerate(locations):
        console.print(f"[yellow]Forecasting: {location}[/yellow]")
        try:
            df = fetch_data(location, traffic_type)
            forecast = create_prophet_forecast(df)
            linreg_y = create_linear_regression(df, forecast['ds'])

            visibility = [False] * (3 * len(locations))
            visibility[i * 3 + 0] = True  # Observed
            visibility[i * 3 + 1] = True  # Prophet
            visibility[i * 3 + 2] = True  # Linear

            buttons.append({
                "label": location,
                "method": "update",
                "args": [{"visible": visibility}]
            })

            fig.add_trace(go.Scatter(
                x=df['ds'], y=df['y'], mode='lines+markers',
                name=f"Observed",
                visible=(i == 0), line=dict(color='black')
            ))

            fig.add_trace(go.Scatter(
                x=forecast['ds'], y=forecast['yhat'], mode='lines',
                name=f"Prophet Forecast",
                visible=(i == 0), line=dict(color='blue')
            ))

            fig.add_trace(go.Scatter(
                x=forecast['ds'], y=linreg_y, mode='lines',
                name=f"Linear Regression",
                visible=(i == 0), line=dict(color='green', dash='dash')
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
    

    safe_name = traffic_type.replace(" ", "_").lower()
    output_path = RESULTS_DIR / f"forecast_chart_{safe_name}.html"

    if output_path.exists():
        console.print(f"[green]Chart already exists: {output_path}[/green]")
        return
    
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
