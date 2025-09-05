import time
import typer
from bs4 import BeautifulSoup
from rich.progress import Progress
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from pathlib import Path
from typing import List, Literal
import os
import requests
from rich.progress import Progress
import datetime
from typer.testing import CliRunner
import re
from rich import print

"""
GOALS
1. Make a CLI tool for downloading YouTube videos, playlists and mix
2. Make it works well and highly stable (error-free) (Do a lot of tests! Note for error (breaking) points!)
3. Make a good code with informative comments and easy to understand codes for my TikTok viewers
4. Make a video about this app as my infienite DevVlog...
"""

# Problem: The requests to Youtube doesn't get the correct HTML, therefore I will implement using selenium instead
# Avoiding errors, optimization, refactoring, documenting
# README documenting
# Future: Proper website documentation using GitHub pages, then finished! 
# https://regex101.com/r/Wbynx0/1
# https://regex101.com/r/vEJAHv/1
"""Today (3 Sep 25)
I've done more research than coding my program.
However, the coding has been very effective, I've removed (simplified) most of my codes, which reduce the size and complexity of this program, making it easier to sustain and more readable
Next, I've tested a lot of stuff regarding youtube's html, and found all the solutions for each cases involving html download from browser for private playlist and mix. I also may find faster method to download a public playlist such that makes it more efficient 
"""

# TODO Browser (or YouTube) didn't load well causing no links to be found 

"""PART A: FUNCTIONS OTHER THAN TYPER CLI"""


APP_ENV = "debug"
DOWNLOAD_DIR = "saved"


def cure_filename(filename: str) -> str:
  """Replace all illegal characters inside filename with legal characters"""
  return re.sub(r'[/\\*?"<>|:]', "_", filename.strip())


def parse_video_id_from_link(link):
  """Parse video ID from link"""
  return link.split("=")[1][:12]


def parse_video_ids_from_playlist(playlist_link: str):
  """Parse all videos data from playlist"""

  # Configure web driver to ensure smooth process
  chrome_options = Options()

  if APP_ENV != "debug":
    chrome_options.add_argument("--headless")

  chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
  chrome_options.add_argument("--disable-logging")
  chrome_options.add_argument("--log-level=3")
  
  driver = webdriver.Chrome(options=chrome_options)

  driver.get(playlist_link)
  time.sleep(1)  # Ensure YouTube has loaded properly
  
  bs = BeautifulSoup(driver.page_source, "html.parser")

  # Find the parent div containing all playlist links
  anchors = bs.find_all("a", { "class": "yt-simple-endpoint style-scope ytd-playlist-video-renderer" })
  video_ids = []
  
  for a in anchors:
    if "/watch?v=" in a.get("href"):
      video_ids.append(parse_video_id_from_link(a.get("href")))

  return video_ids


def parse_video_ids_from_html(path_to_playlist_html: Path):
  """Parse YouTube's playlist HTML file and return `titles`, `channels` & `links` from the playlist"""
  
  # Read HTML file
  with open(path_to_playlist_html, "r", encoding="utf-8") as f:
    content = f.read()

  soup = BeautifulSoup(content, "html.parser")
  # TODO Use only one browser instantiation to speed up process
  # Find the parent div containing all playlist links
  div = soup.find("div", { "id": "items", "class": "playlist-items style-scope ytd-playlist-panel-renderer"})
  raw_links = div.find_all("a")

  # Remove duplicates or unrelated links from the raw links
  links = []
  for l in raw_links:
    if l.get("href", "") != "" and l["href"].find("https://www.youtube.com/watch?v=") != -1:
      parse_l = parse_video_id_from_link(l["href"])  # Grab only video id
      if not (parse_l in links):
        links.append(parse_l)  

  return links


def download_videos(video_ids: List[str], format: Literal["mp3", "mp4"], download_dir: Path, is_silent: bool=False):
  """Download all videos from playlist in MP3/MP4 format with progress bar"""
  
  # Create directory if it doesn't exist
  download_dir.mkdir(parents=True, exist_ok=True)

  # Configure web driver to ensure smooth process
  chrome_options = Options()
  chrome_options.add_argument("--disable-logging")
  chrome_options.add_argument("--log-level=3")
  if APP_ENV != "debug":
    chrome_options.add_argument("--headless")
  chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
  
  driver = webdriver.Chrome(options=chrome_options)

  illegal_char_replacement_flag = False

  for video_id in video_ids:

    # Open YTMP3 website
    driver.get("https://ytmp3.as/cyPH/")

    is_mp3 = format.lower() == "mp3"

    if is_mp3:
      # Override download method inside the JS script to get the download link in Python
      driver.execute_script("""
        window.download = function (e, t, r, n) {
          window._downloadLink = e;
          window._title = n;
        };
      """)
    else:
      driver.execute_script("""
        window.download = function (e, t, r, n) {
          window._downloadLink = e;
        };
      """)

    # Enter YT link in the input element
    link_input_box = driver.find_element(By.ID, "v")
    link_input_box.send_keys(f"https://youtube.com/watch?v={video_id}")

    # Press the submit button
    format_button = driver.find_element(By.XPATH, "//button[1]")  # Default: MP3

    if not is_mp3:
      format_button.click()  # Change to MP4 by clicking

    # Press the convert button
    convert_button = driver.find_element(By.XPATH, "//button[2]")
    convert_button.click()

    # Wait until the download link has been created
    while not driver.execute_script("return window._downloadLink"):
      pass

    # Grab the download link
    download_link = driver.execute_script("return window._downloadLink")

    title = ""
    if is_mp3:
      title = driver.execute_script("return window._title")
    else:
      title = driver.find_element(By.XPATH, "//form/div[1]").text

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

    filename = cure_filename(title)

    if (not illegal_char_replacement_flag) and (filename != title.strip()):
      illegal_char_replacement_flag = True
      print("[chartreuse1]Note: [white]Illegal characters such as '([*?])' are replaced with '_' inside filenames")

    download_path = os.path.join(download_dir, f"{filename}.{format}")

    with open(download_path, 'wb') as file, Progress(disable=is_silent) as progressbar:
      task = progressbar.add_task(description=f'Downloading [yellow]{title} [white]({file_size:.2f}MB)', total=total_size, visible=not is_silent)
      for data in response.iter_content(block_size):
        progressbar.update(task, advance=len(data))
        file.write(data)


def count_folder_today() -> int:
  """Count the number of folders created today inside `saved` directory"""

  if not os.path.exists(DOWNLOAD_DIR):
    return 0
  
  folder_count = 0
  with os.scandir(DOWNLOAD_DIR) as entries:
    for entry in entries:
      if str(datetime.date.today()) in entry.name:
        folder_count += 1
  
  return folder_count


"""PART B: TYPER CLI"""


app = typer.Typer(help='A simple YouTube playlist downloader. Download songs and videos with ease through command-line interface.')
DEFAULT_DOWNLOAD_DIR = Path(f"{DOWNLOAD_DIR}/{datetime.date.today()} #{str(count_folder_today())}")


@app.command()
def download(
  link_or_path: str = typer.Argument(
    ...,
    help="Link to video/playlist OR path to saved HTML"
  ),
  download_location: Path = typer.Argument(
    DEFAULT_DOWNLOAD_DIR,
    exists=False,
    file_okay=False,
    dir_okay=True,
    writable=True,
    resolve_path=True,
    help="Directory to save the file"
  ),
  format: str = typer.Option(
    "mp3",
    "--format",
    "-f",
    case_sensitive=False,
    show_choices=True,
    help="Format of the video"
  ),
  is_silent: bool = typer.Option(
    False,
    "--silent",
    "-s",
    help="Enabling this will hide the progress bar"
  )
):
  """Download video/playlist in MP3/MP4 format"""

  # Determine whether input is a link or HTML

  video_ids = []

  if ".html" in link_or_path:

    # Is HTML
    video_ids = parse_video_ids_from_html(link_or_path)

  elif "v=" in link_or_path:

    video_ids.append(parse_video_id_from_link(link_or_path))

  elif "list=" in link_or_path:
    
    video_ids = parse_video_ids_from_playlist(link_or_path)
    
  if len(video_ids) == 0:

    typer.echo("Invalid link or path")

  else:

    download_videos(video_ids, format, download_location, is_silent)


if __name__ == "__main__":
  app()
