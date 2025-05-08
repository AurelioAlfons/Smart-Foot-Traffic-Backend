# ==================================================
# 🗺️ Heatmap Renderer: Builds the folium.Map object
# ==================================================

import folium
import os
import pandas as pd

from backend.visualizer.utils.sensor_locations import LOCATION_COORDINATES, LOCATION_CENTERS
from backend.visualizer.utils.tooltip_box import generate_tooltip_html
from backend.visualizer.utils.map_shapes import add_zone_circle  # ✅ Updated
from backend.visualizer.utils.marker_helpers import add_center_marker
from backend.visualizer.utils.heatmap_colors import get_color_by_count
from backend.visualizer.utils.description_box import generate_description_box

def render_heatmap_map(df, selected_type, label, time_filter):
    """
    Render the folium heatmap map using the provided DataFrame.
    Returns a folium.Map object.
    """

    # Base map centered around Footscray
    base_map = folium.Map(location=[-37.7975, 144.8876], zoom_start=15.7, tiles='cartodbpositron')

    for loc, coords in LOCATION_COORDINATES.items():
        row_data = df[df["Location"] == loc]

        if not row_data.empty:
            cnt = row_data.iloc[0]["Interval_Count"]
            cnt = cnt if pd.notna(cnt) else 0
            dt_string = row_data.iloc[0]["DateTime_String"]
            weather = row_data.iloc[0].get("Weather", "Unknown")
            temperature = row_data.iloc[0].get("Temperature", "?")
        else:
            cnt = 0
            dt_string = "Unknown"
            weather = "Unknown"
            temperature = "?"

        fill_color = get_color_by_count(cnt) if cnt > 0 else "#444444"

        # Build tooltip
        tooltip_html = generate_tooltip_html(
            location=loc,
            traffic_type=selected_type.replace(' Count', ''),
            count=cnt,
            datetime_string=dt_string,
            season="Unknown",
            weather=weather,
            temperature=temperature
        )

        # 🔁 Swap to add_zone_circle instead of polygon
        add_zone_circle(base_map, loc, fill_color, tooltip_html, LOCATION_CENTERS)
        add_center_marker(base_map, coords, cnt, fill_color)

    # Add bottom description box
    base_map.get_root().html.add_child(
        generate_description_box(label, time_filter or "All", selected_type, df["Location"].unique())
    )

    return base_map
