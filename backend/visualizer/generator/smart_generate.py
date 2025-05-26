import time
from threading import Thread, Lock
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn

from backend.visualizer.generator.generate_heatmap import generate_heatmap
from backend.visualizer.services.data_fetcher import fetch_traffic_data
from backend.forecast.weather import assign_weather
from backend.forecast.temperature import assign_temperature

console = Console()

# Global control variables
current_batch_id = 0
cached_data = {}              # {(date, time, type): DataFrame}
preprocessed_times = set()    # { "08:00:00", ... }
cache_lock = Lock()

def get_all_hourly_times():
    return [f"{h:02}:00:00" for h in range(24)]

# Caches traffic data (no weather/temp here)
def preprocess_heatmap_data(date_filter, time_filter, traffic_type):
    df = fetch_traffic_data(date_filter, time_filter, traffic_type)

    if df is not None and not df.empty:
        with cache_lock:
            cached_data[(date_filter, time_filter, traffic_type)] = df
            preprocessed_times.add(time_filter)

# Entry point for generating + background work
def smart_generate(date_filter, time_filter, traffic_type):
    global current_batch_id
    current_batch_id += 1
    batch_id = current_batch_id

    console.print("\n[bold magenta]========== HEATMAP GENERATION ==========[/bold magenta]")
    console.print(f"Date: [green]{date_filter}[/green]  Time: [green]{time_filter}[/green]  Type: [green]{traffic_type}[/green]")

    # Try to use cached data first
    cache_key = (date_filter, time_filter, traffic_type)
    with cache_lock:
        df = cached_data.get(cache_key)

    if df is not None and not df.empty:
        console.print(f"[green]Using cached data for {time_filter}[/green]")
    else:
        console.print(f"[yellow]No valid cache for {time_filter}, fetching...[/yellow]")
        df = fetch_traffic_data(date_filter, time_filter, traffic_type)

    # Generate the heatmap immediately
    generate_heatmap(date_filter, time_filter, traffic_type, quiet=False, df=df)
    console.print("[green]Heatmap generation completed.[/green]")

    # Background preprocessing thread
    def background_preprocessing():
        time.sleep(1.5)
        console.print("\n[bold magenta]=== Starting Background Preprocessing ===[/bold magenta]")

        try:
            with Progress(
                TextColumn("[bold cyan]Assigning Weather/Temp"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.0f}%",
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task_id = progress.add_task("Assigning Weather/Temp", total=2)

                assign_weather(date_filter)
                progress.advance(task_id)

                assign_temperature(date_filter)
                progress.advance(task_id)

            console.print(f"[green]Weather/temp assignment done for {date_filter}[/green]")

        except Exception as e:
            console.print(f"[red]Failed assigning weather/temp: {e}[/red]")
            return

        preprocessed_hours = []
        hours_to_process = [h for h in get_all_hourly_times() if h != time_filter]

        with Progress(
            TextColumn("[bold cyan]Caching traffic data"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            console=console,
            transient=True
        ) as progress:
            task_id = progress.add_task("Caching traffic data", total=len(hours_to_process))

            for hour in hours_to_process:
                if batch_id != current_batch_id:
                    console.print("[bold red]Preprocessing cancelled due to newer request.[/bold red]")
                    return

                key = (date_filter, hour, traffic_type)
                with cache_lock:
                    if key in cached_data:
                        progress.advance(task_id)
                        continue

                try:
                    df = fetch_traffic_data(date_filter, hour, traffic_type)
                    if df is not None and not df.empty:
                        with cache_lock:
                            cached_data[(date_filter, hour, traffic_type)] = df
                            preprocessed_times.add(hour)
                            preprocessed_hours.append(int(hour.split(":")[0]))
                except Exception:
                    pass  # skip logging errors to avoid clutter

                progress.advance(task_id)

        if preprocessed_hours:
            short_list = sorted(preprocessed_hours)
            console.print(f"[green]Preprocessed [bold]{traffic_type}[/bold] hours: {short_list}[/green]")

    Thread(target=background_preprocessing, daemon=True).start()
