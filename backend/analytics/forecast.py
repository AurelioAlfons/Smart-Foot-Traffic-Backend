import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go

def plot_forecast_interactive(df, prophet_fc, linear_fc, traffic_type, location):
    results_dir = Path("results_plotly")
    results_dir.mkdir(exist_ok=True)

    fig = go.Figure()

    # Observed data
    fig.add_trace(go.Scatter(
        x=df["ds"], y=df["y"],
        mode='markers', name='Observed',
        marker=dict(color='black')
    ))

    # Prophet forecast
    fig.add_trace(go.Scatter(
        x=prophet_fc["ds"], y=prophet_fc["yhat"],
        mode='lines', name='Prophet Forecast',
        line=dict(color='blue')
    ))

    # Prophet uncertainty band
    fig.add_trace(go.Scatter(
        x=pd.concat([prophet_fc["ds"], prophet_fc["ds"][::-1]]),
        y=pd.concat([prophet_fc["yhat_upper"], prophet_fc["yhat_lower"][::-1]]),
        fill='toself',
        fillcolor='rgba(0, 0, 255, 0.1)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        name='Prophet Uncertainty'
    ))

    # Linear regression forecast
    fig.add_trace(go.Scatter(
        x=linear_fc["ds"], y=linear_fc["yhat"],
        mode='lines', name='Linear Regression Forecast',
        line=dict(color='orange')
    ))

    # Layout settings
    fig.update_layout(
        title=f"Forecast for {traffic_type} at {location}",
        xaxis_title="Date",
        yaxis_title="Count",
        template="plotly_white",
        height=600,
        margin=dict(t=50, b=40)
    )

    # Save interactive chart
    filename = f"forecast_{traffic_type.lower().replace(' ', '_')}.html"
    output_path = results_dir / filename
    fig.write_html(str(output_path))

    return output_path.name

# ================================
# ✅ EXAMPLE USAGE
# (Simulated data for demo/testing)
# ================================

# Generate example data
dates = pd.date_range(start="2024-03-04", periods=30, freq='D')
observed = np.random.randint(100, 300, size=30)
prophet_pred = observed + np.random.normal(0, 10, size=30)
linear_pred = observed + np.random.normal(0, 15, size=30)
lower_bound = prophet_pred - 20
upper_bound = prophet_pred + 20

# Format as DataFrames
df = pd.DataFrame({
    "ds": dates,
    "y": observed
})
prophet_fc = pd.DataFrame({
    "ds": dates,
    "yhat": prophet_pred,
    "yhat_lower": lower_bound,
    "yhat_upper": upper_bound
})
linear_fc = pd.DataFrame({
    "ds": dates,
    "yhat": linear_pred
})

# Call the function
plot_forecast_interactive(df, prophet_fc, linear_fc, "Pedestrian Count", "Footscray Library")
