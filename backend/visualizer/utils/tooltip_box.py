def generate_tooltip_html(location, traffic_type, count, datetime_string):
    # 🎨 Choose a color for the traffic type badge
    type_color_map = {
        "Pedestrian": "#3bffc1",  # Cyan
        "Cyclist": "#ffe53b",     # Yellow
        "Vehicle": "#8b4dff"      # Purple
    }

    # 🟪 Default to grey if type is unknown
    color = type_color_map.get(traffic_type, "#ccc")

    # 🧱 Build the full HTML structure of the tooltip
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

        <!-- 🏷️ Location title (bold and big) -->
        <div style="font-weight: bold; font-size: 16px; margin-bottom: 8px;">📍 {location}</div>

        <!-- Line break separator -->
        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">

        <!-- 🚦 Show traffic type with a colored box -->
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span><b>🚦 Type:</b></span>
            <span style="display:flex; align-items:center;">
                <span style="display:inline-block; width:14px; height:14px; background-color:{color}; border-radius:3px; margin-right:8px;"></span>
                {traffic_type}
            </span>
        </div>

        <!-- 🔢 Show the traffic count -->
        <div style="display: flex; justify-content: space-between;">
            <span><b>🔢 Count:</b></span> <span>{count}</span>
        </div>

        <!-- 🕒 Show the time and any extra note -->
        <div style="display: flex; justify-content: space-between;">
            <span><b>🕒 Time:</b></span> <span>{datetime_string.replace(" ", " | ") if datetime_string else 'N/A'}</span>
        </div>

        <!-- Footer with grey note -->
        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">
        <div style="font-size: 14px; color: #888; text-align: center;">
            Smart Foot Traffic System 🚶‍♂️🚴‍♀️🚗
        </div>
    </div>
    """
