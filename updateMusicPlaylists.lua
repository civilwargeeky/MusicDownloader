--This will go to all my music playlists and update the videos within each, then sort them into a folder and copy them to my phone.
local baseFolder = "temp"
local finalFolder = "phoneMusic"
local doneFile = "done.txt"
local simulate = false
local deleteLocal = true
local adbPath = "C:\\Users\\Daniel\\AppData\\Local\\Android\\sdk\\platform-tools\\adb.exe"

dofile("modpackFileAPI.lua")
--[[
if not exists(finalFolder) then
  mkdir(finalFolder) --Make sure this exists, I think stuff will error, can't be sure
end
]]

local urls = {
  Dubstep = "https://www.youtube.com/playlist?list=PLeihsqiyYb0E_Ny6jBSvNdqYwKDQGEns1",
  Shanties = "https://www.youtube.com/playlist?list=PLeihsqiyYb0HmeSfLj9ehwF7P-RcCA8C_",
  Songs = "https://www.youtube.com/playlist?list=PLB859A6DFE9424267",
  Minecraft = "https://www.youtube.com/playlist?list=PLeihsqiyYb0GSJq4WvaYF0hDkjyLRdsNP",
  Other = "https://www.youtube.com/playlist?list=PLeihsqiyYb0GW7OwC54-0k1LxYusZGUSj",
  Rolla = "https://www.youtube.com/playlist?list=PLeihsqiyYb0GHQg1PTMFRwmaCHHBAWxLA"
}
local prefixes = {
  Dubstep = "DUB",
  Shanties = "SHAN",
  Songs = "REG",
  Minecraft = "MC",
}
local exceptions = {
  ["Blue Oyster Cult - (Don't Fear) The Reaper (Audio)"] = "Blue Oyster Cult - Don't Fear The Reaper",
  ["BrySi the Machinima Guy - Never Going Into Nether (Minecraft Parody Taylor Swift 'Never Getting Back Together')"] = "Never Going To The Nether",
  ["Skrillex - Scary Monsters And Nice Sprites (Live Cover by Pinn Panelle)"] = "Pinn Panelle - Scary Monsters And Nice Sprites",
  ["Fall Out Boy - My Songs Know What You Did In The Dark (Light Em Up) - Part 1 of 11"] = "Fall Out Boy - Light Em Up",
}
local updated = {}
local done = {} --For folders

local function capitalize(input)
  return input:sub(1,1):upper() .. input:sub(2)
end
local function handleName(input, prefix) --Will uppercase the first letter of all words
  input = input:gsub("^%s+","",1) --Remove leading whitespace
  if input:sub(1,1) == "'" then --If the first non-whitespace is '
    input = input:match("'([^']+)'")
  end
  return prefix.." "..input:gsub("%w%w+", capitalize)
end
local function alignLeft(input, num)
  while #input < num do
    input = input.." "
  end
  return input
end

local timer
if simulate then
  timer = 1
else
  timer = 5
  
  --os.execute("start /WAIT youtube-dl.exe -U")
  --sleep(10)
  io.popen("start "..adbPath.." start-server")
  
  local handle = io.popen("start /WAIT youtube-dl.exe -U") --This opens up the updater in another window. This is the method I found that actually waits for everything to update.
  handle:read() --This stalls the rest of the program while the handle is closed
  handle:close() --Common courtesy
end

--Download all files (now with coroutines!)
for folder, url in pairs(urls) do
  if not exists(baseFolder:add(folder)) then
    mkDir(baseFolder:add(folder))
  end
  local str = "youtube-dl.exe -o \""..baseFolder.."/"..folder.."/%(title)s.%(ext)s\" -x --audio-format mp3 --audio-quality 0 "..url
  local thread = coroutine.create(function(str, folder)
  print("[Music Updater] Downloading folder: ", folder)
  os.execute("start \""..folder.."\" "..str.." > "..baseFolder:add(folder):add(doneFile):san())
  end)
  if not simulate then coroutine.resume(thread, str, folder) end
end

local folders = {}
for a, b in pairs(urls) do
  table.insert(folders, a)
  print("Inserting ",a)
end

local time = 0 --Time counter
while len(folders) > 0 do --Will keep checking while there are still unfinished folders
  for index, folder in pairs(folders) do --This is so silly. The below works because exists() checks if rename works, which also fails if the file is open, which is what the "start youtube dl" thing is doing
    if exists(baseFolder:add(folder):add(doneFile):san()) then --If the file signifying the program is done is there
      local base, final = baseFolder:add(folder), finalFolder:add(folder)
      if not exists(final) then --Just making sure. Stuff might go wrong
        mkDir(final)
      end
      
      folders[index] = nil --Remove folder from list of waiting
      done[folder] = true --For pretty displaying
      print("Copying files, removing '"..folder.."' from list")
      print("Length of table: ",len(folders),"\n")
      
      for file in scan(base) do
        if file ~= doneFile then --We don't want the doneFile in our music playlist :P
          local songName = handleName(exceptions[file:sub(1,-5)] or file:match("[^%(%.]+"), prefixes[folder] or "")..".mp3" --The regex matches not parentheses and not "."
          local str = final:add(songName)
          if not exists(str) then
            os.execute("copy /y "..base:add(file):sanitize().." "..str:sanitize()) --Not using API function because I want to specify paste name
            table.insert(updated, folder..":   "..songName)
          end
        end
      end
      
      if io.popen(adbPath.." -d get-state"):read() == "device" then
        print("Android device detected! Copying all files")
        io.popen("start "..adbPath.." -d push "..final.." /storage/emulated/0/Music/"..folder)
      else
        print("Android Connection Failed. Ignoring")
      end
      
      break --Because removing screws up pairs()
    end
  end
  if len(folders) > 0 then
    sleep(timer) --Arbitrary sleep
    time = time + timer
    local m = math.floor(time/60)
    local s = time % 60
    print("\n-------------------------------------------------------------------------------")
    print("Running time: "..tostring(m).." Minutes, "..tostring(s).." Seconds | Folders Left: "..tostring(len(folders)))
    for folder, _ in pairs(urls) do
      print(alignLeft(folder..":", 20)..((done[folder] and "DONE") or "PENDING"))
    end
  end
end

print("\n\n\n")
print("Updated Files:\n----------------------")
for i=1, #updated do
  print(updated[i])
end

if deleteLocal and not simulate then
  rmDir(baseFolder)
end
os.execute("echo •") --Bell character