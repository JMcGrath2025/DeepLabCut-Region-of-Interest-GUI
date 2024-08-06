import pandas as pd
from shapely.geometry import Point
from tkinter import filedialog, messagebox, Toplevel, Listbox, Checkbutton, BooleanVar
from utils import center_window
import tkinter as tk
import os
import cv2
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg



class DataProcessor:
    '''
    This class contains the methods responsible for processing data 
    '''
    #initialize file path and app instance
    def __init__(self, app):
        self.app = app
        self.file_path = None
    
    #function to get correct bodypart dictionary
    @staticmethod
    def clean_body_parts(body_parts):
        return {bp for bp in body_parts if bp not in {'bodyparts'}}
    
    #function to keep exclusions the same on different videos with the same body parts
    @staticmethod
    def compare_and_apply_exclusions(current_body_parts, new_body_parts, previous_exclusions):
        #find current and new body parts list
        current_body_parts_set = DataProcessor.clean_body_parts(set(current_body_parts))
        new_body_parts_set = DataProcessor.clean_body_parts(set(new_body_parts))
        
        print(f"Body parts match: {current_body_parts_set == new_body_parts_set}")
        
        #if the excluded body parts are the same as the new return the previous exclusions
        if current_body_parts_set == new_body_parts_set:
            return previous_exclusions.copy()
        else: #clear the exlcusions if they are not the same
            return set()
    
    #this if a function to open the csv or h5 file containing the tracking data
    def open_file(self):
        #open the filedialog for csv and h5 files
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("HDF5 files", "*.h5")])
        #check if the file selected is a csv of h5
        if file_path:
            file_extension = os.path.splitext(file_path)[1]
            if file_extension == '.csv': #if csv read the data accordingly from deeplabcut csv
                new_data = pd.read_csv(file_path, header=[0, 1, 2])
            elif file_extension == '.h5': #if a h5 read accordingly with the hdf5 key
                new_data = pd.read_hdf(file_path, key='/df_with_missing') 
            else: #show message box error if other file type is selected
                messagebox.showerror("Error", "Unsupported file type.")
                return
            
            #find the set of body parts
            new_body_parts = set(new_data.columns.get_level_values(1))

            #use static methods to apply exlusions
            self.app.excluded_body_parts = DataProcessor.compare_and_apply_exclusions(
                self.app.body_parts, new_body_parts, self.app.previous_excluded_body_parts
            )

            #load the new data and body parts
            self.app.data = new_data
            self.app.body_parts = new_body_parts
            self.app.csv_loaded = True #change csv status to True
            self.app.start_button.config(state=tk.NORMAL) #allow the process button the be pressed
            self.app.load_csv_label.config(text=f"File: \n{os.path.basename(file_path)} loaded") #display the file name
            
            #find the body parts set from the data frame
            body_parts_columns = [(col[0], col[1]) for col in self.app.data.columns if col[2] in ['x', 'y']]
            self.app.body_parts = sorted(set(col[1] for col in body_parts_columns))
            self.app.update_body_part_label([bp for bp in self.app.body_parts if bp not in self.app.excluded_body_parts]) #update body parts label

            #store the file path
            self.file_path = file_path

            #debugging log file
            log_file_path = os.path.join(os.path.dirname(file_path), "debug_log.txt")
            self.app.log_file = open(log_file_path, "w")

            #store previous excluded body part as the new exluded body parts
            self.app.previous_excluded_body_parts = self.app.excluded_body_parts.copy()
            
            #popup that the file that was loaded
            self.app.custom_messagebox("File Loaded", f"Successfully loaded file: {os.path.basename(file_path)}", bg_color='#19232D', fg_color='white')
    
    
    def find_columns(self, body_part):
        '''
        This function finds the columns for the x coordinate y coordinate and liklihood
        '''
        columns = self.app.data.columns
        x_col, y_col, likelihood_col = None, None, None

        for col in columns:
            if col[1] == body_part:
                if col[2] == 'x':
                    x_col = col
                elif col[2] == 'y':
                    y_col = col
                elif col[2] == 'likelihood':
                    likelihood_col = col

        if x_col and y_col and likelihood_col:
            return x_col, y_col, likelihood_col
        else:
            raise ValueError(f"Could not find columns for body part: {body_part}")

    def scale_coordinates(self, x, y):
        '''
        This function scales the coordinates from the video to the size of the canvas
        '''
        scaled_x = (x / self.app.video_width) * self.app.canvas_width
        scaled_y = (y / self.app.video_height) * self.app.canvas_height
        return scaled_x, scaled_y

    def verify_frames(self):
        '''
        This function verifies if all the frames in the video exist in the dataframe
        '''
        csv_frames = self.app.data.index.tolist()
        missing_frames = [frame_index for frame_index in range(self.app.total_frames) if frame_index not in csv_frames]
        if missing_frames:
            print(f"Missing frames in file: {missing_frames}")
            if self.app.log_file:
                self.app.log_file.write(f"Missing frames in file: {missing_frames}\n")
        else:
            print("All frames are present in the file.")
            if self.app.log_file:
                self.app.log_file.write("All frames are present in the file.\n")

    def check_body_parts_in_shapes(self):
        '''
        This function is the main processing part that checks each frame to see if the animal appears 
        within the regions of interest
        '''
        
        #check to make sure ROI appears on the canvas
        if not self.app.shape_drawer.shapes:
            print("No shapes defined.")
            return
    
        if not hasattr(self.app, 'start_frame') or not hasattr(self.app, 'end_frame'):
            print("Error: No segment selected.")
            return
    
        #create dictionary to store frames that appear within the shapes 
        frames_in_shapes = {name: set() for name in self.app.shape_drawer.shapes}
        
        #extract columns directly
        body_parts_columns = [(col[0], col[1], col[2]) for col in self.app.data.columns if col[2] in ['x', 'y']]
        num_body_parts = len(set(col[1] for col in body_parts_columns))
        
        #initialize progress bar
        self.app.progress_bar(self.app.end_frame - self.app.start_frame + 1) # account for the initial frame being 0
        
        #loop through each row of the data frame
        for index, row in self.app.data.iterrows():
            #skip the frames not in the selected segment
            if index < self.app.start_frame or index > self.app.end_frame:
                continue
            
            #loop through each defined ROI
            for shape_name, polygon in self.app.shape_drawer.shapes.items():
                #initialize counters and flags
                in_shape_count = 0 # count of frames in shape
                specific_part_in_shape = False
                any_part_in_shape = False
                
                #loop through the body parts columns
                for col in body_parts_columns:
                    if col[1] in self.app.excluded_body_parts:
                        continue
                    
                    #get x y and likelihood values for the current row
                    x = row[(col[0], col[1], 'x')]
                    y = row[(col[0], col[1], 'y')]
                    likelihood = row[(col[0], col[1], 'likelihood')]
                    
                    #check to make sure x and y have values
                    if pd.notna(x) and pd.notna(y):
                        #scale the coordinates
                        scaled_x, scaled_y = self.scale_coordinates(x, y)
                        #create a point using the x and y
                        point = Point(scaled_x, scaled_y)
                        #if the defined ROI contains the point 
                        if polygon.contains(point):
                            #add one to the frames in ROI
                            in_shape_count += 1
                            #check for specific or any part mode to change flag
                            if self.app.track_mode == 'specific' and col[1] == self.app.specific_body_part:
                                specific_part_in_shape = True
                            if self.app.track_mode == 'any_part' and likelihood >= 0.99: #for any part make sure it has a 99% likelihood
                                any_part_in_shape = True
                #update frames that appear in the ROI based on the tracking mode
                if self.app.track_mode == 'specific' and specific_part_in_shape:
                    frames_in_shapes[shape_name].add(index)
                #majority mode by making the body parts in the shape count needing to be greater than a percent of the body parts
                elif self.app.track_mode == 'majority' and in_shape_count >= self.app.percent * num_body_parts:
                    frames_in_shapes[shape_name].add(index)
                elif self.app.track_mode == 'any_part' and any_part_in_shape:
                    frames_in_shapes[shape_name].add(index)
            
            #update the progress bar
            self.app.update_progress(index - self.app.start_frame + 1)
        
        #update the labels to show the time spent in each shape.
        for shape_name, frames in frames_in_shapes.items():
            total_time_in_shape = len(frames) * self.app.frame_duration
            self.app.shape_drawer.time_counters[shape_name] = total_time_in_shape
            print(f"Total frames in shape '{shape_name}': {len(frames)}")
            print(f"Total time in shape '{shape_name}': {total_time_in_shape:.2f} seconds")
            if self.app.log_file:
                self.app.log_file.write(f"Total frames in shape '{shape_name}': {len(frames)}\n")
                self.app.log_file.write(f"Total time in shape '{shape_name}': {total_time_in_shape:.2f} seconds\n")
    
        self.app.update_time_labels()
        self.app.close_progress_bar()
        
    def create_pathing_slideshow(self):
        current_frame_index = self.app.start_frame
        playing = False
        direction = 1
        frame_increment = 5  #increase the increment for faster playback
        frame_delay = int(1000 / self.app.fps / 5)
        
        body_part_popup = Toplevel(self.app.root, bg='#19232D')
        body_part_popup.title("Select Body Parts for Slideshow")
        body_part_popup.geometry("250x250")
        body_part_popup.update_idletasks()
        window_width = body_part_popup.winfo_width()
        window_height = body_part_popup.winfo_height()
        center_window(body_part_popup, window_width, window_height)
        
        def on_close():
            body_part_popup.destroy()
        
        body_part_popup.protocol("WM_DELETE_WINDOW", on_close)
        
        def on_select():
            selected_body_part_indices = listbox.curselection()
            if selected_body_part_indices:
                selected_body_parts = [self.app.body_parts[i] for i in selected_body_part_indices]
                body_part_popup.destroy()
                self.app.specific_body_parts = selected_body_parts
                self.start_slideshow(current_frame_index, playing, direction, frame_increment, frame_delay, path_length=50)
            else:
                messagebox.showerror("Error", "No body part selected.")
        
        frame = tk.Frame(body_part_popup, bg='#19232D')
        frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        listbox = Listbox(frame, selectmode=tk.MULTIPLE, bg="#455364", fg="white", bd=0, highlightthickness=0)
        for part in self.app.body_parts:
            listbox.insert(tk.END, part)
        listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        select_button = self.app.create_rounded_button(frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Select", command=on_select)
        select_button.pack(side=tk.BOTTOM, pady=10)
        
        body_part_popup.mainloop()
    
    def start_slideshow(self, current_frame_index, playing, direction, frame_increment, frame_delay, path_length):
        cap = cv2.VideoCapture(self.app.video_path)
        
        # Define the desired window size for the scaled video
        desired_window_width = 1280
        desired_window_height = 720
    
        # Get original video dimensions
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
        # Calculate scaling factor to maintain aspect ratio
        scaling_factor = min(desired_window_width / original_width, desired_window_height / original_height)
    
        # Calculate new dimensions based on scaling factor
        new_width = int(original_width * scaling_factor)
        new_height = int(original_height * scaling_factor)
    
        # Create a dummy Tkinter window to get screen dimensions
        dummy_root = tk.Tk()
        dummy_root.withdraw()  # Hide the dummy window
        screen_width = dummy_root.winfo_screenwidth()
        screen_height = dummy_root.winfo_screenheight()
        dummy_root.destroy()
    
        # Calculate the position to center the OpenCV window
        x = (screen_width - new_width) // 2
        y = (screen_height - new_height) // 2
    
        # Define a list of colors (you can add more if needed)
        color_list = [
            (51, 204, 204), (0, 204, 255), (0, 153, 255), (0, 102, 255), 
            (51, 102, 255), (102, 102, 255), (153, 102, 255), (204, 51, 255), 
            (255, 0, 255), (255, 51, 204), (255, 51, 153), (255, 0, 102),
            (255, 80, 80), (255, 102, 0), (255, 153, 51), (255, 204, 0),
            (255, 255, 0), (153, 255, 51), (102, 255, 51), (51, 204, 51),
            (0, 255, 153), (0, 255, 204), (0, 153, 51), (0, 51, 153),
            (51, 51, 153), (153, 0, 204), (153, 0, 204), (153, 102, 255),
            (204, 51, 153), (153, 51, 153), (51, 102, 0), (102, 255, 153),
            (102, 255, 204), (255, 153, 204), (153, 204, 255), (153, 255, 204),
            (255, 204, 153), (255, 102, 204), (255, 204, 255), (102, 255, 255),
            (153, 255, 102), (153, 204, 255), (255, 255, 153), (0, 153, 153),
            (0, 153, 204), (153, 51, 102), (204, 102, 0), (0, 179, 179)
        ]
    
        random.shuffle(color_list)
        # Assign each body part a unique color
        body_part_colors = {body_part: color_list[i % len(color_list)] for i, body_part in enumerate(self.app.specific_body_parts)}
    
        if not cap.isOpened():
            print(f"Error opening video file: {self.video_path}")
            return
    
        path_points_dict = {body_part: [] for body_part in self.app.specific_body_parts}
    
        # Create and center the window before entering the loop
        cv2.namedWindow('Tracking Overlay Viewer', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Tracking Overlay Viewer', new_width, new_height)
        cv2.moveWindow('Tracking Overlay Viewer', x, y)
    
        while cv2.getWindowProperty('Tracking Overlay Viewer', cv2.WND_PROP_VISIBLE) >= 1:
            if playing:
                current_frame_index += direction * frame_increment
                if current_frame_index > self.app.end_frame:
                    current_frame_index = self.app.end_frame
                    playing = False
                elif current_frame_index < self.app.start_frame:
                    current_frame_index = self.app.start_frame
                    playing = False
    
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_index)
            ret, frame = cap.read()
            if not ret:
                break
    
            # Resize frame based on scaling factor
            frame = cv2.resize(frame, (new_width, new_height))
    
            for body_part in self.app.specific_body_parts:
                x_col, y_col, likelihood_col = self.find_columns(body_part)
                x = self.app.data.loc[current_frame_index, x_col] * scaling_factor
                y = self.app.data.loc[current_frame_index, y_col] * scaling_factor
                likelihood = self.app.data.loc[current_frame_index, likelihood_col]
    
                if likelihood > 0.9:
                    point = (int(x), int(y))
                    path_points = path_points_dict[body_part]
                    path_points.append(point)
                    if len(path_points) > path_length:
                        path_points.pop(0)
                    for i in range(1, len(path_points)):
                        cv2.line(frame, path_points[i-1], path_points[i], body_part_colors[body_part], 2)
                    cv2.circle(frame, point, 5, body_part_colors[body_part], -1)
    
            cv2.putText(frame, f"Frame: {current_frame_index}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow('Tracking Overlay Viewer', frame)
    
            key = cv2.waitKey(frame_delay) & 0xFF
            if key == ord('a'):
                playing = True
                direction = -1
            elif key == ord('d'):
                playing = True
                direction = 1
            elif key == ord(' '):
                playing = False
    
        cap.release()
        cv2.destroyAllWindows()

    def plot_data(self):
        if self.app.csv_loaded:
            if not hasattr(self.app, 'total_frames') or self.app.total_frames == 0:
                messagebox.showerror("Error", "No video loaded. Please load a video first.")
                return
    
            if not hasattr(self.app, 'start_frame') or self.app.start_frame is None:
                self.app.start_frame = 0
            if not hasattr(self.app, 'end_frame') or self.app.end_frame is None:
                self.app.end_frame = self.app.total_frames - 1
    
            body_part_popup = Toplevel(self.app.root, bg='#19232D')
            body_part_popup.title("Select Body Part")
            body_part_popup.geometry("250x250")
            body_part_popup.update_idletasks()
            window_width = body_part_popup.winfo_width()
            window_height = body_part_popup.winfo_height()
            center_window(body_part_popup, window_width, window_height)
    
            def on_select():
                selected_body_part_index = listbox.curselection()
                if selected_body_part_index:
                    body_part = self.app.body_parts[selected_body_part_index[0]]
                    body_part_popup.destroy()
                    self.process_body_part(body_part)
                else:
                    messagebox.showerror("Error", "No body part selected.")
    
            frame = tk.Frame(body_part_popup, bg='#19232D')
            frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
    
            listbox = Listbox(frame, selectmode=tk.SINGLE, bg='#455364', fg='white', bd=0, highlightthickness=0 )
            for part in self.app.body_parts:
                listbox.insert(tk.END, part)
            listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
            select_button = self.app.create_rounded_button(frame, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Select", command=on_select)
            select_button.pack(side=tk.BOTTOM, pady=10)
    
            body_part_popup.mainloop()
    
    def process_body_part(self, body_part):
        x_col, y_col, likelihood_col = self.find_columns(body_part)
        
        filtered_df = self.app.data.loc[
            (self.app.data.index >= self.app.start_frame) & (self.app.data.index <= self.app.end_frame) &
            (self.app.data[x_col].abs() > 1e-5) & (self.app.data[y_col].abs() > 1e-5) &
            (~self.app.data[x_col].isna()) & (~self.app.data[y_col].isna()) &
            (pd.notna(self.app.data[x_col])) & (pd.notna(self.app.data[y_col])) &
            (self.app.data[likelihood_col] >= .75)
        ]
        
        Q1_x = filtered_df[x_col].quantile(0.25)
        Q3_x = filtered_df[x_col].quantile(0.75)
        IQR_x = Q3_x - Q1_x
        
        Q1_y = filtered_df[y_col].quantile(0.25)
        Q3_y = filtered_df[y_col].quantile(0.75)
        IQR_y = Q3_y - Q1_y
        
        lower_bound_x = Q1_x - 1.5 * IQR_x
        upper_bound_x = Q3_x + 1.5 * IQR_x
        
        lower_bound_y = Q1_y - 1.5 * IQR_y
        upper_bound_y = Q3_y + 1.5 * IQR_y
        
        non_outliers_df = filtered_df[(filtered_df[x_col] >= lower_bound_x) & (filtered_df[x_col] <= upper_bound_x) &
                                      (filtered_df[y_col] >= lower_bound_y) & (filtered_df[y_col] <= upper_bound_y)]
        
        sorted_df = non_outliers_df.sort_values(by=x_col)
        
        x_min = non_outliers_df[x_col].min()
        x_max = non_outliers_df[x_col].max()
        y_min = non_outliers_df[y_col].min()
        y_max = non_outliers_df[y_col].max()
        bounding_box_area = (x_max - x_min) * (y_max - y_min)
        
        auc = np.trapz(sorted_df[y_col], sorted_df[x_col])
        
        path_length = np.sum(np.sqrt(np.diff(non_outliers_df[x_col])**2 + np.diff(non_outliers_df[y_col])**2))
        
        display_options_popup = Toplevel(self.app.root, bg='#19232D')
        display_options_popup.title("Display Options")
        display_options_popup.geometry("300x500")
        display_options_popup.update_idletasks()
        window_width = display_options_popup.winfo_width()
        window_height = display_options_popup.winfo_height()
        center_window(display_options_popup, window_width, window_height)
        
        show_bounding_box_var = BooleanVar(value=False)
        show_roi_var = BooleanVar(value=False)
        show_auc_var = BooleanVar(value=False)
        square_graph_var = BooleanVar(value=False)
        plot_over_video_var = BooleanVar(value=False)
        zoom_in_var = BooleanVar(value=False)
        
        create_custom_checkbutton(display_options_popup, "Show Bounding Box", show_bounding_box_var).pack(anchor=tk.W)
        create_custom_checkbutton(display_options_popup, "Show ROIs", show_roi_var).pack(anchor=tk.W)
        create_custom_checkbutton(display_options_popup, "Show Area Under Curve (AUC)", show_auc_var).pack(anchor=tk.W)
        create_custom_checkbutton(display_options_popup, "Square Graph", square_graph_var).pack(anchor=tk.W)
        create_custom_checkbutton(display_options_popup, "Plot Over Video", plot_over_video_var).pack(anchor=tk.W)
        zoom_in_checkbutton = create_custom_checkbutton(display_options_popup, "Zoom In", zoom_in_var)
        zoom_in_checkbutton.pack(anchor=tk.W)
        
        #custom entry for zoom radius
        zoom_radius_frame = create_custom_entry(display_options_popup, "Zoom Radius (pixels):", self.app.zoom_radius_value)
        zoom_radius_frame.pack_forget()  #initially hide
        
        def toggle_zoom_radius_entry():
            if zoom_in_var.get():
                zoom_radius_frame.pack(after=zoom_in_checkbutton)
            else:
                zoom_radius_frame.pack_forget()
        
        zoom_in_var.trace_add('write', lambda *args: toggle_zoom_radius_entry())
        
        roi_listbox = Listbox(display_options_popup, selectmode=tk.MULTIPLE, bg='#455364', fg='white', bd=0, highlightthickness=0)
        roi_listbox.pack(pady=10, fill=tk.BOTH, expand=True)
        
        for name in self.app.shape_drawer.shapes.keys():
            roi_listbox.insert(tk.END, name)
        
        for i in range(roi_listbox.size()):
            roi_listbox.selection_set(i)
        
        def on_apply():
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if plot_over_video_var.get():
                cap = cv2.VideoCapture(self.app.video_path)
                cap.set(cv2.CAP_PROP_POS_FRAMES, self.app.end_frame)
                ret, frame = cap.read()
                cap.release()
                ax.invert_yaxis()
        
                if not ret:
                    raise ValueError(f"Could not read the frame number {self.app.end_frame} from the video")
        
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                ax.imshow(frame_rgb)
        
            ax.plot(non_outliers_df[x_col], non_outliers_df[y_col], marker='o', linestyle='-', color='b', alpha=0.7, label=f'{body_part} Movement')
        
            bounding_box_length = x_max - x_min
            bounding_box_width = y_max - y_min
        
            if show_bounding_box_var.get():
                rect = plt.Rectangle((x_min, y_min), x_max - x_min, y_max - y_min, linewidth=2, edgecolor='r', facecolor='none', label='Bounding Box')
                ax.add_patch(rect)
        
                print(f'The length of the bounding box is: {bounding_box_length:.2f} pixels')
                print(f'The width of the bounding box is: {bounding_box_width:.2f} pixels')
        
            if show_roi_var.get():
                selected_rois = [roi_listbox.get(i) for i in roi_listbox.curselection()]
                scaled_shapes = self.app.shape_drawer.scale_coordinates(self.app.shape_drawer.shapes)
                for name in selected_rois:
                    polygon = scaled_shapes[name]
                    x, y = polygon.exterior.xy
                    ax.plot(x, y, linestyle='-', linewidth=2, label=f'ROI: {name}')
                    ax.fill(x, y, alpha=0.2)
                    #ax.invert_yaxis()
        
            if show_auc_var.get():
                ax.fill_between(non_outliers_df[x_col], non_outliers_df[y_col], alpha=0.3, label=f'AUC: {auc:.2f}')
        
            if square_graph_var.get():
                ax.set_aspect('equal', 'box')
        
            if zoom_in_var.get():
                try:
                    zoom_radius = float(self.app.zoom_radius_value.get())
                    center_x = (x_max + x_min) / 2
                    center_y = (y_max + y_min) / 2
                    
                    #set zoomed in limits
                    ax.set_xlim([center_x - zoom_radius, center_x + zoom_radius])
                    ax.set_ylim([center_y - zoom_radius, center_y + zoom_radius])
                    
                    #invert the y axis to flip the image and graph
                    ax.invert_yaxis()
                    
                    #adjust the graph coordinates for zoomed in view
                    non_outliers_df_zoomed = non_outliers_df[
                        (non_outliers_df[x_col] >= center_x - zoom_radius) & (non_outliers_df[x_col] <= center_x + zoom_radius) &
                        (non_outliers_df[y_col] >= center_y - zoom_radius) & (non_outliers_df[y_col] <= center_y + zoom_radius)
                    ]
                    
                    ax.plot(non_outliers_df_zoomed[x_col], non_outliers_df_zoomed[y_col], marker='o', linestyle='-', color='b', alpha=0.7, label=f'{body_part} Movement')
                    
                except ValueError:
                    messagebox.showerror("Error", "Invalid zoom radius. Please enter a numeric value.")
        
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_title(f'{body_part.capitalize()} Movement Over Time')
            ax.legend()
            ax.grid(True)
        
            bounding_box_area = bounding_box_length * bounding_box_width
            bounding_box_text = f'The bounding_box area is: {bounding_box_area:.2f} pixels²'
            path_text = f'The total path length is: {path_length:.2f} pixels'
            auc_text = f'The Area Under Curve is: {auc:.2f} pixels²'
            print(bounding_box_text)
            print(path_text)
            print(auc_text)
            ax.text(0.5, -0.15, bounding_box_text, ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.text(0.5, -0.125, path_text, ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.text(0.5, -0.1, auc_text, ha='center', va='center', transform=ax.transAxes, fontsize=12)
        
            self.show_plot_popup(self.app, fig)
            display_options_popup.destroy()
        
        apply_button = self.app.create_rounded_button(display_options_popup, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Apply", command=on_apply)
        apply_button.pack(pady=10)
        
        display_options_popup.mainloop()

        
    def show_plot_popup(self, app, fig):
        popup = Toplevel(app.root, bg='#19232D')
        popup.title("Plot")
    
        #set the size of the popup window
        popup.geometry("1280x720")  # Adjust the size as needed
            
        canvas = FigureCanvasTkAgg(fig, master=popup)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
        #center the popup window after it is created and sized
        popup.update_idletasks()
        window_width = popup.winfo_width()
        window_height = popup.winfo_height()
        center_window(popup, window_width, window_height)
            
        download_button = self.app.create_rounded_button(popup, width=130, height=40, corner_radius=15, bg_color="#455364", fg_color="white", text="Download", command=lambda: self.download_image(fig))
        download_button.pack(pady=10)
            
    
            
    def download_image(self, fig):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if file_path:
            fig.savefig(file_path)
            messagebox.showinfo("Success", f"Image saved to {file_path}")

def create_custom_checkbutton(parent, text, variable, command=None, width=20, height=20):
    def draw_checkbox(canvas, checked):
        canvas.delete("all")  # Clear the canvas
        if checked:
            #draw checked state
            canvas.create_rectangle(0, 0, width, height, fill='#455364', outline="black")
            canvas.create_oval(5, 5, width - 5, height - 5, fill="white", outline="white")
        else:
            #draw unchecked state
            canvas.create_rectangle(0, 0, width, height, fill="#455364", outline="black")

    frame = tk.Frame(parent, bg='#19232D')
    frame.pack(anchor=tk.W, fill=tk.X, expand=True)
    
    canvas = tk.Canvas(frame, width=width, height=height, bg='#19232D', bd=0, highlightthickness=0)
    canvas.pack(side=tk.LEFT, padx=5, pady=5)

    def on_click():
        variable.set(not variable.get())
        draw_checkbox(canvas, variable.get())
        if command:
            command()

    checkbox_text = tk.Label(frame, text=text, bg='#19232D', fg='white')
    checkbox_text.pack(side=tk.LEFT, padx=5)

    draw_checkbox(canvas, variable.get())
    canvas.bind("<Button-1>", lambda e: on_click())
    checkbox_text.bind("<Button-1>", lambda e: on_click())

    return frame

def create_custom_entry(parent, text, variable):
    frame = tk.Frame(parent, bg='#19232D')
    label = tk.Label(frame, text=text, bg='#19232D', fg='white')
    label.pack(side=tk.LEFT, padx=5, pady=5)
    entry = tk.Entry(frame, textvariable=variable)
    entry.pack(side=tk.LEFT, padx=5, pady=5)
    return frame
        
