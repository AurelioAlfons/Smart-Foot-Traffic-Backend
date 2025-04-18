import folium

# 📦 Generates the floating description/info box on the top-left corner of the map
def generate_description_box(date_filter, time_filter, selected_type, included_locations):
    # 🏷️ Clean label for display (removes " Count" from type)
    traffic_label = selected_type.replace(" Count", "")
    
    # 🔤 Sort the list of locations alphabetically
    sorted_locations = sorted(included_locations)

    # 🟢 Create an HTML bullet list of locations with green checkmarks
    loc_list_html = ''.join(
        f'<li style="margin: 4px 0; list-style: none;"><span style="color:green;">✔</span> {loc}</li>' 
        for loc in sorted_locations)

    # 🧱 Return the full description box as an HTML block inside a folium.Element
    return folium.Element(f"""
    <div style="
        position: absolute;               /* 📌 Box position: fixed on the map */
        top: 80px;
        left: 10px;
        width: 240px;
        background-color: #fff;          /* 🎨 White background */
        border: 1px solid #444;          /* 🖤 Dark border */
        z-index: 9999;                   /* ⬆️ Make sure it floats above everything */
        font-size: 12px;
        padding: 12px;
        border-radius: 8px;              /* 🟦 Rounded corners */
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2); /* 💨 Soft shadow */
        line-height: 1.4;
    ">

        <!-- 🧭 Title and basic map info -->
        <b style="color:#0275d8;">ℹ️ Heatmap Info</b><br>
        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">

        <!-- 🗓️ Filters used for this heatmap -->
        <b>Date:</b> {date_filter}<br>
        <b>Time:</b> {time_filter}<br>
        <b>Type:</b> {traffic_label}<br>

        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">

        <!-- 📍 Location List -->
        <b>📍 Locations:</b>
        <ul style="padding-left: 10px; margin-top: 5px;">
            {loc_list_html}
        </ul>

        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">

        <!-- 🧾 Legend for color codes -->
        <b>🔍 Legend</b><br>
        <div style="margin-top: 5px;">
            <span style="display:inline-block;width:12px;height:12px;background:#3bffc1;margin-right:6px;"></span>Pedestrian<br>
            <span style="display:inline-block;width:12px;height:12px;background:#ffe53b;margin-right:6px;"></span>Cyclist<br>
            <span style="display:inline-block;width:12px;height:12px;background:#8b4dff;margin-right:6px;"></span>Vehicle
        </div>

        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">

        <!-- 🥧 Pie chart hint -->
        <div><b>🥧 Pie:</b> shows traffic split per location</div>
    </div>
""")
