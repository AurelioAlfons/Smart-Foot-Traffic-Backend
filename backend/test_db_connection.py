import mysql.connector
from config import DB_CONFIG

# Try connecting to MySQL database
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE();")
    db_name = cursor.fetchone()

    # If the connection is successful, print the database name
    print(f"✅ Successfully connected to database: {db_name[0]}")

# If the connection is successful, check if the connection is open
except mysql.connector.Error as e:
    print(f"❌ Database connection failed: {e}")

# If connected, check if the connection is open
finally:
    if conn.is_connected():
        cursor.close()
        conn.close()
