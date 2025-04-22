import logging
from datetime import datetime
from collections import defaultdict

# =====================================================
# 🚦 TYPES OF TRAFFIC USED IN PROJECT
# These labels match folder names and DB values
# =====================================================
TRAFFIC_TYPES = ['Pedestrian Count', 'Cyclist Count', 'Vehicle Count']

# =====================================================
# 🎨 EMOJIS FOR LOGGING / VISUAL SECTIONS
# Used to show nice icons when printing progress
# =====================================================
FOLDER_ICONS = {
    'Pedestrian Count': '🚶‍♂️',
    'Cyclist Count': '🚴‍♀️',
    'Vehicle Count': '🚗'
}

# =====================================================
# 🏷️ EXTRACT LOCATION FROM FILE NAME
# Converts: vehicle-count---footscray-market__2022.csv
# Into: Footscray Market
# =====================================================
def extract_location(filename):
    # Get the part after the last '---'
    name = filename.lower().split('---')[-1]

    # Remove everything after '__' and replace dashes with spaces
    location = name.split('__')[0].replace('-', ' ').strip()

    # Capitalize first letter of each word
    return location.title()

# =====================================================
# 🕒 CHECK FOR MISSING HOURS PER DAY
# Used to make sure each day has 24 full hours of data
# for one specific location (editable inside query)
# =====================================================
def check_missing_hours(cursor):
    # 👇 Modify this query to check other locations too if needed
    query = """
    SELECT Date, Time, Location
    FROM processed_data
    WHERE Location = 'Footscray Library Car Park'
    ORDER BY Date, Time
    """

    # Run the SQL query
    cursor.execute(query)
    rows = cursor.fetchall()

    # 🧠 This dictionary stores hours recorded per date
    time_data = defaultdict(list)

    # 📅 Group times per date
    for date, time, _ in rows:
        # Combine Date and Time into one datetime object
        full_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
        time_data[date].append(full_dt.hour)

    # 🔎 Check for any hours that are missing in the day
    for date, hours in time_data.items():
        # Get all hours from 0–23, then subtract what's missing
        missing_hours = sorted(set(range(24)) - set(hours))

        if missing_hours:
            # If there are gaps, log them as a warning
            logging.warning(f"🕒 {date} is missing hours: {missing_hours}")
        else:
            # Otherwise, show that it's complete
            logging.info(f"✅ {date} has full 24-hour coverage")
