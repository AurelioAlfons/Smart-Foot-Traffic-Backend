import os
import pandas as pd
import mysql.connector
from config import DB_CONFIG
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

TRAFFIC_TYPES = ['Pedestrian Count', 'Cyclist Count', 'Vehicle Count']
FOLDER_ICONS = {
    'Pedestrian Count': '🚶‍♂️',
    'Cyclist Count': '🚴‍♀️',
    'Vehicle Count': '🚗'
}

def extract_location(filename):
    name = filename.lower().split('---')[-1]
    location = name.split('__')[0].replace('-', ' ').strip()
    return location.title()

def preprocess_data():
    base_path = os.path.join(os.path.dirname(__file__), 'data')

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info("🔌 Connected to MySQL database")
    except mysql.connector.Error as e:
        logging.error(f"❌ Couldn't connect to database: {e}")
        return

    for traffic in TRAFFIC_TYPES:
        icon = FOLDER_ICONS.get(traffic, '📦')
        folder = os.path.join(base_path, traffic)
        print("\n" + "=" * 60)
        logging.info(f"{icon} Processing folder: {folder}")
        print("=" * 60)

        if not os.path.exists(folder):
            logging.warning(f"⚠️ Folder does not exist: {folder}")
            continue

        files = os.listdir(folder)
        if not files:
            logging.warning(f"📂 No CSV files found in: {folder}")
            continue

        for file in files:
            if not file.endswith('.csv'):
                continue

            path = os.path.join(folder, file)
            print("\n" + "-" * 40)
            logging.info(f"📄 Reading file: {file}")
            print("-" * 40)

            try:
                df = pd.read_csv(path)
            except Exception as e:
                logging.error(f"❌ Failed to read {file}: {e}")
                continue

            logging.info(f"📊 Rows loaded: {len(df)}")
            logging.info(f"🧾 Columns found: {df.columns.tolist()}")

            if 'date' not in df.columns or 'value' not in df.columns:
                logging.warning(f"⚠️ Skipping {file} — missing 'date' or 'value' column.")
                continue

            df.drop_duplicates(inplace=True)

            location = extract_location(file)

            # Convert to Melbourne local time and drop timezone
            df['Date_Time'] = pd.to_datetime(df['date'], errors='coerce', utc=True)
            df['Date_Time'] = df['Date_Time'].dt.tz_convert('Australia/Melbourne')
            df['Date_Time'] = df['Date_Time'].dt.tz_localize(None)

            df.dropna(subset=['Date_Time'], inplace=True)
            logging.info(f"✅ Valid datetime rows: {len(df)}")

            df['Date'] = df['Date_Time'].dt.date.astype(str)
            df['Time'] = df['Date_Time'].dt.time.astype(str)
            df['Date_Time'] = df['Date_Time'].dt.strftime('%Y-%m-%d %H:%M:%S')

            median_count = df['value'].median()
            df['value'] = df['value'].fillna(median_count)

            inserted = 0
            for _, row in df.iterrows():
                try:
                    cursor.execute("""
                        INSERT INTO processed_data (Date_Time, Date, Time, Location)
                        VALUES (%s, %s, %s, %s)
                    """, (row['Date_Time'], row['Date'], row['Time'], location))

                    data_id = cursor.lastrowid
                    cursor.execute("""
                        INSERT INTO traffic_counts (Data_ID, Traffic_Type, Traffic_Count)
                        VALUES (%s, %s, %s)
                    """, (data_id, traffic, int(row['value'])))
                    inserted += 1

                except mysql.connector.Error as e:
                    logging.error(f"❌ DB error inserting from {file}: {e}")
                    continue

            logging.info(f"✅ Inserted {inserted} rows from {file}")

    conn.commit()
    cursor.close()
    conn.close()
    logging.info("🏁 All CSVs processed and stored in MySQL.")

if __name__ == "__main__":
    preprocess_data()
