# Built-in dependencies
import os                         # Handling file operations
import re                         # Filename curing (regex)
from pathlib import Path          # Handling file operations
import time
import datetime                   # Naming folders inside `saved` directory
from typing import List, Literal  # Type annotations

# External dependencies
import typer                                           # CLI application tools
import requests                                        # Downloading file
from playwright.sync_api import sync_playwright        # For scraping YTMP3.as
from rich import print                                 # Printing with color support
from rich.progress import Progress                     # Progress bar
from rich.progress import MofNCompleteColumn, SpinnerColumn, TextColumn, BarColumn, TotalFileSizeColumn, TimeElapsedColumn

"""PART A: BACKEND AND CLI-UI FUNCTIONS"""


DEBUG_MODE = False      # If set to True, Debug Mode will open webdriver without --headless-mode (browser will be visible)
DOWNLOAD_DIR = "saved"  # Default folder location for video downloads


def parse_video_id_from_link(link: str) -> str:
  """Parse video ID from link"""

  return link.split("=")[1].split("&")[0]


def parse_video_ids_from_playlist(playlist_link: str) -> List[str]:
  """Parse all video ids from playlist"""

  with sync_playwright() as p:
    
    browser = p.firefox.launch(headless=True)

    page = browser.new_page()

    page.goto(playlist_link)

    # Ensure the whole page is fully loaded
    page.wait_for_load_state("networkidle")

    video_ids = page.evaluate("""
      () => {
          const anchors = Array.from(document.querySelectorAll('a.yt-simple-endpoint'));
          const links = anchors
                          .map(link => link.href)
                          .filter(href => href.includes('watch?v='))
                          .map(href => {
                              const url = new URL(href);
                              return url.searchParams.get('v');
                          })
                          .filter(id => id); // Remove nulls
          return [...new Set(links)]  // Remove duplicates
      }
    """)

    return video_ids


def parse_video_ids_from_html(path_to_playlist_html: Path) -> List[str]:
  """Parse all video ids from playlist in HTML file"""
  
  # Read HTML file
  with open(path_to_playlist_html, "r", encoding="utf-8") as f:

    content = f.read()

  with sync_playwright() as p:
    
    browser = p.firefox.launch(headless=True)

    page = browser.new_page()

    page.set_content(content)
    
    video_ids = page.evaluate("""
      () => {
          const anchors = Array.from(document.querySelectorAll('a.yt-simple-endpoint'));
          const temp = anchors
                          .map(link => link.href)
                          .filter(href => href.includes('watch?v='))
                          .filter(href => href.includes('&'))
          const playlist_link = new URL(temp[0]).searchParams.get('list');
          const links = temp
                          .filter(href => href.includes(playlist_link))
                          .map(href => {
                              const url = new URL(href);
                              return url.searchParams.get('v');
                              })
          return [...new Set(links)]  // Remove duplicates
      }
    """)

    return video_ids


def download_videos(video_ids: List[str], format: Literal["mp3", "mp4"], download_dir: Path, is_silent: bool=False) -> None:
  """Download all videos from playlist in MP3/MP4 format with progress bar"""
  
  # Create directory regardless of its prior existence
  download_dir.mkdir(parents=True, exist_ok=True)
  
  print()

  with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progressbar, sync_playwright() as p:
    
    task = progressbar.add_task(f"Preparing [bright_yellow]{len(video_ids)} [white]downloads in [bright_yellow]{format} [white]to [bright_yellow]{download_dir}", total=1)

    browser = p.firefox.launch(headless=True)

    page = browser.new_page()

    illegal_char_replacement_flag = False
    invalid_links = []

    for video_id in video_ids:

      # Goto YTMP3 website
      page.goto("https://ytmp3.as/cyPH/")

      if not progressbar.finished:
        progressbar.update(task, advance=1, description=f"[bright_green]Download process ready (Location: {download_dir})", completed=True)
        progressbar.stop()

      # Flag for handle MP3 or MP4
      is_mp3 = format.lower() == "mp3"

      if is_mp3:

        # Override default download method from the website to gain download link
        page.evaluate("""
          window.download = function (e, t, r, n) {
            window._downloadLink = e;
            window._title = n;
          };
        """)

      else:

        # Override default download method from the website to gain download link and video title
        page.evaluate("""
          window.download = function (e, t, r, n) {
            window._downloadLink = e;
          };
        """)

      # Enter YouTube link into input element
      link_input_box = page.query_selector("#v")
      link_input_box.fill(f"https://youtube.com/watch?v={video_id}")

      # Button for specifying download format (MP3 or MP4)
      format_button = page.locator("button").first 

      if not is_mp3:
        format_button.click()  # Change to MP4 by simulating clicking button

      # Click convert button to start conversion process
      convert_button = page.locator("button").last
      convert_button.click()

      # Wait until the download link has been created
      while page.evaluate("""() => window._downloadLink""") == None:

        try:

          # Check if there's error happening on the website
          # When the number of button is only 1, it means that an error has occurred
          # (Try it yourself by entering a non-existent YouTube video link and see what happens at ytmp3.as)
          if len(page.query_selector_all("button")) == 1:
            break
          
        except:
          continue

      # Get download link
      download_link = page.evaluate("""() => window._downloadLink""")

      # Case where conversion failed, continue to next video (while keeping track of unsuccessful links)
      if download_link == None:
        
        invalid_links.append(f"https://youtube.com/watch?v={video_id}")
        continue
        
      title = ""
      if is_mp3:
        title = page.evaluate("""() => window._title""")
      else:
        title = page.locator("div").first.text_content()

      # Setup requests to mimic browser behavior for file downloads
      headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': '*/*',
        'Accept-Encoding': 'identity',  # Important for progress tracking
        'Connection': 'keep-alive',
      }

      # Replace illegal characters from video title to avoid file system errors
      filename = re.sub(r'[/\\*?"<>|:]', "_", title.strip())
      download_path = os.path.join(download_dir, f"{filename}.{format}")

      # Get the file
      response = requests.get(download_link, headers=headers, stream=True)
      response.raise_for_status()

      # File metadata
      total_size = int(response.headers.get('content-length', 0))
      block_size = 1024  # 1 Kibibyte
      file_size = total_size / (1024*1024)

      if is_silent and (not illegal_char_replacement_flag) and (filename != title.strip()):

        illegal_char_replacement_flag = True
        print("[bright_green]Note: [white]Illegal characters such as '([*?])' are replaced with '_' inside filenames")

      print()

      # Progress bar for download progress feedback
      with open(download_path, 'wb') as file, Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TotalFileSizeColumn(), TimeElapsedColumn(), disable=is_silent) as progressbar:

        task = progressbar.add_task(description=f'Downloading [yellow]{title}', total=total_size, visible=not is_silent)
        
        for data in response.iter_content(block_size):

          progressbar.update(task, advance=len(data))
          file.write(data)
      
        progressbar.update(task, description=f'[bright_green]Successful: {filename}.{format}', total=total_size, visible=not is_silent)

  # Display download summary
  print(f"\n[green]{len(video_ids) - len(invalid_links)} [white]videos downloaded successfully. [bright_red]{len(invalid_links)} [white]invalid links found.")
  "" if len(invalid_links) == 0 else print(f"\n[bright_red]Invalid links: [white]", end="")
  print(*invalid_links, sep=", ")


def is_valid_video_id(video_id: str) -> bool:
  """Determine whether the video id is correct syntatically"""
  return len(video_id) == 11


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

  # 1. Extract YouTube video links
  with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progressbar:
    
    print()
    type_str = "playlist"
    task = progressbar.add_task(description=f"Finding {type_str} videos from [bright_yellow]{link_or_path}", total=1)

    # Determine whether input is a video link, playlist link or HTML file
    if ".html" in link_or_path:  # HTML file
      
      video_ids = parse_video_ids_from_html(link_or_path)

    elif "v=" in link_or_path:  # Video link
      type_str = "video"
      video_ids.append(parse_video_id_from_link(link_or_path))

    elif "list=" in link_or_path:  # Playlist link
      video_ids = parse_video_ids_from_playlist(link_or_path)
    
    if len(video_ids) == 0:
      progressbar.update(task, description=f"[bright_red]Error: Can't find any {type_str} from {link_or_path}", advance=1)
      print("[bright_red][bold]Please provide a valid link or path")
      return
    
    progressbar.update(task, description=f"[bright_green]Found {len(video_ids)} video" + ("s" if len(video_ids) > 1 else ""), advance=1)
    
  print()

  # 2. Verifying links
  with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), MofNCompleteColumn()) as progressbar:
    
    task = progressbar.add_task("Validating video IDs", total=len(video_ids))
    
    invalids = []
    for v in video_ids:
      progressbar.update(task, advance=1, description="Validating video IDs")
      if not is_valid_video_id(v):
        invalids.append(v)

    time.sleep(1.3)

    valid_count = len(video_ids) - len(invalids)
    progressbar.update(task, description=f"[bright_green]{valid_count} valid ID found. " + (f"[bright_red]{len(invalids)} [white]invalid ID found." if len(invalids) > 0 else ""))

    if invalids:
      print("[bright_red]Invalid links: ", end="")
      print(*[f"[grey74]https://youtube.com/watch?v={id}" for id in invalids], sep="[white], ")

  # 3. Download videos
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

