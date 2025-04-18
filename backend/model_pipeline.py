# model_pipeline.py - Final Fix Version
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
import sys

warnings.filterwarnings("ignore", category=UserWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Constants
TRAFFIC_TYPES = ['Vehicle Count', 'Pedestrian Count', 'Cyclist Count']
FORECAST_PERIODS = 365
LOCATION = 'Footscray Library Car Park'

# Weather configuration
WEATHER_CONFIG = {
    "Summer": {"temp_range": (22, 42), "conditions": ["Sunny", "Cloudy", "Rain", "Storm"]},
    "Autumn": {"temp_range": (12, 28), "conditions": ["Sunny", "Cloudy", "Rain", "Fog"]},
    "Winter": {"temp_range": (6, 16), "conditions": ["Sunny", "Cloudy", "Rain", "Hail"]},
    "Spring": {"temp_range": (14, 28), "conditions": ["Sunny", "Cloudy", "Rain", "Windy"]}
}

# Initialize weather encoder with feature names
weather_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
all_weather = list({condition for season in WEATHER_CONFIG.values() for condition in season['conditions']})
weather_encoder.fit(pd.DataFrame({'weather': all_weather}))
weather_cols = [f"weather_{cat}" for cat in weather_encoder.categories_[0]]

def get_season(date):
    month = date.month
    if month in [12, 1, 2]: return "Summer"
    if month in [3, 4, 5]: return "Autumn"
    if month in [6, 7, 8]: return "Winter"
    return "Spring"

def robust_temperature_cleanup(df):
    """Ensure temperature column has valid values"""
    # Convert all temperatures to float
    df['Temperature'] = pd.to_numeric(df['Temperature'], errors='coerce')
    
    # First pass: Seasonal medians
    df['Season'] = df['ds'].apply(get_season)
    season_medians = df.groupby('Season')['Temperature'].transform('median')
    df['Temperature'] = df['Temperature'].fillna(season_medians)
    
    # Second pass: Overall median
    if df['Temperature'].isna().any():
        overall_median = df['Temperature'].median()
        logger.warning(f"Filling {df['Temperature'].isna().sum()} remaining NaNs with overall median: {overall_median}")
        df['Temperature'] = df['Temperature'].fillna(overall_median)
    
    # Final check
    if df['Temperature'].isna().any():
        logger.error("Critical error: Still found NaN temperatures after cleaning")
        raise ValueError("NaN temperatures remain after cleaning")
    
    return df.drop(columns=['Season'])

def fetch_traffic_data(traffic_type):
    """Retrieve and clean traffic data"""
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
        
        logger.info(f"Fetching {traffic_type} data...")
        df = pd.read_sql(query, engine)
        
        if df.empty:
            raise ValueError(f"No data found for {traffic_type}")
            
        # Convert and clean
        df['ds'] = pd.to_datetime(df['ds'])
        df = robust_temperature_cleanup(df)
        
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

def generate_future_weather(last_date):
    """Generate guaranteed-valid future weather"""
    future_dates = pd.date_range(
        start=last_date + timedelta(days=1),
        periods=FORECAST_PERIODS,
        freq='D'
    )
    
    future = pd.DataFrame({'ds': future_dates})
    future['month'] = future['ds'].dt.month
    future['season'] = future['ds'].apply(get_season)
    
    # Generate guaranteed temperatures
    def generate_temp(row):
        config = WEATHER_CONFIG[row['season']]
        return np.random.uniform(*config['temp_range'])
    
    future['Temperature'] = future.apply(generate_temp, axis=1)
    
    # Generate weather conditions
    def generate_weather(row):
        config = WEATHER_CONFIG[row['season']]
        return np.random.choice(config['conditions'])
    
    future['Weather_Condition'] = future.apply(generate_weather, axis=1)
    
    # Encode weather
    weather_encoded = weather_encoder.transform(future[['Weather_Condition']])
    future[weather_cols] = weather_encoded
    
    # Time features
    future['hour_sin'] = np.sin(2 * np.pi * 12/24)  # Assume noon
    future['hour_cos'] = np.cos(2 * np.pi * 12/24)
    
    return future[['ds', 'Temperature', 'hour_sin', 'hour_cos'] + weather_cols]

def train_safe_prophet_model(train_df, future_df):
    """Robust model training with validation"""
    try:
        # Final validation
        if train_df.isnull().any().any():
            logger.error("Training data contains NaN values:")
            logger.error(train_df.isnull().sum())
            raise ValueError("NaN values in training data")
            
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=True,
            changepoint_prior_scale=0.05
        )
        
        # Add regressors
        for col in future_df.columns:
            if col != 'ds':
                model.add_regressor(col)
        
        model.fit(train_df)
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=FORECAST_PERIODS, freq='D')
        future = future.merge(future_df, on='ds', how='left')
        
        # Generate forecast
        forecast = model.predict(future)
        return model, forecast
    
    except Exception as e:
        logger.error(f"Model training failed: {str(e)}")
        raise

def main():
    """Main execution flow"""
    for traffic_type in TRAFFIC_TYPES:
        try:
            logger.info(f"\n{'='*40}\nProcessing {traffic_type}\n{'='*40}")
            
            # 1. Fetch and clean data
            hist_data = fetch_traffic_data(traffic_type)
            
            # 2. Generate future data
            last_date = hist_data['ds'].max()
            future_data = generate_future_weather(last_date)
            
            # 3. Train model
            model, forecast = train_safe_prophet_model(
                hist_data.rename(columns={'y': 'y'}),
                future_data
            )
            
            # 4. Save results
            dump(model, f"{traffic_type.replace(' ', '_')}_model.joblib")
            logger.info(f"Successfully processed {traffic_type}")
            
        except Exception as e:
            logger.error(f"Failed to process {traffic_type}: {str(e)}")
            continue

if __name__ == '__main__':
    main()