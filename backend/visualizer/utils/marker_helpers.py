import folium

def add_center_marker(map_obj, coords, cnt, fill_color):
    bright_colors = {"#FFEB33", "#FFF066", "#FFF599", "#FFFACB", "#F0F9A3"}
    text_color = "#000000" if fill_color in bright_colors else "#FFFFFF"
    folium.Marker(
        location=coords,
        icon=folium.DivIcon(
            icon_size=(40, 20),
            icon_anchor=(20, 10),
            html=f"""<div style="font-size: 14px; font-weight: 800; color: {text_color}; text-align: center;">{cnt}</div>"""
        )
    ).add_to(map_obj)
