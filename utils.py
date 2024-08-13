import tkinter as tk
from tkinter import Toplevel, ttk
import webbrowser
import os
    
def progress_bar(app, max_value):
    #create a new style for the progress bar
    icon_path = os.path.join('assets', 'icon.ico')
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Custom.Horizontal.TProgressbar",
                    troughcolor='#19232D', 
                    background='#4CAF50', 
                    thickness=20)

    app.progress_window = Toplevel(app.root, bg='#19232D')
    app.progress_window.title("Processing Progress")
    app.progress_window.iconbitmap(icon_path)
    
    center_window(app.progress_window, 350, 100)  # Adjust the width and height as needed

    app.progress_label = tk.Label(app.progress_window, text="Processing...", fg='white', bg='#19232D')
    app.progress_label.pack(pady=10)

    app.progress = ttk.Progressbar(app.progress_window, orient=tk.HORIZONTAL, length=300, mode='determinate', maximum=max_value, style="Custom.Horizontal.TProgressbar")
    app.progress.pack(pady=10)

    app.progress_window.update()

def update_progress(app, value):
    app.progress['value'] = value
    app.progress_window.update()

def close_progress_bar(app):
    app.progress_window.destroy()
    
def center_window(window, width, height):
    #get the screen width and height
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    #calculate the position for the window to be centered
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    #set the geometry of the window
    window.geometry(f'{width}x{height}+{x}+{y}')

def open_website(website):
    webbrowser.open(website)
    
def create_custom_entry(parent, text, variable):
    frame = tk.Frame(parent, bg='#19232D')
    label = tk.Label(frame, text=text, bg='#19232D', fg='white')
    label.pack(padx=5, pady=5)
    entry = tk.Entry(frame, textvariable=variable, bg='#455364', fg="white")
    entry.pack(padx=5, pady=5)
    return frame

    
        


