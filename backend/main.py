# =====================================================
# Project: Smart Foot Traffic
# Group: Aurelio, Mayank, Lloyd, Adham
# ======================================================
# This script runs the entire data pipeline for the project.
# All you need to do everytime just run this file in temrinal and it will:
# 
# 1. Delete old tables (if they exist)
# 2. Create new empty tables for fresh data
# 3. Clean the raw sensor data
# 4. Format timestamps
# 5. Add to processed_data and traffic_counts tables
# 6. Assign and season (summer, winter, etc.)
# 7. Save to weather_season_data table
# 8. Save to heatmaps table
# =====================================================

import subprocess  # Allows us to run other python files from this main script
import sys  # Gives access to system-specific parameters and functions

# Get the path to the current Python (inside your virtual environment)
# Makes it so we can run this script from anywhere
# and it will use the right Python interpreter
python_exec = sys.executable

# =====================================================
# Step 0: Set up the database tables
# =====================================================
# This will:
# 1. Delete old tables (if they exist)
# 2. Create new empty tables for fresh data
print("\n========================================")
print("🛠️  0. Initializing database tables...")
print("========================================")
subprocess.run([python_exec, "backend/db/init_db.py"])

# Automatically create missing indexes
print("\n========================================")
print("⚡  Creating missing indexes if needed...")
print("========================================")
from backend.db.index_setup import create_indexes_if_missing
create_indexes_if_missing()

# =====================================================
# Step 1: Preprocess the raw CSV data
# =====================================================
# This will:
# - Clean the raw sensor data
# - Format timestamps
# - Add to processed_data and traffic_counts tables
print("\n========================================")
print("🔄 1. Running preprocess.py...")
print("========================================")
subprocess.run([python_exec, "backend/pipeline/preprocess.py"])

# =====================================================
# Step 2: Add weather and season data
# =====================================================
# This will:
# - Take the cleaned data
# - Assign weather (sunny, cloudy, etc.) and season (summer, winter, etc.)
# - Save to weather_season_data table
print("\n========================================")
print("🍂 2. Running assign_weather_season.py...")
print("========================================")
subprocess.run([python_exec, "-m", "backend.forecast.init_weather_season"])

# =====================================================
# Final message
# =====================================================
print("\n========================================")
print("✅ All steps completed.")
print("========================================")
