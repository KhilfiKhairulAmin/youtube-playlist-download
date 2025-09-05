from typer.testing import CliRunner
from app import app
import os
import shutil

VIDEO_LINK             = "https://www.youtube.com/watch?v=tPEE9ZwTmy0"
VIDEO_TITLE            = "Shortest Video on Youtube"
PLAYLIST_LINK          = "https://www.youtube.com/playlist?list=PLCcqYFX7d5HC_Gz5pQex5gj708kGgjiRs"
PLAYLIST_VIDEO_TITLES  = ["Shortest Video on Youtube", "World's Shortest YouTube Video! (0.00000000001 sec.)"]
MIX_HTML_PATH          = "tests/example_mix.html"
MIX_VIDEO_TITLES       = ["Shortest Video on Youtube", "World's Shortest YouTube Video! (0.00000000001 sec.)"]
FOLDER                 = "tests/temp"

runner = CliRunner()
cleanup_folder = lambda: None if not os.path.exists(FOLDER) else shutil.rmtree(FOLDER)
setup_folder = lambda: None if os.path.exists(FOLDER) else os.makedirs(FOLDER)

# Ensure temp folder and all its content is reset before test
cleanup_folder()

def test_video_download():

  setup_folder()

  result = runner.invoke(app, [VIDEO_LINK, FOLDER])

  assert result.exit_code == 0
  assert os.path.exists(f"{FOLDER}/{VIDEO_TITLE}.mp3")

  cleanup_folder()

def test_playlist_download():

  setup_folder()

  result = runner.invoke(app, [PLAYLIST_LINK, FOLDER])

  assert result.exit_code == 0
  for title in PLAYLIST_VIDEO_TITLES:
    assert os.path.exists(f"{FOLDER}/{title}.mp3")

  cleanup_folder()

def test_mix_download():

  setup_folder()

  result = runner.invoke(app, [MIX_HTML_PATH, FOLDER])

  assert result.exit_code == 0
  for title in MIX_VIDEO_TITLES:
    assert os.path.exists(f"{FOLDER}/{title}.mp3")

  cleanup_folder()
