"""
This is the backend for song downloads
"""

from time import sleep, time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from Colors import Colors as col

with open("2.html", "r", encoding="utf-8") as f:
  content = f.read()

soup = BeautifulSoup(content, "html.parser")

div = soup.find("div", { "id": "items", "class": "playlist-items style-scope ytd-playlist-panel-renderer"})
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

print("")
print("Total Songs: " + col.yellow(str(i)))

# This code is used to test song links by grabbing its title to verify it's the correct song video
"""
links = list(duplicate_tracker)
for link in links:
  soup_link = BeautifulSoup(requests.get(link).content, "html.parser")
  title = soup_link.find("title").text
  print(title)
"""


chrome_options = Options()
download_dir = "C:\\Users\\infie\\Downloads\\INFIENITE MIX"

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
links = list(duplicate_tracker)

try:
    driver.get("https://ytmp3.as/cyPH/")
    print("Download location: " + col.yellow(download_dir))
    print("Preparing installer...")
    before = time()
    for link in links:
      link_input_box = driver.find_element(By.ID, "v")
      link_input_box.send_keys(link)

      submit_button = driver.find_element(By.XPATH, "//button[2]")
      submit_button.click()

      sleep(7)

      download_button = driver.find_element(By.XPATH, "//button[1]")
      download_button.click()

      div_song_title = driver.find_element(By.XPATH, "//form[1]/div[1]")
      song_title = div_song_title.text

      cur_num_text = "(" + str(j) + "/" + str(i) + ")"
      print(cur_num_text + " Downloading " + col.yellow(song_title) + " ...")
      j += 1 

      sleep(1)

      driver.get("https://ytmp3.as/cyPH/")


finally:
  print("Finishing all downloads...")
  sleep(10)
  driver.quit()
  print("Time elapsed: " + str(time() - before) + " second(s)")
  print(col.green("All songs downloaded! Go to " + download_dir + " to listen to the songs!"))
