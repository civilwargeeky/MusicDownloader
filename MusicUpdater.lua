--MusicUpdater.lua
--by: Daniel Klinger
--This program takes youtube playlists, downloads all songs (converting to mp3)
--  then puts them all in one place and optionally stores them to an attached phone.

--[[In Progress:
  Make folders originally and delete them afterwards
  UI
ToDo:
  Read playlists/names/etc from file instead
  Just downloads list of songs in playlist and checks if they exist, then will download only ones that don't exist.
  ^^ for copying to the android
]]

function copyFile(fromName, toName) --Just copies a sanitized file name
  return os.execute("copy /y "..fromName:sanitize().." "..toName:sanitize())
end
function sanitizeSongName(song)
  song = song:gsub("%b()","") --Remove everything in parentheses
             :gsub("%b[]","") --Same with braces
             :gsub("%s*w?i?t?h? [Ll]yrics?%s*","") --Remove "with Lyrics/lyrics" and spaces
             :gsub("%Wby%W","-") --Replace "by whoever" with "- whoever"
             :gsub(" - An? .+","") --Remove all the "A Minecraft whatever"
             :gsub(" - Original .+","")
             :gsub(" - Minecraft .+","")
             :gsub("\"([^\"]+)\"","%1") --Take things out of quotes
             :gsub("^%s+","") --Remove leading spaces
             :gsub("%s+$","") --Remove trailing spaces
             :gsub("%s+"," ") --Replace all multiple spaces with a single spaces
  return song
end

youtubeDL = {}
youtubeDL.update = function()
  print("Updating Youtube-DL")
  local handle = io.popen("start /WAIT youtube-dl.exe -U") --This opens up the updater in another window. This is the method I found that actually waits for everything to update.
  handle:read() --This stalls the rest of the program while the handle is closed
  handle:close() --Common courtesy
end
youtubeDL.download = function(playlist, outputFolder)
  print("Downloading to folder: "..outputFolder)
  os.execute("youtube-dl.exe -o \""..outputFolder:gsub("\\","/").."/%(title)s.%(ext)s\" -x --audio-format mp3 --audio-quality 0 "..playlist)
end

android = {}
android.adbPath = "C:\\Users\\Daniel\\AppData\\Local\\Android\\sdk\\platform-tools\\adb.exe"
android.start = function()
  io.popen("start "..android.adbPath.." start-server")
end
android.pushFolder = function(folderToPush, name)
  if io.popen(adbPath.." -d get-state"):read() == "device" then
    print("Android device detected! Copying all files to "..name.." directory!")
    --This will start the process and let it take as long as it needs to
    io.popen("start "..android.adbPath.." -d push "..folderToPush:add(name).." /storage/emulated/0/Music/"..name)
  else
    print("No Android Connection, not pushing files")
  end

end

playlist = {}
playlist.tempFolder = "temp" --Relative path
playlist.destFolder = "phoneMusic"
playlist.doneFile = "done.txt"
playlist.playlists = {} --Unordered List
playlist.meta = {__index = playlist }
function playlist:new (url, folder, prefix, exceptions)
  local toReturn = {}
  toReturn.url = url
  toReturn.folder = folder
  toReturn.prefix = prefix
  toReturn.exceptions = exceptions or {}
  setmetatable(toReturn, self.meta)
  
  toReturn.done = false
  toReturn.timeStarted = 0 --Just initializing
  
  playlist.playlists[#playlist.playlists+1] = toReturn
  return toReturn
end

function playlist:handleSongName(name) --Nah screw this, go back and fix this function so it looks nice
  songName = name:sub(1,-5) --Remove .mp3 or whatever
  return (self.prefix and self.prefix.." " or "")..(exceptions[songName] or sanitizeSongName(songName))
end

function playlist:downloadAll() --Expects the "temp" folder already exists
  local destination = self.tempFolder:add(self.folder)
  if not exists(destination) then --Makes a new folder for itself
    mkdir(destination)
  end
  local thread = coroutine.create(youtubeDL.download) --Making a new thread theoretically so that it runs multiple things at once.
  coroutine.resume(self.playlist, self.folder)
end

function playlist:copyFiles() --When all music has downloaded
  local start = self.tempFolder:add(self.folder)
  local finish = self.destFolder:add(self.folder)
  if not exists(finish) then --Make output folder
    mkdir(finish)
  end
  
  --Go through all the files, copy and overwrite in destination
  for file in scan(start) do
    local finalName = self:handleSongName(file)..".mp3"
    if exists(finalName) then
      print("Copying --> "..finalName)
      copyFile(start:add(file), finish:add(finalName))
    end
  end
  
  --If Android is connected, push to android device
  android.pushFolder(self.destFolder, self.folder)
  
  self.done = true
end

---------MAIN PROGRAM----------
print("Initializing Installer")

print("Making temp directory")
if not exists(playlist.tempFolder) then
  mkdir(playlist.tempFolder)
end


