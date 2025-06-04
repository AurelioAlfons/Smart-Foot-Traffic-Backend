#!/bin/bash

while true; do
  clear
  echo "    SMART FOOT TRAFFIC - BACKEND MENU"
  echo "=========================================="
  echo "[1]. Check local IP address"
  echo "[2]. Run Flask server"
  echo "[3]. Run heatmap generator manually"
  echo "[4]. Run data preprocessing (backend.main)"
  echo "------------------------------------------"
  echo "[5]. Activate virtual environment"
  echo "[6]. Install required libraries (requirements.txt)"
  echo "[7]. Exit"
  echo "=========================================="
  read -p "Enter your choice: " choice
  echo

  case $choice in
    1)
      python3 backend/utils/get_ip.py
      read -p "Press enter to continue..."
      ;;
    2)
      python3 server.py
      read -p "Press enter to continue..."
      ;;
    3)
      python3 -m backend.visualizer.generate_heatmap
      read -p "Press enter to continue..."
      ;;
    4)
      python3 -m backend.main
      read -p "Press enter to continue..."
      ;;
    5)
      source venv/bin/activate
      read -p "Virtual environment activated. Press enter to continue..."
      ;;
    6)
      pip3 install -r requirements.txt
      read -p "Libraries installed. Press enter to continue..."
      ;;
    7)
      echo "Exiting..."
      exit 0
      ;;
    *)
      echo "Invalid choice. Please try again."
      read -p "Press enter to continue..."
      ;;
  esac
done

# To run: 
# chmod +x backend_menu.sh
# ./backend_menu.sh
