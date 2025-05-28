# ===========================================================
# Heatmap Renderer for Smart Foot Traffic
# -----------------------------------------------------------
# - Builds and returns a Folium map with:
#   - Colored circles by traffic count
#   - Center markers with abbreviated counts
#   - Tooltip with detailed info per location
#   - Sidebar description box with context
# - Used to generate the full heatmap HTML output
# ===========================================================

import folium
import os
import pandas as pd

from backend.visualizer.map_components.description_box import generate_description_box
from backend.visualizer.map_components.heatmap_colors import get_color_by_count
from backend.visualizer.map_components.map_shapes import add_zone_circle
from backend.visualizer.map_components.marker_helpers import add_center_marker
from backend.visualizer.map_components.sensor_locations import LOCATION_CENTERS, LOCATION_COORDINATES
from backend.visualizer.map_components.tooltip_box import generate_tooltip_html
from backend.visualizer.pt.pt_locations import add_transport_icons


def render_heatmap_map(df, selected_type, label, time_filter):
    """
    Render the folium heatmap map using the provided DataFrame.
    Returns a folium.Map object.
    """

    # Define the strict visible boundary (based on screenshot view)
    bounds = [[-37.809, 144.870], [-37.781, 144.915]] # top-left to bottom-right

    # Initialize map with locked view settings
    base_map = folium.Map(
        location=[-37.7975, 144.8876],  # Center of Footscray
        zoom_start=15.5,               # Initial zoom
        min_zoom=15,                   # Restrict zoom out
        max_zoom=20,                   # Allow zoom in
        max_bounds=True,              # Enable bounds locking
        tiles=None
    )

    # Add tile style options
    folium.TileLayer('OpenStreetMap', name='Detail').add_to(base_map)
    # folium.TileLayer('CartoDB dark_matter', name='Dark').add_to(base_map)
    folium.TileLayer('CartoDB positron', name='Light').add_to(base_map)

    # Add traffic circles and markers per location
    for loc, coords in LOCATION_COORDINATES.items():
        row_data = df[df["Location"] == loc]

        cnt = row_data.iloc[0]["Interval_Count"] if not row_data.empty else 0
        cnt = cnt if pd.notna(cnt) else 0
        dt_string = row_data.iloc[0]["DateTime_String"] if not row_data.empty else "Unknown"
        weather = row_data.iloc[0].get("Weather", "Unknown") if not row_data.empty else "Unknown"
        temperature = row_data.iloc[0].get("Temperature", "?") if not row_data.empty else "?"

        fill_color = get_color_by_count(cnt) if cnt > 0 else "#444444"

        tooltip_html = generate_tooltip_html(
            location=loc,
            traffic_type=selected_type.replace(' Count', ''),
            count=cnt,
            datetime_string=dt_string,
            season="Unknown",
            weather=weather,
            temperature=temperature
        )

        add_zone_circle(base_map, loc, fill_color, tooltip_html, LOCATION_CENTERS)
        add_center_marker(base_map, coords, cnt, fill_color)

    # Add a tile control to switch
    folium.LayerControl(position='topright', collapsed=False).add_to(base_map)

    # Inject style override for bigger layer box
    base_map.get_root().html.add_child(folium.Element("""
    <style>
    .leaflet-control-layers-expanded {
        width: 180px !important;
        font-size: 18px !important;
    }
    
    </style>
    """))

    # Set initial viewport bounds
    base_map.fit_bounds(bounds)

    # Enforce locked bounds
    base_map.options['maxBounds'] = bounds

    # Add dynamic description box
    base_map.get_root().html.add_child(
        generate_description_box(label, time_filter or "All", selected_type, df["Location"].unique())
    )

    # Add public transport logos
    add_transport_icons(base_map)  

    return base_map
