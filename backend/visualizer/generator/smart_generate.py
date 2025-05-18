from rich.console import Console
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn
from backend.visualizer.generator.generate_heatmap import generate_heatmap
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

console = Console()

def get_all_hourly_times():
    return [f"{h:02}:00:00" for h in range(24)]

def smart_generate(date_filter, time_filter, traffic_type):
    # Step 1: Generate selected heatmap visibly
    generate_heatmap(date_filter, time_filter, traffic_type, quiet=False)

    # Step 2: Batch others in background with progress
    def batch_remaining():
        start = time.time()
        tasks = [(hour, traffic_type) for hour in get_all_hourly_times() if hour != time_filter]

        console.print(f"[yellow]⏳ Preloading {len(tasks)} heatmaps for {traffic_type} on {date_filter}...[/yellow]")

        with Progress(
            TextColumn("🔄 [bold cyan]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            console=console,
            transient=True  # 🔧 hides first blank line
        ) as progress:
            task_id = progress.add_task("Batch Progress", total=len(tasks))

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(generate_heatmap, date_filter, hour, traffic_type, True) for hour, _ in tasks]
                for _ in as_completed(futures):
                    progress.advance(task_id)

        console.print(f"[green]✅ All remaining {len(tasks)} heatmaps done in {int(time.time() - start)}s[/green]")

    Thread(target=batch_remaining, daemon=True).start()
