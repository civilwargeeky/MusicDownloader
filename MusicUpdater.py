#MusicUpdater.py
#Version 1.0.0
#This program takes in playlists (or list of songs), downloads and processes them.
"""
Possible expansion ideas:
  Allow user to specify multiple playlist urls and songs in a single playlist.
  Download file list from URL (maybe from a pastebin)
  Help section
  GUI to monitor
  GUI to specify output (possibly have conifg file for program)
    With this, see if anything uses that windows GUI thing off the bat.
  A "LocalPlaylist" class that inherits from Playlist and ignores urls and such, so that you can use this program to parse lists of song names
  
  Restructure threading!
  mainProgram
    watcher thread - holds the blocker, and only creates new threads when free, so all playlists don't make a new thread immediately
    --Second blocker for songs. Each playlist tries to download as many songs as possibly in threads. Each song will get its own thread.
    --This way, if there's only 1 playlist, that playlist can take all 5 download threads at once.
    
"""
####CONFIG####
INPUT_FOLDER  = "Scripts"
OUTPUT_FOLDER = "Music"
#OUTPUT_FOLDER = "Q:\\Coding\\Workspace\\MusicFolder" #"Output"
MAX_SIMULTANEOUS_DOWNLOADS = 5
UPDATE_SPEED = 5 #Seconds between updating "time elapsed" when no events fired


import json, os, os.path, re, subprocess, sys, threading, time
from mutagen.id3 import ID3, ID3NoHeaderError
from mutagen.easyid3 import EasyID3
from mutagen import File as MutagenFile #Common name for var
import tkinter as tk
from tkinter import ttk

#My Libs
import MusicDisplay as Disp

DEBUG = os.path.split(os.getcwd())[1] == "MusicDownloader"
YOUTUBE_STRING = "youtube.com/playlist" #Used to determine if a file is a youtube playlist

####DEFINITIONS####
def debug(*arg, **kwarg):
  if DEBUG:
    if len(arg) == 1 and arg[0] == "pause": return input("Waiting...")
    if not "sep" in kwarg: kwarg["sep"] = ""
    try:
      return print(*arg, **kwarg)
    except UnicodeEncodeError: #Stupid music notes
      return print("Could not print unsupported chars", **kwarg)
      
def firstTimeInstructions():
  FILE = "hasRunOnce"
  if not os.path.exists(FILE):
    Disp.MessageBox("""
    First Time Instructions!
    1. There will be multiple command prompt windows opening. DO NOT CLOSE ANY OF THEM.
    2. After a bit there will only be one. This one displays the current status of the downloads.
    3. When all the music has been downloaded, the window will close. There should be a "Music Folder" shortcut on your desktop to access your music.
    4. Your downloads will begin when you close this window
    5. Enjoy! 
    """, "Instructions")
    open(FILE, "w").close() #Empty file :D

class Data:
  Event = None

  #This class will be an object passed to threads allowing them to communicate with main thread
  def __init__(self):
    self.currSongs = 0
    self.totalSongs = 1
    self.status = None

class Song:
  #A "Song" takes in a url and a name. The name is usually from a youtube playlist search
  def __init__(self, url, name = None, explicit = False):
    if not name: name = "%(title)s" #This will just format it based on downloaded title
    self.url = url
    self.name = name
    self.originalName = name
    self.explicit = explicit #If explicit, will not modify name based on regex
    
  #Pre : in and out should be valid regex expression strings
  #Post: object's name is parsed using the regex
  def parseTitle(self, inputRegex, outputRegex):
    if self.explicit: return False #Don't do anything 
    self.name = re.sub(inputRegex, outputRegex, self.name, flags = re.I) #Do sub, ignoring case
    
  def getFileExtension(self):
    return ".mp3"
    
  #Function to get the current fileName of a downloaded song
  def getFileName(self):
    return self.name+self.getFileExtension()

class Playlist:
  regexList = [] #This is a global list
  shouldGenerateTags = True #Config option
  allSongsDefaultArtist = False #You can set this
  defaultArtist = "DJ Dan" #Tee hee

  def __init__(self, folderName):
    self.folder = folderName
    self.initialized = False #When Playlist contains songs, will be true
    self.songList = []
    self.regexList = [] #List of regex tuples in form of (input, output,)
    self.data = Data() #Interface for threading later. Outside of scope of main class
    
    
  def __repr__(self): #Why not
    return "<Playlist object, name="+repr(self.getFolder())+", init="+repr(self.initialized)+">"
    
  #Just officiating that can add URL if not initializing with songs
  #Returns self because I'm lazy
  def setURL(self, url):
    self.url = url
    return self
    
  #Returns the folder name. May at some point return a cleansed and parsed name
  def getFolder(self):
    return self.folder or ""
    
  #Pre : Expects song to be either a list of Songs or a Song.
  #Post: the playlist's songList parameter is set
  def addSong(self, song):
    if type(song) == list:
      self.songList = song
      self.initialized = True
    elif type(song) == Song:
      self.songList.append(song)
      self.initialized = True
    else:
      raise TypeError("addSong expects a Song or list of Songs, got: ", str(type(song)))
    
  #Returns the path of the requested song with respect to the current working directory
  def getSongPath(self, song):
    return os.path.join(os.path.normpath((OUTPUT_FOLDER+"/"+self.getFolder()) if self.getFolder() else OUTPUT_FOLDER), song.getFileName())
      
  #Pre: playlistUrl should be a valid HTTP url.
  #Post: If url is valid and service working, returns a list of Songs.
  #  If invalid url, raises ValueError.
  #  If no url given, raises AttributeError
  def generateSongList(self, url = None):
    if url == None and hasattr(self, "url"): url = self.url
    if not url: raise AttributeError("could not download playlist. No url")
    #if not "www.youtube.com/playlist?list" in url: raise ValueError("improper playlist url: ",url)
    #Creates a dictionary object from the json given by youtube-dl
    try:
      playlistData = json.loads(subprocess.check_output("youtube-dl.exe -J --flat-playlist -- "+url, shell = True, universal_newlines = True))
    except subprocess.CalledProcessError:
      raise ValueError("could not download playlist. Bad url: ",url)
    
    for song in playlistData["entries"]:
      if song["_type"] == "url":
        self.addSong(Song(song["url"], song["title"]))
        
  #This downloads the song to the proper folder, supressing output
  #Pre : An initialized song and non-blank folder for self
  #Post: The requested song should be downloaded into the current playlist's path as an .mp3
  def downloadSong(self, song):
    outputFolder = (OUTPUT_FOLDER+"/"+self.getFolder()) if self.getFolder() else OUTPUT_FOLDER #If no folder name, set to base directory
    subprocess.call("youtube-dl.exe -o \""+outputFolder+"/"+(song.name or "[ERROR]")+".%(ext)s\" -x --audio-format mp3 --audio-quality 0 -- "+song.url, shell = True, stdout = subprocess.DEVNULL)
    
  #This will do the tag setting and stuff on various songs
  #Pre : song is a valid song that has already been downloaded
  #Post: The song will have tags readable by mp3 readers
  def postProcessSong(self, song):
    if self.shouldGenerateTags:
      try:
        name = self.getSongPath(song)
        localList = song.name.split("- ") #The song should be split as "artist - title". If not, it won't be recognized
        artist = localList[0] if len(localList) > 1 else self.defaultArtist #The artist is usually first if its there. Otherwise no artist
        if self.allSongsDefaultArtist: artist = self.defaultArtist
        title = localList[1] if len(localList) > 1 else localList[0] #If there is no artist, the whole name is the title
        
        artist = artist.lstrip().rstrip()
        title  =  title.lstrip().rstrip()
        
        #Appreciate this. It took upwards of 5 hours to get the damn software to do this.
        try:
          songID = EasyID3(name)
        except ID3NoHeaderError:
          songID = MutagenFile(name, easy = True)
          songID.add_tags()
        songID['artist'] = artist
        songID['title'] = title
        songID.save()
        songID = ID3(name, v2_version=3) #EasyID3 doesn't support saving as 2.3 to get Windows to recognize it
        songID.update_to_v23()
        songID.save(v2_version=3)
      except FileNotFoundError:
        debug("File not found for: ", name)
        
  #Pre : songList is not empty
  #Post: all songs have had their parseTitle methods called on all regex rules
  def parseAllSongs(self):
    for song in self.songList:
      for regex in self.regexList + type(self).regexList : #Adds in global regex and playlist
        song.parseTitle(regex[0], regex[1])
      #Go through all characters and eliminate non-printable characters
      i = 0
      while i < len(song.name): #Because loop limits
        try:
          song.name[i].encode("ascii")
        except UnicodeEncodeError:
          song.name = song.name[:i] + song.name[i+1:] #Take out the offending character
        i += 1
      song.name = song.name.lstrip().rstrip() #Get rid of pesky trailing whitespace
    
  #Pre : Expects an input regex and an output regex
  #Post: Adds the selected regex to the Playlist's regex filter
  def addRegex(self, input, output):
    debug("Adding regex: ")
    debug("  In:  ",input)
    debug("  Out: ",output)
    self.regexList.append((input, output,))
    
  @classmethod
  def addRegexGlobal(cls, input, output):
    debug("Adding globally!")
    cls.addRegex(cls, input, output)
    
Playlist.addRegexGlobal("\|","#") #This is done by ffmpeg anyway. Fixes not finding files
Playlist.addRegexGlobal("\:","-")
Playlist.addRegexGlobal("\\\"","'")
Playlist.addRegexGlobal("\\\\","")
Playlist.addRegexGlobal("\/","")
  
    
#Pre : fileName should be a valid fileName
#Post: If file exists, returns a dictionary of Playlist objects containing necessesary details
#      Dictionary is mapping of folderName to Playlist object
#   If file does not exist, raise FileNotFoundError
#   NOTE: Does not download song lists immediately. Playlists will be un-initialized
def parseInputFile(fileName):
  file = open(fileName, "r") #This can raise any errors. That's fine
  
  toRet = {}
  currPlaylist = None #Initially none
  inRegex = False #Flag as to whether or not flagging regex
  advancedRegex = False #Flag as to whether to escape things or not
  inComment = False #Flag as to whether or not multiline comment
  while True:
    currLine = file.readline() #Get current line
    if not currLine: break #Done with input
    currLine = currLine.rstrip("\r\n") #Get rid of newline
    
    if currLine[:2] == "/*": inComment = True
    if currLine[:2] == "*/":
      inComment = False
      continue #Also continue when this line so it doesn't think new playlist
    if inComment: continue #Ignore current line
    
    debug("Line: ",currLine) #Ignore comments
    
    #If empty line, new playlist
    if not currLine:
      currPlaylist = None
      inRegex = False
      debug("Resetting!")
    elif currLine[:2] == "//":
      debug("Comment!")
      pass #Comments
    #Do this before make a new playlist to allow for global
    elif currLine == "=": #This line distinguishes between regex and not regex
      debug("Switching to regex!")
      inRegex = True
      advancedRegex = False
    elif currLine == "==":
      debug("Switching to advanced regex!")
      inRegex = True
      advancedRegex = True
    #If new playlist, make a new playlist...
    elif not currPlaylist and not inRegex:
      debug("New Playlist!")
      currPlaylist = Playlist(currLine)
      toRet[currLine] = currPlaylist
      inRegex = False
    else:
      if inRegex: #Adds regex to playlist
        debug("Adding regex line!")
        #This adds the unescaped regex if advanced, otherwise escaped
        tab = currLine.split("|")
        toSend = (tab if advancedRegex else [re.escape(tab[0]), tab[1]])
        if currPlaylist:
          currPlaylist.addRegex(*toSend)
        else: #We can add things at the top!
          Playlist.addRegexGlobal(*toSend)
      elif currLine.lower()[:14] == "default artist": #We only use the default artist
        debug("Setting to default artist!")
        currPlaylist.allSongsDefaultArtist = True
      elif "playlist" in currLine: #The youtube url has "playlist?list=..."
        debug("Adding playlist!")
        currPlaylist.setURL(currLine)
      else: #If adding directly by song
        debug("Adding a song!")
        lineParts = currLine.split(" ",1)
        nameGiven = len(lineParts) > 1
        #This adds the url of the song first, then either adds the given name of the song, or a formatter
        #for youtube-dl to automatically generate it
        currPlaylist.addSong(
          Song(lineParts[0], lineParts[1] if nameGiven else "", explicit = not nameGiven))
        
  file.close()
      
  return toRet
  
def path(pathName):
  return os.path.join(OUTPUT_FOLDER,pathName)

####THREAD FUNCTIONS####  
#Pre : playlist should have a valid youtube playlist and a list of 1 or more songs
#Post: playlist will be downloaded and written to proper folder
def Thread_downloadPlaylist(playlist, blocker):
  playlist.data.status = "Waiting"
  playlist.data.totalSongs = max(len(playlist.songList),0)
  blocker.acquire() #Wait to connect
  playlist.data.status = None #Signal download has started
  for song in playlist.songList:
    debug("New song! \n",song.name,"\n",song.originalName)
      
    #Download the song
    playlist.downloadSong(song)
    #When that's done, add mp3 data if requested
    playlist.postProcessSong(song)

    #Update biometrics
    playlist.data.currSongs += 1
    playlist.data.Event.set() #Signal to update watcher
    
  playlist.data.status = "Done"
  blocker.release() #Release loading lock when all songs done

####DISPLAY FUNCTIONS####?
  
def main():
  ####PRE-INIT####
  #Getting input
  inputFile = None
  if len(sys.argv) > 1:
    if os.path.exists(sys.argv[1]):
      inputFile = sys.argv[1]
    else: raise FileNotFoundError("invalid source file")
  if not inputFile: 
    def adjustInputFile(input):
      return os.path.join(INPUT_FOLDER, input) if (input and not os.path.isabs(input)) else input
    
    #Getting values for display
    v_options = []
    for a in os.walk(INPUT_FOLDER):
      for b in a[2]:
        v_options.append(os.path.join(a[0],b)[len(INPUT_FOLDER)+1:]) #Get rid of folder name
        
    root = Disp.MainBox("Music Updater")
    root.minsize(width = 400, height = 200)
    Disp.VarLabel("Choose a file from the list!")
    choiceBox = Disp.VarList(v_options, width = 75)
    def openFile(*args):
      if choiceBox.get():
        debug('"'+adjustInputFile(choiceBox.get())+'"')
        os.system('"'+adjustInputFile(choiceBox.get())+'"') #Just call it and they can open it with whatever
    
    tk.Button(text = "Open file for editing", command = openFile).pack()
    Disp.VarLabel("Or you can put a file or playlist url here")
    choiceEntry = Disp.VarEntry(width = 75)
    
    #Functions
    def quit(*args):
      root.destroy()
      
    def paste(*args):
      try:
        choiceEntry.set(root.clipboard_get())
      except:
        pass #I don't care if there's nothing there
      
    choiceBox.bind("<Double-Button-1>", quit)
    tk.Button(text = "Paste from clipboard", command = paste).pack()
    tk.Button(text = "Start Downloading!", command = quit).pack()
    
    root.shouldStopProgram = False
    def stopProgram(): #If they press the x button
      debug("STOPPING!")
      root.shouldStopProgram = True
      root.destroy()
    root.protocol("WM_DELETE_WINDOW", stopProgram)
    
    root.mainloop() #Run all the things!
    
    if root.shouldStopProgram:
      debug("Exit button pressed!")
      return 0; #Successful code completion
    
    debug("entry: ",choiceEntry.get())
    debug("box:   ", choiceBox.get())
    inputFile = (choiceEntry.get() if choiceEntry.get() else (choiceBox.get() or "")) #Can be None if neither
    #Makes the proper file name
    if not YOUTUBE_STRING in inputFile: inputFile = adjustInputFile(inputFile)
    #if inputFile and not os.path.isabs(inputFile) and not YOUTUBE_STRING in inputFile: inputFile = os.path.join(INPUT_FOLDER, inputFile)
    debug("Resulting path: ", inputFile)
  
  ####INITIALIZATION####
  if YOUTUBE_STRING in inputFile:
    #Get an input playlist
    debug("Using raw playlist input")
    mainList = {"Main Playlist": Playlist("Main Playlist").setURL(inputFile)}
  else:
    #Getting input file
    debug("Getting input from file")
    try:
      mainList = parseInputFile(inputFile)
    except (FileNotFoundError, OSError):
      print("input file \""+inputFile+"\" not found. Terminating")
      Disp.MessageBox("File not found: "+(inputFile or "(blank file)"), "ERROR!")
      return 1; #Exit with error
    
  if len(mainList) == 0:
    if DEBUG:
      raise(ValueError("No input lists in input file"))
    else:
      Disp.MessageBox("There were no playlists in your input file!", "ERROR!")
      return 1;
    
  #Update youtube-dl in a thread
  updateThread = threading.Thread(target = os.system, args = ("start /WAIT youtube-dl.exe -U",))
  updateThread.start()
  
  #After we do that, print first time use instructinos (if necessesary)
  firstTimeInstructions()
  
  print("Generating playlist songs and folders")
  for playlist in mainList.values():
    #Generate song lists from internet sources
    if not playlist.initialized:
      try:
        playlist.generateSongList()
      except ValueError:
        Disp.MessageBox("Could not download playlist: "+playlist.url+"\nThe playlist either does not exist, or is not public.\nTry making your playlist public :)", "ERROR!")
        return 1
    playlist.parseAllSongs()
    #Make folder if not existing
    if not os.path.exists(path(playlist.getFolder())):
      try:
        os.makedirs(path(playlist.getFolder()))
      except OSError:
        Disp.MessageBox("Invalid Playlist Title: "+playlist.getFolder(), "ERROR!")
        return 1;
    #Check for already existing songs, remove them from list
    toRemove = []
    for song in range(len(playlist.songList)):
      if os.path.exists(os.path.join(path(playlist.getFolder()), playlist.songList[song].name+".mp3")):
        toRemove.append(song-len(toRemove)) #minus len remove because if we remove 3, 4 will be new 3 
    for i in toRemove: #Remove all existing songs
      playlist.songList.pop(i)
  
  #Wait for youtube update to finish
  updateThread.join()
  
  ####MAIN PROCESS####
  startTime = int(time.time())
  #The blocker will only allow a certain number of downloads at once
  blocker = threading.Semaphore(MAX_SIMULTANEOUS_DOWNLOADS)
  mainEvent = threading.Event()
  Data.Event = mainEvent #This is what all playlists will use to signal song done
  
  threads = []
  #Start all downloading threads (capped by a semaphore)
  for element in mainList:
    newThread = threading.Thread(target = Thread_downloadPlaylist,
      args = (mainList[element], blocker,), name = element)
    newThread.start()
    threads.append(newThread)
    
  #Display Loop
  flag = True #Initially true
  mainEvent.set() #So it prints once initially
  while flag:
    #Wait for the next song to have downloaded (or 10 secs)
    mainEvent.wait(UPDATE_SPEED)
    mainEvent.clear() #Clear for next song to activate
    time.sleep(0.05) #Wait just a bit
    
    
    #Do display updating things
    timeDelta = int(time.time()) - startTime
    if not DEBUG: print("\n"*80)
    print("Time Elapsed: {}:{:02}".format(timeDelta // 60,timeDelta % 60))
    #Gets the longest folder name string
    maxAlign = min(25, len(max(mainList.keys(), key = len)))
    for thread in sorted(threads, key = lambda a: a.name):
      data = mainList[thread.name].data
      nameString = "{:<"+str(maxAlign)+"}: "
      #If status is not "Copying" or "Done"
      if mainList[thread.name].data.status == None:
        #Prints like "Whatever  : 100 / 150 66%"
        print((nameString + "{:3} / {:3} {:>3.0%}").format(
          thread.name, data.currSongs, data.totalSongs, data.currSongs/(data.totalSongs or 1)))
      else:
        #Prints like "Another   : ====DONE!===="
        print((nameString + "{:=^13}").format(thread.name, data.status.upper()+"!"))
    
    flag = False #Then has to prove itself
    for thread in threads: #If nothing is alive, flag stays false
      if thread.is_alive(): flag = True
      
  
  ####POST PROCESS####
  print("Done!")
  #Display list of updated songs?
  
  
  
#If called be itself, run main
if __name__ == "__main__":
  main()