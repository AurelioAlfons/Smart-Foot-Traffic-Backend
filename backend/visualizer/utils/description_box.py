import folium
from datetime import datetime
from backend.visualizer.utils.sensor_locations import LOCATION_COORDINATES


def generate_description_box(date_filter, time_filter, selected_type, included_locations):
    traffic_label = selected_type.replace(" Count", "")
    all_locations = sorted(LOCATION_COORDINATES.keys())

    season_ranges = {
        "Summer": "December – February",
        "Autumn": "March – May",
        "Winter": "June – August",
        "Spring": "September – November"
    }

    # 🕒 Convert time_filter (e.g. "00:00:00") to Duration format (e.g. "00:00 - 01:00")
    def convert_time_to_duration(time_str):
        try:
            dt = datetime.strptime(time_str, "%H:%M:%S")
            start = dt.strftime("%H:%M")
            end_dt = dt.replace(hour=(dt.hour + 1) % 24)
            end = end_dt.strftime("%H:%M")
            return f"{start} - {end}"
        except:
            return time_str  # fallback

    duration_str = convert_time_to_duration(time_filter)

    # 📅 Auto-assign season if date_filter is a date string
    def get_season_from_date(date_str):
        try:
            month = int(datetime.strptime(date_str, "%Y-%m-%d").month)
            if month in [12, 1, 2]:
                return "Summer"
            elif month in [3, 4, 5]:
                return "Autumn"
            elif month in [6, 7, 8]:
                return "Winter"
            elif month in [9, 10, 11]:
                return "Spring"
        except:
            return None

    current_season = date_filter if date_filter in season_ranges else get_season_from_date(date_filter)
    season_range = season_ranges.get(current_season, "")

    # ⛳ Build HTML for each location
    loc_list_html = ''
    for loc in all_locations:
        if loc in included_locations:
            loc_list_html += f'<li style="margin: 4px 0; list-style: none;"><span style="color:green;">✔</span> {loc}</li>'
        else:
            loc_list_html += f'<li style="margin: 4px 0; list-style: none;"><span style="color:red;">❌</span> {loc}</li>'

    return folium.Element(f"""
    <div style="
        position: absolute;
        top: 80px;
        left: 10px;
        width: 240px;
        background-color: #fff;
        border: 1px solid #444;
        z-index: 9999;
        font-size: 12px;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
        line-height: 1.4;
    ">
        <b style="color:#0275d8;">ℹ️ Heatmap Info</b><br>
        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">
        <b>🌦️ Season:</b> {current_season or "N/A"}<br>
        <b>🗓️ Date:</b> {date_filter}<br>
        <b>🕒 Time:</b> {duration_str}<br>
        <b>📊 Type:</b> {traffic_label}<br>
        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">
        <b>📍 Locations:</b>
        <ul style="padding-left: 10px; margin-top: 5px;">
            {loc_list_html}
        </ul>
        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">
        <b>🔍 Legend</b><br>
        <div style="margin-top: 5px;">
            <span style="display:inline-block;width:12px;height:12px;background:#3bffc1;margin-right:6px;"></span>Pedestrian<br>
            <span style="display:inline-block;width:12px;height:12px;background:#ffe53b;margin-right:6px;"></span>Cyclist<br>
            <span style="display:inline-block;width:12px;height:12px;background:#8b4dff;margin-right:6px;"></span>Vehicle
        </div>
    </div>
    """)
