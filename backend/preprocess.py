# This script processes CSV files containing traffic data, cleans the data, and stores it in a MySQL database.

import os  # For file path handling
import pandas as pd  # For reading & cleaning csv files
import mysql.connector  # For MySQL connection
from config import DB_CONFIG  # Import database configuration
import logging  # For clear logging of info and errors

# Configure logging to show clear, simple messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Each traffic type has its own column for the count
TRAFFIC_COLUMNS = {
    'Pedestrian': 'Total_Pedestrian_Count',
    'Cyclist': 'Cyclist_Count',
    'Vehicle': 'Total_Vehicle_Count'
}

# Get the location name from the filename
# Example filename: '2023-01-01---Location__Pedestrian.csv'
def extract_location(filename):
    name = filename.lower().split('---')[-1]
    location = name.split('__')[0].replace('-', ' ').strip()
    return location.title()

# Preprocess the data
# - Read CSV files from the data directory
# - Clean the data (remove duplicates, fill missing values, etc.)
# - Store the cleaned data in MySQL database
def preprocess_data():
    base_path = os.path.join(os.path.dirname(__file__), 'data')
    # Traffic types are the folders in the data directory
    traffic_types = ['Pedestrian', 'Cyclist', 'Vehicle']

    try:
        # Connect to MySQL database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logging.info("Connected to MySQL database")
    except mysql.connector.Error as e:
        logging.error(f"Couldn't connect to database: {e}")
        return

    # Loop through traffic type folders
    for traffic in traffic_types:
        folder = os.path.join(base_path, traffic)
        count_col = TRAFFIC_COLUMNS[traffic]

        # Go through each CSV file in the folder
        for file in os.listdir(folder):
            if file.endswith('.csv'):
                path = os.path.join(folder, file)
                logging.info(f"Processing file: {file}")
                df = pd.read_csv(path)

                # Skip file if important columns are missing
                if 'Date_Time' not in df.columns or count_col not in df.columns:
                    logging.warning(f"⚠️ Skipping {file} — missing required columns.")
                    continue

                # Remove duplicates to keep data clean
                df.drop_duplicates(inplace=True)
                
                # Get location from filename
                location = extract_location(file)

                # Fix and format Date_Time column properly
                df['Date_Time'] = pd.to_datetime(df['Date_Time'], errors='coerce')
                df['Date_Time'].interpolate(method='time', inplace=True)
                df.dropna(subset=['Date_Time'], inplace=True)  # Drop rows where dates couldn't be fixed
                df['Date_Time'] = df['Date_Time'].dt.strftime('%Y-%m-%d %H:%M:%S')

                # Fill missing traffic count with the median to avoid gaps
                median_count = df[count_col].median()
                df[count_col].fillna(median_count, inplace=True)

                # Insert data into MySQL database with error handling
                for _, row in df.iterrows():
                    try:
                        # Insert data into processed_data table
                        cursor.execute("""
                            INSERT INTO processed_data (Date_Time, Location)
                            VALUES (%s, %s)
                        """, (row['Date_Time'], location))

                        data_id = cursor.lastrowid  # Get the last inserted ID

                        # Insert data into traffic_counts table
                        cursor.execute("""
                            INSERT INTO traffic_counts (Data_ID, Traffic_Type, Traffic_Count)
                            VALUES (%s, %s, %s)
                        """, (data_id, traffic, int(row[count_col])))

                    except mysql.connector.Error as e:
                        logging.error(f"Database insertion error for file {file}: {e}")

    # Save all changes and safely close connection
    conn.commit()
    cursor.close()
    conn.close()
    logging.info("✅ All CSVs processed and stored in MySQL.")

# Run the preprocessing if this file is executed
if __name__ == "__main__":
    preprocess_data()
