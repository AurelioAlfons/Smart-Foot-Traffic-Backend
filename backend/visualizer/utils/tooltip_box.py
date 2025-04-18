def generate_tooltip_html(location, traffic_type, count, datetime_string):
    # 🎨 Assign badge color based on traffic type
    type_color_map = {
        "Pedestrian": "#3bffc1",  # Cyan
        "Cyclist": "#ffe53b",     # Yellow
        "Vehicle": "#8b4dff"      # Purple
    }

    color = type_color_map.get(traffic_type, "#ccc")

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

        <!-- 📍 Location Title -->
        <div style="font-weight: bold; font-size: 16px; margin-bottom: 8px;">📍 {location}</div>

        <!-- Divider -->
        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">

        <!-- 🚦 Traffic Type -->
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span><b>🚦 Type:</b></span>
            <span style="display:flex; align-items:center;">
                <span style="display:inline-block; width:14px; height:14px; background-color:{color}; border-radius:3px; margin-right:8px;"></span>
                {traffic_type}
            </span>
        </div>

        <!-- 🔢 Count -->
        <div style="display: flex; justify-content: space-between;">
            <span><b>🔢 Count:</b></span> <span>{count}</span>
        </div>

        <!-- 🕒 Time -->
        <div style="display: flex; justify-content: space-between;">
            <span><b>🕒 Time:</b></span> <span>{datetime_string if datetime_string else 'N/A'}</span>
        </div>

        <!-- Footer -->
        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">
        <div style="font-size: 14px; color: #888; text-align: center;">
            Smart Foot Traffic System 🚶‍♂️🚴‍♀️🚗
        </div>
    </div>
    """
