# test_tkinter.py
import tkinter as tk

root = tk.Tk()
root.title("Test Window")
label = tk.Label(root, text="If you can see this, tkinter is working!")
label.pack()
root.mainloop()
