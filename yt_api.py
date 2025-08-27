from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pathlib import Path
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

APP_ENV = os.getenv("APP_ENV")


def parse_ytlink_from_html(path_to_html: Path) -> List[str]:
  """Parse playlist links from YouTube's HTML file"""
  
  # Read HTML file
  with open(path_to_html, "r", encoding="utf-8") as f:
    content = f.read()

  soup = BeautifulSoup(content, "html.parser")

  # Find the parent div containing all playlist links
  div = soup.find("div", { "id": "items", "class": "playlist-items style-scope ytd-playlist-panel-renderer"})
  raw_links = div.find_all("a")

  # Remove duplicates or unrelated links from the raw links
  filtered_links = set()
  for l in raw_links:
    if l.get("href", "") != "" and l["href"].find("https://www.youtube.com/watch?v=") != -1:
      parse_l = l["href"].split("&")[0]  # Grab only https://www.youtube.com/watch?v=some_id without any extra parameters
      filtered_links.add(parse_l)
  
  return list(filtered_links)  # Note: this will mess up the order in which the links are originally. However, order is not important for now.


def download_ytlink(ytlinks: List[str], download_dir: Path, format: int):
  """Download the songs from YouTube playlist links"""

  # Setup Web Driver
  chrome_options = Options()

  # Browser setup
  prefs = {
    "download.default_directory": str(download_dir),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
  }
  chrome_options.add_experimental_option("prefs", prefs)
  chrome_options.add_argument("--disable-logging")
  chrome_options.add_argument("--log-level=3")
  if APP_ENV != "debug":
    chrome_options.add_argument("--headless") 

  # Browser driver initialization
  driver = webdriver.Chrome(options=chrome_options)

  # Open YTMP3 website
  driver.get("https://ytmp3.as/cyPH/")

  # Iterate through all links
  for link in ytlinks:
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

    WebDriverWait(driver, 1)

    driver.get("https://ytmp3.as/cyPH/")


if __name__ == "__main__":
  print("Run the application by executing `pthon app.py` in the terminal")
