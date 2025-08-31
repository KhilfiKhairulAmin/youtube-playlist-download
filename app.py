import typer
from bs4 import BeautifulSoup
from yt_event import *
import yt_api
from rich.progress import Progress
from pathlib import Path
from datetime import datetime

# Main application
app = typer.Typer(help='A simple YouTube playlist downloader. Download songs and videos with ease through command-line interface.')

# GLOBAL VARIABLES
DEFAULT_DOWNLOAD_PATH = Path(f"downloads/{str(datetime.today().now()).replace(":", "_")}")
playlist_items = []
media_type = ""


def progress_ui():
  """Display download progress in the form of a dynamic progress bar"""

  await_event_set()  # 1st event for signalling download operation has started

  with Progress() as progress:
    num_of_item = len(playlist_items)
    task = progress.add_task(f"Preparing download sequence", total=num_of_item)
    for item in playlist_items:
      await_event_set()
      progress.update(task, advance=1, description=f"Now: [yellow]{item["title"]}")
    progress.update(task, description="Finishing downloads...")

    await_event_set()

    progress.update(task, description="[green]Complete!")

  
@app.command()
def download(
  path_to_html: Path = typer.Argument(
    ...,
    exists=True,
    file_okay=True,
    dir_okay=False,
    readable=True,
    resolve_path=True,
    help="Source HTML file (download from YouTube playlist page)"
  ),
  download_dir: Path = typer.Argument(
    DEFAULT_DOWNLOAD_PATH,
    exists=False,
    file_okay=False,
    dir_okay=True,
    writable=True,
    resolve_path=True,
    help="Directory to download the playlist"
  ),
  format: int = typer.Option(
    0,
    "--format",
    "-f",
    min=0,
    max=1,
    help="Format of the downloads:\n[0] MP3\n[1] MP4"
  )
):
  """Download YouTube playlist items in MP3 or MP4"""
  
  # Create folders at path if it doesn't exist
  download_dir.mkdir(parents=True, exist_ok=True)

  # Make progress bar on standby for listening to download progress
  start_function(progress_ui)

  # Grab all links
  global playlist_items
  playlist_items = yt_api.parse_ytlink_from_html(path_to_html)

  # Start download process
  yt_api.download_ytlink(playlist_items, download_dir, format)


register_function(progress_ui)

if __name__ == "__main__":
  app()
