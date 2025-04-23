def get_color_by_count(count):
    # 🔴 Red Zone (Warmest → Deepest)
    if count > 600:
        return "#800000"  # 🟥 Deepest Dark Red
    elif count > 550:
        return "#8B0000"  # 🟥 Very Dark Red
    elif count > 500:
        return "#990000"  # 🟥 Dark Red
    elif count > 475:
        return "#A60000"  # 🟥 Rich Crimson
    elif count > 450:
        return "#B30000"  # 🔴 Strong Red
    elif count > 425:
        return "#BF0000"  # 🔴 Bold Red
    elif count > 400:
        return "#e30015"  # 🔴 Clear Red
    elif count > 375:
        return "#e90000"  # 🔴 Bright Red
    elif count > 350:
        return "#F20000"  # 🔴 Intense Red
    elif count > 325:
        return "#FF0033"  # 🔴 Light-Intense Red
    elif count > 300:
        return "#FF0033"  # 🔴 Light Red
    elif count > 180:
        return "#FF3333"  # 🔴 Soft Red

    # 🌸 Pink Zone (Red-Pink Blend)
    elif count > 170:
        return "#ff174b"  # 🌺 Vivid Red-Pink
    elif count > 160:
        return "#FF1A4D"  # 🌺 Deep Pink-Red
    elif count > 150:
        return "#FF2E5A"  # 🌺 Mid Coral Pink
    elif count > 140:
        return "#FF4470"  # 🌸 Rose Pink
    elif count > 130:
        return "#FF5A85"  # 🌸 Blush Pink
    elif count > 120:
        return "#FF7F7A"  # 🌸 Light Coral Pink

    # 🟧 Orange Zone (Bright & Bold)
    elif count > 110:
        return "#FF6600"  # 🟧 Dark Orange
    elif count > 100:
        return "#FF751A"  # 🟧 Bold Orange
    elif count > 90:
        return "#FFAE33"  # 🟧 Medium Orange
    elif count > 85:
        return "#FEB001"  # 🟧 Bright Golden Orange
    elif count > 80:
        return "#FFB101"  # 🟧 Soft Golden Orange

    # 🟨 Yellow Zone (Warm → Pale)
    elif count > 65:
        return "#FFCC00"  # 🟨 Strong Yellow
    elif count > 55:
        return "#FFD200"  # 🟨 Bright Yellow
    elif count > 50:
        return "#FFC133"  # 🟨 Light Orange-Yellow
    elif count > 40:
        return "#FFC000"  # 🟨 Golden Yellow
    elif count > 30:
        return "#FFD000"  # 🟨 Yellow-Gold
    elif count > 20:
        return "#FFDF00"  # 🟨 Soft Yellow-Gold
    elif count > 10:
        return "#FFE800"  # 🟨 Light Yellow
    elif count > 1:
        return "#FFEA00"  # 🟨 Faint Yellow

    else:
        return "#E0E0E0"  # ⚪ No Data (Neutral Gray)
