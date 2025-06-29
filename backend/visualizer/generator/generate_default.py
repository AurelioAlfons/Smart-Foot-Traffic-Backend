# ====================================================
# Default Heatmap Generator for Smart Foot Traffic
# ----------------------------------------------------
# - Creates a heatmap with zero data for all locations
# - Used when no filters are applied on first load
# - Saves default map to heatmaps/default_map.html
# ====================================================

import math as m
import pandas as pd
import os
from backend.visualizer.map_components.sensor_locations import LOCATION_COORDINATES
from backend.visualizer.services.map_renderer import render_heatmap_map

def generate_default_map():
    output_path = os.path.join("heatmaps", "default_map.html")

    # Skip generation if the file already exists
    if os.path.exists(output_path):
        print("Default map already exists. Skipping generation.")
        return

    df = pd.DataFrame({
        "Location": list(LOCATION_COORDINATES.keys()),
        "Interval_Count": [0] * len(LOCATION_COORDINATES),
        "DateTime_String": ["N/A"] * len(LOCATION_COORDINATES),
        "Weather": ["N/A"] * len(LOCATION_COORDINATES),
        "Temperature": ["N/A"] * len(LOCATION_COORDINATES)
    })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    map_obj = render_heatmap_map(df, "Pedestrian Count", "Default Map", None)
    map_obj.save(output_path)
