import mysql.connector
from config import DB_CONFIG

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

cursor.execute("INSERT INTO processed_data (Date_Time, Location) VALUES ('2024-04-01 12:00:00', 'Test Location')")
conn.commit()

cursor.execute("SELECT * FROM processed_data")
print(cursor.fetchall())

cursor.close()
conn.close()
