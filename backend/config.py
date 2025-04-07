import os
from dotenv import load_dotenv

load_dotenv()  # Loads environment variables from your .env file

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT'))
}

# DB_CONFIG = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'password',
#     'database': 'smart_foot_traffic',
#     'port': 3306
# }