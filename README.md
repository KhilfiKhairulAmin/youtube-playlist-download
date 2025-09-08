## YouTube Playlist Download
A CLI application that can download all videos/songs from a YouTube playlist.

### Still in development
This README will serve as my temporary development notes for jolting down ideas, TODOs, and random stuff about this project.

### Getting started
To start using this app, clone this repository onto your device. Make sure you have Python v3+ installed.
\
Install all dependencies
```
pip install -r requirements.txt
```

Download YouTube's playlist HTML file by right click and `Save` the page.

Run the application
```
python app.py "path_to_html" 
```

**Note: Since the CLI is still in development, I will update this section to include more detailed instructions.**

### Ideas
1. For a YouTube playlist that is not a personal playlist, user can just enter the link instead of downloading the HTML of the playlist page
  - TODO: Implement handler for non-personal playlist
2. Since it can download a whole playlist, it'd be a great idea to integrate downloading a single video from YouTube since the functionality is already present in the application
  - TODO: Implement handler for single video
3. A download analytics feature where user can view their past downloads activity and then show them where the file is downloaded, when, etc. It's just like a data browser feature, but through CLI
  - I'm not sure about this yet since it seems to be a big feature overall

COOL!
