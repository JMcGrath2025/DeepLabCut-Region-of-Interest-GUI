import tkinter as tk
from tkinter import filedialog, Toplevel, messagebox, ttk
from PIL import Image, ImageTk
import cv2
from utils import center_window

class VideoHandler:
    '''
    This class handles the opening and extraction of data from the video that will be processed
    '''
    def __init__(self, app):
        #initilaize the filepath
        self.app = app
        self.file_path = None

    def open_video(self):
        '''
        This function is responsible for opening the video and extracting variables relatinging to aspects from the video
        '''
        #open file dialog to look for mp4 avi and mov files
        self.file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if self.file_path:
            #clear shapes when a new video is opened
            self.app.shape_drawer.clear_shapes()
            #initilaize video capture
            self.app.cap = cv2.VideoCapture(self.file_path)
            if not self.app.cap.isOpened():
                print("Error: Could not open video.")
                return
            
            self.app.video_path = self.file_path  #store video path
            self.app.total_frames = int(self.app.cap.get(cv2.CAP_PROP_FRAME_COUNT)) #store total frames
            self.app.fps = self.app.cap.get(cv2.CAP_PROP_FPS) #store fps
            self.app.frame_duration = 1.0 / self.app.fps #store time of frame
            self.app.video_width = int(self.app.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) #store video height and width
            self.app.video_height = int(self.app.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            #open the frame selector to get screenshot to draw on
            self.open_frame_selector()
            self.app.start_frame = 0
            #end frame is the total frames - 1
            self.app.end_frame = self.app.total_frames - 1
            self.app.video_loaded = True
            
    def open_frame_selector(self):
        '''
        This function opens a window that allows you to scroll through every frame in a video and select one to draw ROIs over
        '''
        #define the window title and bring it to the top level
        self.app.selector_window = Toplevel(self.app.root, bg='#19232D')
        self.app.selector_window.title("Select Frame")
        self.app.selector_window.iconbitmap(self.app.icon_path)
        
        #style for the ttk Scale
        style = ttk.Style()
        style.theme_use('clam')  # Use 'clam' theme for more customization options
        style.configure("TScale", troughcolor="#455364")

        #create a slider to scroll through each frame starting at 0 and going to the end frame
        self.app.frame_slider = ttk.Scale(self.app.selector_window, from_=0, to=self.app.total_frames-1, orient=tk.HORIZONTAL, style="TScale")
        self.app.frame_slider.pack(fill=tk.X)

        #create select button that selects the frame to use as the canvas
        self.app.select_button = self.app.create_rounded_button(self.app.selector_window, width=130, height=40, corner_radius=15, bg_color='#455364', fg_color='white', text="Select", command=self.select_frame)
        self.app.select_button.pack(pady=10)

        #create label to display the current frame
        self.app.frame_label = tk.Label(self.app.selector_window, bg='#19232D', fg='white')
        self.app.frame_label.pack()

        #bind the slider to mouse motion and update the frame being shown when the slider changes
        self.app.frame_slider.bind("<Motion>", self.update_frame_preview)
        self.update_frame_preview(None)

        self.app.selector_window.update_idletasks()
        #find the window width and height and center the window when it pops up
        window_width = self.app.selector_window.winfo_width()
        window_height = self.app.selector_window.winfo_height()
        center_window(self.app.selector_window, window_width, window_height)


    def update_frame_preview(self, event):
        '''
        This function updates the frame that is being shown in the frame selector
        '''
        #the frame index is the current frame the slider is on
        frame_index = self.app.frame_slider.get()
        #set the screenshot at that frame to the preview
        self.app.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        
        #read the frame from the video capture object at the current position
        ret, frame = self.app.cap.read()
        #if ret is true the frame is read successfully
        if ret:
            #resize the frame to the preview window size
            frame = cv2.resize(frame, (400, 300))
            #convert to rgb
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            #create the image from the frame in the video
            self.app.frame_image = ImageTk.PhotoImage(image=Image.fromarray(frame))
            #configure label to display new image
            self.app.frame_label.config(image=self.app.frame_image)
            self.app.frame_label.image = self.app.frame_image

    def select_frame(self):
        '''
        This function select the frame during when the frame selector window is open
        '''
        #get the frame index of where the slider is currently at
        frame_index = self.app.frame_slider.get()
        self.app.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = self.app.cap.read()
        #if ret is resize the frame to the canvas width and height and display it on the canvas
        if ret:
            frame = cv2.resize(frame, (self.app.canvas_width, self.app.canvas_height))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.app.canvas_image = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.app.canvas.create_image(0, 0, anchor=tk.NW, image=self.app.canvas_image)
            self.app.canvas.image = self.app.canvas_image
        self.app.selector_window.destroy()
        self.app.custom_messagebox("Frame Selected", f"Frame {frame_index} has been selected.", bg_color='#19232D', fg_color='white')
            
    def open_segment_selector(self):
        '''
        This function opens the window that has sliders to change the start and end frame of the video
        '''
        #check that the video is opened
        if not hasattr(self.app, 'cap') or not self.app.cap.isOpened():
            print("Error: No video loaded.")
            return

        #name the window and bring it to the TopLevel
        self.app.segment_window = Toplevel(self.app.root, bg='#19232D')
        self.app.segment_window.title("Select Segment")
        self.app.segment_window.withdraw()
        self.app.segment_window.iconbitmap(self.app.icon_path)

        #style for the ttk Scale
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TScale", troughcolor="#455364")

        #create label and slider to define the start frame
        self.app.start_frame_label = tk.Label(self.app.segment_window, text="Start Frame:", bg='#19232D', fg='white')
        self.app.start_frame_label.pack()
        self.app.start_frame_slider = ttk.Scale(self.app.segment_window, from_=0, to=self.app.total_frames-1, orient=tk.HORIZONTAL, style="TScale")
        self.app.start_frame_slider.pack(fill=tk.X)

        #show the time in normal format
        self.app.start_frame_time_frame = tk.Frame(self.app.segment_window, bg='#19232D')
        self.app.start_frame_time_frame.pack()

        #create entries for the start frame hour, minute, and second
        self.app.start_frame_hour_entry = tk.Entry(self.app.start_frame_time_frame, width=3)
        self.app.start_frame_hour_entry.pack(side=tk.LEFT)
        self.app.start_frame_minute_entry = tk.Entry(self.app.start_frame_time_frame, width=3)
        self.app.start_frame_minute_entry.pack(side=tk.LEFT)
        self.app.start_frame_second_entry = tk.Entry(self.app.start_frame_time_frame, width=3)
        self.app.start_frame_second_entry.pack(side=tk.LEFT)

        #create button to move the start frame up by one second or down by one second
        self.app.start_frame_up_button = tk.Button(self.app.start_frame_time_frame, text="▲", bg='#455364', fg='white', command=lambda: self.adjust_time(self.app.start_frame_hour_entry, self.app.start_frame_minute_entry, self.app.start_frame_second_entry, self.app.start_frame_slider, 1, 'start'))
        self.app.start_frame_up_button.pack(side=tk.LEFT, pady=2.5, padx=1.5)
        self.app.start_frame_down_button = tk.Button(self.app.start_frame_time_frame, text="▼", bg='#455364', fg='white', command=lambda: self.adjust_time(self.app.start_frame_hour_entry, self.app.start_frame_minute_entry, self.app.start_frame_second_entry, self.app.start_frame_slider, -1, 'start'))
        self.app.start_frame_down_button.pack(side=tk.LEFT, pady=2.5, padx=1.5)

        #create label and slider for the end frame
        self.app.end_frame_label = tk.Label(self.app.segment_window, text="End Frame:", bg='#19232D', fg='white')
        self.app.end_frame_label.pack()
        self.app.end_frame_slider = ttk.Scale(self.app.segment_window, from_=0, to=self.app.total_frames-1, orient=tk.HORIZONTAL, style="TScale")
        self.app.end_frame_slider.pack(fill=tk.X)

        #convert the frames into standard time format
        self.app.end_frame_time_frame = tk.Frame(self.app.segment_window, bg='#19232D')
        self.app.end_frame_time_frame.pack()

        #create entries for the standard time for the end frame
        self.app.end_frame_hour_entry = tk.Entry(self.app.end_frame_time_frame, width=3)
        self.app.end_frame_hour_entry.pack(side=tk.LEFT)
        self.app.end_frame_minute_entry = tk.Entry(self.app.end_frame_time_frame, width=3)
        self.app.end_frame_minute_entry.pack(side=tk.LEFT)
        self.app.end_frame_second_entry = tk.Entry(self.app.end_frame_time_frame, width=3)
        self.app.end_frame_second_entry.pack(side=tk.LEFT)

        #create way to move one second above or below the current time
        self.app.end_frame_up_button = tk.Button(self.app.end_frame_time_frame, text="▲", bg='#455364', fg='white', command=lambda: self.adjust_time(self.app.end_frame_hour_entry, self.app.end_frame_minute_entry, self.app.end_frame_second_entry, self.app.end_frame_slider, 1, 'end'))
        self.app.end_frame_up_button.pack(side=tk.LEFT, pady=2.5, padx=1.5)
        self.app.end_frame_down_button = tk.Button(self.app.end_frame_time_frame, text="▼", bg='#455364', fg='white', command=lambda: self.adjust_time(self.app.end_frame_hour_entry, self.app.end_frame_minute_entry, self.app.end_frame_second_entry, self.app.end_frame_slider, -1, 'end'))
        self.app.end_frame_down_button.pack(side=tk.LEFT, pady=2.5, padx=1.5)

        #bind motion on the start and end frame sliders
        self.app.start_frame_slider.bind("<Motion>", lambda event: self.update_entry_and_preview(self.app.start_frame_slider, 'start'))
        self.app.end_frame_slider.bind("<Motion>", lambda event: self.update_entry_and_preview(self.app.end_frame_slider, 'end'))

        #bind enter to change the start frame and end frame by entering the standard time
        self.app.start_frame_hour_entry.bind("<Return>", lambda event: self.update_slider_from_time_entry(self.app.start_frame_slider, self.app.start_frame_hour_entry, self.app.start_frame_minute_entry, self.app.start_frame_second_entry, 'start'))
        self.app.start_frame_minute_entry.bind("<Return>", lambda event: self.update_slider_from_time_entry(self.app.start_frame_slider, self.app.start_frame_hour_entry, self.app.start_frame_minute_entry, self.app.start_frame_second_entry, 'start'))
        self.app.start_frame_second_entry.bind("<Return>", lambda event: self.update_slider_from_time_entry(self.app.start_frame_slider, self.app.start_frame_hour_entry, self.app.start_frame_minute_entry, self.app.start_frame_second_entry, 'start'))

        self.app.end_frame_hour_entry.bind("<Return>", lambda event: self.update_slider_from_time_entry(self.app.end_frame_slider, self.app.end_frame_hour_entry, self.app.end_frame_minute_entry, self.app.end_frame_second_entry, 'end'))
        self.app.end_frame_minute_entry.bind("<Return>", lambda event: self.update_slider_from_time_entry(self.app.end_frame_slider, self.app.end_frame_hour_entry, self.app.end_frame_minute_entry, self.app.end_frame_second_entry, 'end'))
        self.app.end_frame_second_entry.bind("<Return>", lambda event: self.update_slider_from_time_entry(self.app.end_frame_slider, self.app.end_frame_hour_entry, self.app.end_frame_minute_entry, self.app.end_frame_second_entry, 'end'))

        #create segment select button to select the segment of video to analyze
        self.app.segment_select_button = self.app.create_rounded_button(self.app.segment_window, width=130, height=40, corner_radius=15, bg_color='#455364', fg_color='white', text="Select Segment", command=self.select_segment)
        self.app.segment_select_button.pack(pady=10)

        #update the time entry based on the slider
        self.update_time_entry(self.app.start_frame_slider.get(), self.app.start_frame_hour_entry, self.app.start_frame_minute_entry, self.app.start_frame_second_entry)
        self.update_time_entry(self.app.end_frame_slider.get(), self.app.end_frame_hour_entry, self.app.end_frame_minute_entry, self.app.end_frame_second_entry)

        #center the window
        self.app.segment_window.update_idletasks()
        center_window(self.app.segment_window, 500, 800)
        
        self.app.segment_window.deiconify()
            
    
    
    def update_entry_and_preview(self, slider, frame_type):
        '''
        This function updates the preview in the popup windows that select the segment
        '''
        frame_index = slider.get()
        #if the frame type 
        if frame_type == 'start':
            self.update_time_entry(frame_index, self.app.start_frame_hour_entry, self.app.start_frame_minute_entry, self.app.start_frame_second_entry)
        else:
            self.update_time_entry(frame_index, self.app.end_frame_hour_entry, self.app.end_frame_minute_entry, self.app.end_frame_second_entry)
        self.update_frame_preview_from_slider(frame_index, frame_type)

    def update_time_entry(self, frame_index, hour_entry, minute_entry, second_entry):
        '''
        This function updates the frame index into hour minute second time format
        '''
        total_seconds = frame_index / self.app.fps
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        hour_entry.delete(0, tk.END)
        hour_entry.insert(0, f"{int(hours):02}")
        minute_entry.delete(0, tk.END)
        minute_entry.insert(0, f"{int(minutes):02}")
        second_entry.delete(0, tk.END)
        second_entry.insert(0, f"{int(seconds):02}")

    def update_slider_from_time_entry(self, slider, hour_entry, minute_entry, second_entry, frame_type):
        '''
        Update the time entry when the slider changes position
        '''
        try:
            hours = int(hour_entry.get())
            minutes = int(minute_entry.get())
            seconds = int(second_entry.get())
            total_seconds = hours * 3600 + minutes * 60 + seconds
            frame_index = int(total_seconds * self.app.fps)
            slider.set(frame_index)
            self.update_frame_preview_from_slider(frame_index, frame_type)
        except ValueError:
            pass

    def adjust_time(self, hour_entry, minute_entry, second_entry, slider, delta, frame_type):
        '''
        This function allows you to adjust the time by entering hour minute and second 
        '''
        try:
            hours = int(hour_entry.get())
            minutes = int(minute_entry.get())
            seconds = int(second_entry.get())
            total_seconds = hours * 3600 + minutes * 60 + seconds + delta
            if total_seconds < 0:
                total_seconds = 0
            frame_index = int(total_seconds * self.app.fps)
            self.update_time_entry(frame_index, hour_entry, minute_entry, second_entry)
            slider.set(frame_index)
            self.update_frame_preview_from_slider(frame_index, frame_type)
        except ValueError:
            pass

    def update_frame_preview_from_slider(self, frame_index, frame_type):
        '''
        This function updates the frame preview when the slider changes position
        '''
        self.app.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = self.app.cap.read()
        if ret:
            frame = cv2.resize(frame, (400, 300))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.app.frame_image = ImageTk.PhotoImage(image=Image.fromarray(frame))
            if frame_type == 'start':
                self.app.start_frame_label.config(image=self.app.frame_image)
                self.app.start_frame_label.image = self.app.frame_image
            elif frame_type == 'end':
                self.app.end_frame_label.config(image=self.app.frame_image)
                self.app.end_frame_label.image = self.app.frame_image

    def select_segment(self):
        '''
        This function defines the start frame and the end frame when called
        '''
        self.app.start_frame = self.app.start_frame_slider.get()
        self.app.end_frame = self.app.end_frame_slider.get()
        start_seconds = self.app.frame_to_time(self.app.start_frame)
        end_seconds = self.app.frame_to_time(self.app.end_frame)
        if self.app.start_frame >= self.app.end_frame:
            print("Error: Start frame must be less than end frame.")
            return
        print(f"Selected segment from frame {self.app.start_frame} to frame {self.app.end_frame}.")
        self.app.segment_window.destroy()
        self.app.custom_messagebox("Segment Selected", f"Selected segment in frames:\n{self.app.start_frame} - {self.app.end_frame}.\n Segment in Seconds:\n {start_seconds} - {end_seconds} ", "#19232D", "white")
        
        
        
        
        
        
        
        
        
        
        