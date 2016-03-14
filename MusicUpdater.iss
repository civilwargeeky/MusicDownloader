;My Installer for the GenerateHeader.py setup
#define _VERSION "1.2.3"

[Setup]
AppName="Music Downloader"
AppVersion={#_VERSION}
DefaultDirName={userdesktop}\MusicDownloader
DisableProgramGroupPage=yes
Compression=lzma2
OutputBaseFilename=MusicDownloader_v{#_VERSION}
SolidCompression=yes
Uninstallable=no
OutputDir="release"

[Files]
Source: "dist\*"; DestDir: "{app}\code"
Source: "dist\Scripts\*"; DestDir: "{app}\code\Scripts"
Source: "lib\*"; DestDir: "{app}\lib"; Flags: recursesubdirs

[Dirs]
Name: "{app}\code\Music"

[Icons]
Name: "{userdesktop}\Music Downloader"; FileName: "{app}\code\MusicUpdater.exe"; WorkingDir: "{app}\code"; IconFilename: "{app}\code\Youtube.ico" 
Name: "{userdesktop}\Music Folder"; Filename: "{app}\code\Music";
Name: "{userdesktop}\Scripts Folder"; Filename: "{app}\code\Scripts";