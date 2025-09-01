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
from typing import List
from dotenv import load_dotenv
import os
import requests
from rich.progress import Progress


"""PART A: FUNCTIONS OTHER THAN TYPER CLI"""


load_dotenv()
APP_ENV = os.getenv("APP_ENV")


class Playlist:
  """Class to represent playlist items data
  
  Example data:
      ```
[{
  "title": "Mirareru Mirror feat. Kaai Yuki",
  "channel": "namitape",
  "link": "https://www.youtube.com/watch?v=1vvhL81fsmg"
},
...]
```
  """

  def __init__(self, title, channel, link):
    self.title = title
    self.channel = channel
    self.link = link


def get_playlist_items(path_to_html: Path) -> List[Playlist]:
  """Parse YouTube's playlist HTML file and return `titles`, `channels` & `links` from the playlist

  Example return:
    ```
[{
  "title": "Mirareru Mirror feat. Kaai Yuki",
  "channel": "namitape",
  "link": "https://www.youtube.com/watch?v=1vvhL81fsmg"
},
...]
```
  """
  
  # Read HTML file
  with open(path_to_html, "r", encoding="utf-8") as f:
    content = f.read()

  soup = BeautifulSoup(content, "html.parser")

  # Find the parent div containing all playlist links
  div = soup.find("div", { "id": "items", "class": "playlist-items style-scope ytd-playlist-panel-renderer"})
  raw_titles = div.find_all("span", { "id": "video-title", "class": "style-scope ytd-playlist-panel-video-renderer"})
  raw_ytchannels = div.find_all("span", { "id": "byline", "class": "style-scope ytd-playlist-panel-video-renderer" })
  raw_links = div.find_all("a")

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
  playlist_items: List[Playlist] = []
  for i in range(len(titles)):
    playlist_items.append(Playlist(titles[i], ytchannels[i], filtered_links[i]))

  return playlist_items


def handle_download(playlist_items: List[Playlist], download_dir: Path, format: int):
  """Download videos/songs from playlist while displaying progress bar inside terminal"""

  # Create directory if it doesn't exist
  download_dir.mkdir(parents=True, exist_ok=True)

  # Configure web driver to ensure smooth process
  chrome_options = Options()
  chrome_options.add_argument("--disable-logging")
  chrome_options.add_argument("--log-level=3")
  chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
  chrome_options.add_argument('--disable-dev-shm-usage')
  chrome_options.add_argument('--no-sandbox')
  if APP_ENV != "debug":
    chrome_options.add_argument("--headless") 
  
  # Chrome web driver
  driver = webdriver.Chrome(options=chrome_options)

  for p in playlist_items:

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
    link_input_box.send_keys(p.link)

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

    download_path = os.path.join(download_dir, f"{p.title}.mp3")

    with open(download_path, 'wb') as file, Progress() as progressbar:
      task = progressbar.add_task(description=f'Downloading [yellow]{p.title} [white]by [green]{p.channel} [white]({file_size:.2f}MB)', total=total_size)
      for data in response.iter_content(block_size):
        progressbar.update(task, advance=len(data))
        file.write(data)


"""PART B: TYPER CLI"""


app = typer.Typer(help='A simple YouTube playlist downloader. Download songs and videos with ease through command-line interface.')
DEFAULT_DOWNLOAD_PATH = Path(f"downloads/{str(datetime.today().now()).replace(":", "_")}")


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

  playlist_items = get_playlist_items(path_to_html)

  # Start download process
  handle_download(playlist_items, download_dir, format)


if __name__ == "__main__":
  app()
