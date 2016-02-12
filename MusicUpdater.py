#MusicUpdater.py
#Version 1.0.0
#This program takes in playlists (or list of songs), downloads and processes them.
"""
Possible expansion ideas:
  Allow user to specify multiple playlist urls and songs in a single playlist.
  Download file list from URL (maybe from a pastebin)
  Help section
  GUI to monitor
  Maybe have something to parse song names and get mp3 titles and artists
    http://id3-py.sourceforge.net/
    https://wiki.python.org/moin/PythonInMusic
  Be able to specify output folder from input file
  "Freeze" this with CX-Freeze?
  Make an installer (see that thing from last semester)
  A "LocalPlaylist" class that inherits from Playlist and ignores urls and such, so that you can use this program to parse lists of song names
"""
####CONFIG####
OUTPUT_FOLDER = "Music"
#OUTPUT_FOLDER = "Q:\\Coding\\Workspace\\MusicFolder" #"Output"
MAX_SIMULTANEOUS_DOWNLOADS = 5
UPDATE_SPEED = 5 #Seconds between updating "time elapsed" when no events fired
DEBUG = False


import json, os, re, subprocess, sys, threading, time

####DEFINITIONS####
def debug(*arg, **kwarg):
  if DEBUG:
    if len(arg) == 1 and arg[0] == "pause": return input("Waiting...")
    if not "sep" in kwarg: kwarg["sep"] = ""
    return print(*arg, **kwarg)

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

class Playlist:
  regexList = [] #This is a global list

  def __init__(self, folderName):
    self.folder = folderName
    self.initialized = False #When Playlist contains songs, will be true
    self.songList = []
    self.regexList = [] #List of regex tuples in form of (input, output,)
    
    
  def __repr__(self): #Why not
    return "<Playlist object, name="+repr(self.getFolder())+", init="+repr(self.initialized)+">"
    
  #Just officiating that can add URL if not initializing with songs
  def setURL(self, url):
    self.url = url
    
  #Returns the folder name. May at some point return a cleansed and parsed name
  def getFolder(self):
    return self.folder
    
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
    
  #Pre : songList is not empty
  #Post: all songs have had their parseTitle methods called on all regex rules
  def parseAllSongs(self):
    for song in self.songList:
      for regex in self.regexList + type(self).regexList : #Adds in global regex and playlist
        song.parseTitle(regex[0], regex[1])
    
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
      currPlaylist.data = Data() #Interface for threading later. Outside of scope of main class
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
      elif "playlist" in currLine:
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
  """
  #TEMPORARY
  for i in list(toRet.keys()): #Because I'm not dealing with getting stuff from playlist yet
    if not toRet[i].initialized:
      del toRet[i] """
      
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
    try:
      debug("New song! \n",song.name,"\n",song.originalName)
    except:
      print("Could not display song info")
    #This downloads the song to the proper folder, supressing output
    subprocess.call("youtube-dl.exe -o \""+OUTPUT_FOLDER+"/"+playlist.getFolder()+"/"+(song.name or "[ERROR]")+".%(ext)s\" -x --audio-format mp3 --audio-quality 0 -- "+song.url, shell = True, stdout = subprocess.DEVNULL)
    #Update biometrics
    playlist.data.currSongs += 1
    playlist.data.Event.set() #Signal to update watcher
    
  playlist.data.status = "Done"
  blocker.release() #Release loading lock when all songs done

####DISPLAY FUNCTIONS####?
  
def main():
  ####PRE-INIT####
  #Getting input file to parse
  inputFile = None
  if len(sys.argv) > 1:
    if os.path.exists(sys.argv[1]):
      inputFile = sys.argv[1]
    else: raise FileNotFoundError("invalid source file")
  if not inputFile: inputFile = input("What file to use for input? ")
  
  ####INITIALIZATION####
  #Getting input file
  try:
    mainList = parseInputFile(inputFile)
  except FileNotFoundError:
    print("input file \""+inputFile+"\" not found. Terminating")
    return 1; #Exit with error
    
  #Update youtube-dl in a thread
  updateThread = threading.Thread(target = os.system, args = ("start /WAIT youtube-dl -U",))
  updateThread.start()
  
  print("Generating playlist songs and folders")
  for playlist in mainList.values():
    #Generate song lists from internet sources
    if not playlist.initialized:
      playlist.generateSongList()
    playlist.parseAllSongs()
    #Make folder if not existing
    if not os.path.exists(path(playlist.getFolder())):
      os.makedirs(path(playlist.getFolder()))
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