📊 Smart Foot Traffic Monitoring System

This project is a backend system designed to clean, process, and store traffic data (🚶‍♂️ pedestrian, 🚴‍♀️ cyclist, 🚗 vehicle counts) from sensors deployed in various locations around Footscray. The system helps transform raw, unstructured sensor CSV files into organized, filtered datasets stored in a MySQL database. These datasets can later be used to generate interactive visualizations like traffic heatmaps based on user-selected filters such as time, date, weather, or season.

--------------------------------------------------

🗂️ Project Structure

SMART_FOOT_TRAFFIC/
├── backend/
│   ├── __pycache__/
│   ├── data/                         📁 (Raw CSV files go here)
│   ├── assign_weather_season.py     🌦️ (Assign season & weather to each record based on timestamp)
│   ├── config.py                    ⚙️ (Contains database configuration settings)
│   ├── preprocess.py                🧹 (Main script for preprocessing and storing traffic data)
│   ├── run_pipeline.py              🔁 (Combines preprocessing and season assignment into one process)
│   ├── tes_insert.py                🧪 (Script for testing individual data insertions)
│   ├── test_db_connection.py       🔌 (Tests database connection settings)
├── requirements.txt                 📦 (List of required Python packages)
├── .env                             🔒 (Environment variables file)
├── README.md                        📄 (This file)
└── venv/                            🐍 (Python virtual environment)

--------------------------------------------------

✨ Features Implemented

1. 🧹 Preprocessing Script (preprocess.py)
- 📥 Reads CSV files from the /data folder.
- 🧼 Cleans and formats data (e.g., standardizes datetime format, removes duplicates).
- ⏱️ Converts UTC timestamps to Melbourne local time.
- 🧠 Extracts key metadata like location name, date, time, and traffic counts.
- 🗃️ Stores cleaned data in two MySQL tables: `processed_data` and `traffic_counts`.

--------------------------------------------------

2. 🌦️ Weather & Season Assignment (assign_weather_season.py)
- 🗓️ Assigns seasonal labels (Summer, Autumn, Winter, Spring) to each traffic entry using timestamps.
- ☁️ Future updates will integrate historical weather data using a weather API.
- 💾 Updates results into a MySQL table called `weather_season_data` for advanced filtering and visualization.

--------------------------------------------------

3. 🔁 Combined Pipeline (run_pipeline.py)
- ⚙️ A wrapper script that runs both the preprocessing and weather/season assignment steps in one go.
- 🚀 Ensures efficient automation for bulk data preparation.
- 📊 Includes rich terminal logs and a progress bar to enhance the user experience.

--------------------------------------------------

4. 📝 Logging and Comments
- 💬 All major scripts are commented for clarity.
- 🎨 Console outputs use emojis and progress bars (via the `rich` library) for an engaging and informative runtime.
- 🧯 Error handling and informative logs help trace issues easily during execution.

--------------------------------------------------

🛠️ Setup & How to Run (Step-by-Step)

1. 💻 Install VS Code  
https://code.visualstudio.com

--------------------------------------------------

2. 🐍 Install Python  
https://python.org  
✅ Make sure to check "Add Python to PATH" during install.

--------------------------------------------------

3. ⬇️ Clone the Repository

git clone https://github.com/AurelioAlfons/Smart-Foot-Traffic.git  
cd Smart-Foot-Traffic

--------------------------------------------------

4. 🧪 Create Virtual Environment

python -m venv venv

--------------------------------------------------

5. 🔄 Activate Virtual Environment

Windows:
venv\Scripts\activate

Mac/Linux:
source venv/bin/activate

--------------------------------------------------

6. 🧩 Install Extensions in VS Code
- 🐍 Python Extension
- 📓 Jupyter (optional)
- 🗄️ MySQL or SQLTools (for viewing DB contents)

--------------------------------------------------

7. 📦 Install Required Packages

pip install -r backend/requirements.txt

Or manually:

pip install pandas mysql-connector-python rich python-dotenv

--------------------------------------------------

8. ⚙️ Create config.py inside backend/

DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_user',
    'password': 'your_password',
    'database': 'your_db'
}

--------------------------------------------------

9. ▶️ Run Preprocessing Script

python backend/preprocess.py

--------------------------------------------------

10. ▶️ Run the Whole Pipeline

python backend/run_pipeline.py

--------------------------------------------------

✅ Once completed, the system will insert all cleaned and structured traffic data into your MySQL database. This prepares your dataset for heatmap generation and analytics based on filters like location, date, traffic type, weather, and season.
