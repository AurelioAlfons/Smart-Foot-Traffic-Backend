How to Run Python Script in VS Code (Step-by-Step)

1. Install VS Code  
👉 https://code.visualstudio.com

2. Install Python  
👉 https://python.org  
✅ Make sure to check "Add Python to PATH" during install.

3. Open VS Code & Clone the Repo
--------------------------------------------------
git clone https://github.com/AurelioAlfons/Smart-Foot-Traffic.git
cd Smart-Foot-Traffic

4. Create Virtual Environment
--------------------------------------------------
python -m venv venv

5. Activate Virtual Environment
--------------------------------------------------
# Windows Terminal
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

6. Install Required Packages
--------------------------------------------------
pip install pandas mysql-connector-python

7. Create config.py File
--------------------------------------------------
# config.py
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_user',
    'password': 'your_password',
    'database': 'your_db'
}

8. Run the Script
--------------------------------------------------
python backend/preprocess.py

✅ Done! Your data should now be processed and inserted into MySQL.
