# 📄 backend/visualizer/utils/transport_icons.py

import folium
import json
from folium.features import CustomIcon

# 🔧 Config
ICON_FOLDER = "backend/visualizer/icon"
ICON_SIZE = (28, 28)
STOPS_FILE = "backend/visualizer/data/nearby_pt_stops.json"

# 🗺️ Icon mapping by transport type
ICON_MAP = {
    "Bus Stop": "logo_bus.png",
    "Tram Stop": "logo_tram.png",
    "Train Station": "logo_metro.png",  
}

def _add_stops(folium_map, stops_by_type):
    for stop_type, icon_file in ICON_MAP.items():
        for stop in stops_by_type.get(stop_type, []):
            icon_path = f"{ICON_FOLDER}/{icon_file}"
            icon = CustomIcon(icon_image=icon_path, icon_size=ICON_SIZE, icon_anchor=(14, 14))
            folium.Marker(
                location=[stop["lat"], stop["lon"]],
                tooltip=f"{stop['name']} ({stop_type})",
                icon=icon
            ).add_to(folium_map)

def add_transport_icons(folium_map: folium.Map):
    # 🧾 Load PT stops from file
    try:
        with open(STOPS_FILE, "r") as f:
            all_stops = json.load(f)
    except FileNotFoundError:
        print("⚠️ PT stops file not found.")
        return

    # 📦 Organize by type
    stops_by_type = {}
    for stop in all_stops:
        stop_type = stop.get("type")
        if stop_type in ICON_MAP:
            stops_by_type.setdefault(stop_type, []).append(stop)

    _add_stops(folium_map, stops_by_type)
