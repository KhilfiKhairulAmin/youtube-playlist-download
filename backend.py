"""
This is the backend for song downloads
"""

import threading
from time import sleep, time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from Colors import Colors as col

"""
1. Scan all links for total songs
2. Progress bar updates
"""

class Backend:
  def __init__(self, html_filepath):
    with open(html_filepath, "r", encoding="utf-8") as f:
      content = f.read()

    self.soup = BeautifulSoup(content, "html.parser")

    div = self.soup.find("div", { "id": "items", "class": "playlist-items style-scope ytd-playlist-panel-renderer"})
    anchors = div.find_all("a")
    duplicate_tracker = set()
    i = 0

    for a in anchors:
      if a.get("href", "") != "" and a["href"].find("https://www.youtube.com/watch?v=") != -1:
        parse_a = a["href"].split("&")[0]
        if not parse_a in duplicate_tracker:
          i += 1
          print(parse_a)
          duplicate_tracker.add(parse_a)

    self.song_links = list(duplicate_tracker)
    print("Total Songs: " + col.yellow(str(len(self.song_links))))
  
  def get_total_songs(self):
    return len(self.song_links)
  
  def get_current_song(self):
    return self.song_names[-1]

  def download_songs(self, download_dir, event: threading.Event=None):
    self.song_names = []
    chrome_options = Options()

    prefs = {
      "download.default_directory": download_dir,
      "download.prompt_for_download": False,
      "download.directory_upgrade": True,
      "safebrowsing.enabled": True
    }

    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)
    j = 1

    try:
        driver.get("https://ytmp3.as/cyPH/")
        print("Download location: " + col.yellow(download_dir))
        print("Preparing installer...")
        before = time()
        for link in self.song_links:
          link_input_box = driver.find_element(By.ID, "v")
          link_input_box.send_keys(link)

          submit_button = driver.find_element(By.XPATH, "//button[2]")
          submit_button.click()

          while True:
            sleep(5)
            try:
              download_button = driver.find_element(By.XPATH, "//button[1]")
            except:
              continue
            finally:
              download_button.click()
              break
              

          div_song_title = driver.find_element(By.XPATH, "//form[1]/div[1]")
          song_title = div_song_title.text

          self.song_names.append(song_title)
          event.set()
          event.clear()
          cur_num_text = "(" + str(j) + "/" + str(self.get_total_songs()) + ")"
          print(cur_num_text + " Downloading " + col.yellow(song_title) + " ...")

          j += 1 

          sleep(1)

          driver.get("https://ytmp3.as/cyPH/")
    finally:
      print("Finishing all downloads...")
      event.set()
      sleep(10)
      driver.quit()
      print("Time elapsed: " + str(time() - before) + " second(s)")
      print(col.green("All songs downloaded! Go to " + download_dir + " to listen to the songs!"))



# This code is used to test song links by grabbing its title to verify it's the correct song video
"""
links = list(duplicate_tracker)
for link in links:
  soup_link = BeautifulSoup(requests.get(link).content, "html.parser")
  title = soup_link.find("title").text
  print(title)
"""


