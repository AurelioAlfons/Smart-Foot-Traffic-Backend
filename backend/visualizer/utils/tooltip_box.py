# backend/visualizer/utils/tooltip_box.py

def generate_tooltip_html(location, traffic_type, count, datetime_string):
    return f"""
        <div style="
            font-size: 14px;
            font-weight: normal;
            line-height: 1.5;
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 10px 12px;
            background-color: white;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            width: 280px;
        ">
            <div style="font-weight: bold; margin-bottom: 6px;">{location}</div>
            <hr style="margin: 6px 0;">
            <div style="display: flex; justify-content: space-between;">
                <span><b>Type:</b></span> <span>{traffic_type}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span><b>Count:</b></span> <span>{count}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span><b>Time:</b></span> <span>{datetime_string}</span>
            </div>
        </div>
    """
