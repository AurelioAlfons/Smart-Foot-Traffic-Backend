# ======================================
# Get Local Wi-Fi IP Address
# --------------------------------------
# - Finds your computer's IP on the local network (e.g. 192.168.x.x)
# - Useful for testing server access from phone/devices
# - Just run this file to see your IP
# ======================================

import socket

def get_local_ip():
    try:
        # Connect to a common external address (Google DNS), no data actually sent
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return f"Error getting IP: {e}"

if __name__ == "__main__":
    ip = get_local_ip()
    print(f"📡 Your local Wi-Fi IP address is: {ip}")

# To run => python get_ip.py
