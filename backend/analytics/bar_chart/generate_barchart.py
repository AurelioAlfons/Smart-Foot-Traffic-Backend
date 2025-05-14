import os
import plotly.express as px

def export_bar_chart_html(bar_data: dict, date=None, time=None, traffic_type=None):
    if not bar_data:
        print("⚠️ No bar chart data to export.")
        return

    # 🛡️ Make sure the output folder exists
    os.makedirs("barchart", exist_ok=True)

    # 🧠 Generate dynamic filename if all params are provided
    filename = "bar_chart.html"
    if date and time and traffic_type:
        safe_type = traffic_type.replace(" ", "")
        hour_str = time[:2]
        filename = f"bar_{date}_{hour_str}_{safe_type}.html"

    output_path = f"barchart/{filename}"

    # 📊 Generate and save bar chart
    fig = px.bar(
        x=list(bar_data.keys()),
        y=list(bar_data.values()),
        labels={'x': 'Location', 'y': 'Traffic Count'},
        title=f"📊 {traffic_type} by Location at {time} on {date}",
    )
    fig.update_layout(
        bargap=0.25,
        title_x=0.5,
        xaxis_tickangle=-30,
        plot_bgcolor='white'
    )
    fig.write_html(output_path)
    print(f"✅ Plotly bar chart saved to {output_path}")
