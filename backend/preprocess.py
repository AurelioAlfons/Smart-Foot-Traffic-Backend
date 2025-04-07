import os
import pandas as pd
import mysql.connector
from config import DB_CONFIG
import logging
from collections import defaultdict
from datetime import datetime

# Setup how messages appear in terminal (for info, warnings, errors)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# These are the only types of traffic data we're processing
TRAFFIC_TYPES = ['Pedestrian Count', 'Cyclist Count', 'Vehicle Count']

# Just to make folder logs look nicer
FOLDER_ICONS = {
    'Pedestrian Count': '🚶‍♂️',
    'Cyclist Count': '🚴‍♀️',
    'Vehicle Count': '🚗'
}

# Extract location name from filename (e.g. footscray-library-car-park → Footscray Library Car Park)
def extract_location(filename):
    name = filename.lower().split('---')[-1]
    location = name.split('__')[0].replace('-', ' ').strip()
    return location.title()

# Main function to load CSVs and insert them into the MySQL database
def preprocess_data():
    base_path = os.path.join(os.path.dirname(__file__), 'data')

    # Try connecting to MySQL
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info("🔌 Connected to MySQL")
    except mysql.connector.Error as e:
        logging.error(f"❌ Connection failed: {e}")
        return

    # Go through each traffic type folder (e.g. Pedestrian Count folder)
    for traffic in TRAFFIC_TYPES:
        icon = FOLDER_ICONS.get(traffic, '📦')
        folder = os.path.join(base_path, traffic)

        print("\n" + "=" * 60)
        logging.info(f"{icon} Processing: {traffic}")
        print("=" * 60)

        if not os.path.exists(folder):
            logging.warning(f"⚠️ Missing folder: {folder}")
            continue

        files = sorted([f for f in os.listdir(folder) if f.endswith('.csv')])
        if not files:
            logging.warning(f"📂 No CSVs found in: {folder}")
            continue

        for index, file in enumerate(files, 1):
            print("\n" + "-" * 40)
            logging.info(f"{index}. 📄 Reading: {file}")
            print("-" * 40)

            path = os.path.join(folder, file)

            try:
                df = pd.read_csv(path)
            except Exception as e:
                logging.error(f"❌ Couldn't read file: {e}")
                continue

            logging.info(f"📊 Rows loaded: {len(df)}")
            logging.info(f"🧾 Columns: {df.columns.tolist()}")

            # Make sure the file has the columns we need
            if 'date' not in df.columns or 'value' not in df.columns:
                logging.warning("⚠️ Skipping — missing 'date' or 'value'")
                continue

            df.drop_duplicates(inplace=True)
            location = extract_location(file)

            # Convert the date string to a datetime object and adjust to Melbourne time
            df['Date_Time'] = pd.to_datetime(df['date'], errors='coerce', utc=True)
            df['Date_Time'] = df['Date_Time'].dt.tz_convert('Australia/Melbourne').dt.tz_localize(None)
            df.dropna(subset=['Date_Time'], inplace=True)

            logging.info(f"✅ Valid datetime rows: {len(df)}")

            # Split into separate date and time columns
            df['Date'] = df['Date_Time'].dt.date.astype(str)
            df['Time'] = df['Date_Time'].dt.time.astype(str)
            df['Date_Time'] = df['Date_Time'].dt.strftime('%Y-%m-%d %H:%M:%S')

            # Fill any missing 'value' with the middle value (median)
            df['value'] = df['value'].fillna(df['value'].median())

            # Sort by time so interval counts make sense
            df.sort_values(by='Date_Time', inplace=True)

            # Calculate interval count per day (resets each midnight)
            df['Interval_Count'] = df.groupby('Date')['value'].diff().fillna(df['value']).clip(lower=0).astype(int)

            inserted = 0  # track how many rows got inserted

            # Insert one row at a time into the database
            for _, row in df.iterrows():
                try:
                    # Insert into processed_data
                    cursor.execute("""
                        INSERT INTO processed_data (Date_Time, Date, Time, Location)
                        VALUES (%s, %s, %s, %s)
                    """, (row['Date_Time'], row['Date'], row['Time'], location))
                    data_id = cursor.lastrowid

                    # Insert into traffic_counts
                    try:
                        cursor.execute("""
                            INSERT INTO traffic_counts (Data_ID, Traffic_Type, Total_Count, Interval_Count)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            data_id,
                            traffic,
                            int(row['value']),
                            int(row['Interval_Count'])
                        ))
                        inserted += 1

                    except mysql.connector.Error as e:
                        # Undo the previous insert if this one fails
                        conn.rollback()
                        logging.error(f"❌ Insert failed for Data_ID {data_id}, rolled back: {e}")

                except mysql.connector.Error as e:
                    logging.error(f"❌ DB insert error (processed_data): {e}")
                    continue

            logging.info(f"✅ Inserted {inserted} rows from: {file}")

    # Save all changes to the DB
    conn.commit()
    logging.info("📦 Finished inserting all CSV data. Now checking for missing hours...\n")

    # Check for any missing time ranges per day
    check_missing_hours(cursor)

    cursor.close()
    conn.close()
    logging.info("🏁 All data saved to MySQL and hour check complete!")

# This checks what hours are missing each day
def check_missing_hours(cursor):
    query = """
    SELECT Date, Time, Location
    FROM processed_data
    WHERE Location = 'Footscray Library Car Park'
    ORDER BY Date, Time
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    time_data = defaultdict(list)

    for date, time, _ in rows:
        full_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
        time_data[date].append(full_dt.hour)

    for date, hours in time_data.items():
        missing_hours = sorted(set(range(24)) - set(hours))
        if missing_hours:
            logging.warning(f"🕒 {date} is missing hours: {missing_hours}")
        else:
            logging.info(f"✅ {date} has full 24-hour coverage")

# Run everything
if __name__ == "__main__":
    preprocess_data()
