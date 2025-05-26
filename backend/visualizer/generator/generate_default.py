# backend/generate_default_map.py

import math as m
import pandas as pd
import os
from backend.visualizer.map_components.sensor_locations import LOCATION_COORDINATES
from backend.visualizer.services.map_renderer import render_heatmap_map

def generate_default_map():
    df = pd.DataFrame({
        "Location": list(LOCATION_COORDINATES.keys()),
        "Interval_Count": [0] * len(LOCATION_COORDINATES),
        "DateTime_String": ["N/A"] * len(LOCATION_COORDINATES),
        "Weather": ["N/A"] * len(LOCATION_COORDINATES),
        "Temperature": ["N/A"] * len(LOCATION_COORDINATES)
    })

    output_path = os.path.join("heatmaps", "default_map.html")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    map_obj = render_heatmap_map(df, "Pedestrian Count", "Default Map", None)
    map_obj.save(output_path)

    print("[1] Default_map.html generated.")
