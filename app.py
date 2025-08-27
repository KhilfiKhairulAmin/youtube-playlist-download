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
num_of_links = 0
media_type = ""


def progress_ui():
  """Display download progress in the form of a dynamic progress bar"""

  await_event_set()  # 1st event for signalling download operation has started

  with Progress() as progress:
    task = progress.add_task(f"Downloading all {media_type}...", total=num_of_links)
    for _ in range(num_of_links):
      await_event_set()
      progress.update(task, advance=1)


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

  # Grab all links
  links = yt_api.parse_ytlink_from_html(path_to_html)

  # Make progress bar on standby for listening to download progress
  start_function(progress_ui)

  global num_of_links, media_type
  num_of_links = len(links)
  media_type = "song" if format == 0 else "video"
  media_type += "s" if num_of_links > 1 else ""

  # Start download process
  yt_api.download_ytlink(links, download_dir, format)


register_function(progress_ui)

if __name__ == "__main__":
  app()
