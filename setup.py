from distutils.core import setup
import py2exe, shutil, os.path

outputFolder = "dist"

setup(
  name="Music Updater",
  version="1.0",
  description="Downloads music from youtube using youtube-dl",
  author="DJ Dan",
  dist_dir = outputFolder,
  console=["MusicUpdater.py"],
  options={"py2exe":{
    "ignores": ['win32evtlog', 'win32evtlogutil']
    }
  },
  )
  
files = [
  "ffmpeg.exe",
  "ffprobe.exe",
  "exampleInput.config",
  "youtube-dl.exe",
  "downloadSong.bat",
  "Youtube.ico",
]

for i in files:
  shutil.copyfile(i, os.path.join(outputFolder, i))