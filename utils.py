import tkinter as tk
from tkinter import Toplevel, ttk



def show_help(root):
    help_window = Toplevel(root)
    help_window.title("Help")

    help_text = """
    This tool can be used to get a more accurate and objective measurement of the time 
    an animal spends in a region of interest.
    
    In order to use this program you must have a csv file containing the tracking data
    from a video analyzed by DEEPLABCUT.
    
    This program works by allowing the user to draw any shape on screen and define the 
    shape as a region of interest.
    
    Then it will process the csv file containing the tracking data and count the number
    of frames in which the animal appears within the set region of interest.
    
    This program contains features that allow you to decide which body parts to track
    and what percent of body parts have to be in the defined region(s) for it to determine
    the animal is in the region of interest.
    
    This program is also capable of very quikly generating a plot witch shows the path
    the animal took throughout the video with the regions of interest shown on the plot.
    
    For step by step instructions on how to use this program click the button below.
        
    """
    
    help_label = tk.Label(help_window, text=help_text, justify=tk.CENTER)
    help_label.pack(padx=10, pady=10)

    def show_instructions():
        instructions_window = Toplevel(help_window)
        instructions_window.title("Step-by-Step Instructions")
        instructions_text = """
        Drawing Region of Interest:
            1) Open the video using the "Load Video" button
            2) Select a frame using the popup that has a clear view of the ROI
            3) Use left click to plot points that will connect with a line
            4) Use Right Click when finished drawing to complete and name the ROI
            5) (Optional) Save the ROI to use on other videos that are filmed in the exact same positioning
            6) Load the ROI using the "Load ROI" button to use a previously saved ROI
            7) Click the "Clear Shapes" button to clear the shapes if you want to redefine the ROI
        Plotting:
            1) Open a video to be analyzed
            2) Load or draw ROI
            3) Click "Load CSV" and load the csv data from the video that will be analyzed
            4) Click "Plot"
            5) (Optional) Download Plot from popup window
        Process Time Spent in ROI:
            1) Load the video to be analyzed using "Load Video"
            2) Draw new ROI or load ROI using "Load ROI"
            3) Open the csv file that corresponds with the file you loaded using "Load CSV"
            4) Click "Get Video Segment" and change the start frame and end frame to change the portion of the video to be analyzed
            There are a few different ways to determine when an animal enters into the ROI
            Percentage Mode:(default mode)
                1) By default it is set to detect when at least 50% of the body parts are in the ROI
                2) Click "Change Percentage to change the percent of the animal that needs to be in the ROI
                3) You can also exlude body parts from the tracking data that may skew the results 
                   for example you may exlude the tail of a mouse or if you only wanted to track a specific
                   group of body parts.
                4) Then click "Start Processing"
                5) Look at the results
            Any Body Part Mode:
                1) Click "Any Body Part" to change the mode
                2) Start processing to get the data from when any body part crosses into the ROI
            Body Part Mode:
                1) Click "Body Part Mode"
                2) Click "Start Processing" to get the data from when a specific body part crosses into the ROI
            5) To analyze a different video click "Load Video" load a new video to automatically clear the old ROI
            6) Repeat steps to analyze new videos
        """
        instructions_label = tk.Label(instructions_window, text=instructions_text, justify=tk.LEFT)
        instructions_label.pack(padx=10, pady=10)
        instructions_window.update_idletasks()  # Ensure the window dimensions are calculated
        window_width = instructions_window.winfo_width()
        window_height = instructions_window.winfo_height()
        center_window(instructions_window, window_width, window_height)
        
    instruction_button = tk.Button(help_window, text="Instructions", command=show_instructions)
    instruction_button.pack(padx=10, pady=10)
    help_window.update_idletasks()  # Ensure the window dimensions are calculated
    window_width = help_window.winfo_width()
    window_height = help_window.winfo_height()
    center_window(help_window, window_width, window_height)

def progress_bar(app, max_value):
    app.progress_window = Toplevel(app.root)
    app.progress_window.title("Processing Progress")

    app.progress_label = tk.Label(app.progress_window, text="Processing...")
    app.progress_label.pack()

    app.progress = ttk.Progressbar(app.progress_window, orient=tk.HORIZONTAL, length=300, mode='determinate', maximum=max_value)
    app.progress.pack()

    app.progress_window.update()

def update_progress(app, value):
    app.progress['value'] = value
    app.progress_window.update()

def close_progress_bar(app):
    app.progress_window.destroy()
    
def center_window(window, width, height):
    # Get the screen width and height
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Calculate the position for the window to be centered
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    # Set the geometry of the window
    window.geometry(f'{width}x{height}+{x}+{y}')

        


