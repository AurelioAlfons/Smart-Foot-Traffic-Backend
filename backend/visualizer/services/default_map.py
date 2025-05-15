# backend/generate_default_map.py

import pandas as pd
import os
from backend.visualizer.services.map_renderer import render_heatmap_map

# Ensure heatmap folder exists
os.makedirs("heatmaps", exist_ok=True)

# 🔧 Create an empty DataFrame with all 11 locations
from backend.visualizer.utils.sensor_locations import LOCATION_COORDINATES

df = pd.DataFrame({
    "Location": list(LOCATION_COORDINATES.keys()),
    "Interval_Count": [0] * len(LOCATION_COORDINATES),
    "DateTime_String": ["N/A"] * len(LOCATION_COORDINATES),
    "Weather": ["N/A"] * len(LOCATION_COORDINATES),
    "Temperature": ["N/A"] * len(LOCATION_COORDINATES)
})

# 📍 Set default metadata
default_type = "Pedestrian Count"
default_label = "Default Map"
default_time = None

# 🗺️ Generate the map using your custom renderer
default_map = render_heatmap_map(df, default_type, default_label, default_time)

# 💾 Save as default_map.html
default_map.save("heatmaps/default_map.html")
print("✅ Default map generated at heatmaps/default_map.html")
