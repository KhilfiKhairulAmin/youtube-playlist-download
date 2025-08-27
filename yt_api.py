from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.remote_connection import LOGGER
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from yt_event import *
import os
import logging

load_dotenv()

APP_ENV = os.getenv("APP_ENV")

def parse_ytlink_from_html(path_to_html: Path) -> List[dict]:
  """Parse playlist links from YouTube's HTML file"""
  
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

  # Store in dictionary/JSON-like structure for ease of use
  playlist_items = []
  for i in range(len(titles)):
    playlist_items.append({
      "title": titles[i],
      "channel": ytchannels[i],
      "link": filtered_links[i]
    })

  return playlist_items


def download_ytlink(playlist_items: List[dict], download_dir: Path, format: int):
  """Download the songs from YouTube playlist links"""


  # Setup Web Driver
  chrome_options = Options()

  # Suppress selenium logging
  logging.getLogger('selenium').setLevel(logging.WARNING)
  logging.getLogger('urllib3').setLevel(logging.WARNING)

  # Browser setup
  prefs = {
    "download.default_directory": str(download_dir),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    'excludeSwitches': ['enable-logging']  # disable logging completely from selenium
  }

  chrome_options.add_experimental_option("prefs", prefs)
  chrome_options.add_argument("--disable-logging")
  chrome_options.add_argument("--log-level=3")
  chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
  chrome_options.add_argument('--disable-dev-shm-usage')
  chrome_options.add_argument('--no-sandbox')
  if APP_ENV != "debug":
    chrome_options.add_argument("--headless") 
    

  # Browser driver initialization
  driver = webdriver.Chrome(options=chrome_options)

  # Open YTMP3 website
  driver.get("https://ytmp3.as/cyPH/")

  # Clear log message produced by selenium
  print("\u001b[1A")
  print("\u001b[K")

  # Signal progress bar that download process is preparing to download
  signal_event()

  # Iterate through all links
  for item in playlist_items:
    link_input_box = driver.find_element(By.ID, "v")
    link_input_box.send_keys(item["link"])

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

    signal_event()  # Signal event song download progress +1

    WebDriverWait(driver, 1)

    driver.get("https://ytmp3.as/cyPH/")

  WebDriverWait(driver, 5)


register_function(download_ytlink)

if __name__ == "__main__":
  print("Run the application by executing `pthon app.py` in the terminal")
