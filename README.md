# 📊 Smart Foot Traffic Monitoring System

This project is a backend system designed to clean, process, and store traffic data (🚶‍♂️ pedestrian, 🚴‍♀️ cyclist, 🚗 vehicle counts) from sensors deployed in various locations around Footscray. The system helps transform raw, unstructured sensor CSV files into organized, filtered datasets stored in a MySQL database. These datasets can later be used to generate interactive visualizations like traffic heatmaps based on user-selected filters such as time, date, weather, or season.

--------------------------------------------------

🗂️ Project Structure

![image](https://github.com/user-attachments/assets/50fa94bc-c468-4147-8dc4-b29fecd783fe)


SMART_FOOT_TRAFFIC/
├── backend/
│   ├── config.py                    ⚙️ (Database configuration settings)
│   ├── preprocess.py                🧹 (Cleans and stores traffic data)
│   ├── run_pipeline.py              🔁 (Runs full preprocessing + weather assignment)
│   ├── forecast/                    🌦️ (Assign season and weather to records)
│   ├── pipeline/                    🧪 (Helper scripts for ETL)
│   ├── visualizer/
│   │   ├── generate_heatmap.py      🌐 (Generates and logs HTML heatmaps)
│   │   ├── services/                🧠 (data_fetcher, map_renderer, db_logger)
│   │   └── utils/                   🔧 (tooltip, colors, shapes, markers)
├── heatmaps/                        🗺️ (Generated heatmap HTML files)
├── server.py                        🚀 (Flask server to serve heatmaps)
├── data/                            📂 (Raw CSV files go here)
├── requirements.txt                 📦 (List of required Python packages)
├── .env                             🔒 (Environment variables)
└── README.md                        📄 (This file)

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

🛠️ Setup & How to Run (Step-by-Step)

1. 💻 Install VS Code  
https://code.visualstudio.com

--------------------------------------------------

2. 🐍 Install Python  
https://python.org  
✅ Check "Add Python to PATH" during install

--------------------------------------------------

3. ⬇️ Clone the Repository

```bash
git clone https://github.com/AurelioAlfons/Smart-Foot-Traffic.git
cd Smart-Foot-Traffic
```

--------------------------------------------------

4. 🧪 Create Virtual Environment

```bash
python -m venv venv
```

--------------------------------------------------

5. 🔄 Activate Virtual Environment

```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

--------------------------------------------------

6. 📦 Install Required Packages

```bash
pip install -r requirements.txt
```

--------------------------------------------------

7. ⚙️ Create config.py inside `backend/`

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_user',
    'password': 'your_password',
    'database': 'your_db'
}
```

--------------------------------------------------

8. ▶️ Run Preprocessing Script

```bash
python backend/preprocess.py
```

--------------------------------------------------

9. 🌦️ Run Weather/Season Assignment

```bash
python backend/forecast/init_weather_season.py
```

--------------------------------------------------

10. 🌐 Generate a Heatmap

```bash
python backend/visualizer/generate_heatmap.py
```

--------------------------------------------------

11. 🚀 Serve Heatmaps with Flask

```bash
python server.py
```

🖥️ Visit your browser:  
[http://localhost:5000/heatmaps/heatmap_YYYY-MM-DD_HH-MM-SS_TrafficType.html](http://localhost:5000/heatmaps/...)

--------------------------------------------------

✅ Done! Your traffic heatmaps are now stored, served, and ready for frontend integration!
