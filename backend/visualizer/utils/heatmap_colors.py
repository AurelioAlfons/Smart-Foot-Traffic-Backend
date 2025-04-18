# heatmap_colors.py

# 🎨 Gradient: Green → Yellow → Orange → Red → Deep Red
def get_color_by_count(count):
    if count > 8000:
        return "#3B0000"  # 🩸 Very Dark Red (extremely high traffic)
    elif count > 6000:
        return "#6D1A1A"  # 🩸 Deep Red
    elif count > 4000:
        return "#B71C1C"  # 🔴 Dark Red
    elif count > 3000:
        return "#C62828"  # 🔴 Strong Red
    elif count > 2500:
        return "#D84315"  # 🔴 Reddish-Orange
    elif count > 2000:
        return "#E64A19"  # 🟠 Red-Orange
    elif count > 1500:
        return "#F4511E"  # 🟠 Orange-Red
    elif count > 1200:
        return "#FF5722"  # 🟠 Bright Orange
    elif count > 1000:
        return "#FF7043"  # 🟠 Soft Red-Orange
    elif count > 900:
        return "#FF8A65"  # 🟧 Light Orange
    elif count > 750:
        return "#FFA726"  # 🟧 Orange
    elif count > 600:
        return "#FFCA28"  # 🟡 Yellow-Orange
    elif count > 450:
        return "#FFD54F"  # 🟡 Bright Yellow
    elif count > 300:
        return "#FFE082"  # 🟡 Pale Yellow
    elif count > 200:
        return "#FFF176"  # 🟡 Very Light Yellow
    elif count > 120:
        return "#DCE775"  # 🟡 Yellow-Green
    elif count > 70:
        return "#AED581"  # 🟢 Light Green
    elif count > 30:
        return "#81C784"  # 🟢 Mid Green
    elif count > 0:
        return "#66BB6A"  # 🟢 Dark Green
    else:
        return "#E0E0E0"  # ⚪ No Data (gray)
