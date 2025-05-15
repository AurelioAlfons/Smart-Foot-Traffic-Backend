# 📊 Smart Foot Traffic Monitoring System

This project is a backend system designed to clean, process, and store traffic data (🚶‍♂️ pedestrian, 🚴‍♀️ cyclist, 🚗 vehicle counts) from sensors deployed in various locations around Footscray. The system helps transform raw, unstructured sensor CSV files into organized, filtered datasets stored in a MySQL database. These datasets can later be used to generate interactive visualizations like traffic heatmaps based on user-selected filters such as time, date, weather, or season.

--------------------------------------------------

🗂️ Project Structure

![image](https://github.com/user-attachments/assets/207ab51c-0ae6-4971-a29a-71dfefeee347)

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
