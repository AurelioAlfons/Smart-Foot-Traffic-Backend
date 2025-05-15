# ===========================================================
# Marker Utilities for Heatmap Center Labels
# -----------------------------------------------------------
# - Adds count markers to the center of each location on the map
# - Abbreviates large numbers (e.g., 47000 → 47K)
# - Automatically adjusts text color for better contrast
# ===========================================================

import folium

def abbreviate_count(count):
    if count >= 1_000_000:
        return f"{count // 100_000 / 10:.1f}M".rstrip("0").rstrip(".")  # e.g., 2.5M
    elif count >= 1_0000:
        return f"{count // 1000}K"  # e.g., 47K
    else:
        return str(count)

def add_center_marker(map_obj, coords, cnt, fill_color):
    bright_colors = {"#FFEB33", "#FFF066", "#FFF599", "#FFFACB", "#F0F9A3"}
    text_color = "#000000" if fill_color in bright_colors else "#FFFFFF"
    display_count = abbreviate_count(cnt)

    folium.Marker(
        location=coords,
        icon=folium.DivIcon(
            icon_size=(40, 20),
            icon_anchor=(20, 10),
            html=f"""
                <div style="font-size: 14px; font-weight: 800; color: {text_color}; text-align: center;">
                    {display_count}
                </div>
            """
        )
    ).add_to(map_obj)
