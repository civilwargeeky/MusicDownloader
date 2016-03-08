from os import system
#Update this before doign anything else
system("start /WAIT resources/youtube-dl.exe -U")

from distutils.core import setup
import py2exe, shutil, os

outputFolder = "dist"

setup(
  name="Music Updater",
  version="1.0.0",
  description="Downloads music from youtube using youtube-dl",
  author="DJ Dan",
  console=["MusicUpdater.py"],
  options={"py2exe":{
    "ignores": ['win32evtlog', 'win32evtlogutil']
    }
  },
  )
  
files = [
  "resources/ffmpeg.exe",
  "resources/ffprobe.exe",
  "resources/youtube-dl.exe",
  "downloadSong.bat",
  "resources/Youtube.ico",
  "MusicDisplay.py",
]
scripts = [
  "scripts/exampleInput.config",
  "scripts/Simple Example.txt",
]

def copyFile(fr, to=""):
  try:
    print("Copying file ",fr)
    folder = os.path.join(outputFolder, to)
    if not os.path.isdir(folder):
      os.makedirs(folder)
    shutil.copyfile(os.path.normpath(fr), os.path.join(folder, os.path.split(fr)[1]))
  except FileNotFoundError:
    print("[BUILD] Error in build! File not found: '"+fr+"'")

for i in files:
  copyFile(i)
  
for i in scripts:
  copyFile(i, "Scripts")