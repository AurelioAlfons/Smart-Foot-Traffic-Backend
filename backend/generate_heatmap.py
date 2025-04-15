# =====================================================
# 🗺️ Smart Foot Traffic Heatmap Generator with Pie Charts
# Description: Fetches traffic data and visualizes it on a map using Folium
# =====================================================

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
DB_CONFIG = {
    "host": "localhost",  # Database host
    "user": "root",       # Database user
    "password": "",       # Database password
    "database": "smart_foot_traffic"  # Database name
}

# =====================================================
# 📍 COORDINATES FOR ALL SENSOR LOCATIONS
# =====================================================
LOCATION_COORDINATES = {
    "Footscray Library Car Park": (-37.800565, 144.896968),
    "Footscray Market Hopkins And Irving": (-37.800196, 144.902611),
    "Footscray Market Hopkins And Leeds": (-37.800034, 144.901267),
    "Footscray Market Irving St Train Stn": (-37.801180, 144.901592),
    "Footscray Park Gardens": (-37.793248, 144.905659),
    "Footscray Park Rowing Club": (-37.790830, 144.902119),
    "Nic St Campus": (-37.804216, 144.898786),
    "Nicholson Mall Clock Tower": (-37.800911, 144.899231),
    "Salt Water Child Care Centre": (-37.795053, 144.900278),
    "Snap Fitness": (-37.799950, 144.899407),
    "West Footscray Library": (-37.804569, 144.901022)
}

# =====================================================
# 🥧 CREATE PIE CHART IMAGE FOR EACH LOCATION
# =====================================================
def create_pie_chart_icon(counts, location_name, output_folder="icons"):
    """
    Function to create a pie chart representing traffic data and save it as an image.

    Args:
        counts: A list of counts for each traffic type [Pedestrian, Cyclist, Vehicle].
        location_name: The name of the location (used as part of the image filename).
        output_folder: The folder where the images will be saved.
        
    Returns:
        file_path: The path of the saved image.
    """
    os.makedirs(output_folder, exist_ok=True)

    # Traffic type labels and colors
    labels = ['Pedestrian', 'Cyclist', 'Vehicle']
    colors = ['red', '#FFA500', '#6A5ACD']  # Red, Yellow-Orange, Purple-Blue

    # Calculate the percentages for each slice
    total = sum(counts)
    if total == 0:  # Prevent division by zero
        percentages = [0, 0, 0]
    else:
        percentages = [(c / total) * 100 for c in counts]

    # Create labels with percentages
    pie_labels = [f'{p:.1f}%' if p > 0 else '' for p in percentages]

    # Create the pie chart
    fig, ax = plt.subplots(figsize=(1.6, 1.6), dpi=100)
    ax.pie(
        counts,
        labels=pie_labels,
        colors=colors,
        startangle=90,
        autopct=None,  # Do not display percentage labels automatically
        textprops={'fontsize': 14, 'fontweight': 'bold', 'color': 'black'}
    )
    ax.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.

    # Save the image
    file_path = os.path.join(output_folder, f"{location_name}.png")
    plt.savefig(file_path, transparent=True)  # Save as transparent PNG
    plt.close()  # Close the plot to release memory
    return file_path

# =====================================================
# 📊 FETCH LATEST TRAFFIC DATA FOR EACH LOCATION
# =====================================================
def fetch_latest_data_per_location(date_filter, time_filter):
    """
    Function to fetch the most recent traffic data for each location before the selected time.

    Args:
        date_filter: The selected date for the data.
        time_filter: The selected time for the data.
        
    Returns:
        df: A pandas DataFrame containing the traffic data.
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    # Subquery to get the most recent time for each location
    subquery = """
        SELECT Location, MAX(Time) as MaxTime
        FROM processed_data
        WHERE Date = %s AND Time <= %s
        GROUP BY Location
    """
    cursor.execute(subquery, (date_filter, time_filter))
    latest_times = cursor.fetchall()

    if not latest_times:
        conn.close()
        return pd.DataFrame()

    # Build condition to fetch full data for those latest timestamps
    conditions = " OR ".join([
        f"(pd.Location = '{row['Location']}' AND pd.Time = '{row['MaxTime']}')" for row in latest_times
    ])

    main_query = f"""
        SELECT pd.Location, tc.Traffic_Type, tc.Interval_Count, pd.Time
        FROM processed_data pd
        JOIN traffic_counts tc ON pd.Data_ID = tc.Data_ID
        WHERE pd.Date = %s AND ({conditions})
    """

    df = pd.read_sql(main_query, conn, params=(date_filter,))
    conn.close()
    return df

# =====================================================
# 🗃️ SAVE HEATMAP GENERATION RECORD IN DATABASE
# =====================================================
def insert_heatmap_record(date_filter, time_filter, traffic_type, heatmap_url):
    """
    Function to insert heatmap generation details into the database.

    Args:
        date_filter: The selected date for the heatmap.
        time_filter: The selected time for the heatmap.
        traffic_type: The type of traffic for the heatmap (e.g., 'All').
        heatmap_url: The URL of the generated heatmap.
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    query = """
        INSERT INTO heatmaps (Generated_At, Traffic_Type, Date_Filter, Time_Filter, Status, Heatmap_URL)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    now = datetime.now()
    cursor.execute(query, (
        now,
        traffic_type,
        date_filter,
        time_filter,
        'Generated',
        heatmap_url
    ))
    conn.commit()
    cursor.close()
    conn.close()

# =====================================================
# 📝 CREATE DESCRIPTION BOX ON THE LEFT SIDE
# =====================================================
def generate_description_box(date_filter, time_filter, traffic_types, included_locations):
    """
    Function to generate an HTML description box showing heatmap details.

    Args:
        date_filter: The selected date.
        time_filter: The selected time.
        traffic_types: List of traffic types included in the heatmap.
        included_locations: List of locations included in the heatmap.
        
    Returns:
        description_html: The HTML content for the description box.
    """
    traffic_string = ', '.join(traffic_types)
    locations_html = ''.join(f'<li>✅ {loc}</li>' for loc in included_locations)

    return folium.Element(f'''
    <div style="position: fixed; top: 90px; left: 30px; width: 260px; background-color: white;
         border:2px solid #444; z-index:9999; font-size:14px; padding: 15px;">
        <b>ℹ️ Heatmap Info</b><br><br>
        <b>Date:</b> {date_filter}<br>
        <b>Time:</b> {time_filter}<br>
        <b>Traffic Types:</b> {traffic_string}<br><br>
        <b>Included Locations:</b>
        <ul style="margin-top: 5px; padding-left: 20px;">{locations_html}</ul>
    </div>
    ''')

# =====================================================
# 🔥 GENERATE THE HEATMAP + PIE CHART ICONS
# =====================================================
def generate_heatmap(date_filter, time_filter):
    """
    Function to generate the heatmap with pie chart icons for each location.

    Args:
        date_filter: The selected date.
        time_filter: The selected time.
    """
    df = fetch_latest_data_per_location(date_filter, time_filter)

    # Setup the map centered around Footscray
    base_map = folium.Map(location=[-37.7995, 144.8990], zoom_start=16.5, tiles='cartodbpositron')

    # Responsive style to fit map in the window
    base_map.get_root().header.add_child(folium.Element('''
    <style>
        html, body { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; }
        #map { position: absolute; width: 100%; height: 100%; }
    </style>
    '''))

    # Define traffic types
    traffic_types = ["Pedestrian Count", "Cyclist Count", "Vehicle Count"]
    location_counts = {loc: [0, 0, 0] for loc in LOCATION_COORDINATES}

    heat_data = []

    # Aggregate counts for pie chart + heatmap
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

    # Add pie chart markers for each location
    for loc, counts in location_counts.items():
        if sum(counts) == 0:
            continue

        coords = LOCATION_COORDINATES[loc]
        icon_path = create_pie_chart_icon(counts, loc.replace(" ", "_"))
        pie_icon = CustomIcon(icon_image=icon_path, icon_size=(50, 50))

        # Styled tooltip using HTML (bigger, bolder, prettier)
        tooltip_html = folium.Tooltip(f"""
        <div style="font-size: 20px; font-weight: bold;">
            📍 <b>{loc}</b><br>
            <hr style="margin: 8px 0; border: none; height: 2px; background-color: black;">
            🔴 Pedestrian: {counts[0]}<br>
            🟠 Cyclist: {counts[1]}<br>
            🟣 Vehicle: {counts[2]}
        </div>
    """, sticky=True)


        folium.Marker(location=coords, icon=pie_icon, tooltip=tooltip_html).add_to(base_map)

    # Add heatmap overlay
    HeatMap(heat_data, radius=25).add_to(base_map)

    # Add legend box
    base_map.get_root().html.add_child(folium.Element('''
    <div style="position: fixed; bottom: 30px; left: 30px; width: 230px; background-color: white;
     border:2px solid grey; z-index:9999; font-size:14px; padding: 10px;">
    <b>Heatmap Legend</b><br>
    <hr style="margin: 8px 0; border: none; height: 2px; background-color: #000;">
    🔴 Pedestrian Count<br>
    🟠 Cyclist Count <br>
    🟣 Vehicle Count <br>
    <hr style="margin: 8px 0; border: none; height: 2px; background-color: #000;">
    🥧 Pie Chart: Distribution per sensor<br>
    Gradient: Density level
    </div>
    '''))

    # Add description box on the left side
    info_box = generate_description_box(
        date_filter,
        time_filter,
        df["Traffic_Type"].unique(),
        df["Location"].unique()
    )
    base_map.get_root().html.add_child(info_box)

    # Save HTML to file
    os.makedirs("backend/heatmaps", exist_ok=True)
    filename = f"backend/heatmaps/heatmap_{date_filter}_{time_filter.replace(':', '-')}.html"
    base_map.save(filename)

    # Log heatmap generation record in database
    insert_heatmap_record(date_filter, time_filter, "All", filename.replace("\\", "/"))

# =====================================================
# ▶️ RUN GENERATION SCRIPT FOR TESTING
# =====================================================
generate_heatmap("2025-03-03", "12:55:00")
