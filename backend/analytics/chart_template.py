# backend/utils/chart_template.py

def wrap_plotly_chart(fig_html: str, title: str) -> str:
    return f"""
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: white;
            }}
            h2 {{
                text-align: center;
                margin-top: 20px;
                font-size: 20px;
            }}
            .scroll-container {{
                height: 700px;
                overflow-y: scroll;
                border-top: 2px solid #eee;
            }}
            .plot-container,
            .js-plotly-plot .plotly,
            .plotly-graph-div {{
                border-radius: 0 !important;
                box-shadow: none !important;
                border: none !important;
                outline: none !important;
                margin: 0 !important;
                padding: 0 !important;
            }}
        </style>
    </head>
    <body>
        <h2>{title}</h2>
        <div class="scroll-container">
            {fig_html}
        </div>
    </body>
    </html>
    """
