#Display library for the MusicDownloader program
#Has text boxes and display boxes and what have you

import tkinter as tk
from tkinter import ttk

root = None #Global root (only supports one window)

class MainBox(tk.Tk):
  def __init__(self, title = "Window", *args, **kwargs):
    global root
    root = self #Set global for all other window things
    super().__init__(*args, **kwargs)
    self.title(title)
    
class VarLabel(ttk.Label):
  def __init__(self, displayValue, *args, **kwargs):
    self.data = tk.StringVar(root, displayValue)
    self.type = displayValue.__class__ #Store the type of the variable. Var is reconstructed on return
    super().__init__(textvariable = self.data, *args, **kwargs)
    self.pack()
    
  def get(self):
    return self.type(self.data.get()) #Returns the variable as its original type (makes a new object)
  
  def set(self, value): 
    self.data.set(value)
    self.type = value.__class__ #update the class, just in case
    
class VarEntry(ttk.Entry):
  def __init__(self, type = str, *args, **kwargs):
    self.data = tk.StringVar(root, "")
    self.type = type #Store the type of the variable. Var is reconstructed on return
    super().__init__(textvariable = self.data, *args, **kwargs)
    self.pack()
    
  def get(self):
    return self.type(self.data.get()) #Returns the variable as its original type (makes a new object)
    
  def set(self, value): 
    self.data.set(value)
    self.type = value.__class__ #update the class, just in case
    
class VarList(tk.Listbox):
  def __init__(self, dataList, *args, **kwargs):
    self.toRet = None
    self.data = dataList
    super().__init__(*args, **kwargs)
    for val in self.data: #Add all data
      self.insert(tk.END, val)
    self.bind("<ButtonRelease-1>", self.onClick, add="+") #Add a function to auto-set things
    self.pack()
    
  def get(self):
    try:
      toRet = self.curselection()
      if len(toRet) > 0:
        self.toRet = self.data[toRet[0]] #Set object variable
        return self.toRet
      else:
        raise AttributeError("VarList has no item currently selected")
    except: #Its like _tkinter.TclError but nah imports
      return self.toRet
      
  def onClick(self, event):
    self.get()
      
class MessageBox():
  minSize = (200, 200) #Arbitrary size
  def __init__(self, text, title = "Message!", size = None):
    if type(size) == list:
      minSize = size[:]
    root = MainBox(title)
    root.minsize(width = self.minSize[0], height = self.minSize[1])
    VarLabel(text)
    tk.Button(text = "OK", command = lambda _=None: root.destroy()).pack()
    root.mainloop()