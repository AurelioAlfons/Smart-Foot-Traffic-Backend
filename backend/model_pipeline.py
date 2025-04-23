import pandas as pd
import numpy as np
from prophet import Prophet
from sqlalchemy import create_engine
from joblib import dump
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
from config import DB_CONFIG
import glob
import os
from rich.progress import Progress
from rich.console import Console
from datetime import datetime, timedelta
import holidays

# Configure style
plt.style.use('seaborn')
sns.set_palette("husl")
console = Console()

# Constants
TRAFFIC_TYPES = ['Vehicle Count', 'Pedestrian Count', 'Cyclist Count']
FORECAST_PERIODS = 365
MODEL_COLORS = {
    'prophet': '#1f77b4',
    'linear': '#ff7f0e'
}

def clean_old_results():
    """Remove previous result files"""
    for f in glob.glob('results/*.png') + glob.glob('results/*.joblib'):
        try:
            os.remove(f)
        except Exception as e:
            console.print(f"[red]Error deleting {f}: {str(e)}[/red]")

def fetch_traffic_data(traffic_type):
    """Enhanced data fetching with validation"""
    engine = create_engine(
        f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    
    query = f"""
    SELECT 
        p.Date_Time AS ds,
        t.Total_Count AS y,
        ws.Temperature,
        ws.Weather_Condition
    FROM processed_data p
    JOIN traffic_counts t ON p.Data_ID = t.Data_ID
    JOIN weather_season_data ws ON p.Data_ID = ws.Data_ID
    WHERE p.Location = 'Footscray Library Car Park'
    AND t.Traffic_Type = '{traffic_type}'
    """
    
    df = pd.read_sql(query, engine)
    
    # Data validation
    df['ds'] = pd.to_datetime(df['ds'])
    df = df.sort_values('ds').drop_duplicates('ds')
    df['y'] = df['y'].clip(lower=0)
    
    if df.empty:
        raise ValueError(f"No data found for {traffic_type}")
    
    return df

def train_prophet_model(df):
    """Enhanced Prophet model with holidays"""
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=True,
        changepoint_prior_scale=0.05,
        holidays=holidays.Australia(),
        uncertainty_samples=1000
    )
    
    # Add weather regressors
    for col in ['Temperature']:
        model.add_regressor(col)
    
    model.fit(df)
    future = model.make_future_dataframe(periods=FORECAST_PERIODS)
    future = future.merge(df[['ds', 'Temperature']], on='ds', how='left')
    forecast = model.predict(future)
    return model, forecast

def train_linear_regression(df):
    """Enhanced linear regression model with time features"""
    # Create time features
    df['days'] = (df['ds'] - df['ds'].min()).dt.days
    X = df[['days', 'Temperature']].values
    y = df['y'].values
    
    # Train model
    lr = LinearRegression()
    lr.fit(X, y)
    
    # Create future dates
    last_date = df['ds'].max()
    future_dates = [last_date + timedelta(days=x) for x in range(1, FORECAST_PERIODS+1)]
    future_df = pd.DataFrame({'ds': future_dates})
    future_df['days'] = (future_df['ds'] - df['ds'].min()).dt.days
    future_df['Temperature'] = df['Temperature'].mean()  # Use average temp
    
    # Predict
    future_y = lr.predict(future_df[['days', 'Temperature']])
    future_df['yhat'] = future_y
    
    return lr, future_df

def generate_insights(df, prophet_forecast, lr_forecast, traffic_type):
    """Generate comprehensive insights with visualizations"""
    # Merge data
    combined = pd.concat([
        df[['ds', 'y']].assign(model='actual'),
        prophet_forecast[['ds', 'yhat']].assign(model='prophet'),
        lr_forecast[['ds', 'yhat']].assign(model='linear')
    ])
    
    # Create figure
    plt.figure(figsize=(16, 9))
    
    # Plot historical data
    plt.subplot(2, 1, 1)
    sns.lineplot(data=combined[combined['model'] == 'actual'],
                 x='ds', y='y', label='Actual Data')
    
    # Plot forecasts
    sns.lineplot(data=combined[combined['model'] == 'prophet'],
                 x='ds', y='yhat', color=MODEL_COLORS['prophet'], label='Prophet Forecast')
    sns.lineplot(data=combined[combined['model'] == 'linear'],
                 x='ds', y='yhat', color=MODEL_COLORS['linear'], label='Linear Forecast')
    
    plt.title(f'{traffic_type} Traffic Forecast Comparison', fontsize=14)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Traffic Count', fontsize=12)
    plt.legend()
    
    # Add metrics table
    prophet_mae = mean_absolute_error(df['y'], prophet_forecast[:len(df)]['yhat'])
    lr_mae = mean_absolute_error(df['y'], lr_forecast[:len(df)]['yhat'])
    
    metrics_text = (
        f"Prophet MAE: {prophet_mae:.1f}\n"
        f"Linear MAE: {lr_mae:.1f}\n"
        f"Prophet R²: {r2_score(df['y'], prophet_forecast[:len(df)]['yhat']):.2f}\n"
        f"Linear R²: {r2_score(df['y'], lr_forecast[:len(df)]['yhat']):.2f}"
    )
    
    plt.subplot(2, 1, 2)
    plt.axis('off')
    plt.text(0.1, 0.5, metrics_text, fontsize=12, family='monospace')
    
    plt.tight_layout()
    plot_path = f'results/{traffic_type.replace(" ", "_")}_comparison.png'
    plt.savefig(plot_path, bbox_inches='tight')
    plt.close()
    
    return {
        'traffic_type': traffic_type,
        'plot_path': plot_path,
        'prophet_mae': prophet_mae,
        'linear_mae': lr_mae,
        'last_actual_date': df['ds'].max().strftime('%Y-%m-%d'),
        'prophet_peak': prophet_forecast['yhat'].max(),
        'linear_peak': lr_forecast['yhat'].max(),
    }

def main():
    """Main execution flow"""
    clean_old_results()
    os.makedirs('results', exist_ok=True)
    all_insights = []
    
    with Progress() as progress:
        task = progress.add_task("Processing...", total=len(TRAFFIC_TYPES))
        
        for traffic_type in TRAFFIC_TYPES:
            progress.console.print(f"\n[bold cyan]Processing {traffic_type}[/bold cyan]")
            
            try:
                # Data preparation
                df = fetch_traffic_data(traffic_type)
                
                # Prophet model
                prophet_model, prophet_forecast = train_prophet_model(df)
                
                # Linear regression
                lr_model, lr_forecast = train_linear_regression(df)
                
                # Generate insights
                insights = generate_insights(df, prophet_forecast, lr_forecast, traffic_type)
                all_insights.append(insights)
                
                # Save models
                dump(prophet_model, f'results/{traffic_type.replace(" ", "_")}_prophet.joblib')
                dump(lr_model, f'results/{traffic_type.replace(" ", "_")}_linear.joblib')
                
                progress.update(task, advance=1)
                
            except Exception as e:
                progress.console.print(f"[bold red]Error in {traffic_type}: {str(e)}[/bold red]")
                continue
    
    # Generate final report
    console.print("\n[bold green]📊 Final Traffic Insights Report[/bold green]")
    for insight in all_insights:
        console.print(f"\n[bold]{insight['traffic_type']}:[/bold]")
        console.print(f"  📈 Last Actual Date: {insight['last_actual_date']}")
        console.print(f"  🔮 Prophet Forecast Peak: {insight['prophet_peak']:.0f}")
        console.print(f"  📉 Linear Forecast Peak: {insight['linear_peak']:.0f}")
        console.print(f"  📊 Model Comparison Plot: {insight['plot_path']}")
        console.print(f"  ⚖️  Prophet MAE: {insight['prophet_mae']:.1f}")
        console.print(f"  ⚖️  Linear MAE: {insight['linear_mae']:.1f}")

if __name__ == '__main__':
    main()