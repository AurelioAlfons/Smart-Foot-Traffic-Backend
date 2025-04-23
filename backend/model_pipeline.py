import os
import logging
from pathlib import Path

import pandas as pd
from prophet import Prophet
from sqlalchemy import create_engine
from joblib import dump
import matplotlib.pyplot as plt
from rich.progress import Progress
from rich.console import Console

# Import DB config from external file
from config import DB_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

# Constants
TRAFFIC_TYPES = ['Vehicle Count', 'Pedestrian Count', 'Cyclist Count']
FORECAST_PERIODS = 365  # days to forecast into the future
NUM_TRAINING_RUNS = 3
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

class TrafficForecaster:
    def __init__(self):
        # Build and test DB connection string
        conn_str = (
            f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        self.engine = create_engine(conn_str)

    def _clean_old_results(self):
        """Remove all files in the results directory"""
        for file in RESULTS_DIR.iterdir():
            try:
                file.unlink()
                logger.info(f"Deleted old result: {file.name}")
            except Exception as e:
                logger.error(f"Error deleting {file.name}: {e}")

    def fetch_traffic_data(self, traffic_type: str) -> pd.DataFrame:
        """Query traffic data for a given type and clean it"""
        query = (
            "SELECT p.Date_Time AS ds, t.Total_Count AS y "
            "FROM processed_data p "
            "JOIN traffic_counts t ON p.Data_ID = t.Data_ID "
            "WHERE p.Location = 'Footscray Library Car Park' "
            "AND t.Traffic_Type = %(traffic_type)s"
        )
        try:
            df = pd.read_sql(query, self.engine, params={'traffic_type': traffic_type})
            if df.empty:
                raise ValueError(f"No data found for {traffic_type}")

            df['ds'] = pd.to_datetime(df['ds'])
            df = df.drop_duplicates('ds').sort_values('ds')
            df['y'] = df['y'].clip(lower=0)
            return df[['ds', 'y']]
        except Exception:
            logger.exception(f"Failed to fetch data for {traffic_type}")
            raise

    def _create_prophet_model(self) -> Prophet:
        """Initialize a new Prophet model with sensible defaults"""
        return Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
            interval_width=0.95
        )

    def train_ensemble_model(self, df: pd.DataFrame) -> pd.DataFrame:
        """Train multiple Prophet models and average the forecasts"""
        all_forecasts = []
        for run in range(1, NUM_TRAINING_RUNS + 1):
            logger.info(f"Training run {run}/{NUM_TRAINING_RUNS}")
            model = self._create_prophet_model()
            model.fit(df)

            future = model.make_future_dataframe(periods=FORECAST_PERIODS, freq='D')
            forecast = model.predict(future)
            all_forecasts.append(
                forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
            )

        combined = pd.concat(all_forecasts)
        avg_forecast = (
            combined.groupby('ds')
                    .agg(
                        yhat=('yhat', 'mean'),
                        yhat_lower=('yhat_lower', 'min'),
                        yhat_upper=('yhat_upper', 'max')
                    )
                    .reset_index()
                    .sort_values('ds')
        )
        return avg_forecast

    def _calculate_trend_growth(self, forecast: pd.DataFrame) -> float:
        """Compute percentage change from first to last forecasted point"""
        start = forecast['yhat'].iloc[0]
        end = forecast['yhat'].iloc[-1]
        if start == 0:
            return 0.0
        return round((end - start) / start * 100, 2)

    def generate_insights(self, forecast: pd.DataFrame, traffic_type: str) -> dict:
        """Create summary metrics from the forecast"""
        peak_idx = forecast['yhat'].idxmax()
        peak_date = forecast.at[peak_idx, 'ds'].date().isoformat()
        return {
            'traffic_type': traffic_type,
            'last_training_date': forecast['ds'].max().date().isoformat(),
            'peak_date': peak_date,
            'avg_demand': round(forecast['yhat'].mean(), 2),
            'trend_growth': self._calculate_trend_growth(forecast)
        }

    def plot_forecast(self, df: pd.DataFrame, forecast: pd.DataFrame, traffic_type: str):
        """Plot historical vs forecasted data and save as PNG"""
        plt.figure(figsize=(14, 8))
        plt.plot(df['ds'], df['y'], 'k.', label='Observed', alpha=0.5)
        plt.plot(forecast['ds'], forecast['yhat'], label='Forecast')
        plt.fill_between(
            forecast['ds'],
            forecast['yhat_lower'],
            forecast['yhat_upper'],
            alpha=0.2
        )
        plt.title(f"{traffic_type} Forecast with 95% Interval")
        plt.xlabel('Date')
        plt.ylabel('Count')
        plt.legend()
        plt.grid(alpha=0.3)

        out_path = RESULTS_DIR / f"{traffic_type.lower().replace(' ', '_')}_forecast.png"
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        plt.close()
        logger.info(f"Plot saved to {out_path}")

    def _generate_final_report(self, insights: list):
        """Print a console summary for all traffic types"""
        console.print("\n[bold green]📊 FINAL TRAFFIC FORECAST REPORT[/bold green]")
        for ins in insights:
            console.print(f"\n[bold cyan]{ins['traffic_type']}[/bold cyan]")
            console.print(f"  📅 Last Training Date: {ins['last_training_date']}")
            console.print(f"  🔮 Peak Date: {ins['peak_date']}")
            console.print(f"  📈 Avg Demand: {ins['avg_demand']}")
            console.print(f"  📈 Trend Growth: {ins['trend_growth']}%")
            console.print(f"  📂 Results Dir: {RESULTS_DIR.resolve()}")

    def run_pipeline(self):
        """Run the full ETL, modeling, and reporting pipeline"""
        self._clean_old_results()
        all_insights = []

        with Progress() as progress:
            task = progress.add_task("[cyan]Processing traffic types...", total=len(TRAFFIC_TYPES))

            for ttype in TRAFFIC_TYPES:
                progress.console.log(f"\n[bold]Processing {ttype}[/bold]")
                try:
                    df = self.fetch_traffic_data(ttype)
                    forecast = self.train_ensemble_model(df)
                    insights = self.generate_insights(forecast, ttype)
                    self.plot_forecast(df, forecast, ttype)
                    dump(insights, RESULTS_DIR / f"{ttype.lower().replace(' ', '_')}_insights.joblib")
                    all_insights.append(insights)
                except Exception as e:
                    progress.console.log(f"[red]Error on {ttype}: {e}[/red]")
                finally:
                    progress.update(task, advance=1)

        self._generate_final_report(all_insights)
        self.engine.dispose()


if __name__ == '__main__':
    TrafficForecaster().run_pipeline()
