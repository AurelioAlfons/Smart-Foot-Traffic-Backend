# model_pipeline.py - Enhanced Version with Weather/Season Integration
import pandas as pd
import numpy as np
from prophet import Prophet
from sqlalchemy import create_engine
from joblib import dump
import matplotlib.pyplot as plt
import holidays
from sklearn.preprocessing import OneHotEncoder
from datetime import datetime, timedelta
import logging
from config import DB_CONFIG
import warnings
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn
from rich.console import Console
import sys
import os

# Suppress warnings and configure logging
warnings.filterwarnings("ignore", category=UserWarning)
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Constants
TRAFFIC_TYPES = ['Vehicle Count', 'Pedestrian Count', 'Cyclist Count']
FORECAST_PERIODS = 365
NUM_TRAINING_RUNS = 3
LOCATION = 'Footscray Library Car Park'

# Weather configuration
WEATHER_CONFIG = {
    "Summer": {"temp_range": (22, 42), "conditions": ["Sunny", "Cloudy", "Rain", "Storm"]},
    "Autumn": {"temp_range": (12, 28), "conditions": ["Sunny", "Cloudy", "Rain", "Fog"]},
    "Winter": {"temp_range": (6, 16), "conditions": ["Sunny", "Cloudy", "Rain", "Hail"]},
    "Spring": {"temp_range": (14, 28), "conditions": ["Sunny", "Cloudy", "Rain", "Windy"]}
}

# Initialize weather encoder
weather_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
all_weather = list({condition for season in WEATHER_CONFIG.values() for condition in season['conditions']})
weather_encoder.fit(pd.DataFrame({'weather': all_weather}))
weather_cols = [f"weather_{cat}" for cat in weather_encoder.categories_[0]]

# Rich progress setup
console = Console()
progress = Progress(
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    TimeElapsedColumn(),
    console=console
)

def get_season(date):
    """Determine season from date object"""
    month = date.month
    if month in [12, 1, 2]: return "Summer"
    if month in [3, 4, 5]: return "Autumn"
    if month in [6, 7, 8]: return "Winter"
    return "Spring"

def fetch_traffic_data(traffic_type):
    """Retrieve traffic data with weather/season features"""
    try:
        engine = create_engine(
            f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        
        query = f"""
        SELECT 
            p.Date_Time AS ds,
            t.Total_Count AS y,
            ws.Weather_Condition,
            ws.Temperature,
            HOUR(p.Date_Time) AS hour
        FROM processed_data p
        JOIN traffic_counts t ON p.Data_ID = t.Data_ID
        JOIN weather_season_data ws ON p.Data_ID = ws.Data_ID
        WHERE p.Location = '{LOCATION}'
        AND t.Traffic_Type = '{traffic_type}'
        ORDER BY p.Date_Time
        """
        
        with progress:
            task = progress.add_task(f"Fetching {traffic_type} data...", total=1)
            df = pd.read_sql(query, engine)
            progress.update(task, advance=1)
        
        # Convert and clean data
        df['ds'] = pd.to_datetime(df['ds'])
        df['Temperature'] = pd.to_numeric(df['Temperature'], errors='coerce')
        
        # Handle missing temperatures
        df['Season'] = df['ds'].apply(get_season)
        season_medians = df.groupby('Season')['Temperature'].transform('median')
        df['Temperature'] = df['Temperature'].fillna(season_medians)
        df['Temperature'] = df['Temperature'].fillna(df['Temperature'].median())
        
        # Encode weather
        weather_encoded = weather_encoder.transform(df[['Weather_Condition']])
        df[weather_cols] = weather_encoded
        
        # Time features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour']/24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour']/24)
        
        return df[['ds', 'y', 'Temperature', 'hour_sin', 'hour_cos'] + weather_cols]
    
    except Exception as e:
        logger.error(f"Data fetch failed: {str(e)}")
        raise

def generate_future_regressors(last_date):
    """Generate future weather/temporal features"""
    future_dates = pd.date_range(
        start=last_date + timedelta(days=1),
        periods=FORECAST_PERIODS,
        freq='D'
    )
    
    future = pd.DataFrame({'ds': future_dates})
    future['month'] = future['ds'].dt.month
    future['season'] = future['ds'].apply(get_season)
    
    # Generate weather and temperature
    future['Temperature'] = future['season'].apply(
        lambda s: np.random.uniform(*WEATHER_CONFIG[s]['temp_range'])
    )
    future['Weather_Condition'] = future['season'].apply(
        lambda s: np.random.choice(WEATHER_CONFIG[s]['conditions'])
    )
    
    # Encode weather
    weather_encoded = weather_encoder.transform(future[['Weather_Condition']])
    future[weather_cols] = weather_encoded
    
    # Time features
    future['hour_sin'] = np.sin(2 * np.pi * 12/24)
    future['hour_cos'] = np.cos(2 * np.pi * 12/24)
    
    return future[['ds', 'Temperature', 'hour_sin', 'hour_cos'] + weather_cols]

def train_ensemble_model(df, future_regressors):
    """Train ensemble model with progress tracking"""
    forecasts = []
    
    with progress:
        task = progress.add_task("Training model...", total=NUM_TRAINING_RUNS)
        
        for _ in range(NUM_TRAINING_RUNS):
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=True,
                changepoint_prior_scale=0.05
            )
            
            # Add regressors
            for col in future_regressors.columns:
                if col != 'ds':
                    model.add_regressor(col)
            
            model.fit(df)
            future = model.make_future_dataframe(periods=FORECAST_PERIODS)
            future = future.merge(future_regressors, on='ds', how='left')
            forecast = model.predict(future)
            forecasts.append(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']])
            progress.update(task, advance=1)
    
    # Ensemble averaging
    avg_forecast = pd.concat(forecasts).groupby('ds').mean().reset_index()
    return model, avg_forecast

def generate_insights(model, forecast, traffic_type):
    """Generate comprehensive insights"""
    insights = {
        'traffic_type': traffic_type,
        'peak_date': forecast.loc[forecast['yhat'].idxmax(), 'ds'].strftime('%Y-%m-%d'),
        'avg_demand': round(forecast['yhat'].mean(), 2),
        'trend_growth': round((forecast['yhat'].iloc[-1] - forecast['yhat'].iloc[0]) / forecast['yhat'].iloc[0] * 100, 2),
        'components_plot': None,
        'forecast_plot': None
    }
    
    # Component analysis
    fig = model.plot_components(forecast)
    components_path = f"results/{traffic_type.replace(' ', '_')}_components.png"
    plt.savefig(components_path)
    plt.close()
    insights['components_plot'] = components_path
    
    # Forecast plot
    plt.figure(figsize=(12, 6))
    plt.plot(forecast['ds'], forecast['yhat'], label='Forecast')
    plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], alpha=0.3)
    plt.title(f'{traffic_type} Forecast with Uncertainty')
    plt.xlabel('Date')
    plt.ylabel('Traffic Count')
    plt.legend()
    forecast_path = f"results/{traffic_type.replace(' ', '_')}_forecast.png"
    plt.savefig(forecast_path)
    plt.close()
    insights['forecast_plot'] = forecast_path
    
    return insights

def main():
    """Main execution flow"""
    os.makedirs("results", exist_ok=True)
    all_insights = []
    
    with progress:
        main_task = progress.add_task("Overall Progress", total=len(TRAFFIC_TYPES))
        
        for traffic_type in TRAFFIC_TYPES:
            try:
                progress.console.print(f"\n[bold cyan]Processing {traffic_type}[/bold cyan]")
                
                # Fetch data
                df = fetch_traffic_data(traffic_type)
                
                # Generate future regressors
                future_regressors = generate_future_regressors(df['ds'].max())
                
                # Train model
                model, forecast = train_ensemble_model(df, future_regressors)
                
                # Generate insights
                insights = generate_insights(model, forecast, traffic_type)
                all_insights.append(insights)
                
                # Save outputs
                dump(insights, f"results/{traffic_type.replace(' ', '_')}_insights.joblib")
                dump(model, f"results/{traffic_type.replace(' ', '_')}_model.joblib")
                
                progress.update(main_task, advance=1)
                
            except Exception as e:
                progress.console.print(f"[bold red]Error in {traffic_type}: {str(e)}[/bold red]")
                continue
    
    # Print summary
    progress.console.print("\n[bold green]📊 Final Report[/bold green]")
    for insight in all_insights:
        progress.console.print(f"\n[bold]{insight['traffic_type']}:[/bold]")
        progress.console.print(f"  📅 Peak Date: {insight['peak_date']}")
        progress.console.print(f"  📈 Avg Daily Demand: {insight['avg_demand']}")
        progress.console.print(f"  📈 Trend Growth: {insight['trend_growth']}%")
        progress.console.print(f"  📊 Components Plot: {insight['components_plot']}")
        progress.console.print(f"  📈 Forecast Plot: {insight['forecast_plot']}")

if __name__ == '__main__':
    main()