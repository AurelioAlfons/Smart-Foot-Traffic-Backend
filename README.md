# Smart Foot Traffic Monitoring System

This project is a backend system designed to clean, process, and store traffic data (🚶‍♂️ pedestrian, 🚴‍♀️ cyclist, 🚗 vehicle counts) from sensors deployed in various locations around Footscray. The system helps transform raw, unstructured sensor CSV files into organized, filtered datasets stored in a MySQL database. These datasets can later be used to generate interactive visualizations like traffic heatmaps based on user-selected filters such as time, date, weather, or season.

In addition to data processing and serving APIs, the system generates and stores multiple types of interactive HTML visualizations locally within the repository. These include:

- Heatmaps (`/heatmaps/`) showing traffic density by location and time
- Bar charts (`/barchart/`) for comparing traffic volumes across different categories
- Line charts (`/linechart/`) for observing temporal trends
- Pie charts (`/piechart/`) displaying traffic type distributions
- Forecast charts (`/forecast/`) showing predicted traffic patterns
- Downloadable export reports (`/downloads/`) combining all the above charts with metadata

--------------------------------------------------

🗂️ Project Structure

![image](https://github.com/user-attachments/assets/207ab51c-0ae6-4971-a29a-71dfefeee347)

--------------------------------------------------
Use Case Examples

- Generate a heatmap of cyclist activity at 9:00 AM on weekends to assist city planning.
- Download a full report for vehicle traffic during summer mornings.
- Analyze seasonal foot traffic trends near Footscray Library using the line chart.

--------------------------------------------------

Database Schema

The following diagram shows the structure of the MySQL database used for traffic data storage and visualization:

![Database Schema](https://github.com/AurelioAlfons/Smart-Foot-Traffic-Backend/raw/main/Database%20Schema/Smart%20Foot%20Traffic%20-%20Database%20Schema.png)

![Database Structure](https://github.com/AurelioAlfons/Smart-Foot-Traffic-Backend/raw/main/Database%20Schema/Smart%20Foot%20Traffic.png)

--------------------------------------------------


Features Implemented

1. Preprocessing Script (`preprocess.py`)
- Reads CSV files from `/data`
- Cleans and formats datetime
- Converts UTC to Melbourne local time
- Calculates interval counts
- Stores data into:
  - `processed_data`
  - `traffic_counts`

--------------------------------------------------

2. Weather & Season Assignment (`assign_weather_season.py`)
- Labels each row with the correct season
- Integrates temperature and weather (Open-Meteo API)
- Results go to `weather_season_data` table

--------------------------------------------------

3. Heatmap Generation (`generate_heatmap.py`)
- Generates filtered interactive heatmaps
- Highlights sensor zones by traffic density
- Saves result as HTML in `/heatmaps`
- Logs metadata to `heatmaps` table in MySQL
- Avoids duplicates and regenerates if needed

--------------------------------------------------

4. Flask Server (`server.py`)
- Serves heatmap HTMLs locally
- Use `http://localhost:5000/heatmaps/...`

--------------------------------------------------

1. Open a terminal in the root of the project directory.

2. Run the menu script based on your operating system:

   - For Windows:
     ```
     .\backend_menu.bat
     ```

   - For macOS/Linux:
     ```
     sh backend_menu.sh
     ```

3. From the menu:
   - First, select option `6` to install all required Python libraries from `requirements.txt`.
   - Then, select option `4` to preprocess and insert cleaned data into the database.
   - Finally, select option `2` to run the Flask server.

--------------------------------------------------

API Endpoints

| Endpoint                     | Method | Description                                                   |
|-----------------------------|--------|---------------------------------------------------------------|
| `/api/summary_stats`        | POST   | Returns summary statistics (JSON)                             |
| `/api/generate_linechart`   | POST   | Generates a line chart and returns the chart URL              |
| `/api/generate_piechart`    | POST   | Generates a pie chart dashboard and returns the chart URL     |
| `/api/generate_forecast`    | POST   | Generates a forecast chart and returns the chart URL          |
| `/api/generate_heatmap`     | POST   | Generates a filtered heatmap and returns the HTML URL         |
| `/api/statistics/bar_chart` | GET    | Returns bar chart HTML comparing seasonal/location trends     |
| `/api/location_snapshot`    | POST   | Returns traffic + weather data for each sensor at a given hour|
| `/api/download_report`      | GET    | Generates full HTML report combining all charts and heatmaps  |


