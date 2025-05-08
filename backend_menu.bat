@echo off
:MENU
cls
echo     SMART FOOT TRAFFIC - BACKEND MENU
echo ==========================================
echo [1]. Check local IP address
echo [2]. Run Flask server
echo [3]. Run heatmap generator manually
echo [4]. Run data preprocessing (backend.main)
echo ------------------------------------------ 
echo [5]. Activate virtual environment
echo [6]. Install required libraries (requirements.txt)
echo [7]. Exit
echo ==========================================
set /p choice="Enter your choice: "
echo.

if "%choice%"=="1" (
    python backend/utils/get_ip.py
    pause
    goto MENU
)

if "%choice%"=="2" (
    python server.py
    pause
    goto MENU
)

if "%choice%"=="3" (
    python -m backend.visualizer.generate_heatmap
    pause
    goto MENU
)

if "%choice%"=="4" (
    python -m backend.main
    pause
    goto MENU
)

if "%choice%"=="5" (
    call venv\Scripts\activate
    pause
    goto MENU
)

if "%choice%"=="6" (
    pip install -r requirements.txt
    pause
    goto MENU
)

if "%choice%"=="7" (
    exit
)

goto MENU
