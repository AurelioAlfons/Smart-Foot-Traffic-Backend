import os
from rich.console import Console

console = Console()

def log_heatmap_duration(date_filter, time_filter, selected_type, season_filter, timings, start_time):
    total = timings["save"] - start_time
    durations = {
        "🧠 Weather assign":       timings["weather"]    - start_time,
        "🌡️ Temperature assign":   timings["temperature"] - timings["weather"],
        "📊 Data Fetch":           timings["fetch"]       - timings["temperature"],
        "🗺️ Map Render":           timings["render"]      - timings["fetch"],
        "💾 Save HTML":            timings["save"]        - timings["render"],
        "⏱️ Total Duration":       total
    }

    log_msg = (
        f"\n{'=' * 50}\n"
        f"📅 Date:    {date_filter}    🕒 Time: {time_filter or 'All'}\n"
        f"🚦 Type:    {selected_type}    🍂 Season: {season_filter or 'N/A'}\n"
        f"{'-' * 50}\n"
        + "\n".join(f"{label:<22} {seconds:>6.2f}s" for label, seconds in durations.items()) +
        f"\n{'=' * 50}\n"
    )

    console.print(log_msg)
    os.makedirs("logs", exist_ok=True)
    with open("logs/heatmap_profiling.log", "a", encoding="utf-8") as f:
        f.write(log_msg)

