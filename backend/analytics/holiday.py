import plotly.graph_objects as go
from pathlib import Path
import pandas as pd

# Define the official VU holiday dates
VU_HOLIDAY_DATES = pd.DatetimeIndex([
    *pd.date_range("2024-02-12", "2024-02-16"),
    *pd.date_range("2024-03-29", "2024-04-04"),
    *pd.date_range("2024-04-22", "2024-04-26"),
    *pd.date_range("2024-07-29", "2024-09-20"),
    *pd.date_range("2024-09-23", "2024-09-27"),
    *pd.date_range("2024-11-25", "2025-02-12")
])

def analyze_holiday_vs_normal_plotly(df, traffic_type, results_dir, logger):
    df = df.copy()
    df['date'] = df['ds'].dt.date
    df['is_holiday'] = df['ds'].dt.date.isin([d.date() for d in VU_HOLIDAY_DATES])

    avg_normal = df[~df['is_holiday']]['y'].mean()
    avg_holiday = df[df['is_holiday']]['y'].mean()

    # Create interactive bar chart
    fig = go.Figure(data=[
        go.Bar(name='Normal Days', x=["Normal Days"], y=[avg_normal], marker_color='blue'),
        go.Bar(name='VU Holidays', x=["VU Holidays"], y=[avg_holiday], marker_color='orange')
    ])

    fig.update_layout(
        title=f"{traffic_type} Comparison: Normal Days vs VU Holidays",
        yaxis_title="Average Count",
        xaxis_title="Day Type",
        template="plotly_white",
        height=500
    )

    output_dir = Path(results_dir)
    output_dir.mkdir(exist_ok=True)
    filename = f"holiday_comparison_{traffic_type.lower().replace(' ', '_')}.html"
    output_path = output_dir / filename
    fig.write_html(str(output_path))

    logger.info(f"Saved holiday comparison to {output_path}")
    return output_path.name
