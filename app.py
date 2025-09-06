# Built-in dependencies
import os                         # Handling file operations
import re                         # Filename curing (regex)
import time                       # Handling sleep (await)
from pathlib import Path          # Handling file operations
import datetime                   # Naming folders inside `saved` directory
from typing import List, Literal  # Type annotations

# External dependencies
import typer                                           # CLI tools
import requests                                        # Downloading files
from bs4 import BeautifulSoup                          # Parsing HTML
from selenium import webdriver                         # Simulating browser (access YTMP3 website)
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from rich import print                                 # Rich printing with color support
from rich.progress import Progress                     # Progress bar


"""PART A: BACKEND AND CLI-UI FUNCTIONS"""


DEBUG_MODE = False      # If set to True, Debug Mode will open webdriver without --headless-mode (browser will be visible)
DOWNLOAD_DIR = "saved"  # Default folder location for video downloads


def create_web_driver():
  """Create a new configured Chrome web driver for browsing"""

  # Connect to existing instance
  options = Options()

  if not DEBUG_MODE:
    options.add_argument("--headless")

  driver = webdriver.Chrome(options=options)

  return driver


def parse_video_id_from_link(link: str) -> str:
  """Parse video ID from link"""

  return link.split("=")[1].split("&")[0]


def parse_video_ids_from_playlist(playlist_link: str) -> List[str]:
  """Parse all video ids from playlist"""

  driver = create_web_driver()

  driver.get(playlist_link)  # Get playlist page
  time.sleep(1)              # Ensure YouTube has loaded properly
  
  bs = BeautifulSoup(driver.page_source, "html.parser")

  # Get all anchors
  anchors = bs.find_all("a", { "class": "yt-simple-endpoint style-scope ytd-playlist-video-renderer" })
  
  video_ids = []

  # Filter anchors for only related links to playlist
  for a in anchors:
    if "/watch?v=" in a.get("href"):
      video_ids.append(parse_video_id_from_link(a.get("href")))

  return video_ids


def parse_video_ids_from_html(path_to_playlist_html: Path) -> List[str]:
  """Parse all video ids from playlist in HTML file"""
  
  # Get HTML content
  with open(path_to_playlist_html, "r", encoding="utf-8") as f:
    content = f.read()

  soup = BeautifulSoup(content, "html.parser")

  # Find the parent div containing all playlist links
  div = soup.find("div", { "id": "items", "class": "playlist-items style-scope ytd-playlist-panel-renderer"})
  links = div.find_all("a")

  # Remove duplicates or unrelated links
  video_ids = []
  for l in links:
    if l.get("href", "") != "" and l["href"].find("https://www.youtube.com/watch?v=") != -1:
      parse_l = parse_video_id_from_link(l["href"])
      if not (parse_l in video_ids):
        video_ids.append(parse_l)  

  return video_ids


def download_videos(video_ids: List[str], format: Literal["mp3", "mp4"], download_dir: Path, is_silent: bool=False) -> None:
  """Download all videos from playlist in MP3/MP4 format with progress bar"""
  
  # Create directory if it doesn't exist
  download_dir.mkdir(parents=True, exist_ok=True)
  
  driver = create_web_driver()

  illegal_char_replacement_flag = False
  invalid_links = []

  for video_id in video_ids:
    if len(video_id) != 11:
      invalid_links.append(f"https://youtube.com/watch?v={video_id}")
      continue

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
      try:
        if driver.find_element(By.XPATH, "//button[1]"):
          break
      except:
        continue

    # Grab the download link
    download_link = driver.execute_script("return window._downloadLink")

    if not download_link:
      invalid_links.append(f"https://youtube.com/watch?v={video_id}")
      continue

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

    # Cure filename by replacing illegal characters with '_'
    filename = re.sub(r'[/\\*?"<>|:]', "_", title.strip())

    if is_silent and (not illegal_char_replacement_flag) and (filename != title.strip()):
      illegal_char_replacement_flag = True
      print("[chartreuse1]Note: [white]Illegal characters such as '([*?])' are replaced with '_' inside filenames")

    download_path = os.path.join(download_dir, f"{filename}.{format}")

    with open(download_path, 'wb') as file, Progress(disable=is_silent) as progressbar:
      task = progressbar.add_task(description=f'Downloading [yellow]{title} [white]({file_size:.2f}MB)', total=total_size, visible=not is_silent)
      for data in response.iter_content(block_size):
        progressbar.update(task, advance=len(data))
        file.write(data)

  # Display download summary
  print(f"\n[green]{len(video_ids) - len(invalid_links)} [white]videos downloaded successfully. [bright_red]{len(invalid_links)} [white]invalid links found.")
  "" if len(invalid_links) == 0 else print(f"\n[bright_red]Invalid links: [white]", end="")
  print(*invalid_links, sep=", ")


def get_next_folder_number() -> int:
  """Count the next number to be appended in default folder name in `saved` directory"""

  if not os.path.exists(DOWNLOAD_DIR):
    return 0
  
  folder_count = 0
  with os.scandir(DOWNLOAD_DIR) as entries:
    for entry in entries:
      if str(datetime.date.today()) in entry.name:  # Only append number if the folder's date is today
        folder_count += 1
  
  return folder_count


"""PART B: CLI INTEGRATION FUNCTION"""


app = typer.Typer(help='A simple YouTube playlist downloader. Download songs and videos with ease through command-line interface.')
DEFAULT_DOWNLOAD_DIR = Path(f"{DOWNLOAD_DIR}/{datetime.date.today()} #{str(get_next_folder_number())}")


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
    help="Format of the videos"
  ),
  is_silent: bool = typer.Option(
    False,
    "--silent",
    "-s",
    help="Enabling this will hide the progress bar"
  )
):
  """This app downloads videos/playlist from YouTube in MP3 and MP4 format"""

  video_ids = []

  print("\nParsing the video links...")

  # Determine whether input is a video link, playlist link or HTML file
  if ".html" in link_or_path:  # HTML file
    video_ids = parse_video_ids_from_html(link_or_path)

  elif "v=" in link_or_path:  # Video link
    video_ids.append(parse_video_id_from_link(link_or_path))

  elif "list=" in link_or_path:  # Playlist link
    video_ids = parse_video_ids_from_playlist(link_or_path)
  
  if len(video_ids) == 0:
    print("[bright_red]Invalid link or path")

  else:
    download_videos(video_ids, format, download_location, is_silent)


if __name__ == "__main__":
  app()


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
  # TODO Use only one browser instantiation to speed up process

