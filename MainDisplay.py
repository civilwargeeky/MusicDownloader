#Main Display Class
#Handles complicated user interface

import tkinter as tk
from tkinter import ttk
import MusicDisplay as Disp

SCRIPTS_FOLDER = "Scripts"

def blankSpace():
  return Disp.VarLabel("", width = 5)

def main():
  root = Disp.MainBox()#.size(200,200)
  Disp.VarButton("Playlist 1").grid(columnspan=5)
  blankSpace().grid(row = 1, column = 0)
  Disp.VarButton("First thing").grid(row = 1, column = 1, columnspan = 4)
  
  
  root.mainloop()
  
if __name__ == "__main__":
  main()