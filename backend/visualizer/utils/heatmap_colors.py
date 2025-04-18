# heatmap_colors.py

# 🎨 Color mapping based on count threshold
def get_color_by_count(count):
    if count > 900:
        return "#A23BEC"  # 🟣 Reddish Purple (softer)
    elif count >= 850:
        return "#C965E9"  # 🟣 Lighter Red-Purple
    elif count >= 800:
        return "#DB70E3"  # 🟣 Light Red-Purple
    elif count >= 750:
        return "#B22222"  # 🔴 Firebrick
    elif count >= 701:
        return "#C62828"  # 🔴 Strong Red
    elif count >= 660:
        return "#E53935"  # 🔴 Mid Red
    elif count >= 620:
        return "#F44336"  # 🔴 Bright Red
    elif count >= 590:
        return "#FF5252"  # 🔴 Light Red
    elif count >= 560:
        return "#FF6E6E"  # 🔴 Soft Red
    elif count >= 530:
        return "#FF7A7A"  # 🔴 Rose Red
    elif count >= 500:
        return "#FF8A65"  # 🟧 Red-Orange
    elif count >= 470:
        return "#FF7043"  # 🟧 Rich Orange
    elif count >= 440:
        return "#FF5722"  # 🟧 Deep Orange
    elif count >= 410:
        return "#FF6F00"  # 🟧 Darker Amber
    elif count >= 370:
        return "#FF8C42"  # 🟧 Dark Orange
    elif count >= 330:
        return "#FFA500"  # 🟧 Orange
    elif count >= 290:
        return "#FFB347"  # 🟧 Light Orange
    elif count >= 250:
        return "#FFD180"  # 🟧 Soft Peach
    elif count >= 210:
        return "#FFD700"  # 🟡 Dark Yellow
    elif count >= 160:
        return "#FFFF00"  # 🟡 Yellow
    elif count >= 120:
        return "#FFFF66"  # 🟡 Light Yellow
    elif count >= 70:
        return "#ADFF2F"  # 🟢 Yellow-Green
    elif count >= 40:
        return "#99FF99"  # 🟩 Light Green
    elif count >= 11:
        return "#CCFFCC"  # 🟩 Very Light Green
    elif count >= 1:
        return "#E5FFE5"  # 🟩 Faintest Green
    else:
        return "#F0F0F0"  # ⚪ No Data
