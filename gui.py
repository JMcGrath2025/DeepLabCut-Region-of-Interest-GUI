import tkinter as tk
from tkinter import filedialog, Toplevel, simpledialog, messagebox, Listbox, MULTIPLE
from tkinter import ttk
from shapes import ShapeDrawer
from processing import DataProcessor
from video_handling import VideoHandler
from utils import progress_bar, update_progress, close_progress_bar, center_window, open_website, create_custom_entry
import threading
import os
import json
from shapely.geometry import Polygon, MultiPolygon
import pandas as pd
import cv2
import ctypes


def get_scaling_factor():
    #use ctypes to call the necessary Windows APIs
    try:
        awareness = ctypes.c_int()
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Set the awareness level
        ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))

        dpi_x = ctypes.c_uint()
        dpi_y = ctypes.c_uint()
        monitor = ctypes.windll.user32.MonitorFromWindow(ctypes.windll.user32.GetForegroundWindow(), 1)
        ctypes.windll.shcore.GetDpiForMonitor(monitor, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y))

        scaling_factor = dpi_x.value / 96.0  #standard DPI is 96
        return scaling_factor
    except Exception as e:
        print(f"Error obtaining scaling factor: {e}")
        return 1.0  #default to normal scaling if the scaling factor is not available
    
class Application:
    def __init__(self, root):
        #set root and title
        self.root = root
        self.root.title("Region of Interest Tool")
        
        
        #construct the path to the icon file
        self.icon_path = os.path.join('assets', 'icon.ico')
        
        #set the window icon
        self.root.iconbitmap(self.icon_path)
                
        self.root.resizable(False, True)
        
        #define window size based on scaling factor
        scaling_factor = get_scaling_factor()
        self.window_width = 1200
        self.base_window_height = 950
        self.window_height = self.base_window_height
        
        print(scaling_factor)
        if scaling_factor > 1:
            self.window_height = int(self.base_window_height / scaling_factor) 

        #center window on screen
        center_window(self.root, self.window_width, self.window_height)

        self.root.configure(bg='#19232D')

        #define main canvas
        self.main_canvas = tk.Canvas(root, bg='#19232D', bd=0, highlightthickness=0)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        #always add vertical scroll bar if scaling factor is above 100%
        if scaling_factor > 1:
            #vertical scroll bar
            self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.main_canvas.yview)
            self.scrollbar.pack(side=tk.RIGHT, fill="y")
            self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
            self.main_canvas.bind('<Configure>', lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))

            #bind scroll wheel to scrollbar
            self.root.bind_all("<MouseWheel>", self._on_mouse_wheel)

        #create frame inside of canvas to hold other UI
        self.main_frame = tk.Frame(self.main_canvas, bg='#19232D')
        self.main_canvas.create_window((0, 0), window=self.main_frame, anchor="nw")

        #create top frame to hold canvas
        self.top_frame = tk.Frame(self.main_frame, bg='#19232D')
        self.top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(70, 25), pady=10)

        #create bottom frame to hold buttons and labels
        self.bottom_frame = tk.Frame(self.main_frame, bg='#19232D')
        self.bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(70, 25), pady=10)

        #configure columns and rows to expand equally
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.columnconfigure(1, weight=1)
        self.bottom_frame.columnconfigure(2, weight=1)
        self.bottom_frame.rowconfigure(0, weight=1)

        #define left bottom frame
        self.left_frame = tk.Frame(self.bottom_frame, bg='#19232D')
        self.left_frame.grid(row=0, column=0, padx=(20, 50), pady=10, sticky="nsew")

        #define bottom center frame
        self.center_frame = tk.Frame(self.bottom_frame, bg='#19232D')
        self.center_frame.grid(row=0, column=1, padx=(210, 65), pady=10, sticky="nsew")

        #define right bottom frame
        self.right_frame = tk.Frame(self.bottom_frame, bg='#19232D')
        self.right_frame.grid(row=0, column=2, padx=(50, 25), pady=10, sticky="nsew")

        #canvas for drawing ROI
        self.canvas_width = 1056
        self.canvas_height = 594
        self.canvas = tk.Canvas(self.top_frame, bg="#455364", width=self.canvas_width, height=self.canvas_height, bd=0, highlightthickness=0)
        self.canvas.pack()

        #initialize other classes
        self.shape_drawer = ShapeDrawer(self.canvas, self)  #drawing the shape
        self.video_handler = VideoHandler(self)  #handling video data
        self.data_processor = DataProcessor(self)  #processing csv files

        #initialize variables
        self.track_mode = 'majority'  #starting mode
        self.specific_body_part = None  #body part to track
        self.csv_loaded = False  #is the csv file loaded
        self.video_loaded = False
        self.saved_details = []  #the details to save if processing multiple videos at once
        self.previous_excluded_body_parts = set()  #previously excluded body parts
        self.excluded_body_parts = set()
        self.body_parts = set()
        self.percent = .5
        self.zoom_radius_value = tk.StringVar(value="100")
        self.zoom_radius_value.trace("w", self.update_zoom_radius)
        self.start_frame = 0
        self.end_frame = None
        self.fps = None



        #add widgets
        self.setup_widgets()
        self.bind_events()  # Bind click events
    
    
    def setup_widgets(self):
        '''
        Setup the buttons and labels
        '''
        #set up bottom center frame
        self.time_label = tk.Label(self.center_frame, text="Time inside Regions Of Interest:", bg="#19232D", fg='white')
        self.time_label.grid(row=0, column=0, padx=5, pady=5, sticky="n")
    
        self.body_parts_label = tk.Label(self.center_frame, text="Tracking Body Parts:\nNone", wraplength=175, bg="#19232D", fg='white')
        self.body_parts_label.grid(row=3, column=0, padx=5, pady=5, sticky="n")
        
        self.plot_button = self.create_rounded_button(self.center_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Plot", command=self.plot_type_popup)
        self.plot_button.grid(row=5, column=0, padx=5, pady=5, sticky="n")
        
        self.path_button = self.create_rounded_button(self.center_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Pathing", command=self.create_pathing_slideshow)
        self.path_button.grid(row=6, column=0, padx=5, pady=5, sticky="n")
        
        #set up bottom left frame
        self.current_mode_label = tk.Label(self.left_frame, text="Current Mode:\n Majority Mode", bg="#19232D", fg='white')
        self.current_mode_label.grid(row=1, column=0, padx=5, pady=5, sticky="n")
    
        self.load_csv_label = tk.Label(self.left_frame, text="CSV File:\n not loaded", wraplength=100, bg="#19232D", fg='white')
        self.load_csv_label.grid(row=2, column=0, padx=5, pady=5, sticky="n")
        
        self.change_percent_button = self.create_rounded_button(self.left_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Change Percentage", command=self.change_percent)
        self.change_percent_button.grid(row=3, column=0, padx=5, pady=5, sticky="n")
        
        self.percentage_label = tk.Label(self.left_frame, text="Current Percent:\n50%", bg="#19232D", fg='white')
        self.percentage_label.grid(row=4, column=0, padx=5, pady=5, sticky="n")
        
        self.help_button = self.create_rounded_button(self.left_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Instructions", command=self.show_help)
        self.help_button.grid(row=0, column=0, padx=5, pady=5, sticky="n")
    
        #set up bottom right frame
        self.open_video_button = self.create_rounded_button(self.right_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Load Video", command=self.open_video)
        self.open_video_button.grid(row=0, column=0, padx=5, pady=5, sticky="n")
    
        self.open_csv_button = self.create_rounded_button(self.right_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Load Tracking", command=self.open_csv)
        self.open_csv_button.grid(row=1, column=0, padx=5, pady=5, sticky="n")
    
        self.analyze_segment_button = self.create_rounded_button(self.right_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Get Video Segment", command=self.open_segment_selector)
        self.analyze_segment_button.grid(row=1, column=1, padx=5, pady=5, sticky="n")
    
        self.save_zones_button = self.create_rounded_button(self.right_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Save ROI", command=self.save_zones)
        self.save_zones_button.grid(row=2, column=0, padx=5, pady=5, sticky="n")
    
        self.load_zones_button = self.create_rounded_button(self.right_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Load ROI", command=self.load_zones)
        self.load_zones_button.grid(row=2, column=1, padx=5, pady=5, sticky="n")
    
        self.majority_mode_button = self.create_rounded_button(self.right_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Percentage Mode", command=self.switch_to_majority_mode)
        self.majority_mode_button.grid(row=3, column=0, padx=5, pady=5, sticky="n")
    
        self.specific_body_part_mode_button = self.create_rounded_button(self.right_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Body Part Mode", command=self.switch_to_specific_body_part_mode)
        self.specific_body_part_mode_button.grid(row=3, column=1, padx=5, pady=5, sticky="n")
    
        self.any_part_mode_button = self.create_rounded_button(self.right_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Any Part Mode", command=self.switch_to_any_part_mode)
        self.any_part_mode_button.grid(row=4, column=0, padx=5, pady=5, sticky="n")
    
        self.start_button = self.create_rounded_button(self.center_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Start Processing", command=self.start_processing)
        self.start_button.grid(row=2, column=0, padx=5, pady=5, sticky="n")
        self.start_button.config(state=tk.DISABLED) # Disable initially
    
        self.clear_shapes_button = self.create_rounded_button(self.right_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Clear Shapes", command=self.clear_shapes)
        self.clear_shapes_button.grid(row=0, column=1, padx=5, pady=5, sticky="n")
    
        self.exclude_body_parts_button = self.create_rounded_button(self.right_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Exclude Body Parts", command=self.exclude_body_parts)
        self.exclude_body_parts_button.grid(row=4, column=1, padx=5, pady=5, sticky="n")
    
        self.process_saved_details_button = self.create_rounded_button(self.right_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Process Saved Details", command=self.process_saved_details)
        self.process_saved_details_button.grid(row=5, column=1, padx=5, pady=5, sticky="n")
    
        self.show_saved_details_button = self.create_rounded_button(self.right_frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Save Details", command=self.save_details_and_show)
        self.show_saved_details_button.grid(row=5, column=0, padx=5, pady=5, sticky="n")
        
    def _on_mouse_wheel(self, event):
        self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _adjust_color(self, color, amount):
        '''
        This function changes the darkens the shape of the color when the button is pressed
        '''
        import colorsys
        color = self.root.winfo_rgb(color)
        color = [x/65535 for x in color]
        color = colorsys.rgb_to_hls(*color)
        color = list(color)
        color[1] = max(0, min(1, color[1] + amount))
        color = colorsys.hls_to_rgb(*color)
        color = [int(x * 255) for x in color]
        return "#%02x%02x%02x" % tuple(color)
    
    
    def create_rounded_button(self, parent, width, height, corner_radius, bg_color, fg_color, text, command=None):
        '''
        This function creates a button with rounded corners
        '''
        
        button = tk.Canvas(parent, borderwidth=0, highlightthickness=0, background=parent["background"],
                           width=width, height=height)
        
        pressed_color = self._adjust_color(bg_color, -0.2)
        released_color = bg_color
        
        def draw_button(canvas, color, width, height, corner_radius, text, fg_color):
            '''
            This function creates the shapes of the rounded buttons
            '''
            canvas.delete("all")  # clear the canvas
            if corner_radius > height / 2:
                corner_radius = height / 2
            if corner_radius > width / 2:
                corner_radius = width / 2
    
            canvas.create_arc((0, 0, corner_radius * 2, corner_radius * 2), start=90, extent=90, fill=color, outline=color)
            canvas.create_arc((width - corner_radius * 2, 0, width, corner_radius * 2), start=0, extent=90, fill=color, outline=color)
            canvas.create_arc((0, height - corner_radius * 2, corner_radius * 2, height), start=180, extent=90, fill=color, outline=color)
            canvas.create_arc((width - corner_radius * 2, height - corner_radius * 2, width, height), start=270, extent=90, fill=color, outline=color)
    
            canvas.create_rectangle((corner_radius, 0, width - corner_radius, height), fill=color, outline=color)
            canvas.create_rectangle((0, corner_radius, width, height - corner_radius), fill=color, outline=color)
    
            canvas.create_text(width / 2, height / 2, text=text, fill=fg_color, font=("Helvetica", 9), anchor="center")
        
        def on_press(event=None):
            draw_button(button, pressed_color, width, height, corner_radius, text, fg_color)
        
        def on_release(event=None):
            draw_button(button, released_color, width, height, corner_radius, text, fg_color)
            if command:
                command()
    
        draw_button(button, released_color, width, height, corner_radius, text, fg_color)
        button.bind("<ButtonPress-1>", on_press)
        button.bind("<ButtonRelease-1>", on_release)
        
        #bind the Enter key to the button press and release actions
        parent.bind("<Return>", on_press)
        parent.bind("<Return>", on_release)
    
        return button

    
    def bind_events(self):
        '''
        This function binds the right and left click to add points and complete the ROI shape
        '''
        self.canvas.bind("<Button-1>", self.shape_drawer.add_point)
        self.canvas.bind("<Button-3>", self.shape_drawer.complete_shape)
        self.canvas.bind("<Motion>", lambda e: self.shape_drawer.mouse_move(e))
        self.root.bind("<Shift_L>", lambda e: self.shape_drawer.shift_press(e))
        self.root.bind("<KeyRelease-Shift_L>", lambda e: self.shape_drawer.shift_release(e))
        self.root.bind("<space>", self.shape_drawer.complete_rectangle)
        
    
    def switch_to_majority_mode(self):
        '''
        This Function changes the mode back to majority mode which is the default mode wher 50% or more body parts need to be in the ROI
        '''
        self.track_mode = 'majority'
        self.specific_body_part = None #clear the specific body part to track
        self.update_mode_label() #update the mode label
    
    def switch_to_specific_body_part_mode(self):
        '''
        This function changes the mode to specific body part mode which will track only one part of the animals body
        '''
        #switch the tracking mode
        self.track_mode = 'specific'

        #create a popup window to prompt which body part to switch to
        body_part_popup = Toplevel(self.root, bg='#19232D')
        body_part_popup.title("Select Body Part")
        body_part_popup.geometry("250x250")
        body_part_popup.update_idletasks()
        #center the window
        window_width = body_part_popup.winfo_width()
        window_height = body_part_popup.winfo_height()
        center_window(body_part_popup, window_width, window_height)
        
        def on_select():
            '''
            This function selects the body part to track and stores it to process just the specific body part
            '''
            selected_body_part_index = listbox.curselection()
            if selected_body_part_index:
                body_part = self.body_parts[selected_body_part_index[0]]
                body_part_popup.destroy()
                self.specific_body_part = body_part #store the specific body part to process
                self.update_mode_label()
                self.update_body_part_label([self.specific_body_part])
            else:
                self.custom_messagebox("Error", "No body part selected.", "#19232D", "white")

        #create a frame to hold the body part popup
        frame = tk.Frame(body_part_popup, bg='#19232D')
        frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        #define the listbox to hold the body parts from the body part set
        listbox = Listbox(frame, selectmode=tk.SINGLE, bg='#455364', fg='white', bd=0, highlightthickness=0)
        for part in self.body_parts:
            listbox.insert(tk.END, part)
        listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        #create a select button
        select_button = self.create_rounded_button(frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Apply", command=on_select)
        select_button.pack(side=tk.BOTTOM, pady=10)

        body_part_popup.mainloop()
    
    def switch_to_any_part_mode(self):
        '''
        This function switches to the any body part mode which finds out how long any one of the body parts is in the ROI
        '''
        self.track_mode = 'any_part'
        self.specific_body_part = None #clear specific body part
        self.update_mode_label()
        self.update_body_part_label(self.body_parts)
    
    def update_mode_label(self):
        '''
        This function changes the label that shows which mode the program is currently operating in
        '''
        mode_text = {
            'majority': '\nMajority Mode',
            'specific': f'\nSpecific Body Part: \n{self.specific_body_part}',
            'any_part': '\nAny Part Mode'
        }
        #change the current label
        self.current_mode_label.config(text=f"Current Mode: {mode_text[self.track_mode]}")
    
    def update_csv_label(self, file_path):
        '''
        This function changes the label that shows the csv file that is loaded
        '''
        #change the csv label
        base_name = os.path.basename(file_path)
        display_name = (base_name[:27] + '...') if len(base_name) > 30 else base_name
        self.load_csv_label.config(text=f"CSV File: \n{display_name} loaded")
    
    def update_time_labels(self):
        '''
        This function update the time labels to show the time spent in each defined ROI
        '''
        time_text = "Time inside Regions Of Interest:\n"
        for roi_name, time in self.shape_drawer.time_counters.items(): #find the time spent in regions of interest
            time_text += f"{roi_name}: {time:.2f} seconds\n"
        self.time_label.config(text=time_text)
    
    def start_processing(self):
        '''
        This function starts processing the each frame in the video and returns the time spent in each ROI
        '''
        if self.csv_loaded: #only process if the csv is loaded
            threading.Thread(target=self.data_processor.verify_frames).start()
            threading.Thread(target=self.data_processor.check_body_parts_in_shapes).start()

    
    def load_zones(self):
            '''
            This function loads the polygons which make up the ROI's from a .json file which contains the points of the polygon.
            '''
            file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")]) # Open the .json file holding polygon data
            if file_path: 
                with open(file_path, 'r') as f: #load the file
                    loaded_shapes = json.load(f)
                    
                for shape_name, points in loaded_shapes.items():
                    #check if the points represent a single polygon or multiple polygons
                    if isinstance(points[0][0], (float, int)): #its a single polygon if the first element is a tuple of coords
                        loaded_polygon = Polygon(points)
                    else: #multipolygon
                        polygons = [Polygon(p) for p in points]
                        loaded_polygon = MultiPolygon(polygons)
                    
                    if shape_name in self.shape_drawer.shapes:
                        #combine with existing polygon
                        self.shape_drawer.shapes[shape_name] = self.shape_drawer.shapes[shape_name].union(loaded_polygon)
                    else:
                        self.shape_drawer.shapes[shape_name] = loaded_polygon
                    
                    #draw the combined or new polygon onto the canvas
                    for geom in loaded_polygon.geoms if isinstance(loaded_polygon, MultiPolygon) else [loaded_polygon]:
                        self.canvas.create_polygon(list(geom.exterior.coords), outline=self.shape_drawer.current_color, fill='', width=3, tags='shape')
                        self.shape_drawer.current_color = self.shape_drawer.get_random_color() 
                
                print(f"Zones loaded from {file_path}")

    def save_zones(self):
        '''
        This function saves the ROI's that you draw on the canvas so you can load them later.
        '''
        if not self.shape_drawer.shapes:
            print("No zones to save.")
            return
        
        #create the file to save the zones to
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path: #if the file is specified
            shapes_to_save = {}
            
            for name, polygon in self.shape_drawer.shapes.items():
                if isinstance(polygon, Polygon):
                    #if it's a single polygon save the exterior coords
                    shapes_to_save[name] = list(polygon.exterior.coords)
                elif isinstance(polygon, MultiPolygon):
                    #if it's a multipolygon save all exterior coords of the contained polygons
                    shapes_to_save[name] = [list(poly.exterior.coords) for poly in polygon.geoms]
            
            with open(file_path, 'w') as f:
                json.dump(shapes_to_save, f)
            print(f"Zones saved to {file_path}")
    
    def exclude_body_parts(self):
        '''
        This function excludes body parts while processing if there are body parts that could be disregarded
        '''
        if not hasattr(self, 'body_parts') or not self.body_parts:
            self.custom_messagebox("Warning", "Please load a CSV file first.", "#19232D", "white")  #load the CSV file first to get body parts
            return

        #bring the excluded window to the top level
        self.exclude_window = Toplevel(self.root)
        self.exclude_window.title("Exclude Body Parts")
        self.exclude_window.configure(bg='#19232D')
        self.exclude_window.geometry("250x250")
        self.exclude_window.iconbitmap(self.icon_path)
        center_window(self.exclude_window, 250, 250)
        frame = tk.Frame(self.exclude_window, bg='#19232D')
        frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        #create listbox for body parts
        self.excluded_body_parts_vars = {}
        listbox = Listbox(frame, selectmode=tk.MULTIPLE, bg="#455364", fg="white", bd=0, highlightthickness=0)
        for body_part in self.body_parts:
            listbox.insert(tk.END, body_part)
            if body_part in self.excluded_body_parts:
                listbox.selection_set(tk.END)

        listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        def apply_exclusions():
            selected_indices = listbox.curselection()
            self.excluded_body_parts = {self.body_parts[i] for i in selected_indices}
            self.previous_excluded_body_parts = self.excluded_body_parts.copy()
            self.exclude_window.destroy()
            self.update_body_part_label([bp for bp in self.body_parts if bp not in self.excluded_body_parts])

        #use create_rounded_button method for the Apply button
        apply_button = self.create_rounded_button(frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Apply", command=apply_exclusions
        )
        apply_button.pack(side=tk.BOTTOM, pady=10)
        
    
    def update_body_part_label(self, body_parts):
        '''
        This function update the body parts that are going to be processes
        '''
        body_parts_text = "Tracking Body Parts:\n" + ", ".join(body_parts)
        self.body_parts_label.config(text=body_parts_text)
        
    
    def change_percent(self):
        '''
        This function changes the percent of the body parts that have to appear within the ROI to start the time
        '''
        
        #create a custom dialog
        dialog = tk.Toplevel()
        dialog.title("Input")
        dialog.config(bg="#19232D")
        dialog.geometry("250x175")
        dialog.iconbitmap(self.icon_path)
        tk.Label(dialog, text="Enter Percent of Animal in ROI:", bg="#19232D", fg="white").pack(pady=10)
        entry = tk.Entry(dialog, bg="#455364", fg="white")
        entry.pack(pady=10)
        
        def on_apply():
            try:
                #convert the input to an integer
                percent_value = int(entry.get())
                
                #check if it's within the range 0 to 100
                if 0 <= percent_value <= 100:
                    percent = percent_value / 100
                    percentage_text = f"Current Percent:\n{percent * 100:.0f}%"
                    self.percentage_label.config(text=percentage_text)
                    self.percent = percent
                    print(self.percent)
                    dialog.destroy()
                else:
                    self.custom_messagebox("Error", "Invalid Input - Enter an integer between 0 and 100.", "#19232D", "white")
            
            except ValueError:
                #handle the case where the input is not an integer
                self.custom_messagebox("Error", "Invalid Input - Enter an integer between 0 and 100.", "#19232D", "white")
        
        self.create_rounded_button(dialog, 130, 40, 20, "#455364", "white", "Apply", command=on_apply).pack(pady=10)
        center_window(dialog, 250, 175)
        
        
    def update_zoom_radius(self, *args):
        '''
        This function updates how far to zoom in onto an image when plotting it
        '''
        try:
            self.zoom_radius = int(self.zoom_radius_value.get())
            print(f"Zoom radius updated to: {self.zoom_radius}")
        except ValueError:
            #handle the case where the entered value is not a valid integer
            self.zoom_radius = 100
            print(f"Invalid entry. Zoom radius reset to: {self.zoom_radius}")
        
    def clear_shapes(self):
        '''
        This function clears the shapes and the labels
        '''
        self.shape_drawer.clear_shapes()
        self.update_time_labels()
        print("All shapes cleared.")
    
    def frame_to_time(self, frame_number):
        '''
        This function finds the number of frames in standard time format
        '''
        total_seconds = frame_number / self.fps
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def save_details_and_show(self):
        '''
        This function saves multiple different sets of details to process all at once.
        '''
        if not hasattr(self, 'cap') or not hasattr(self, 'data'):
            self.custom_messagebox("Error", "Please load a video and a CSV file first.", "#19232D", "white")
            return
    
        if not hasattr(self, 'start_frame') or not hasattr(self, 'end_frame'):
            self.custom_messagebox("Error", "Please select a segment of the video.", "#19232D", "white")
            return
    
        if not self.shape_drawer.shapes:
            self.custom_messagebox("Error", "Please load or draw ROI's", "#19232D", "white")
            return
    
        name_popup = tk.Toplevel()
        name_popup.title("Enter Details Name")
        name_popup.configure(bg="#19232D")
        name_popup.iconbitmap(self.icon_path)
        name_popup.geometry("250x150")
    
        name_label = tk.Label(name_popup, text="Enter details name: ", bg="#19232D", fg="white")
        name_label.pack(pady=10)
        name_entry = tk.Entry(name_popup, width=25)
        name_entry.pack(pady=10)
        name_entry.configure(bg="#455364", fg="white")
    
        def on_apply():
            details_name = name_entry.get().strip()
            if not details_name:
                self.custom_messagebox("Details Not Named", "Please enter a name for the saved details", "#19232D", "white")
                return 
    
            details = {
                'name': details_name,
                'video_path': self.video_path,
                'csv_path': self.data_processor.file_path,
                'start_frame': self.start_frame,
                'end_frame': self.end_frame,
                'shapes': {
                    name: (
                        [list(polygon.exterior.coords) for polygon in shape.geoms]
                        if isinstance(shape, MultiPolygon)
                        else list(shape.exterior.coords)
                    )
                    for name, shape in self.shape_drawer.shapes.items()
                },
                'excluded_body_parts': list(self.excluded_body_parts),
                'mode': self.track_mode  
            }
    
            self.saved_details.append(details)
            name_popup.destroy()
            self.show_saved_details_window()
    
        apply_button = self.create_rounded_button(name_popup, 130, 40, 15, "#455364", "white", "Apply", command=on_apply)
        apply_button.pack(pady=10, padx=20)
        center_window(name_popup, 250, 150)
    
    def process_saved_details(self):
        '''
        This function processes all the saved details all at once and can output a CSV file containing the time spent in each ROI.
        '''
        if not self.saved_details:
            self.custom_messagebox("Error", "No details saved to process.", "#19232D", "white")
            return
    
        results = []
    
        for i, details in enumerate(self.saved_details):
            #load video
            self.cap = cv2.VideoCapture(details['video_path'])
            if not self.cap.isOpened():
                print(f"Error: Could not open video {details['video_path']}.")
                continue
    
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.frame_duration = 1.0 / self.fps
            self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
            #load CSV
            self.data = pd.read_csv(details['csv_path'], header=[0, 1, 2])
            self.csv_loaded = True
            self.start_frame = details['start_frame']
            self.end_frame = details['end_frame']
    
            #load ROIs
            self.shape_drawer.shapes = {}
            for name, points in details['shapes'].items():
                if isinstance(points[0][0], (float, int)):
                    #single polygon
                    self.shape_drawer.shapes[name] = Polygon(points)
                else:
                    #multipolygon (ROIs with same names)
                    self.shape_drawer.shapes[name] = MultiPolygon([Polygon(p) for p in points])
    
            self.excluded_body_parts = set(details['excluded_body_parts'])
    
            #process each video segment
            self.data_processor.verify_frames()
            self.data_processor.check_body_parts_in_shapes()
    
            #convert frame numbers to HH:MM:SS format
            start_time = self.frame_to_time(self.start_frame)
            end_time = self.frame_to_time(self.end_frame)
    
            #prepare result for this video
            result = {
                'details_name': details['name'],
                'video_file': details['video_path'],
                'mode': details['mode'],
                'start_time': start_time,
                'end_time': end_time
            }
            for shape_name, time in self.shape_drawer.time_counters.items():
                result[shape_name] = time
            results.append(result)
    
        #save results to a single CSV
        if results:
            results_df = pd.DataFrame(results)
            results_file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if results_file_path:
                results_df.to_csv(results_file_path, index=False)
                self.custom_messagebox("Success", f"Results saved to {results_file_path}.", "#19232D", "white")
                
    def show_saved_details_window(self):
        '''
        This function shows a window with the details of what will be processed in the saved details
        '''
        if hasattr(self, 'saved_details_window') and self.saved_details_window.winfo_exists():
            self.update_saved_details_listbox()
            self.saved_details_window.lift()
            return
        
        #create a new Toplevel window
        self.saved_details_window = Toplevel(self.root)
        self.saved_details_window.title("Saved Details")
        self.saved_details_window.geometry("300x400")
        self.saved_details_window.configure(bg="#19232D")
        self.saved_details_window.iconbitmap(self.icon_path)
        #self.saved_details_window.iconbitmap(self.icon_path)
        center_window(self.saved_details_window, 300, 400)
    
        #create a listbox to display saved details
        self.saved_details_listbox = Listbox(self.saved_details_window, selectmode=MULTIPLE, bg="#455364", fg="white", bd=0, highlightthickness=0)
        self.saved_details_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
        #add saved details to the listbox
        self.update_saved_details_listbox()
    
        #add a delete button
        delete_button = self.create_rounded_button(self.saved_details_window, 130, 40, 15, "#455364", "white", "Delete Detail", command=self.delete_selected_details)
        delete_button.pack(pady=10)
    
    def update_saved_details_listbox(self):
        '''
        This function updates the listbox that shows some details in the popupwindow like video path, start time, and end time
        '''
        self.saved_details_listbox.delete(0, tk.END)
        for i, detail in enumerate(self.saved_details):
            video_name = os.path.basename(detail['video_path'])
            start_time = self.frame_to_time(detail['start_frame'])
            end_time = self.frame_to_time(detail['end_frame'])
            detail_name = detail['name']
            self.saved_details_listbox.insert(tk.END, f"{i+1}.) {detail_name}: {video_name}, {start_time} - {end_time}")
    
    def delete_selected_details(self):
        '''
        This function deletes details to be processed in the saved details
        '''
        selected_indices = self.saved_details_listbox.curselection()
        if not selected_indices:
            self.custom_messagebox("Warning", "No details selected to delete.", bg_color="#19232D", fg_color="white")
            return
        
        for index in reversed(selected_indices):
            del self.saved_details[index]
        self.update_saved_details_listbox()
    
    def custom_messagebox(self, title, message, bg_color, fg_color):
        '''
        This function creates a custom messagebox that can be styled unlike a simple messagebox
        '''
        msg_box = Toplevel()
        msg_box.title(title)
        msg_box.configure(bg=bg_color)
        msg_box.iconbitmap(self.icon_path)
        msg_box.lift()
        msg_box.focus_force()
        #center the window
        window_width = 300
        window_height = 150
        screen_width = msg_box.winfo_screenwidth()
        screen_height = msg_box.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        msg_box.geometry(f'{window_width}x{window_height}+{x}+{y}')
    
        tk.Label(msg_box, text=message, bg=bg_color, fg=fg_color, wraplength=250).pack(pady=20, padx=20)
        
        def close_messagebox():
            msg_box.destroy()
    
        ok_button = self.create_rounded_button(msg_box, width=130, height=40, corner_radius=15, bg_color='#455364', fg_color='white', text="OK", command=close_messagebox)
        ok_button.pack()
        
    def show_help(self):

        
        help_window = Toplevel(self.root)
        help_window.title("Help")
        help_window.configure(bg="#19232D")
        help_window.iconbitmap(self.icon_path)

        def show_plotting_instructions():
            instructions_window = Toplevel(help_window)
            instructions_window.title("Step-by-Step Plotting Instructions")
            instructions_window.configure(bg="#19232D")
            instructions_window.iconbitmap(self.icon_path)
            instructions_text = """
            Plotting Graphs:
                How to plot the tracking data in different ways
                1) Load the video using the "Load Video" button
                2) Load the CSV file by using the "Load CSV" button
                3) (Optional) Select a video segment from the loaded video
                4) (Optional) Draw or load regions of interest
                5) Press the "Plot" button
                6) Select the body part you would like to plot and press "Select"
                7) (Optional) Click checkboxes to manipulate how the data will be plotted
                    A) "Show Bounding Box" will show an outline that encapsulates all the plotted points
                    B) "Show ROIs" will show the regions of interest overtop of the plot
                    C) "Show Area Under Curve" will show the area under curve displayed on the graph
                    D) "Square Graph" will show the graph displayed in equal aspect ratio instead of landscape
                    E) "Plot Over Video" will show the plot over the last frame in the selected segment
                    F) "Zoom In" will show a zoomed in version of the graph
                    G) "Zoom In Radius" entry box shows the radius around the center point of the tracking data
                8) After selecting checkboxes click "Apply"
                9) (Optional) Click "Download" and save plot
            """
            
            instructions_label = tk.Label(instructions_window, text=instructions_text, justify=tk.LEFT, bg="#19232D", fg="white", font=16)
            instructions_label.pack(padx=10, pady=10)
            instructions_window.update_idletasks()  # Ensure the window dimensions are calculated
            window_width = instructions_window.winfo_width()
            window_height = instructions_window.winfo_height()
            center_window(instructions_window, window_width, window_height)
            
        
        def show_pathing_instructions():
            instructions_window = Toplevel(help_window)
            instructions_window.title("Step-by-Step Pathing Instructions")
            instructions_window.configure(bg="#19232D")
            instructions_window.iconbitmap(self.icon_path)
            instructions_text = """
            Pathing Instructions:
                1) Load video using "Load Video" button
                2) Load tracking data using "Load CSV" button
                3) (Optional) Select the video segment using the "Select Segment" button
                4) Click the "Pathing" button
                5) Use the "D" key to move forward through the video
                6) Use the "A" key to move backwards through the video
                7) Use the "space-bar" to pause the video
            """
            pathing_controls_text = """
            Pathing Controls
            ===================
            "D" - moves slideshow towards the end of the video
            "A" - moves slideshow backwards to the start of the video
            "Spave-Bar" - pauses the slideshow
            """
            pathing_control_label = tk.Label(instructions_window, text=pathing_controls_text, justify=tk.LEFT, bg="#19232D", fg="white", font=16)
            pathing_control_label.pack(padx=10, pady=(10, 0))
            instructions_label = tk.Label(instructions_window, text=instructions_text, justify=tk.LEFT, bg="#19232D", fg="white", font=16)
            instructions_label.pack(padx=10, pady=10)
            instructions_window.update_idletasks()  # Ensure the window dimensions are calculated
            window_width = instructions_window.winfo_width()
            window_height = instructions_window.winfo_height()
            center_window(instructions_window, window_width, window_height)
            
            
        def show_roi_instructions():
            instructions_window = Toplevel(help_window)
            instructions_window.title("Step-by-Step ROI Instructions")
            instructions_window.configure(bg="#19232D")
            instructions_window.iconbitmap(self.icon_path)
            instructions_text = """
            Drawing Region of Interest:
                How to draw shapes on the video frame to define the regions of interest
                1) Open the video using the "Load Video" button
                2) Select a frame using the popup that has a clear view of the ROI
                3) Use left click to plot points that will connect with a line
                4) Use Right Click when finished drawing to complete and name the ROI
                5) (Optional) Save the ROI to use on other videos that are filmed in the exact same positioning
                6) Load the ROI using the "Load ROI" button to use a previously saved ROI
                7) Click the "Clear Shapes" button to clear the shapes if you want to redefine the ROI
            Process Time Spent in ROI:
                How to process a single segment of a video at a time
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
            Batch Processing:
                How to process multiple different details across the same video or multiple different videos
                1) Follow the steps for processing time spent in an ROI normally but do not press the "Start Processing"
                2) Instead of pressing "Start Processing" click save details
                3) Select and delete any details to not be processed using the "Delete" button
                4) Once all details are selected across all videos to be processed press "Process Saved Details"
                5) Once done processing all details save the csv file with all of the data
            """
            controls_text = """
            ROI Drawing
            ==============
            "Left-Click" - plots a point on the canvas
            "Left-Shift-Hold" - create straight line between points
            "Right-Click" - completes shape
            "Space-Bar" - plots 4th point to make perfect rectangle
            """
            roi_controls_label = tk.Label(instructions_window, text=controls_text, justify=tk.LEFT, bg="#19232D", fg="white", font=16)
            roi_controls_label.pack(padx=10, pady=(10,0))
            instructions_label = tk.Label(instructions_window, text=instructions_text, justify=tk.LEFT, bg="#19232D", fg="white", font=16)
            instructions_label.pack(padx=10, pady=10)
            instructions_window.update_idletasks()  # Ensure the window dimensions are calculated
            window_width = instructions_window.winfo_width()
            window_height = instructions_window.winfo_height()
            center_window(instructions_window, window_width, window_height)
            
        #controls_label = tk.Label(help_window, text=controls_text, anchor="center", justify="left", bg="#19232D", fg="white", font=12)
        #controls_label.pack(pady=(10, 5), padx=10, fill=tk.BOTH, expand=True)
            
        roi_button = self.create_rounded_button(help_window, 180, 40, 15, "#455364", "white", "Region Of Interest Instructions", command=show_roi_instructions)
        roi_button.pack(padx=10, pady=(10, 10))
        plotting_button = self.create_rounded_button(help_window, 180, 40, 15, "#455364", "white", "Plotting Instructions", command=show_plotting_instructions)
        plotting_button.pack(padx=10, pady=(10, 10))
        
        #pathing_control_label = tk.Label(help_window, text=pathing_controls_text, anchor="center", justify="left", bg="#19232D", fg="white", font=12)
        #pathing_control_label.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        pathing_button = self.create_rounded_button(help_window, 180, 40, 15, "#455364", "white", "Pathing Instructions", command=show_pathing_instructions)
        pathing_button.pack(padx=10, pady=(10, 10))
        
        link_label = tk.Label(help_window, text="Intructions with pictures on Github and video tutorial on Youtube", bg="#19232D", fg="white", font=12)
        link_label.pack(padx=10, pady=10)
        github_button = self.create_rounded_button(help_window, 180, 40, 15, "#455364", "white", "GitHub", command=lambda: open_website("https://github.com/JMcGrath2025/DeepLabCut-Region-of-Interest-GUI/blob/master/README.md"))
        github_button.pack(padx=10, pady=(10, 10))
        yt_button = self.create_rounded_button(help_window, 180, 40, 15, "#455364", "white", "YouTube")
        yt_button.pack(padx=10, pady=(10, 10))
        
        help_window.update_idletasks()  #ensure the window dimensions are calculated
        window_width = help_window.winfo_width()
        window_height = help_window.winfo_height()
        center_window(help_window, window_width, window_height)
    
    def plot_type_popup(self):
        '''
        This function creates a popup that decides which way the data will be plotted
        '''
        
        #create the popup window
        popup = Toplevel()
        popup.title("Plot Type")
        popup.configure(bg="#19232D")
        popup.iconbitmap(self.icon_path)
        popup.geometry("300x200")
        
        #center window
        center_window(popup, 300, 200)
        
        
        if self.video_loaded and self.csv_loaded:
            #create a label
            tk.Label(popup, text="Select Plotting Option", bg="#19232D", fg="white", font=12).pack(pady=5)
            #create buttons for each type of plot
            self.create_rounded_button(popup, 130, 40, 20, "#455364", "white", "Plot Location", command=self.plot).pack(pady=5)            
            self.create_rounded_button(popup, 130, 40, 20, "#455364", "white", "Plot Speed", command=self.data_processor.plot_speed).pack(pady=5)           
            self.create_rounded_button(popup, 130, 40, 20, "#455364", "white", "Plot Velocity", command=self.data_processor.plot_velocity).pack(pady=5)
            
        else: #if the tracking file and video file are not loaded show the message box 
            self.custom_messagebox("Error", "Please load video and tracking file.", "#19232D", "white")
        
                
        
    '''
    These are getter functions to get functions from other files
    '''
    def progress_bar(self, max_value):
        #get method for the progress bar
        progress_bar(self, max_value)
    
    def update_progress(self, value):
        #get method to update progress
        update_progress(self, value)
    
    def close_progress_bar(self):
        #get method to close progress bar
        close_progress_bar(self)
        
    def open_video(self):
        #open video button from video handler object for the button
        self.video_handler.open_video()
    
    def open_csv(self):
        #open csv from the processor object for the button
        self.data_processor.open_file()
        
    def create_pathing_slideshow(self):
        self.data_processor.create_pathing_slideshow()
        
    def plot(self):
        self.data_processor.plot_data()
    
    def open_segment_selector(self):
        #get the segment selector for the button
        self.video_handler.open_segment_selector()
        
        


