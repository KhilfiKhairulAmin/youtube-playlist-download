import typer
from bs4 import BeautifulSoup
import yt_api
from pathlib import Path
from datetime import datetime



app = typer.Typer(help='A simple YouTube playlist downloader. Download songs and videos with ease through command-line interface.')

datetime_str = str(datetime.today().now()).replace(":", "_")
DEFAULT_DOWNLOAD_PATH = Path(f"downloads/{datetime_str}")

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

  # Start download process
  yt_api.download_ytlink(links, download_dir, format)


if __name__ == "__main__":
  app()

