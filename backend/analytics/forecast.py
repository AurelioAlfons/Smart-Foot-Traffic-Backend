import os
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from prophet import Prophet
from sqlalchemy import create_engine, text
from joblib import dump
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np
from rich.progress import Progress
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.panel import Panel
from rich.table import Table
from backend.config import DB_CONFIG

# Constants
NUM_TRAINING_RUNS = 1
RESULTS_DIR = Path("model_results")
RESULTS_DIR.mkdir(exist_ok=True)
console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VU_HOLIDAYS = [
    ("2024-02-12", "2024-02-16"),
    ("2024-03-29", "2024-04-04"),
    ("2024-04-22", "2024-04-26"),
    ("2024-09-23", "2024-09-27"),
    ("2024-07-29", "2024-09-20"),
    ("2024-11-25", "2025-02-12")
]
holiday_ranges = [pd.date_range(start, end) for start, end in VU_HOLIDAYS]
all_holidays = pd.DatetimeIndex(np.concatenate(holiday_ranges))
VU_HOLIDAY_DATES = all_holidays

class TrafficForecaster:
    def __init__(self, location, traffic_type, start_datetime, end_datetime, forecast_end_date):
        conn_str = (
            f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        self.engine = create_engine(conn_str)
        self.location = location
        self.traffic_type = traffic_type
        self.start = start_datetime
        self.end = end_datetime
        self.forecast_end_date = forecast_end_date

    def fetch_data(self):
        query = (
            "SELECT p.Date_Time AS ds, t.Interval_Count AS y "
            "FROM processed_data p "
            "JOIN traffic_counts t ON p.Data_ID = t.Data_ID "
            "WHERE p.Location = %(location)s AND t.Traffic_Type = %(traffic_type)s "
            "AND p.Date_Time BETWEEN %(start)s AND %(end)s"
        )
        df = pd.read_sql(query, self.engine, params={
            'location': self.location,
            'traffic_type': self.traffic_type,
            'start': self.start,
            'end': self.end
        })
        if df.empty:
            raise ValueError("No data found for selected inputs.")
        df['ds'] = pd.to_datetime(df['ds'], errors='coerce')
        df = df.dropna(subset=['ds'])
        df = df.drop_duplicates('ds').sort_values('ds')
        df['y'] = df['y'].clip(lower=0)
        return df[['ds', 'y']]

    def _create_prophet_model(self):
        return Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
            interval_width=0.95
        )

    def prophet_forecast(self, df):
        df = df.dropna(subset=['ds', 'y'])
        if df.empty:
            raise ValueError("Dataframe is empty after dropping invalid rows.")
        df = df.set_index('ds').asfreq('D').fillna(method='ffill').reset_index()
        logger.info(f"Sample data passed to Prophet:\n{df.head()}")

        model = self._create_prophet_model()
        model.fit(df)
        forecast_periods = (self.forecast_end_date - df['ds'].max().date()).days
        future = model.make_future_dataframe(periods=forecast_periods)

        all_forecasts = []
        for run in range(NUM_TRAINING_RUNS):
            logger.info(f"Training Prophet model {run + 1}/{NUM_TRAINING_RUNS}")
            model = self._create_prophet_model()
            model.fit(df)
            forecast = model.predict(future)
            all_forecasts.append(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].set_index('ds'))

        combined = pd.concat(all_forecasts, axis=1)
        avg_forecast = pd.DataFrame({
            'ds': future['ds'],
            'yhat': combined.filter(like='yhat').mean(axis=1),
            'yhat_lower': combined.filter(like='yhat_lower').min(axis=1),
            'yhat_upper': combined.filter(like='yhat_upper').max(axis=1)
        })
        return avg_forecast

    def linear_regression_forecast(self, df):
        df = df.copy()
        if df.empty or df['ds'].isnull().any():
            raise ValueError("Dataframe is empty or contains invalid datetime values.")

        df['timestamp'] = df['ds'].astype(np.int64) // 10 ** 9
        X = df['timestamp'].values.reshape(-1, 1)
        y = df['y'].values
        model = LinearRegression().fit(X, y)

        future_dates = pd.date_range(start=df['ds'].max() + pd.Timedelta(days=1), end=self.forecast_end_date, freq='D')
        if future_dates.isnull().any():
            raise ValueError("Generated future dates contain NaT.")

        future_timestamps = ((future_dates.astype(np.int64) // 10 ** 9).values).reshape(-1, 1)
        y_pred = model.predict(future_timestamps)

        return pd.DataFrame({'ds': future_dates, 'yhat': y_pred})

    def plot_forecast(self, df, prophet_fc, linear_fc):
        plt.figure(figsize=(15, 8))
        plt.plot(df['ds'], df['y'], 'k.', label='Observed')
        plt.plot(prophet_fc['ds'], prophet_fc['yhat'], label='Prophet Forecast', alpha=0.8)
        # plt.plot(linear_fc['ds'], linear_fc['yhat'], label='Linear Regression Forecast', alpha=0.5)
        plt.fill_between(prophet_fc['ds'], prophet_fc['yhat_lower'], prophet_fc['yhat_upper'], alpha=0.2)
        plt.title(f"Forecast for {self.traffic_type} at {self.location}")
        plt.xlabel("Date")
        plt.ylabel("Count")
        plt.legend()
        plt.grid()
        plt.tight_layout()
        path = RESULTS_DIR / f"forecast_{self.traffic_type.lower().replace(' ', '_')}.png"
        plt.savefig(path)
        plt.close()
        logger.info(f"Saved forecast to {path}")

    def analyze_holiday_vs_normal(self, df):
        df = df.copy()
        df['date'] = df['ds'].dt.date
        df['is_holiday'] = df['ds'].dt.date.isin([d.date() for d in VU_HOLIDAY_DATES])

        avg_normal = df[~df['is_holiday']]['y'].mean()
        avg_holiday = df[df['is_holiday']]['y'].mean()

        plt.figure(figsize=(8, 6))
        plt.bar(['Normal Days', 'VU Holidays'], [avg_normal, avg_holiday], color=['blue', 'orange'])
        plt.title(f"{self.traffic_type} Comparison: Normal Days vs VU Holidays")
        plt.ylabel("Average Count")
        plt.tight_layout()
        path = RESULTS_DIR / f"holiday_comparison_{self.traffic_type.lower().replace(' ', '_')}.png"
        plt.savefig(path)
        plt.close()
        logger.info(f"Saved holiday comparison to {path}")

    def run(self):
        with Progress() as progress:
            task = progress.add_task("[green]Processing data...", total=3)
            df = self.fetch_data()
            progress.update(task, advance=1)
            prophet_fc = self.prophet_forecast(df)
            progress.update(task, advance=1)
            linear_fc = self.linear_regression_forecast(df)
            self.plot_forecast(df, prophet_fc, linear_fc)
            self.analyze_holiday_vs_normal(df)
            progress.update(task, advance=1)
            console.rule("[bold green]✅ Forecast Complete![/bold green]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Output", style="dim")
            table.add_column("Description")
            table.add_row("forecast_*.png", "Forecast plot with Prophet & Linear Regression")
            table.add_row("holiday_comparison_*.png", "Holiday vs Normal Day comparison")
            console.print(table)
            console.print(Panel.fit(f"[green]📁 Plots saved in:[/green] {RESULTS_DIR.resolve()}", title="Result Directory"))

if __name__ == "__main__":
    console.rule("[bold cyan]🚦 Smart Traffic Forecasting System 🚦")
    console.print("[yellow]Please select your forecast parameters below.[/yellow]\n")

    conn_str = (
        f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    engine = create_engine(conn_str)

    with engine.connect() as conn:
        LOCATIONS = [row[0] for row in conn.execute(text("SELECT DISTINCT Location FROM processed_data")).fetchall()]
        TRAFFIC_TYPES = [row[0] for row in conn.execute(text("SELECT DISTINCT Traffic_Type FROM traffic_counts")).fetchall()]

    console.print("\nAvailable Locations:")
    for idx, loc in enumerate(LOCATIONS, 1):
        console.print(f"[{idx}] {loc}")
    loc_index = IntPrompt.ask("Enter location number", choices=[str(i) for i in range(1, len(LOCATIONS)+1)])
    location = LOCATIONS[int(loc_index) - 1]
    console.print(f"You selected: [green]{location}[/green]")

    traffic_type = Prompt.ask("Select traffic type", choices=TRAFFIC_TYPES, default=TRAFFIC_TYPES[0])

    while True:
        start_date = Prompt.ask("Enter start date (YYYY-MM-DD between 2024-03-04 and 2025-03-04)", default="2024-03-04")
        end_date = Prompt.ask("Enter end date (YYYY-MM-DD between 2024-03-04 and 2025-03-04)", default="2025-03-04")
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            if start_dt < datetime(2024, 3, 4) or end_dt > datetime(2025, 3, 4):
                raise ValueError("Dates out of range.")
            if start_dt > end_dt:
                raise ValueError("Start date must be before end date.")
            break
        except ValueError as e:
            console.print(f"[red]Invalid date input: {e}[/red]")

    while True:
        start_time = Prompt.ask("Enter start time (HH:MM in 24-hour format)", default="00:00")
        end_time = Prompt.ask("Enter end time (HH:MM in 24-hour format)", default="23:59")
        try:
            datetime.strptime(start_time, "%H:%M")
            datetime.strptime(end_time, "%H:%M")
            break
        except ValueError:
            console.print("[red]Invalid time format. Use HH:MM in 24-hour format.[/red]")

    forecast_end_year = IntPrompt.ask("Enter the forecast end year (e.g., 2026 or 2029)", default=2026)
    forecast_end_month = IntPrompt.ask("Enter forecast end month (1-12)", choices=[str(m) for m in range(1, 13)], default=12)
    forecast_end_date = datetime(forecast_end_year, forecast_end_month, 1).date()
    next_month = forecast_end_month % 12 + 1
    if next_month == 1:
        forecast_end_year += 1
    forecast_end_date = datetime(forecast_end_year if next_month != 1 else forecast_end_year, next_month, 1).date() - pd.Timedelta(days=1)
    console.print(f"Forecast will run until: [cyan]{forecast_end_date}[/cyan]")

    start_datetime = f"{start_date} {start_time}:00"
    end_datetime = f"{end_date} {end_time}:00"

    model = TrafficForecaster(location, traffic_type, start_datetime, end_datetime, forecast_end_date)
    model.run()