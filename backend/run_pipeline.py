import subprocess  # Lets us run other Python files like scripts
import sys  # Helps us get the current Python interpreter

# 🐍 Get the path to the current Python (inside your virtual environment)
python_exec = sys.executable

# --- Step 0: Set up the database tables ---
# This will:
# 1. Delete old tables (if they exist)
# 2. Create new empty tables for fresh data
print("\n🛠️  Initializing database tables...")
subprocess.run([python_exec, "backend/init_db.py"])

# --- Step 1: Preprocess the raw CSV data ---
# This will:
# - Clean the raw sensor data
# - Format timestamps
# - Add to processed_data and traffic_counts tables
print("\n🔄 Running preprocess.py...")
subprocess.run([python_exec, "backend/preprocess.py"])

# --- Step 2: Add weather and season data ---
# This will:
# - Take the cleaned data
# - Assign weather (sunny, cloudy, etc.) and season (summer, winter, etc.)
# - Save to weather_season_data table
print("\n🍂 Running assign_weather_season.py...")
subprocess.run([python_exec, "backend/assign_weather_season.py"])

# 🎉 Final message when all steps are done
print("\n✅ All steps completed.")
