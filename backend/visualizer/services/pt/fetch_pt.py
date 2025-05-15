# 📄 scripts/fetch_pt_stops.py
import requests
import json
import os

# 🚀 Increased search radius (in meters)
SEARCH_RADIUS = 3000  # 3km radius around Footscray

# 🧭 Center of Footscray
CENTER_LAT = -37.799
CENTER_LON = 144.899

# 📦 Output file path
output_path = "backend/visualizer/data/nearby_pt_stops.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

query = f"""
[out:json];
(
  node(around:{SEARCH_RADIUS},{CENTER_LAT},{CENTER_LON})["highway"="bus_stop"];
  node(around:{SEARCH_RADIUS},{CENTER_LAT},{CENTER_LON})["railway"="tram_stop"];
  node(around:{SEARCH_RADIUS},{CENTER_LAT},{CENTER_LON})["railway"="station"];
);
out body;
"""

try:
    res = requests.get("https://overpass-api.de/api/interpreter", params={'data': query})
    res.raise_for_status()
    data = res.json()

    # 🧹 Simplify extracted data
    stops = []
    for el in data["elements"]:
        stop_type = (
            "Bus Stop" if el["tags"].get("highway") == "bus_stop"
            else "Tram Stop" if el["tags"].get("railway") == "tram_stop"
            else "Train Station"
        )
        stops.append({
            "name": el["tags"].get("name", "Unnamed"),
            "type": stop_type,
            "lat": el["lat"],
            "lon": el["lon"]
        })

    with open(output_path, "w") as f:
        json.dump(stops, f, indent=2)

    print(f"✅ PT stops saved to {os.path.abspath(output_path)}")

except Exception as e:
    print("❌ Error fetching PT stops:", e)
