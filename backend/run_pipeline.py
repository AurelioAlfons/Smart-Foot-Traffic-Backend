import subprocess
import sys

# Get the current Python interpreter (from venv)
python_exec = sys.executable

# --- Step 1: Run preprocessing ---
print("\n🔄 Running preprocess.py...")
subprocess.run([python_exec, "backend/preprocess.py"])

# --- Step 2: Run season assignment ---
print("\n🍂 Running assign_weather_season.py...")
subprocess.run([python_exec, "backend/assign_weather_season.py"])

print("\n✅ All steps completed.")
