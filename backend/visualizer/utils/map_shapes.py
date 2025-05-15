# ===========================================================
# Circle Overlay Utility for Heatmap Zones
# -----------------------------------------------------------
# - Draws a colored circular zone for each sensor location
# - Uses coordinates from LOCATION_CENTERS
# - Attaches a custom HTML tooltip to each circle
# ===========================================================

import folium

def add_zone_circle(map_obj, location, fill_color, tooltip_html, LOCATION_CENTERS):
    # LOCATION_CENTERS[location] should be a tuple: (lat, lon)
    center_lat, center_lon = LOCATION_CENTERS[location]

    folium.Circle(
        location=[center_lat, center_lon],
        radius=70,  # Radius in meters (adjust as needed)
        color=fill_color,
        fill=True,
        fill_color=fill_color,
        fill_opacity=0.7,
        tooltip=folium.Tooltip(tooltip_html, sticky=True)
    ).add_to(map_obj)
