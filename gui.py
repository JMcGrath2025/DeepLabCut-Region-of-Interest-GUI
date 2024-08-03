import tkinter as tk
from tkinter import filedialog, Toplevel, simpledialog, messagebox, Listbox, MULTIPLE
from tkinter import ttk
from shapes import ShapeDrawer
from processing import DataProcessor
from video_handling import VideoHandler
from utils import show_help, progress_bar, update_progress, close_progress_bar, center_window
import threading
import os
import json
from shapely.geometry import Polygon
import pandas as pd
import cv2



    
class Application:
    def __init__(self, root):
        #set root and title
        self.root = root
        self.root.title("Region of Interest Tool")
    
        #define window size
        self.window_width = 1100
        self.window_height = 900
        #center window on screen
        center_window(self.root, self.window_width, self.window_height)
        
        #define main canvas
        self.main_canvas = tk.Canvas(root)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        #vertical scroll bar
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.main_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill="y")
        
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.main_canvas.bind('<Configure>', lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))
    
        #create frame inside of canvas to hold other UI
        self.main_frame = tk.Frame(self.main_canvas)
        self.main_canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
    
        #create top frame to hold canvas
        self.top_frame = tk.Frame(self.main_frame)
        self.top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(50, 25), pady=10)
        
        #create bottom frame to hold buttons and labels
        self.bottom_frame = tk.Frame(self.main_frame)
        self.bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(50, 25), pady=10)
        
        #configure columns and rows expand equally
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.columnconfigure(1, weight=1)
        self.bottom_frame.columnconfigure(2, weight=1)
        self.bottom_frame.rowconfigure(0, weight=1)
        
        #define left bottom frame
        self.left_frame = tk.Frame(self.bottom_frame)
        self.left_frame.grid(row=0, column=0, padx=(25, 50), pady=10, sticky="nsew")
        
        #define bottom center frame
        self.center_frame = tk.Frame(self.bottom_frame)
        self.center_frame.grid(row=0, column=1, padx=(200, 75), pady=10, sticky="nsew")
        
        #define right bottom frame
        self.right_frame = tk.Frame(self.bottom_frame)
        self.right_frame.grid(row=0, column=2, padx=(50, 25), pady=10, sticky="nsew")
    
        #canvas for drawing ROI
        self.canvas_width = 960 #dimensions of canvas
        self.canvas_height = 540
        self.canvas = tk.Canvas(self.top_frame, bg="white", width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()
        
    
        #initialize other classes
        self.shape_drawer = ShapeDrawer(self.canvas, self) #drawing the shape
        self.video_handler = VideoHandler(self) #handling video data
        self.data_processor = DataProcessor(self) #processing csv files
    
        #initialize variables
        self.track_mode = 'majority' #starting mode
        self.specific_body_part = None #body part to track
        self.csv_loaded = False #is the csv file is loaded
        self.saved_details = [] #the details to save if processing multiple videos at once
        self.previous_excluded_body_parts = set() #previously excluded body parts
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
        self.bind_events() #bind click events
    
    #set up the labels and buttons
    def setup_widgets(self):
        
        #set up bottom center frame
        self.time_label = tk.Label(self.center_frame, text="Time inside Regions Of Interest:")
        self.time_label.grid(row=0, column=0, padx=5, pady=5, sticky="n")
    
        self.body_parts_label = tk.Label(self.center_frame, text="Tracking Body Parts:\nNone", wraplength=175)
        self.body_parts_label.grid(row=3, column=0, padx=5, pady=5, sticky="n")
        
        self.plot_button = tk.Button(self.center_frame, text="Plot", command=self.plot, width=15, height=2)
        self.plot_button.grid(row=5, column=0, padx=5, pady=5, sticky="n")
        
        self.path_button = tk.Button(self.center_frame, text="Pathing", command=self.create_pathing_slideshow, width=15, height=2)
        self.path_button.grid(row=6, column=0, padx=5, pady=5, sticky="n")
        
        
        #set up bottom left frame
        self.current_mode_label = tk.Label(self.left_frame, text="Current Mode:\n Majority Mode")
        self.current_mode_label.grid(row=1, column=0, padx=5, pady=5, sticky="n")
    
        self.load_csv_label = tk.Label(self.left_frame, text="CSV File:\n not loaded", wraplength=100)
        self.load_csv_label.grid(row=2, column=0, padx=5, pady=5, sticky="n")
        
        self.change_percent_button = tk.Button(self.left_frame, text="Change Percentage", command=self.change_percent, width=15, height=2)
        self.change_percent_button.grid(row=3, column=0, padx=5, pady=5, sticky="n")
        
        self.percentage_label = tk.Label(self.left_frame, text="Current Percent:\n50%")
        self.percentage_label.grid(row=4, column=0, padx=5, pady=5, sticky="n")
        
        self.help_button = tk.Button(self.left_frame, text="Instructions", command=self.show_help, width=15, height=2)
        self.help_button.grid(row=0, column=0, padx=5, pady=5, sticky="n")
    
        #set up bottom right frame
        self.open_video_button = tk.Button(self.right_frame, text="Open Video", command=self.open_video, width=15, height=2)
        self.open_video_button.grid(row=0, column=0, padx=5, pady=5, sticky="n")
    
        self.open_csv_button = tk.Button(self.right_frame, text="Open CSV", command=self.open_csv, width=15, height=2)
        self.open_csv_button.grid(row=1, column=0, padx=5, pady=5, sticky="n")
    
        self.analyze_segment_button = tk.Button(self.right_frame, text="Get Video Segment", command=self.open_segment_selector, width=15, height=2)
        self.analyze_segment_button.grid(row=1, column=1, padx=5, pady=5, sticky="n")
    
        self.save_zones_button = tk.Button(self.right_frame, text="Save ROI", command=self.save_zones, width=15, height=2)
        self.save_zones_button.grid(row=2, column=0, padx=5, pady=5, sticky="n")
    
        self.load_zones_button = tk.Button(self.right_frame, text="Load ROI", command=self.load_zones, width=15, height=2)
        self.load_zones_button.grid(row=2, column=1, padx=5, pady=5, sticky="n")
    
        self.majority_mode_button = tk.Button(self.right_frame, text="Percentage Mode", command=self.switch_to_majority_mode, width=15, height=2)
        self.majority_mode_button.grid(row=3, column=0, padx=5, pady=5, sticky="n")
    
        self.specific_body_part_mode_button = tk.Button(self.right_frame, text="Body Part Mode", command=self.switch_to_specific_body_part_mode, width=15, height=2)
        self.specific_body_part_mode_button.grid(row=3, column=1, padx=5, pady=5, sticky="n")
    
        self.any_part_mode_button = tk.Button(self.right_frame, text="Any Part Mode", command=self.switch_to_any_part_mode, width=15, height=2)
        self.any_part_mode_button.grid(row=4, column=0, padx=5, pady=5, sticky="n")
    
        self.start_button = tk.Button(self.center_frame, text="Start Processing", command=self.start_processing, state=tk.DISABLED, width=15, height=2)
        self.start_button.grid(row=2, column=0, padx=5, pady=5, sticky="n")
    
        self.clear_shapes_button = tk.Button(self.right_frame, text="Clear Shapes", command=self.clear_shapes, width=15, height=2)
        self.clear_shapes_button.grid(row=0, column=1, padx=5, pady=5, sticky="n")
    
        self.exclude_body_parts_button = tk.Button(self.right_frame, text="Exclude Body Parts", command=self.exclude_body_parts, width=15, height=2)
        self.exclude_body_parts_button.grid(row=4, column=1, padx=5, pady=5, sticky="n")
    
        self.process_saved_details_button = tk.Button(self.right_frame, text="Process Saved Details", command=self.process_saved_details, width=15, height=2)
        self.process_saved_details_button.grid(row=5, column=1, padx=5, pady=5, sticky="n")
    
        self.show_saved_details_button = tk.Button(self.right_frame, text="Save Details", command=self.save_details_and_show, width=15, height=2)
        self.show_saved_details_button.grid(row=5, column=0, padx=5, pady=5, sticky="n")
        
    
    def bind_events(self):
        '''
        This function binds the right and left click to add points and complete the ROI shape
        '''
        self.canvas.bind("<Button-1>", self.shape_drawer.add_point)
        self.canvas.bind("<Button-3>", self.shape_drawer.complete_shape)
    
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
        body_part_popup = Toplevel(self.root)
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
                messagebox.showerror("Error", "No body part selected.")

        #create a frame to hold the body part popup
        frame = tk.Frame(body_part_popup)
        frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        #define the listbox to hold the body parts from the body part set
        listbox = Listbox(frame, selectmode=tk.SINGLE)
        for part in self.body_parts:
            listbox.insert(tk.END, part)
        listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        #create a select button
        select_button = tk.Button(frame, text="Select", command=on_select)
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
        This function loads the polygons which make up the ROI's from a .json file which contains the points of the polygon
        '''
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")]) #open the .json file holding polygon data
        if file_path: 
            with open(file_path, 'r') as f: #with the file path open
                self.shape_drawer.shapes = json.load(f)
            for shape_name, points in self.shape_drawer.shapes.items(): #draw each polygon onto the canvas
                self.shape_drawer.shapes[shape_name] = Polygon(points)
                self.canvas.create_polygon(points, outline='black', fill='', width=2, tags='shape')
            print(f"Zones loaded from {file_path}")
    
    def save_zones(self):
        '''
        This function saves the ROI's that you draw on the canvas so you can load them later
        '''
        if not self.shape_drawer.shapes:
            print("No zones to save.")
            return
        #create the file to save the zones to
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path: #if the file is specified 
            shapes_to_save = {name: list(polygon.exterior.coords) for name, polygon in self.shape_drawer.shapes.items()} #save the shapes in a dictionary then save to json file
            with open(file_path, 'w') as f:
                json.dump(shapes_to_save, f)
            print(f"Zones saved to {file_path}")
    
    def exclude_body_parts(self):
        '''
        This function excludes body parts while processing if there are body parts that could be disregarded
        '''
        if not hasattr(self, 'body_parts') or not self.body_parts:
            messagebox.showwarning("Warning", "Please load a CSV file first.")  # Load the CSV file first to get body parts
            return

        #bring the excluded window to the top level
        self.exclude_window = Toplevel(self.root)
        self.exclude_window.title("Exclude Body Parts")  # Title the window "Exclude Body Parts"

        #dictionary that contains excluded body parts
        self.excluded_body_parts_vars = {}
        for body_part in self.body_parts: #create checkbox window for bodyparts
            var = tk.BooleanVar(value=body_part in self.excluded_body_parts)
            chk = tk.Checkbutton(self.exclude_window, text=body_part, variable=var)
            chk.pack(anchor=tk.W)
            self.excluded_body_parts_vars[body_part] = var

        #apply button to apply the exclusions
        self.exclude_button = tk.Button(self.exclude_window, text="Apply", command=self.apply_exclusions)
        self.exclude_button.pack()
        
        #opens the window in the center of the screen
        self.exclude_window.update_idletasks()
        window_width = self.exclude_window.winfo_width()
        window_height = self.exclude_window.winfo_height()
        center_window(self.exclude_window, window_width, window_height)

    def apply_exclusions(self):
        '''
        This function applies the exclusions to the body part set
        '''
        self.excluded_body_parts = {body_part for body_part, var in self.excluded_body_parts_vars.items() if var.get()}
        #store to keep previous excluded body parts for same animal
        self.previous_excluded_body_parts = self.excluded_body_parts.copy()
        self.exclude_window.destroy()
        self.update_body_part_label([bp for bp in self.body_parts if bp not in self.excluded_body_parts])
        
    
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
        percent = simpledialog.askstring("Input", "Enter Percent of Animal in ROI:")
        percent = float(percent) / 100
        percentage_text = f"Current Percent:\n{percent * 100:.0f}%"
        self.percentage_label.config(text=percentage_text)
        self.percent = percent
    
    def update_zoom_radius(self, *args):
        '''
        This function updates how far to zoom in onto an image when plotting it
        '''
        try:
            self.zoom_radius = int(self.zoom_radius_value.get())
            print(f"Zoom radius updated to: {self.zoom_radius}")
        except ValueError:
            # Handle the case where the entered value is not a valid integer
            self.zoom_radius = 100
            print(f"Invalid entry. Zoom radius reset to: {self.zoom_radius}")
        
    
    def clear_shapes(self):
        '''
        This function clears the shapes and the labels
        '''
        self.shape_drawer.clear_shapes()
        self.update_time_labels()  # Reset the time labels to reflect the cleared shapes
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
        This funciton saves multiple different sets of details to process all at once
        '''
        if not hasattr(self, 'cap') or not hasattr(self, 'data'):
            messagebox.showerror("Error", "Please load a video and a CSV file first.")
            return
    
        if not hasattr(self, 'start_frame') or not hasattr(self, 'end_frame'):
            messagebox.showerror("Error", "Please select a segment of the video.")
            return
    
        if not self.shape_drawer.shapes:
            messagebox.showerror("Error", "Please load or draw ROI shapes.")
            return
    
        details = {
            'video_path': self.video_path,  # Use the stored video path
            'csv_path': self.data_processor.file_path,
            'start_frame': self.start_frame,
            'end_frame': self.end_frame,
            'shapes': {name: list(polygon.exterior.coords) for name, polygon in self.shape_drawer.shapes.items()},
            'excluded_body_parts': list(self.excluded_body_parts),
            'mode': self.track_mode  # Save the current mode
        }
    
        self.saved_details.append(details)
        self.show_saved_details_window()
    
    def process_saved_details(self):
        '''
        This function processes all the saved details all at once and can ouput a csv file containing the time spent in each ROI
        '''
        if not self.saved_details:
            messagebox.showerror("Error", "No details saved to process.")
            return
    
        results = []
    
        for i, details in enumerate(self.saved_details):
            # Load video
            self.cap = cv2.VideoCapture(details['video_path'])
            if not self.cap.isOpened():
                print(f"Error: Could not open video {details['video_path']}.")
                continue
    
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.frame_duration = 1.0 / self.fps
            self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
            # Load CSV
            self.data = pd.read_csv(details['csv_path'], header=[0, 1, 2])
            self.csv_loaded = True
            self.start_frame = details['start_frame']
            self.end_frame = details['end_frame']
    
            # Load ROIs
            self.shape_drawer.shapes = {name: Polygon(points) for name, points in details['shapes'].items()}
            self.excluded_body_parts = set(details['excluded_body_parts'])
    
            # Process each video segment
            self.data_processor.verify_frames()
            self.data_processor.check_body_parts_in_shapes()
    
            # Convert frame numbers to HH:MM:SS format
            start_time = self.frame_to_time(self.start_frame)
            end_time = self.frame_to_time(self.end_frame)
    
            # Prepare result for this video
            result = {
                'video_file': details['video_path'],
                'start_time': start_time,
                'end_time': end_time,
                'mode': details['mode']
            }
            for shape_name, time in self.shape_drawer.time_counters.items():
                result[shape_name] = time
            results.append(result)
    
        # Save results to a single CSV
        if results:
            results_df = pd.DataFrame(results)
            results_file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if results_file_path:
                results_df.to_csv(results_file_path, index=False)
                messagebox.showinfo("Success", f"Results saved to {results_file_path}.")
                
    def show_saved_details_window(self):
        '''
        This function shows a window with the details of what will be processed in the saved details
        '''
        if hasattr(self, 'saved_details_window') and self.saved_details_window.winfo_exists():
            self.update_saved_details_listbox()
            self.saved_details_window.lift()  # Bring the window to the front
            return
        
        # Create a new Toplevel window
        self.saved_details_window = Toplevel(self.root)
        self.saved_details_window.title("Saved Details")
        self.saved_details_window.geometry("300x400")
        center_window(self.saved_details_window, 300, 400)
    
        # Create a listbox to display saved details
        self.saved_details_listbox = Listbox(self.saved_details_window, selectmode=MULTIPLE)
        self.saved_details_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
        # Add saved details to the listbox
        self.update_saved_details_listbox()
    
        # Add a delete button
        delete_button = tk.Button(self.saved_details_window, text="Delete Selected", command=self.delete_selected_details)
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
            self.saved_details_listbox.insert(tk.END, f"Detail {i + 1}: {video_name}, {start_time} - {end_time}")
    
    def delete_selected_details(self):
        '''
        This function deletes details to be processed in the saved details
        '''
        selected_indices = self.saved_details_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "No details selected to delete.")
            return
    
        for index in reversed(selected_indices):
            del self.saved_details[index]
        self.update_saved_details_listbox()
    
    
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
    
    def show_help(self):
        show_help(self.root)    
        
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

