Smart Foot Traffic Monitoring System

This project is a backend system designed to clean, process, and store traffic data (pedestrian, cyclist, and vehicle counts) from sensors deployed in various locations around Footscray. The system includes preprocessing scripts, weather and season assignment logic, and seamless integration with a MySQL database for storage and further visualization (e.g., heatmaps).

--------------------------------------------------

## 📁 Project Structure

SMART_FOOT_TRAFFIC/
├── backend/
│   ├── __pycache__/
│   ├── data/                         # Raw CSV files go here
│   ├── assign_weather_season.py     # Assign season & weather to each record
│   ├── config.py                    # MySQL config (user, password, db)
│   ├── preprocess.py                # Preprocess raw data and insert into DB
│   ├── run_pipeline.py              # Runs preprocess + season assignment
│   ├── tes_insert.py                # Test script for database insert
│   ├── test_db_connection.py       # Test MySQL connection script
├── requirements.txt
├── .env
├── README.md
└── venv/                            # Python virtual environment

--------------------------------------------------

Features Implemented

1. Preprocessing Script (preprocess.py)
- Cleans CSV files (fix formatting, timestamps, remove duplicates).
- Converts time to Melbourne timezone.
- Extracts metadata (location, date, time).
- Inserts structured records into two MySQL tables: processed_data and traffic_counts.

--------------------------------------------------

2. Weather & Season Assignment (assign_weather_season.py)
- Analyzes timestamps and assigns the correct season.
- (Weather API integration coming soon.)
- Stores results in the weather_season_data table.

--------------------------------------------------

3. Combined Pipeline (run_pipeline.py)
- Automates both preprocessing and weather/season assignment.
- Displays progress bars and logs for a smooth terminal experience.

--------------------------------------------------

4. Logging and Comments
- Clean, readable code with emoji-enhanced logging.
- Clear comments for all major functions and logic.

--------------------------------------------------

Setup & How to Run (Step-by-Step)

1. Install VS Code
https://code.visualstudio.com

--------------------------------------------------

2. Install Python
https://python.org  
Make sure to check "Add Python to PATH" during install

--------------------------------------------------

3. Clone the Repository

git clone https://github.com/AurelioAlfons/Smart-Foot-Traffic.git
cd Smart-Foot-Traffic

--------------------------------------------------

4. Create Virtual Environment

python -m venv venv

--------------------------------------------------

5. Activate Virtual Environment

Windows:
venv\Scripts\activate

Mac/Linux:
source venv/bin/activate

--------------------------------------------------

6. Install Extensions in VS Code
- Python Extension
- Jupyter (optional)
- MySQL or SQLTools (for DB browsing)

--------------------------------------------------

7. Install Required Packages

pip install -r backend/requirements.txt

Or manually:

pip install pandas mysql-connector-python rich python-dotenv

--------------------------------------------------

8. Create config.py inside backend/

DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_user',
    'password': 'your_password',
    'database': 'your_db'
}

--------------------------------------------------

9. Run Preprocessing Script

python backend/preprocess.py

--------------------------------------------------

10. Run the Whole Pipeline

python backend/run_pipeline.py

--------------------------------------------------

That's it! Your cleaned and tagged data should now be stored in MySQL ready for analysis.

Let us know if you want to contribute, generate heatmaps, or build a frontend!

