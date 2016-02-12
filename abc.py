class Tab:
  tab = []
  def __init__(self):
    self.tab = []
    
  def addValue(self, value):
    self.tab.append(value)
    
  @classmethod
  def addGlobal(cls, value):
    cls.addValue(cls, value)
    
    
Tab.addGlobal("hello!")
a = Tab()
a.addValue("hey!")
a.addGlobal("test!")

print(Tab.tab)
print(a.tab)
print(type(a).tab)
import sys
print(sys.argv)