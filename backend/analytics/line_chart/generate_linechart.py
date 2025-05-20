import os
from jinja2 import Template

def export_line_chart_html(line_chart_data: dict, date: str, time: str, traffic_type: str) -> str:
    """
    Generates a standalone HTML file with a Chart.js line chart showing
    per-hour traffic counts, and returns its relative path.
    """
    # Prepare labels & values
    labels = list(line_chart_data.keys())
    values = list(line_chart_data.values())

    # A tiny Jinja template for Chart.js
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <title>{{ traffic_type }} Hourly Trend</title>
      <style>
        body { margin: 40px; font-family: sans-serif; }
        canvas { max-width: 800px; }
      </style>
    </head>
    <body>
      <h3>{{ traffic_type }} per Hour on {{ date }}</h3>
      <canvas id="lineChart"></canvas>
      <script>
        const ctx = document.getElementById('lineChart').getContext('2d');
        new Chart(ctx, {
          type: 'line',
          data: {
            labels: {{ labels }},
            datasets: [{
              label: '{{ traffic_type }} count',
              data: {{ values }},
              fill: false,
              tension: 0.2,
              pointRadius: 4
            }]
          },
          options: {
            scales: {
              x: {
                title: { display: true, text: 'Hour of Day' }
              },
              y: {
                title: { display: true, text: 'Count' },
                beginAtZero: true
              }
            }
          }
        });
      </script>
    </body>
    </html>
    """

    rendered = Template(html_template).render(
        labels=labels,
        values=values,
        date=date,
        traffic_type=traffic_type
    )

    # Where to save it
    out_dir = os.path.join("charts", "line")
    os.makedirs(out_dir, exist_ok=True)
    # e.g. charts/line/VehicleCount_20240505_140000.html
    safe_tt = traffic_type.replace(" ", "")
    safe_date = date.replace("-", "")
    safe_time = time.replace(":", "")
    filename = f"{safe_tt}_{safe_date}_{safe_time}.html"
    path = os.path.join(out_dir, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(rendered)

    return path
