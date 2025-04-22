# model_pipeline.py - Final Corrected Version
import pandas as pd
import numpy as np
from prophet import Prophet
from sqlalchemy import create_engine, inspect
from joblib import dump
import matplotlib.pyplot as plt
import holidays
from sklearn.linear_model import LinearRegression
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

# Constants - Match exact database values
TRAFFIC_TYPES = ['Vehicle Count', 'Pedestrian Count', 'Cyclist Count']
FORECAST_PERIODS = 365
NUM_TRAINING_RUNS = 3
LOCATION = 'Footscray Library Car Park'

# Weather configuration matching database entries
WEATHER_CONFIG = {
    "Summer": {"temp_range": (22, 42), "conditions": ["Sunny", "Cloudy", "Rain", "Storm"]},
    "Autumn": {"temp_range": (12, 28), "conditions": ["Sunny", "Cloudy", "Rain", "Fog"]},
    "Winter": {"temp_range": (6, 16), "conditions": ["Sunny", "Cloudy", "Rain", "Hail"]},
    "Spring": {"temp_range": (14, 28), "conditions": ["Sunny", "Cloudy", "Rain", "Windy"]}
}

# Initialize weather encoder with correct column name
weather_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
all_weather = list({condition for season in WEATHER_CONFIG.values() for condition in season['conditions']})
weather_encoder.fit(pd.DataFrame({'Weather_Condition': all_weather}))  # Correct column name
weather_cols = [f"Weather_Condition_{cat}" for cat in weather_encoder.categories_[0]]  # Correct prefix

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

def verify_database_connection():
    """Validate database structure before operations"""
    try:
        engine = create_engine(
            f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        
        inspector = inspect(engine)
        required_tables = {'processed_data', 'traffic_counts', 'weather_season_data'}
        existing_tables = set(inspector.get_table_names())
        
        missing_tables = required_tables - existing_tables
        if missing_tables:
            raise ValueError(f"Missing tables: {', '.join(missing_tables)}")
            
        return True
    except Exception as e:
        logger.error(f"Database verification failed: {str(e)}")
        raise

def fetch_traffic_data(traffic_type):
    """Retrieve traffic data with enhanced validation"""
    try:
        engine = create_engine(
            f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        
        # Optimized query with exact field names
        query = f"""
        SELECT 
            p.Date_Time AS ds,
            t.Total_Count AS y,
            ws.Weather_Condition,
            ws.Temperature,
            HOUR(p.Date_Time) AS hour
        FROM processed_data p
        INNER JOIN traffic_counts t ON p.Data_ID = t.Data_ID
        INNER JOIN weather_season_data ws ON p.Data_ID = ws.Data_ID
        WHERE p.Location = '{LOCATION}'
        AND t.Traffic_Type = '{traffic_type}'
        AND ws.Season IS NOT NULL
        ORDER BY p.Date_Time
        """
        
        with progress:
            task = progress.add_task(f"Fetching {traffic_type} data...", total=1)
            df = pd.read_sql(query, engine)
            
            if df.empty:
                progress.console.print(f"\n[bold yellow]QUERY DEBUG[/bold yellow]\n{query}")
                raise ValueError(f"No data for {traffic_type} at {LOCATION}")
                
            progress.update(task, advance=1)
        
        # Data conversion
        df['ds'] = pd.to_datetime(df['ds'], errors='coerce', format='%Y-%m-%d %H:%M:%S')
        df = df.dropna(subset=['ds'])
        
        # Enhanced temperature handling
        df['Temperature'] = pd.to_numeric(df['Temperature'], errors='coerce')
        
        # Debugging: Log initial missing values
        initial_nulls = df['Temperature'].isnull().sum()
        logger.info(f"Initial null Temperatures: {initial_nulls}")
        
        # Handle missing data
        df['Season'] = df['ds'].apply(get_season)
        season_medians = df.groupby('Season')['Temperature'].transform('median')
        df['Temperature'] = df['Temperature'].fillna(season_medians)
        
        # Fill remaining NaNs with global median
        global_median = df['Temperature'].median()
        df['Temperature'] = df['Temperature'].fillna(global_median)
        
        # Final safeguard: Fill any remaining NaNs with 0
        df['Temperature'] = df['Temperature'].fillna(0)
        
        # Validate no NaNs remain
        if df['Temperature'].isnull().any():
            raise ValueError("NaN values persist in Temperature after all cleaning steps")
        
        # Weather encoding with correct column name
        if df['Weather_Condition'].isnull().any():
            raise ValueError("Missing weather conditions in retrieved data")
        weather_encoded = weather_encoder.transform(df[['Weather_Condition']])
        df[weather_cols] = weather_encoded
        
        # Time features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour']/24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour']/24)
        
        return df[['ds', 'y', 'Temperature', 'hour_sin', 'hour_cos'] + weather_cols]
    
    except Exception as e:
        logger.error(f"Data fetch failed: {str(e)}")
        raise

def generate_linear_trend_plot(df, traffic_type):
    """Generate linear regression visualization"""
    plt.figure(figsize=(12, 6))
    X = np.array(pd.to_numeric(df['ds'])).reshape(-1, 1)
    y = df['y']
    
    model = LinearRegression()
    model.fit(X, y)
    
    plt.scatter(df['ds'], y, color='black', alpha=0.5, label='Actual Data')
    plt.plot(df['ds'], model.predict(X), color='blue', linewidth=2, label='Linear Trend')
    plt.title(f'{traffic_type} Linear Regression Trend')
    plt.xlabel('Date')
    plt.ylabel('Traffic Count')
    plt.legend()
    
    plot_path = f"results/{traffic_type.replace(' ', '_')}_linear_trend.png"
    plt.savefig(plot_path)
    plt.close()
    return plot_path

def generate_future_regressors(last_date):
    """Generate future weather/temporal features"""
    future_dates = pd.date_range(
        start=last_date + timedelta(days=1),
        periods=FORECAST_PERIODS,
        freq='D'
    )
    
    future = pd.DataFrame({'ds': future_dates})
    future['season'] = future['ds'].apply(get_season)
    
    # Weather simulation
    np.random.seed(42)
    future['Temperature'] = future['season'].apply(
        lambda s: np.random.normal(
            loc=np.mean(WEATHER_CONFIG[s]['temp_range']),
            scale=np.diff(WEATHER_CONFIG[s]['temp_range'])[0]/6
        )
    )
    future['Weather_Condition'] = future['season'].apply(
        lambda s: np.random.choice(WEATHER_CONFIG[s]['conditions'])
    )
    
    # Encode weather with correct column name
    weather_encoded = weather_encoder.transform(future[['Weather_Condition']])
    future[weather_cols] = weather_encoded
    
    # Time features
    future['hour_sin'] = np.sin(2 * np.pi * 12/24)
    future['hour_cos'] = np.cos(2 * np.pi * 12/24)
    
    return future[['ds', 'Temperature', 'hour_sin', 'hour_cos'] + weather_cols]

def train_ensemble_model(df, future_regressors):
    """Train ensemble model with cross-validation"""
    forecasts = []
    models = []
    
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
            models.append(model)
            progress.update(task, advance=1)
    
    # Ensemble averaging
    avg_forecast = pd.concat(forecasts).groupby('ds').agg({
        'yhat': 'mean',
        'yhat_lower': 'min',
        'yhat_upper': 'max'
    }).reset_index()
    
    return models[0], avg_forecast

def generate_insights(model, forecast, traffic_type, df):
    """Generate comprehensive insights"""
    insights = {
        'traffic_type': traffic_type,
        'peak_date': forecast.loc[forecast['yhat'].idxmax(), 'ds'].strftime('%Y-%m-%d'),
        'avg_demand': round(forecast['yhat'].mean(), 2),
        'trend_growth': round((forecast['yhat'].iloc[-1] - forecast['yhat'].iloc[0]) / forecast['yhat'].iloc[0] * 100, 2),
        'components_plot': None,
        'forecast_plot': None,
        'linear_trend_plot': None
    }
    
    # Prophet components
    fig = model.plot_components(forecast)
    components_path = f"results/{traffic_type.replace(' ', '_')}_components.png"
    plt.savefig(components_path)
    plt.close()
    insights['components_plot'] = components_path
    
    # Forecast plot
    plt.figure(figsize=(12, 6))
    plt.plot(df['ds'], df['y'], 'k.', label='Historical Data')
    plt.plot(forecast['ds'], forecast['yhat'], label='Forecast', color='#0072B2')
    plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], 
                    color='#0072B2', alpha=0.2, label='Uncertainty')
    plt.title(f'{traffic_type} Forecast')
    plt.xlabel('Date')
    plt.ylabel('Traffic Count')
    plt.legend()
    forecast_path = f"results/{traffic_type.replace(' ', '_')}_forecast.png"
    plt.savefig(forecast_path)
    plt.close()
    insights['forecast_plot'] = forecast_path
    
    # Linear trend
    insights['linear_trend_plot'] = generate_linear_trend_plot(df, traffic_type)
    
    return insights

def main():
    """Main execution flow"""
    os.makedirs("results", exist_ok=True)
    all_insights = []
    
    try:
        verify_database_connection()
    except Exception as e:
        console.print(f"[bold red]Database Error: {str(e)}[/bold red]")
        return

    with progress:
        main_task = progress.add_task("Overall Progress", total=len(TRAFFIC_TYPES))
        
        for traffic_type in TRAFFIC_TYPES:
            try:
                progress.console.print(f"\n[bold cyan]Processing {traffic_type}[/bold cyan]")
                
                df = fetch_traffic_data(traffic_type)
                df = df.sort_values('ds').reset_index(drop=True)
                df = df.drop_duplicates('ds')
                df['y'] = df['y'].clip(lower=0)
                
                last_date = df['ds'].max()
                future_regressors = generate_future_regressors(last_date)
                
                model, forecast = train_ensemble_model(df, future_regressors)
                insights = generate_insights(model, forecast, traffic_type, df)
                all_insights.append(insights)
                
                dump(insights, f"results/{traffic_type.replace(' ', '_')}_insights.joblib")
                dump(model, f"results/{traffic_type.replace(' ', '_')}_model.joblib")
                
                progress.update(main_task, advance=1)
                
            except Exception as e:
                progress.console.print(f"[bold red]Error in {traffic_type}: {str(e)}[/bold red]")
                continue
    
    # Final report
    progress.console.print("\n[bold green]📊 Final Report[/bold green]")
    for insight in all_insights:
        progress.console.print(f"\n[bold]{insight['traffic_type']}:[/bold]")
        progress.console.print(f"  📅 Peak Date: {insight['peak_date']}")
        progress.console.print(f"  📈 Average Demand: {insight['avg_demand']}")
        progress.console.print(f"  📈 Trend Growth: {insight['trend_growth']}%")
        progress.console.print(f"  📊 Components: {insight['components_plot']}")
        progress.console.print(f"  📈 Forecast: {insight['forecast_plot']}")
        progress.console.print(f"  📉 Linear Trend: {insight['linear_trend_plot']}")

if __name__ == '__main__':
    main()