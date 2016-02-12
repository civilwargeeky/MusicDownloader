@echo off
set /p test=???
youtube-dl.exe -U
youtube-dl.exe -o "Output/%%(title)s.%%(ext)s" -x --audio-format mp3 --audio-quality 0 %test%