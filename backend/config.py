import os
from dotenv import load_dotenv

load_dotenv()  # Loads environment variables from your .env file

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'smart_foot_traffic',
    'port': 3306
}
