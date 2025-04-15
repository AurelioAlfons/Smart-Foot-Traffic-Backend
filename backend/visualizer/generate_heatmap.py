import os
import folium
from folium.plugins import HeatMap
from folium.features import CustomIcon
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# =====================================================
# 🔌 DATABASE CONFIGURATION
# =====================================================
from backend.config import DB_CONFIG

# =====================================================
# 📍 COORDINATES FOR ALL SENSOR LOCATIONS
# =====================================================
LOCATION_COORDINATES = {
    "Footscray Library Car Park": (-37.800791, 144.897828),
    "Footscray Market Hopkins And Irving": (-37.800195, 144.902611),
    "Footscray Market Hopkins And Leeds": (-37.800034, 144.901267),
    "Nic St Campus": (-37.804216, 144.898786),
    "Footscray Park Rowing Club": (-37.79083, 144.902119),
    "Footscray Park Gardens": (-37.793248, 144.905659),
    "Footscray Market Irving St Train Stn": (-37.80118, 144.901592),
    "Nicholson Mall Clock Tower": (-37.800925, 144.899215),
    "West Footscray Library": (-37.7975982, 144.8755734),
    "Snap Fitness": (-37.799949, 144.899409),
    "Salt Water Child Care Centre": (-37.795044, 144.900284)
}

# =====================================================
# 🥧 CREATE PIE CHART IMAGE FOR EACH LOCATION
# =====================================================
def create_pie_chart_icon(counts, location_name, output_folder="icons"):
    # Create folder if not exists
    os.makedirs(output_folder, exist_ok=True)
    
    labels = ['Pedestrian', 'Cyclist', 'Vehicle']
    colors = ['#3bffc1', '#ffe53b', '#8b4dff']  # Pedestrian, Cyclist, Vehicle
    total = sum(counts)
    percentages = [(c / total) * 100 if total else 0 for c in counts]
    pie_labels = [f'{p:.1f}%' if p > 0 else '' for p in percentages]

    # Generate pie chart with proportional slices
    fig, ax = plt.subplots(figsize=(1.6, 1.6), dpi=100)
    ax.pie(counts, labels=pie_labels, colors=colors, startangle=90, autopct=None,
           textprops={'fontsize': 10, 'fontweight': 'bold', 'color': 'black'})
    ax.axis('equal')

    # Save the pie chart as a transparent image
    file_path = os.path.join(output_folder, f"{location_name}.png")
    plt.savefig(file_path, transparent=True)
    plt.close()
    return file_path

# =====================================================
# 📊 FETCH LATEST TRAFFIC DATA FOR EACH LOCATION
# =====================================================
def fetch_latest_data_per_location(date_filter, time_filter):
    # Connect to MySQL and get the most recent time entry per location
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT Location, MAX(Time) as MaxTime
        FROM processed_data
        WHERE Date = %s AND Time <= %s
        GROUP BY Location
    """, (date_filter, time_filter))
    latest_times = cursor.fetchall()

    # If no results, return empty DataFrame
    if not latest_times:
        conn.close()
        return pd.DataFrame()

    # Construct WHERE clause to fetch only the latest entry per location
    conditions = " OR ".join([
        f"(pd.Location = '{row['Location']}' AND pd.Time = '{row['MaxTime']}')" for row in latest_times
    ])

    # Join processed data with traffic counts using Data_ID foreign key
    df = pd.read_sql(f"""
        SELECT pd.Location, tc.Traffic_Type, tc.Interval_Count, pd.Time
        FROM processed_data pd
        JOIN traffic_counts tc ON pd.Data_ID = tc.Data_ID
        WHERE pd.Date = %s AND ({conditions})
    """, conn, params=(date_filter,))
    conn.close()
    return df

# =====================================================
# 🗃️ SAVE HEATMAP GENERATION RECORD IN DATABASE
# =====================================================
def insert_heatmap_record(date_filter, time_filter, traffic_type, heatmap_url):
    # Log generated heatmap metadata into the database
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO heatmaps (Generated_At, Traffic_Type, Date_Filter, Time_Filter, Status, Heatmap_URL)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (datetime.now(), traffic_type, date_filter, time_filter, 'Generated', heatmap_url))
    conn.commit()
    cursor.close()
    conn.close()

# =====================================================
# 📝 CREATE DESCRIPTION BOX ON THE LEFT SIDE
# =====================================================
def generate_description_box(date_filter, time_filter, traffic_types, included_locations):
    traffic_string = ', '.join(traffic_types)

    # ✅ Sort by length first, then alphabetically
    sorted_locations = sorted(included_locations, key=lambda loc: (len(loc), loc.lower()))

    # ✅ Checklist layout with no bullets, aligned to the top-left
    locations_html = ''.join(
        f'''
        <li style="margin-bottom: 6px; list-style: none; display: flex; align-items: flex-start;">
            <span style="margin-right: 6px;">✅</span>
            <span>{loc}</span>
        </li>
        ''' for loc in sorted_locations)

    return folium.Element(f'''
        <div style="position: fixed; top: 90px; left: 30px; width: 280px; background-color: white;
             border:2px solid #444; z-index:9999; font-size:14px; padding: 15px;">
            <b style="color:#0275d8;">ℹ️ Heatmap Info</b><br><br>
            <b>Date:</b> {date_filter}<br>
            <b>Time:</b> {time_filter}<br>
            <b>Traffic Types:</b> {traffic_string}<br><br>
            <b>Included Locations:</b>
            <ul style="margin-top: 5px; padding-left: 0px;">{locations_html}</ul>
        </div>
    ''')


# =====================================================
# 🔥 GENERATE THE HEATMAP + PIE CHART ICONS
# =====================================================
def generate_heatmap(date_filter, time_filter):
    df = fetch_latest_data_per_location(date_filter, time_filter)

    # Each sensor location is defined with its latitude and longitude.
    # You can adjust the coordinates slightly to move marker position visually:
    #   ↑ Move Up    → Increase Latitude    (e.g. -37.8000 → -37.7990)
    #   ↓ Move Down  → Decrease Latitude    (e.g. -37.8000 → -37.8010)
    #   ← Move Left  → Decrease Longitude   (e.g. 144.9000 → 144.8990)
    #   → Move Right → Increase Longitude   (e.g. 144.9000 → 144.9010)
    # Initialize Folium base map centered around Footscray
    # =====================================================
    base_map = folium.Map(
        location=[-37.7975, 144.8876],  # Central coordinate of the map
        zoom_start=15.7,
        tiles='cartodbpositron'
    )

    # Custom CSS to prevent scrollbars and fit map
    base_map.get_root().header.add_child(folium.Element('''
        <style>
            html, body { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; }
            #map { position: absolute; width: 100%; height: 100%; }
        </style>
    '''))

    # Prepare traffic data
    traffic_types = ["Pedestrian Count", "Cyclist Count", "Vehicle Count"]
    location_counts = {loc: [0, 0, 0] for loc in LOCATION_COORDINATES}
    heat_data = []

    # Aggregate counts per location and type
    for traffic_type in traffic_types:
        subset = df[df["Traffic_Type"] == traffic_type]
        idx = traffic_types.index(traffic_type)
        for _, row in subset.iterrows():
            loc = row["Location"]
            cnt = row["Interval_Count"]
            if loc in location_counts:
                location_counts[loc][idx] += cnt
                coords = LOCATION_COORDINATES[loc]
                heat_data.append([coords[0], coords[1], cnt])

    # Add pie chart icons (one per location with traffic)
    for loc, counts in location_counts.items():
        if sum(counts) == 0:
            continue
        coords = LOCATION_COORDINATES[loc]
        icon_path = create_pie_chart_icon(counts, loc.replace(" ", "_"))
        pie_icon = CustomIcon(icon_image=icon_path, icon_size=(100, 100))

        tooltip_html = folium.Tooltip(f"""
        <div style="font-size: 20px; font-weight: bold;">
            📍 <b>{loc}</b><br>
            <hr style="margin: 8px 0; border: none; height: 2px; background-color: black;">
            <span style="display:inline-block; width:14px; height:14px; background-color:#3bffc1; margin-right:6px;"></span> Pedestrian: {counts[0]}<br>
            <span style="display:inline-block; width:14px; height:14px; background-color:#ffe53b; margin-right:6px;"></span> Cyclist: {counts[1]}<br>
            <span style="display:inline-block; width:14px; height:14px; background-color:#8b4dff; margin-right:6px;"></span> Vehicle: {counts[2]}
        </div>
    """, sticky=True)


        folium.Marker(location=coords, icon=pie_icon, tooltip=tooltip_html).add_to(base_map)

    # Add heatmap layer to visualize density across Footscray
    HeatMap(heat_data, radius=25).add_to(base_map)

    # Add heatmap legend with larger colored squares
    base_map.get_root().html.add_child(folium.Element('''
        <div style="position: fixed; bottom: 30px; left: 30px; width: 230px; background-color: white;
        border:2px solid grey; z-index:9999; font-size:14px; padding: 10px;">
        <b>Heatmap Legend</b><br>
        <hr style="margin: 8px 0; border: none; height: 2px; background-color: #000;">
        <span style="display:inline-block; width:14px; height:14px; background-color:#3bffc1; margin-right:6px;"></span> Pedestrian<br>
        <span style="display:inline-block; width:14px; height:14px; background-color:#ffe53b; margin-right:6px;"></span> Cyclist<br>
        <span style="display:inline-block; width:14px; height:14px; background-color:#8b4dff; margin-right:6px;"></span> Vehicle
        <hr style="margin: 8px 0; border: none; height: 2px; background-color: #000;">
        🥧 Pie Chart: Distribution per sensor<br>
        Gradient: Density level
        </div>
    '''))

    # Add information sidebar showing metadata
    info_box = generate_description_box(
        date_filter,
        time_filter,
        df["Traffic_Type"].unique(),
        df["Location"].unique()
    )
    base_map.get_root().html.add_child(info_box)

    # Save map as HTML file
    os.makedirs("backend/heatmaps", exist_ok=True)
    filename = os.path.join("heatmaps", f"heatmap_{date_filter}_{time_filter.replace(':', '-')}.html")
    base_map.save(filename)

    # Store the output record in the database
    insert_heatmap_record(date_filter, time_filter, "All", filename.replace("\\", "/"))

# ▶️ Test run
generate_heatmap("2025-03-03", "12:55:00")
