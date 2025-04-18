def get_color_by_count(count):
    if count > 8000:
        return "#3B0000"  # 🩸 Extremely high traffic - Very Dark Red
    elif count > 7500:
        return "#420000"  # 🩸 Deeper Maroon
    elif count > 7000:
        return "#4B0000"  # 🩸 Deep Maroon
    elif count > 6500:
        return "#540000"  # 🩸 Rich Dark Red
    elif count > 6000:
        return "#5C0000"  # 🩸 Deep Crimson
    elif count > 5500:
        return "#640000"  # 🔴 Strong Crimson
    elif count > 5000:
        return "#6D0000"  # 🔴 Deep Red
    elif count > 4500:
        return "#760000"  # 🔴 Bold Red
    elif count > 4000:
        return "#7E0000"  # 🔴 Darker Red
    elif count > 3600:
        return "#850808"  # 🔴 Red-Blood
    elif count > 3200:
        return "#8F0000"  # 🔴 Bold Red
    elif count > 2900:
        return "#991111"  # 🔴 Sharp Red
    elif count > 2600:
        return "#9F1A1A"  # 🔴 Strong Reddish Tone
    elif count > 2400:
        return "#A42222"  # 🔴 Mid Red
    elif count > 2200:
        return "#AF2B2B"  # 🔴 Slightly Muted Red
    elif count > 2000:
        return "#B93333"  # 🔴 Brightening Red
    elif count > 1800:
        return "#BF3C3C"  # 🔴 Mid Reddish-Orange
    elif count > 1650:
        return "#C54444"  # 🔴 Transitioning Red-Orange
    elif count > 1500:
        return "#CF4D4D"  # 🔴 Soft Red
    elif count > 1350:
        return "#D55555"  # 🟠 Reddish-Orange Blend
    elif count > 1200:
        return "#DF5E5E"  # 🟠 Red-Orange Blend
    elif count > 1100:
        return "#E76666"  # 🟠 Light Red-Orange
    elif count > 1000:
        return "#EF6F6F"  # 🟠 Orange-Red Edge
    elif count > 950:
        return "#F57766"  # 🟠 Deeper Orange-Red
    elif count > 900:
        return "#FF7F7F"  # 🟠 Light Red-Tint
    elif count > 875:
        return "#FF8366"  # 🟠 Soft Orange-Red
    elif count > 850:
        return "#FF8666"  # 🟠 Orange-Red
    elif count > 825:
        return "#FF8A66"  # 🟠 Bold Orange
    elif count > 800:
        return "#FF8F66"  # 🟠 Deep Orange
    elif count > 775:
        return "#FF944C"  # 🟠 Mid Orange
    elif count > 750:
        return "#FF984C"  # 🟠 Warm Orange
    elif count > 725:
        return "#FFA033"  # 🟠 Slight Yellow-Orange
    elif count > 700:
        return "#FFA133"  # 🟠 Warm Orange
    elif count > 675:
        return "#FFA82A"  # 🟠 Rich Orange
    elif count > 650:
        return "#FFAA2A"  # 🟠 Yellow-Orange
    elif count > 625:
        return "#FFAD1A"  # 🟠 Orange-Gold
    elif count > 600:
        return "#FFB31A"  # 🟠 Light Orange
    elif count > 550:
        return "#FFBF1A"  # 🟡 Yellow-Orange
    elif count > 500:
        return "#FFCC00"  # 🟡 Dark Yellow
    elif count > 450:
        return "#FFDD00"  # 🟡 Yellow Gold
    elif count > 400:
        return "#FFEB33"  # 🟡 Bright Yellow
    elif count > 350:
        return "#FFF066"  # 🟡 Soft Yellow
    elif count > 300:
        return "#FFF599"  # 🟡 Faint Yellow
    elif count > 250:
        return "#FFFACB"  # 🟡 Very Pale Yellow
    elif count > 200:
        return "#F0F9A3"  # 💚 Yellow-Green Tint
    elif count > 170:
        return "#E0F683"  # 💚 Faint Green-Yellow
    elif count > 140:
        return "#D0F363"  # 💚 Light Lime
    elif count > 110:
        return "#C0F043"  # 💚 Light Green
    elif count > 90:
        return "#B0ED33"  # 💚 Soft Green
    elif count > 75:
        return "#A0EA29"  # 🟢 Light Green
    elif count > 60:
        return "#90E720"  # 🟢 Grass Green
    elif count > 45:
        return "#80E416"  # 🟢 Mid Green
    elif count > 30:
        return "#70E10D"  # 🟢 Slightly Darker
    elif count > 20:
        return "#60DE05"  # 🟢 Rich Green
    elif count > 10:
        return "#50DB00"  # 🟢 Vibrant Green
    elif count > 5:
        return "#40C000"  # 🟢 Dark Green
    elif count > 3:
        return "#30A000"  # 🟢 Deep Forest Green
    elif count > 2:
        return "#208000"  # 🟢 Faint Green
    elif count > 1:
        return "#106000"  # 🟢 Minimal Green
    elif count == 1:
        return "#004000"  # 🟢 Smallest Positive
    else:
        return "#E0E0E0"  # ⚪ No Data (gray)