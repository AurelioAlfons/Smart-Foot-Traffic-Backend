# ================================================
# Database Configuration for Smart Foot Traffic
# --------------------------------
# - Supports local, Railway (cloud), or .env-based setup
# - Used by all backend scripts to connect to MySQL
# - Switch by commenting/uncommenting the desired block
# ================================================

import os
from dotenv import load_dotenv

# 📥 Load environment variables from .env file (optional but useful)
load_dotenv()

# ==========================================
# 🌐 DEFAULT: Connect to Railway MySQL (Cloud)
# ==========================================
# DB_CONFIG = {
#     "host": "metro.proxy.rlwy.net",
#     "port": 56408,
#     "user": "root",
#     "password": "FhhxYrQmqSbGiJUbbhnHWfVUeXWyOBiD",
#     "database": "railway"
# }

# ==========================================
# 🛠️ ALTERNATIVE: Use Localhost MySQL for Dev
# 👉 To use this, comment the Railway block above and uncomment this one
# ==========================================
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'smart_foot_traffic'
}

# ==========================================
# 📦 OPTIONAL: Use environment variables (.env) for local or Render
# 👉 Only use this if you've set up DB_HOST, DB_USER, etc. in .env or Render dashboard
# ==========================================
# DB_CONFIG = {
#     'host': os.getenv('DB_HOST'),
#     'port': int(os.getenv('DB_PORT')),
#     'user': os.getenv('DB_USER'),
#     'password': os.getenv('DB_PASSWORD'),
#     'database': os.getenv('DB_NAME')
# }
