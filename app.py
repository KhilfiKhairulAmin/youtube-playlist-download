import typer
from bs4 import BeautifulSoup
from rich.progress import Progress
from pathlib import Path
from datetime import datetime
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from pathlib import Path
from typing import List, Literal
from dotenv import load_dotenv
import os
import requests
from rich.progress import Progress


# Problem: The requests to Youtube doesn't get the correct HTML, therefore I will implement using selenium instead
# Avoiding errors, optimization, refactoring, documenting
# README documenting
# Future: Proper website documentation using GitHub pages, then finished! 


"""PART A: FUNCTIONS OTHER THAN TYPER CLI"""


load_dotenv()
APP_ENV = os.getenv("APP_ENV")


class Video:
  """Class to represent YouTube's video data.
  
  Example data:
      ```
  self.title   = "Mirareru Mirror feat. Kaai Yuki",
  self.channel = "namitape",
  self.link    = "https://www.youtube.com/watch?v=1vvhL81fsmg"
```
  """

  def __init__(self, title: str, channel: str, link: str):
    self.title = title
    self.channel = channel
    self.link = link


class Playlist:
  """Class to represent Playlist's data"""

  def __init__(self, name: str, videos: List[Video]):
    self.name = name
    self.videos = videos


def initialize_web_driver():
  """Create and return Chrome web driver"""

  # Configure web driver to ensure smooth process
  chrome_options = Options()
  chrome_options.add_argument("--disable-logging")
  chrome_options.add_argument("--log-level=3")
  if APP_ENV != "debug":
    chrome_options.add_argument("--headless") 
  
  return webdriver.Chrome(options=chrome_options)


def get_video(link: str) -> Video:
  """Get video data from URL"""
  pass



def parse_playlist_videos(html_content: str) -> Playlist:

  soup = BeautifulSoup(html_content, "html.parser")

  # Find the parent div containing all playlist links
  div = soup.find("div", { "id": "items", "class": "playlist-items style-scope ytd-playlist-panel-renderer"})
  raw_titles = div.find_all("span", { "id": "video-title", "class": "style-scope ytd-playlist-panel-video-renderer"})
  raw_ytchannels = div.find_all("span", { "id": "byline", "class": "style-scope ytd-playlist-panel-video-renderer" })
  raw_links = div.find_all("a")

  # Get playlist name
  h3 = soup.find("h3", { "class": "style-scope ytd-playlist-panel-renderer" })
  playlist_name = h3.find("a").text

  # Get all titles
  titles = []
  for t in raw_titles:
    titles.append(t.getText().strip())

  # Get all YT channels
  ytchannels = [] 
  for ytc in raw_ytchannels:
    ytchannels.append(ytc.getText().strip())

  # Remove duplicates or unrelated links from the raw links
  filtered_links = []
  for l in raw_links:
    if l.get("href", "") != "" and l["href"].find("https://www.youtube.com/watch?v=") != -1:
      parse_l = l["href"].split("&")[0]  # Grab only https://www.youtube.com/watch?v=some_id without any extra parameters
      if not (parse_l in filtered_links):
        filtered_links.append(parse_l)  

  # Store in Playlist class for ease of use
  videos: List[Video] = []
  for i in range(len(titles)):
    videos.append(Video(titles[i], ytchannels[i], filtered_links[i]))

  return Playlist(playlist_name, videos)


def get_playlist_videos(playlist_link: str) -> Playlist:
  """Parse all videos data from playlist"""

  # Open playlist link HTML
  response = requests.get(playlist_link)

  bs = BeautifulSoup(response.content, "html.parser")

  a = bs.find("a", { "id": "video-title", "class": "yt-simple-endpoint style-scope ytd-playlist-video-renderer" })
  first_video_link = a.get("href")

  response = requests.get(first_video_link)

  return parse_playlist_videos(response.content)


def get_playlist_videos_from_html(path_to_playlist_html: Path) -> Playlist:
  """Parse YouTube's playlist HTML file and return `titles`, `channels` & `links` from the playlist"""
  
  # Read HTML file
  with open(path_to_playlist_html, "r", encoding="utf-8") as f:
    content = f.read()

  return parse_playlist_videos(content)


def handle_video_download(video: Video, format: Literal["mp3", "mp4"], download_dir: Path, is_silent: bool=False):
  """Download single video in MP3/MP4 format"""

  # Create directory if it doesn't exist
  download_dir.mkdir(parents=True, exist_ok=True)

  driver = initialize_web_driver()

  # Open YTMP3 website
  driver.get("https://ytmp3.as/cyPH/")

  # Override download method inside the JS script to get the download link in Python
  driver.execute_script("""
    window.download = function (e, t, r, n) {
      window._downloadLink = e;
    };
  """)

  # Enter YT link in the input element
  link_input_box = driver.find_element(By.ID, "v")
  link_input_box.send_keys(video.link)

  # Press the submit button
  submit_button = driver.find_element(By.XPATH, "//button[2]")
  submit_button.click()

  # Wait until the download link has been created
  while not driver.execute_script("return window._downloadLink"):
    pass

  # Grab the download link
  download_link = driver.execute_script("return window._downloadLink")

  # Mimic browser behavior
  headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': '*/*',
    'Accept-Encoding': 'identity',  # Important for progress tracking
    'Connection': 'keep-alive',
  }

  response = requests.get(download_link, headers=headers, stream=True)
  response.raise_for_status()

  total_size = int(response.headers.get('content-length', 0))
  block_size = 1024  # 1 Kibibyte
  file_size = total_size / (1024*1024)

  download_path = os.path.join(download_dir, f"{video.title}.{format}")

  with open(download_path, 'wb') as file, Progress(disable=is_silent) as progressbar:
    task = progressbar.add_task(description=f'Downloading [yellow]{video.title} [white]by [green]{video.channel} [white]({file_size:.2f}MB)', total=total_size, visible=not is_silent)
    for data in response.iter_content(block_size):
      progressbar.update(task, advance=len(data))
      file.write(data)


def handle_playlist_download(playlist: Playlist, format: Literal["mp3", "mp4"], download_dir: Path, is_silent: bool=False):
  """Download all videos from playlist in MP3/MP4 format with progress bar"""

  for video in playlist:
    handle_video_download(video, format, download_dir, is_silent)


"""PART B: TYPER CLI"""


app = typer.Typer(help='A simple YouTube playlist downloader. Download songs and videos with ease through command-line interface.')
DEFAULT_DOWNLOAD_PATH = Path(f"saved/{str(datetime.today().now()).replace(":", "_")}")


@app.command()
def download(
  link: str = typer.Argument(
    ...,
    help="Link to video/playlist"
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
  format: str = typer.Option(
    "mp3",
    "--format",
    "-f",
    case_sensitive=False,
    show_choices=True,
    help="Format of the video"
  ),
  silent: bool = typer.Option(
    False,
    "--silent",
    "-s",
    help="Enabling this will hide the progress bar"
  )
):
  """Download video/playlist in MP3/MP4 format"""

  # Differentiate between video and playlist link
  if not ("playlist" in link):
    # Video link
    video = Video("", "", link)
    handle_video_download(video, format, download_dir, silent)
  else:
    # Playlist link
    playlist = get_playlist_videos(link)
    handle_playlist_download(playlist, format, download_dir, silent)


@app.command()
def download_mix(
  path_to_html: Path = typer.Argument(
    ...,
    exists=True,
    file_okay=True,
    dir_okay=False,
    readable=True,
    resolve_path=True,
    help="Source HTML file (download from YouTube mix page)"
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
  format: str = typer.Option(
    0,
    "--format",
    "-f",
    formats=["mp3", "mp4"],
    help='Format of the downloads'
  )
):
  """Download your mix in MP3/MP4 format

  PLEASE READ THIS!

  - Mix are personal playlists unique to you created by YouTube

  - To download mix, open your mix page on browser & save the page as HTML file (see Step below)

  - Step: Right-click on the page > 'Save as' > Save as type "Webpage, Complete"

  - Copy the path of the downloaded HTML file and re-run this command with it  
  """
  playlist_items = get_playlist_videos(path_to_html)

  # Start download process
  handle_playlist_download(playlist_items, download_dir, format)


if __name__ == "__main__":
  app()
