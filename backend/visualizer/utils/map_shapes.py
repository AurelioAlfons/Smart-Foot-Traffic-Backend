import folium

def add_zone_polygon(map_obj, location, fill_color, tooltip_html, LOCATION_ZONES):
    folium.Polygon(
        locations=[[lat, lon] for lon, lat in LOCATION_ZONES[location]],
        color=fill_color,
        fill=True,
        fill_color=fill_color,
        fill_opacity=1.0,
        tooltip=folium.Tooltip(tooltip_html, sticky=True)
    ).add_to(map_obj)
