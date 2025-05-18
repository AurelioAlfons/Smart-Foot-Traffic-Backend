# ===========================================================
# Tooltip Generator for Smart Foot Traffic Heatmaps
# -----------------------------------------------------------
# - Builds rich HTML content for map markers
# - Displays type, count, date, time, weather, and season
# - Used by the heatmap renderer to show data in tooltips
# ===========================================================

import pandas as pd

def generate_tooltip_html(location, traffic_type, count, datetime_string, 
                          season="Unknown", weather="Unknown", temperature="?"):
    # 🎨 Color for each traffic type
    type_color_map = {
        "Pedestrian": "#3bffc1",
        "Cyclist": "#ffe53b",
        "Vehicle": "#8b4dff"
    }

    color = type_color_map.get(traffic_type, "#ccc")

    # 🗓️ Season to month range
    season_ranges = {
        "Summer": "December – February",
        "Autumn": "March – May",
        "Winter": "June – August",
        "Spring": "September – November"
    }

    is_season_mode = season in season_ranges

    # ✅ Ensure datetime string format
    safe_datetime_str = str(datetime_string) if pd.notna(datetime_string) else "N/A"

    # ✅ Extract date and time
    if isinstance(safe_datetime_str, str) and " " in safe_datetime_str:
        parts = safe_datetime_str.split(" ")
        date_part = parts[0]
        time_part = parts[-1]
    else:
        date_part = safe_datetime_str
        time_part = "N/A"

    # 🍂 Auto-infer season if not provided
    if season == "Unknown" and pd.notna(date_part) and "-" in date_part:
        try:
            month = int(date_part.split("-")[1])
            if month in [12, 1, 2]:
                season = "Summer"
            elif month in [3, 4, 5]:
                season = "Autumn"
            elif month in [6, 7, 8]:
                season = "Winter"
            elif month in [9, 10, 11]:
                season = "Spring"
        except:
            season = "Unknown"

    show_time = "Unknown" if is_season_mode else time_part
    show_date = date_part
    show_season = season if season in season_ranges else "Unknown"

    return f"""
    <div style="
        font-size: 14px;
        line-height: 1.6;
        font-weight: normal;
        border: 1px solid #ccc;
        border-radius: 10px;
        padding: 14px 16px;
        background-color: #ffffff;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
        width: 350px;
    ">
        <div style="font-weight: bold; font-size: 16px; margin-bottom: 8px;">📍 {location}</div>

        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">

        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span><b>🚦 Type:</b></span>
            <span style="display:flex; align-items:center;">
                <span style="display:inline-block; width:14px; height:14px; background-color:{color}; border-radius:3px; margin-right:8px;"></span>
                {traffic_type}
            </span>
        </div>

        <div style="display: flex; justify-content: space-between;">
            <span><b>🔢 Count:</b></span> <span>{count}</span>
        </div>

        <div style="display: flex; justify-content: space-between;">
            <span><b>📅 Date:</b></span> <span>{show_date}</span>
        </div>

        <div style="display: flex; justify-content: space-between;">
            <span><b>🕒 Time:</b></span> <span>{show_time}</span>
        </div>

        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">
        <div style="display: flex; justify-content: space-between;">
            <span><b>🌿 Season:</b></span> <span>{show_season}</span>
        </div>

        <div style="display: flex; justify-content: space-between;">
            <span><b>☁️ Weather:</b></span> <span>{weather}</span>
        </div>

        <div style="display: flex; justify-content: space-between;">
            <span><b>🌡️ Temperature:</b></span> <span>{temperature}°C</span>
        </div>

        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">
        <div style="font-size: 14px; color: #888; text-align: center;">
            Smart Foot Traffic System 🚶‍♂️🚴‍♀️🚗
        </div>
    </div>
    """
