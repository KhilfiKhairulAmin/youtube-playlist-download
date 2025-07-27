"""
This is a terminal program that can extract watch links from YouTube HTML file downloaded from your browser
"""

import requests
from bs4 import BeautifulSoup

with open("1.html", "r", encoding="utf-8") as f:
  content = f.read()

soup = BeautifulSoup(content, "html.parser")

anchors = soup.find_all("a")

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
print("Total Watch Links: " + str(i))

links = list(duplicate_tracker)
for link in links:
  soup_link = BeautifulSoup(requests.get(link).content, "html.parser")
  title = soup_link.find("title").text
  print(title)
