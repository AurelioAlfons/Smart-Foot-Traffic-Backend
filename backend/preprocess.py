import os  # use folders and paths
import pandas as pd  # read table files (csv go brrr)
import mysql.connector  # talk to the MySQL database
from config import DB_CONFIG  # get the DB login info
import logging  # prints logs like “yo I did something”

# how the logs should look like
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# these are the 3 traffic folder types
TRAFFIC_TYPES = ['Pedestrian Count', 'Cyclist Count', 'Vehicle Count']

# emojis for each folder (cute mode)
FOLDER_ICONS = {
    'Pedestrian Count': '🚶‍♂️',
    'Cyclist Count': '🚴‍♀️',
    'Vehicle Count': '🚗'
}

# this gets the location name from the file name
def extract_location(filename):
    name = filename.lower().split('---')[-1]  # take the end part
    location = name.split('__')[0].replace('-', ' ').strip()  # cleanup
    return location.title()  # make first letters big

# this function does the whole magic
def preprocess_data():
    # where the folders live
    base_path = os.path.join(os.path.dirname(__file__), 'data')

    # try to connect to MySQL
    try:
        conn = mysql.connector.connect(**DB_CONFIG)  # connect
        cursor = conn.cursor()
        logging.info("🔌 Connected to MySQL database")
    except mysql.connector.Error as e:
        logging.error(f"❌ Couldn't connect to database: {e}")
        return  # stop if no connection

    # go through each folder
    for traffic in TRAFFIC_TYPES:
        icon = FOLDER_ICONS.get(traffic, '📦')  # get emoji
        folder = os.path.join(base_path, traffic)  # full path

        print("\n" + "=" * 60)
        logging.info(f"{icon} Processing folder: {traffic}")  # log it
        print("=" * 60)

        # folder not found?
        if not os.path.exists(folder):
            logging.warning(f"⚠️ Folder does not exist: {folder}")
            continue

        # only take .csv files
        files = sorted([f for f in os.listdir(folder) if f.endswith('.csv')])

        # if no files inside, skip
        if not files:
            logging.warning(f"📂 No CSV files found in: {folder}")
            continue

        # go through each file
        for index, file in enumerate(files, 1):
            print("\n" + "-" * 40)
            logging.info(f"{index}. 📄 Reading file: {file}")  # show number
            print("-" * 40)

            path = os.path.join(folder, file)  # file path

            try:
                df = pd.read_csv(path)  # open file
            except Exception as e:
                logging.error(f"❌ Failed to read {file}: {e}")
                continue  # skip if broken

            logging.info(f"📊 Rows loaded: {len(df)}")
            logging.info(f"🧾 Columns found: {df.columns.tolist()}")

            # if needed columns missing, skip
            if 'date' not in df.columns or 'value' not in df.columns:
                logging.warning(f"⚠️ Skipping {file} — missing 'date' or 'value' column.")
                continue

            df.drop_duplicates(inplace=True)  # remove repeats
            location = extract_location(file)  # get where

            # make the time look pretty
            df['Date_Time'] = pd.to_datetime(df['date'], errors='coerce', utc=True)
            df['Date_Time'] = df['Date_Time'].dt.tz_convert('Australia/Melbourne')
            df['Date_Time'] = df['Date_Time'].dt.tz_localize(None)
            df.dropna(subset=['Date_Time'], inplace=True)

            logging.info(f"✅ Valid datetime rows: {len(df)}")

            # split datetime into date and time
            df['Date'] = df['Date_Time'].dt.date.astype(str)
            df['Time'] = df['Date_Time'].dt.time.astype(str)
            df['Date_Time'] = df['Date_Time'].dt.strftime('%Y-%m-%d %H:%M:%S')

            # fill missing values with the middle value
            median_count = df['value'].median()
            df['value'] = df['value'].fillna(median_count)

            # make all rows into a list for faster inserting
            processed_data = [(row['Date_Time'], row['Date'], row['Time'], location) for _, row in df.iterrows()]
            cursor.executemany("""
                INSERT INTO processed_data (Date_Time, Date, Time, Location)
                VALUES (%s, %s, %s, %s)
            """, processed_data)

            # get the first new ID added
            start_id = cursor.lastrowid - len(processed_data) + 1

            # now add traffic counts
            traffic_data = [
                (start_id + i, traffic, int(df.iloc[i]['value']))
                for i in range(len(processed_data))
            ]
            cursor.executemany("""
                INSERT INTO traffic_counts (Data_ID, Traffic_Type, Traffic_Count)
                VALUES (%s, %s, %s)
            """, traffic_data)

            logging.info(f"✅ Inserted {len(df)} rows from file {index}: {file}")  # done

    conn.commit()  # save to MySQL
    cursor.close()  # close cursor
    conn.close()  # close DB
    logging.info("🏁 All CSVs processed and stored in MySQL.")  # all done!

# run the code
if __name__ == "__main__":
    preprocess_data()
