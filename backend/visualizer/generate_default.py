# backend/generate_default_map.py

import pandas as pd
import os
from backend.visualizer.services.map_renderer import render_heatmap_map
from backend.visualizer.utils.sensor_locations import LOCATION_COORDINATES

def generate_default_map():
    df = pd.DataFrame({
        "Location": list(LOCATION_COORDINATES.keys()),
        "Interval_Count": [0] * len(LOCATION_COORDINATES),
        "DateTime_String": ["N/A"] * len(LOCATION_COORDINATES),
        "Weather": ["N/A"] * len(LOCATION_COORDINATES),
        "Temperature": ["N/A"] * len(LOCATION_COORDINATES)
    })

    m = render_heatmap_map(df, "Pedestrian Count", "Default Map", None)
    os.makedirs("heatmaps", exist_ok=True)
    m.save("heatmaps/default_map.html")
    print("✅ default_map.html generated.")
