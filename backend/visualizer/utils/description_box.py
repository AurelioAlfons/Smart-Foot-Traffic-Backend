import folium

def generate_description_box(date_filter, time_filter, selected_type, included_locations):
    # 🎯 Clean up the traffic type label (e.g. "Pedestrian Count" → "Pedestrian")
    traffic_label = selected_type.replace(" Count", "")

    # ✅ Sort and create the list of locations with a green checkmark
    sorted_locations = sorted(included_locations)

    # 🧱 Build each <li> HTML item for the location list
    loc_list_html = ''.join(
        f'<li style="margin-bottom: 8px; list-style: none; display: flex; align-items: center;">'
        f'<span style="margin-right: 8px;">✅</span>{loc}</li>' for loc in sorted_locations)

    # 🧾 Return the final HTML element that gets rendered on the map
    return folium.Element(f"""
    <div style="
        position: fixed;  /* Keeps the box in the same place when scrolling */
        top: 90px;         /* Distance from the top of the screen */
        left: 30px;        /* Distance from the left of the screen */
        width: 300px;      /* Width of the info box */
        background-color: white;  /* White background */
        border: 2px solid #444;   /* Border style */
        z-index: 9999;     /* Makes sure it's above other map layers */
        font-size: 14px;
        padding: 20px;     /* Padding inside the box */
        border-radius: 8px; /* Rounded corners */
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); /* Soft drop shadow */
    ">

        <!-- 🔹 Title -->
        <b style="color:#0275d8;">ℹ️ Heatmap Info</b><br>
        <hr style="margin: 12px 0; border: none; height: 2px; background-color: black;">
                          
        <!-- 📅 Date and Time Info -->
        <b>Date:</b> {date_filter}<br>
        <b>Time:</b> {time_filter}<br>
        <b>Traffic Type:</b> {traffic_label}<br>

        <!-- Divider before locations -->
        <hr style="margin: 12px 0; border: none; height: 2px; background-color: black;">

        <!-- 📍 Locations -->
        <b>Included Locations:</b>
        <ul style="padding-left: 0; margin-top: 10px;">
            {loc_list_html}
        </ul>

        <!-- Divider before legend -->
        <hr style="margin: 14px 0 10px 0; border: none; height: 2px; background-color: black;">

        <!-- 🧭 Legend -->
        <b style="color:#0275d8;">🔍 Legend</b><br><br>
        <div><span style="display:inline-block; width:16px; height:16px; background-color:#3bffc1; margin-right:8px;"></span> Pedestrian</div>
        <div><span style="display:inline-block; width:16px; height:16px; background-color:#ffe53b; margin-right:8px;"></span> Cyclist</div>
        <div><span style="display:inline-block; width:16px; height:16px; background-color:#8b4dff; margin-right:8px;"></span> Vehicle</div>

        <!-- Divider before pie chart info -->
        <hr style="margin: 14px 0 10px 0; border: none; height: 2px; background-color: black;">

        <!-- 🥧 Pie chart note -->
        <div><b>🥧 Pie chart</b>: shows traffic type breakdown per location</div>
    </div>
""")
