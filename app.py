import typer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime

app = typer.Typer(help='A simple YouTube playlist downloader. Download songs and videos with ease through command-line interface.')

datetime_str = str(datetime.today().now()).replace(":", "_")
DEFAULT_DOWNLOAD_PATH = Path(f"downloads/{datetime_str}")

@app.command()
def download(
  source_html: Path = typer.Argument(
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
  
  # Create a new directory at the given paths
  download_dir.mkdir(parents=True, exist_ok=True)

  # Setup Web Driver
  chrome_options = Options()

  prefs = {
    "download.default_directory": str(download_dir),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
  }

  chrome_options.add_experimental_option("prefs", prefs)
  chrome_options.add_argument("--disable-logging")
  chrome_options.add_argument("--log-level=3")
  # chrome_options.add_argument("--headless")

  driver = webdriver.Chrome(options=chrome_options)

  # Grab the links from the playlist item
  with open(source_html, "r", encoding="utf-8") as f:
    content = f.read()

  soup = BeautifulSoup(content, "html.parser")

  div = soup.find("div", { "id": "items", "class": "playlist-items style-scope ytd-playlist-panel-renderer"})
  raw_links = div.find_all("a")

  # Parse and filter unrelated links
  filtered_links = set()
  i = 0

  for l in raw_links:
    if l.get("href", "") != "" and l["href"].find("https://www.youtube.com/watch?v=") != -1:
      parse_l = l["href"].split("&")[0]
      if not parse_l in filtered_links:
        i += 1
        filtered_links.add(parse_l)

  # Download the songs/videos from the playlist
  driver.get("https://ytmp3.as/cyPH/")

  for link in filtered_links:
    link_input_box = driver.find_element(By.ID, "v")
    link_input_box.send_keys(link)

    submit_button = driver.find_element(By.XPATH, "//button[2]")
    submit_button.click()

    download_button = None

    while True:
      download_button = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//button[1]"))
      )
      break

    download_button.click()

    div_song_title = driver.find_element(By.XPATH, "//form[1]/div[1]")
    song_title = div_song_title.text

    # self.song_names.append(song_title)
    # event.set()
    # event.clear()
    # cur_num_text = "(" + str(j) + "/" + str(self.get_total_songs()) + ")"
    # print(cur_num_text + " Downloading " + col.yellow(song_title) + " ...")

    j += 1 

    WebDriverWait(driver, 1)

    driver.get("https://ytmp3.as/cyPH/")

  # print("Finishing all downloads...")
  # sleep(5)
  # event.set()
  # driver.quit()
  # print("Time elapsed: " + str(time() - before) + " second(s)")
  # print(col.green("All songs downloaded! Go to " + download_dir + " to listen to the songs!"))

if __name__ == "__main__":
  app()

