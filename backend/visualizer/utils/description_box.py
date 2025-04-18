import folium

def generate_description_box(date_filter, time_filter, selected_type, included_locations):
    traffic_label = selected_type.replace(" Count", "")
    sorted_locations = sorted(included_locations)

    loc_list_html = ''.join(
        f'<li style="margin: 4px 0; list-style: none;"><span style="color:green;">✔</span> {loc}</li>' 
        for loc in sorted_locations)

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

        <b>Date:</b> {date_filter}<br>
        <b>Time:</b> {time_filter}<br>
        <b>Type:</b> {traffic_label}<br>

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

        <hr style="margin: 8px 0; border: none; height: 1px; background-color: #444;">
        <div><b>🥧 Pie:</b> shows traffic split per location</div>
    </div>
""")
