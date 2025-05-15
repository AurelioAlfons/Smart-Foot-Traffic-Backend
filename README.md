# 📊 Smart Foot Traffic Monitoring System

This project is a backend system designed to clean, process, and store traffic data (🚶‍♂️ pedestrian, 🚴‍♀️ cyclist, 🚗 vehicle counts) from sensors deployed in various locations around Footscray. The system helps transform raw, unstructured sensor CSV files into organized, filtered datasets stored in a MySQL database. These datasets can later be used to generate interactive visualizations like traffic heatmaps based on user-selected filters such as time, date, weather, or season.

--------------------------------------------------

🗂️ Project Structure

![image](https://github.com/user-attachments/assets/cc342aa7-336f-461f-aab0-3a2ab3a24b8e)
![image](https://github.com/user-attachments/assets/78ab8065-774c-47b5-ac7e-cb35f0426fe1)

backend/
├── analytics/                        🧠 Analytics logic (summary, charts)
│   ├── bar_chart/
│   │   └── generate_barchart.py     📊 Generates Plotly bar chart HTML
│   └── seasonal_stats.py            📈 Generates summary stats for dashboard
│
├── db/
│   ├── index_setup.py               🧩 Creates indexes for optimization
│   └── init_db.py                   🗃️ Resets all MySQL tables
│
├── forecast/                        🌦️ Weather and season logic
│   ├── init_weather_season.py       🌱 Resets weather + assigns season
│   ├── season.py                    🍁 Maps month to season
│   ├── temperature.py               🌡️ Fetches real temperature via API
│   └── weather.py                   🌧️ Fetches real weather via API
│
├── pipeline/                        🛠️ Preprocessing engine
│   ├── helpers/
│   │   └── helpers.py               🧪 Location extractor, hour checker
│   └── preprocess.py                🧼 Main logic for processing CSVs
│
├── utils/
│   └── get_ip.py                    🌐 Prints local IP address for dev
│
├── visualizer/
│   ├── generate_heatmap.py          🗺️ Generates heatmap HTML from DB
│   ├── services/
│   │   ├── data_fetcher.py          🧲 Queries traffic data for maps
│   │   ├── db_logger.py             📝 Logs heatmap info to MySQL
│   │   ├── heatmap_log.py           ⏱️ Logs timing info to console + file
│   │   └── map_renderer.py          🖼️ Renders Folium map with all layers
│   └── utils/
│       ├── description_box.py       🧾 Sidebar with heatmap info
│       ├── heatmap_colors.py        🎨 Color scale for traffic intensity
│       ├── map_shapes.py            🔵 Adds zone circles to the map
│       ├── marker_helpers.py        🏷️ Adds label markers to the map
│       ├── sensor_locations.py      📍 Coordinates for each location
│       └── tooltip_box.py           💬 Tooltip popup generator
│
config.py                            ⚙️ MySQL connection config
main.py                              🚀 Optional main entry point
server.py                            🌐 Flask server to serve heatmaps/charts
start_server.bat                     🧮 Windows helper to run the server
requirements.txt                     📦 List of required Python packages
README.md                            📘 Project overview
.env                                 🔐 Local environment variables

barchart/                            📊 Output bar chart HTML files
heatmaps/                            🗺️ Output heatmap HTML files
logs/                                📁 Log files for profiling
data/                                🧾 Raw CSV files

--------------------------------------------------

✨ Features Implemented

1. 🧹 Preprocessing Script (preprocess.py)
- 📥 Reads CSV files from `/data`
- 🧼 Cleans and formats datetime
- 🕐 Converts UTC to Melbourne local time
- 📊 Calculates interval counts
- 🗃️ Stores data into:
  - `processed_data`
  - `traffic_counts`

--------------------------------------------------

2. 🌦️ Weather & Season Assignment (assign_weather_season.py)
- 🗓️ Labels each row with the correct season
- 🌡️ Integrates temperature and weather (Open-Meteo API)
- 💾 Results go to `weather_season_data` table

--------------------------------------------------

3. 🌐 Heatmap Generation (generate_heatmap.py)
- 🎯 Generates filtered interactive heatmaps
- 📍 Highlights sensor zones by traffic density
- 🗂️ Saves result as HTML in `/heatmaps`
- 🧠 Logs metadata to `heatmaps` table in MySQL
- 🔄 Avoids duplicates and regenerates if needed

--------------------------------------------------

4. 🚀 Flask Server (server.py)
- Serves heatmap HTMLs locally
- 📡 Use `http://localhost:5000/heatmaps/...`

--------------------------------------------------
