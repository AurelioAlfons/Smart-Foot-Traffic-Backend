# backend/run_pipeline.py
import subprocess
import sys

python_exec = sys.executable

def run_pipeline():
    try:
        print("\n🚀 Starting Data Pipeline")
        
        # Step 1: Preprocessing
        print("\n🔄 Step 1/3: Data Preprocessing")
        subprocess.run([python_exec, "backend/preprocess.py"], check=True)
        
        # Step 2: Weather/Season
        print("\n🌦️ Step 2/3: Weather Assignment")
        subprocess.run([python_exec, "backend/assign_weather_season.py"], check=True)
        
        # Step 3: ML Training
        print("\n🤖 Step 3/3: Model Training")
        subprocess.run([python_exec, "backend/model_pipeline.py"], check=True)
        
        print("\n✅ All pipeline steps completed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Pipeline failed at step: {e.cmd}")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    run_pipeline()