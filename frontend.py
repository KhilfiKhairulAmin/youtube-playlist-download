import threading
import tkinter as tk
from tkinter import ttk, filedialog

from backend import Backend
"""
1. Press Proceed or Exit
2a. Upload HTML
3. Choose song download folder
4. Display n update progress bar
5. Finish message
2b. Help page
"""

class Frontend:
  cur_window: tk.Tk = None
  backend: Backend = None
  event = threading.Event()
  download_path = ""

  def on_start_button_click(self):
    self.cur_window.destroy()
    self.create_html_window()

  def on_help_button_click(self):
    self.cur_window.destroy()
    self.create_help_window()

  def on_html_select_button_click(self):
    filepath_html = filedialog.askopenfilename(initialdir="/", title="Select YT Mix - HTML Page", filetypes=(("HTML files", "*.html"), ("All files", "*.*")))
    self.download_path = filedialog.askdirectory(initialdir="/", title="Select Song Download Folder Location")
    if filepath_html and self.download_path:
      self.backend = Backend(filepath_html)
      self.cur_window.destroy()
      self.create_download_window()

  def on_download_button_click(self):
    self.cur_window.destroy()
    self.create_progressbar_window()

  def update_download_progress(self, label: tk.Label, progressbar: ttk.Progressbar):
    """
    Here update the progressbar, perhaps use a caller-listener architecture
    """
    total_songs = self.backend.get_total_songs()
    for i in range(total_songs):
      self.event.wait()
      song_name = self.backend.get_current_song()
      label.config(text="Installing " + song_name + "...")
      progressbar["value"] += 1/total_songs*100
    
    self.event.wait()
    self.cur_window.destroy()
    self.create_finish_window()


  def on_download_more_button_click(self):
    self.cur_window.destroy()
    self.create_start_window()

  def on_back_button_click(self):
    self.cur_window.destroy()
    self.create_start_window()

  # 1
  def create_start_window(self):
    self.cur_window = tk.Tk()
    self.cur_window.title("Start")
    headings_label = tk.Label(self.cur_window, text="BS4 YT Music Mix Master", font=("Sans", 24))
    start_button = tk.Button(self.cur_window, text="Start", command=self.on_start_button_click)
    help_button = tk.Button(self.cur_window, text="Help", command=self.on_help_button_click)
    headings_label.pack()
    start_button.pack()
    help_button.pack()
    self.cur_window.mainloop()

  #2a
  def create_html_window(self):
    self.cur_window = tk.Tk()
    self.cur_window.title("Upload YT Music Page HTML")
    html_select_button = tk.Button(self.cur_window, text="Select YT Mix - HTML file", command=self.on_html_select_button_click)
    html_select_button.pack()
    self.cur_window.mainloop()

  #3
  def create_download_window(self):
    self.cur_window = tk.Tk()
    self.cur_window.title("Ready to Download")
    total_songs = self.backend.get_total_songs()
    song_information_label = tk.Label(self.cur_window, text="Total Songs: " + str(total_songs))
    download_button = tk.Button(self.cur_window, text="Begin download", command=self.on_download_button_click)
    song_information_label.pack()
    download_button.pack()
    self.cur_window.mainloop()

  #4
  def create_progressbar_window(self):
    self.cur_window = tk.Tk()
    self.cur_window.title("Downloading...")
    song_name_label = tk.Label(self.cur_window, text="Grabbing song titles...")
    progressbar = ttk.Progressbar(self.cur_window, orient=tk.HORIZONTAL, length=300, mode="determinate")
    song_name_label.pack()
    progressbar.pack()
    t1 = threading.Thread(target=lambda: self.update_download_progress(song_name_label, progressbar))
    t2 = threading.Thread(target=lambda: self.backend.download_songs(self.download_path, self.event))
    t1.start()
    t2.start()
    self.cur_window.mainloop()

  #5
  def create_finish_window(self):
    self.cur_window = tk.Tk()
    self.cur_window.title("Success!")
    finish_text = ""
    finish_label = tk.Label(self.cur_window, text=finish_text)
    finish_button = tk.Button(self.cur_window, text="Finish", command=lambda : self.cur_window.destroy())
    download_more_button = tk.Button(self.cur_window, text="Download more...", command=self.on_download_more_button_click)
    finish_label.pack()
    finish_button.pack()
    download_more_button.pack()
    self.cur_window.mainloop()

  #2b
  def create_help_window(self):
    self.cur_window = tk.Tk()
    self.cur_window.title("Help")
    help_text = ""
    help_label = tk.Label(self.cur_window, text=help_text)
    back_button = tk.Button(self.cur_window, text="Back", command=self.on_back_button_click)
    help_label.pack()
    back_button.pack()
    self.cur_window.mainloop()

if __name__ == "__main__":
  Frontend().create_start_window()
