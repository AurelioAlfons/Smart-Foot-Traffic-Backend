import time
from threading import Thread, Lock
from rich.console import Console

from backend.visualizer.generator.generate_heatmap import generate_heatmap
from backend.visualizer.services.data_fetcher import fetch_traffic_data
from backend.forecast.weather import assign_weather
from backend.forecast.temperature import assign_temperature

console = Console()

# 🔄 Global control variables
current_batch_id = 0
cached_data = {}              # {(date, time, type): DataFrame}
preprocessed_times = set()    # { "08:00:00", ... }
cache_lock = Lock()

def get_all_hourly_times():
    return [f"{h:02}:00:00" for h in range(24)]

def preprocess_heatmap_data(date_filter, time_filter, traffic_type):
    assign_weather(date_filter)
    assign_temperature(date_filter)

    df = fetch_traffic_data(date_filter, time_filter, traffic_type)

    if df is not None and not df.empty:
        with cache_lock:
            cached_data[(date_filter, time_filter, traffic_type)] = df
            preprocessed_times.add(time_filter)
    else:
        console.print(f"[red]⚠️ No data to cache for {time_filter}[/red]")

def smart_generate(date_filter, time_filter, traffic_type):
    global current_batch_id
    current_batch_id += 1
    batch_id = current_batch_id

    cache_key = (date_filter, time_filter, traffic_type)
    with cache_lock:
        df = cached_data.get(cache_key)

    if df is not None and not df.empty:
        console.print(f"[green]⚡ Using cached data for {time_filter}[/green]")
    else:
        console.print(f"[yellow]🔄 No valid cache for {time_filter}, refetching...[/yellow]")
        df = fetch_traffic_data(date_filter, time_filter, traffic_type)

    generate_heatmap(date_filter, time_filter, traffic_type, quiet=False, df=df)

    # Background preprocess
    def background_preprocessing():
        time.sleep(1.5)
        preprocessed_hours = []

        for hour in get_all_hourly_times():
            if hour == time_filter:
                continue
            if batch_id != current_batch_id:
                console.print("[red]🚫 Preprocessing cancelled (new request).[/red]")
                return

            key = (date_filter, hour, traffic_type)
            with cache_lock:
                if key in cached_data:
                    continue

            try:
                preprocess_heatmap_data(date_filter, hour, traffic_type)
                hour_int = int(hour.split(":")[0])
                preprocessed_hours.append(hour_int)
            except Exception as e:
                console.print(f"[red]❌ Failed to preprocess {hour}:[/red] {e}")

        if preprocessed_hours:
            console.print(f"\nPreprocessed {traffic_type}:\n{preprocessed_hours}")
        if 0 not in preprocessed_hours:
            console.print("⚠️ Skipped hour: 00")

        console.print("[green]✅ All times preprocessed and cached.[/green]")

    Thread(target=background_preprocessing, daemon=True).start()
