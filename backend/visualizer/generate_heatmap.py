# =====================================================
# Rules of this script:
# 1. Shows data closest / recent to the selected time
# 2. If exact time doesnt exist, shows data from the last 30 minutes (max)
# 3. Display heatmap in Pie chart format (per location)
# 4. Save the map as an HTML file in the backend/heatmaps folder

# =====================================================
# 📦 IMPORTS & SETUP
# =====================================================
import os
import sys
import folium
from folium.plugins import HeatMap
from folium.features import CustomIcon
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn
from rich.console import Console

# Styled console output instance
console = Console()

# 🛠 Add the project root to sys.path (2 levels up from this script)
# So we can import backend modules from any subdirectory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 🔌 Load database login config
from backend.config import DB_CONFIG

# =====================================================
# 📍 SENSOR LOCATIONS (Name → Lat, Lng)
# Used to place pie chart markers on the map
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
# 🥧 GENERATE PIE CHART ICON (per location)
# Creates a PNG image showing traffic distribution
# =====================================================
def create_pie_chart_icon(counts, location_name, output_folder="icons"):
    os.makedirs(output_folder, exist_ok=True)
    labels = ['Pedestrian', 'Cyclist', 'Vehicle']
    colors = ['#3bffc1', '#ffe53b', '#8b4dff']
    total = sum(counts)
    percentages = [(c / total) * 100 if total else 0 for c in counts]
    pie_labels = [f'{p:.1f}%' if p > 0 else '' for p in percentages]

    fig, ax = plt.subplots(figsize=(1.6, 1.6), dpi=100)
    ax.pie(counts, labels=pie_labels, colors=colors, startangle=90, autopct=None,
           textprops={'fontsize': 10, 'fontweight': 'bold', 'color': 'black'})
    ax.axis('equal')
    file_path = os.path.join(output_folder, f"{location_name}.png")
    plt.savefig(file_path, transparent=True)
    plt.close()
    return file_path

# =====================================================
# 🔍 FETCH LATEST DATA (per traffic type and location)
# Returns only recent entries (max 30 min old) for selected time
# =====================================================
def fetch_latest_data_per_location(date_filter, time_filter, max_age_minutes=30):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    traffic_types = ['Pedestrian Count', 'Cyclist Count', 'Vehicle Count']
    location_type_rows = []
    selected_time = datetime.strptime(time_filter, "%H:%M:%S")

    for t_type in traffic_types:
        cursor.execute("""
            SELECT pd.Location, tc.Traffic_Type, tc.Interval_Count, pd.Time
            FROM processed_data pd
            JOIN traffic_counts tc ON pd.Data_ID = tc.Data_ID
            WHERE pd.Date = %s AND tc.Traffic_Type = %s AND pd.Time <= %s
              AND pd.Time = (
                  SELECT MAX(pd2.Time)
                  FROM processed_data pd2
                  JOIN traffic_counts tc2 ON pd2.Data_ID = tc2.Data_ID
                  WHERE pd2.Date = %s AND pd2.Location = pd.Location AND tc2.Traffic_Type = %s AND pd2.Time <= %s
              )
        """, (date_filter, t_type, time_filter, date_filter, t_type, time_filter))

        for row in cursor.fetchall():
            parsed_time = row["Time"]

            # Fix: handle both datetime.time and timedelta safely
            if isinstance(parsed_time, timedelta):
                total_minutes = parsed_time.total_seconds() // 60
            elif isinstance(parsed_time, datetime):
                total_minutes = parsed_time.hour * 60 + parsed_time.minute
            elif isinstance(parsed_time, str):
                parsed_time_obj = datetime.strptime(parsed_time, "%H:%M:%S")
                total_minutes = parsed_time_obj.hour * 60 + parsed_time_obj.minute
            else:
                total_minutes = parsed_time.hour * 60 + parsed_time.minute  # fallback for time object

            age_minutes = selected_time.hour * 60 + selected_time.minute - total_minutes
            if age_minutes <= max_age_minutes:
                location_type_rows.append(row)

    conn.close()
    return pd.DataFrame(location_type_rows)

# =====================================================
# 💾 INSERT HEATMAP GENERATION RECORD
# Saves map metadata to MySQL (used for tracking outputs)
# =====================================================
def insert_heatmap_record(date_filter, time_filter, traffic_type, heatmap_url):
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
# 📋 DESCRIPTION BOX + LEGEND (for map UI)
# Shows date, time, traffic types, legend & pie chart explanation
# =====================================================
def generate_description_box(date_filter, time_filter, traffic_types, included_locations):
    traffic_string = ', '.join(traffic_types)
    sorted_locations = sorted(included_locations, key=lambda loc: (len(loc), loc.lower()))
    locations_html = ''.join(
        f'''<li style="margin-bottom: 6px; list-style: none; display: flex; align-items: flex-start;">
                <span style="margin-right: 6px;">✅</span><span>{loc}</span>
            </li>''' for loc in sorted_locations)

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
        <div style="position: fixed; bottom: 30px; left: 30px; width: 220px; background-color: white;
             border: 2px solid #444; z-index:9999; font-size: 14px; padding: 10px;">
            <b style="color:#0275d8;">🔍 Legend</b><br>
            <hr style="margin: 8px 0; border: none; height: 2px; background-color: black;">
            <div><span style="display:inline-block; width:16px; height:16px; background-color:#3bffc1; margin-right:8px;"></span> Pedestrian</div>
            <div><span style="display:inline-block; width:16px; height:16px; background-color:#ffe53b; margin-right:8px;"></span> Cyclist</div>
            <div><span style="display:inline-block; width:16px; height:16px; background-color:#8b4dff; margin-right:8px;"></span> Vehicle</div>
            <hr style="margin: 8px 0; border: none; height: 2px; background-color: black;">
            <div style="margin-top:8px;"><b>🥧 Pie chart</b>: shows traffic type breakdown per location</div>
        </div>
    ''')

# =====================================================
# 🔥 GENERATE HEATMAP (Main Function)
# =====================================================
def generate_heatmap(date_filter, time_filter):
    console.print("\n[bold yellow]📌 Starting Heatmap Generation[/bold yellow]")

    progress = Progress(
        TextColumn("[bold cyan]📍 Heatmap Progress"),
        BarColumn(bar_width=None, complete_style="green"),
        "[progress.percentage]{task.percentage:>3.1f}%",
        TimeElapsedColumn(),
        console=console
    )

    with progress:
        task = progress.add_task("🔍 Fetching data...", total=5)

        # Step 1: Fetch latest traffic data
        df = fetch_latest_data_per_location(date_filter, time_filter)
        df["Time"] = pd.to_datetime(df["Time"], errors='coerce').dt.strftime("%H:%M:%S")
        progress.update(task, advance=1, description="🗺️ Creating base map...")

        # Step 2: Create the base map object
        base_map = folium.Map(location=[-37.7975, 144.8876], zoom_start=15.7, tiles='cartodbpositron')
        base_map.get_root().header.add_child(folium.Element('''<style>html, body { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; } #map { position: absolute; width: 100%; height: 100%; }</style>'''))

        # Step 3: Calculate location-wise counts
        progress.update(task, advance=1, description="🔥 Processing traffic data...")
        traffic_types = ["Pedestrian Count", "Cyclist Count", "Vehicle Count"]
        location_counts = {loc: [0, 0, 0] for loc in LOCATION_COORDINATES}
        heat_data = []

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

        # Step 4: Add pie chart icons as custom markers
        progress.update(task, advance=1, description="📍 Adding pie chart markers...")
        for loc, counts in location_counts.items():
            if sum(counts) == 0:
                continue
            coords = LOCATION_COORDINATES[loc]
            icon_path = create_pie_chart_icon(counts, loc.replace(" ", "_"))
            pie_icon = CustomIcon(icon_image=icon_path, icon_size=(100, 100))

            tooltip_html = folium.Tooltip(f"""
            <div style=\"font-size: 18px; font-weight: bold;\">
                📍 <b>{loc}</b><br>
                <hr style=\"margin: 8px 0; border: none; height: 2px; background-color: black;\">
                <span style=\"display:inline-block; width:14px; height:14px; background-color:#3bffc1; margin-right:6px;\"></span> Pedestrian: {counts[0]}<br><br>
                <span style=\"display:inline-block; width:14px; height:14px; background-color:#ffe53b; margin-right:6px;\"></span> Cyclist: {counts[1]}<br><br>
                <span style=\"display:inline-block; width:14px; height:14px; background-color:#8b4dff; margin-right:6px;\"></span> Vehicle: {counts[2]}
            </div>
            """, sticky=True)

            folium.Marker(location=coords, icon=pie_icon, tooltip=tooltip_html).add_to(base_map)

        # Step 5: Finalize the map — add heat layer, info box, and save
        progress.update(task, advance=1, description="💾 Saving map and logging...")
        HeatMap(heat_data, radius=25).add_to(base_map)
        info_box = generate_description_box(date_filter, time_filter, df["Traffic_Type"].unique(), df["Location"].unique())
        base_map.get_root().html.add_child(info_box)

        filename = os.path.join("heatmaps", f"heatmap_{date_filter}_{time_filter.replace(':', '-')}.html")
        os.makedirs("backend/heatmaps", exist_ok=True)
        base_map.save(filename)
        insert_heatmap_record(date_filter, time_filter, "All", filename.replace("\\", "/"))
        progress.update(task, advance=1)

    console.print("\n✅ [bold green]Heatmap generated and saved successfully.[/bold green]\n")

# ▶️ Sample test run (comment/uncomment different days for debugging)
generate_heatmap("2025-03-03", "12:55:00")
# generate_heatmap("2024-12-25", "08:30:00")
# generate_heatmap("2025-01-27", "09:10:00")
# generate_heatmap("2024-11-06", "14:15:00")
