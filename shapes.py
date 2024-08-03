from shapely.geometry import Polygon
from tkinter import simpledialog

class ShapeDrawer:
    '''
    This class is used to manage and draw shapes on a tkinter canvas
    '''
    def __init__(self, canvas, app_instance):
        #initialize the shapedrawer withe a tkinter canvas
        self.canvas = canvas 
        self.points = [] #list to store points for current polygon to be cleared after completed shape
        self.shapes = {} #dictionary to store named shapes
        self.polygon_points = [] #list to store points for current polygon
        self.current_polygon = None #shapely object for the current polygon
        self.time_counters = {} #Dictionary to keep track of time
        self.app_instance = app_instance
        
    def add_point(self, event):
        #add points to the canvas to make a region of interest 
        if self.current_polygon is None: #check if current polygon being drawn
            x, y = event.x, event.y #get mouse click coords
            self.points.append((x, y)) #append to points list
            self.canvas.create_oval(x-2, y-2, x+2, y+2, fill='black', tags='shape') #plot small ovals where you click
            
            if len(self.points) > 1:
                self.canvas.create_line(self.points[-2][0], self.points[-2][1], x, y, tags='shape') #draw lines between points

    def complete_shape(self, event):
        #complete the shape and name it
        if len(self.points) > 2: #must have more than 2 points to make a shape
            self.polygon_points = self.points.copy() #copy points from the polygon
            self.canvas.create_polygon(self.points, outline='black', fill='', width=2, tags='shape') #create the shape using the polygon
            self.current_polygon = Polygon(self.points) #create shapely polygon with the points
            self.points = [] #clear the current points
            self.name_shape_popup() #name the ROI

    def name_shape_popup(self):
        #name the region of interest
        region_name = simpledialog.askstring("Region of Interest Name", "Enter a name for this Region of Interest:") #prompt user for name
        if region_name:
            self.shapes[region_name] = self.current_polygon #add tthe current polygon to the shapes dictionart
            self.time_counters[region_name] = 0.0 #initialze 0.0 seconds for the timer
            self.current_polygon = None #set the current polygon empty
            print(f"Region of Interest '{region_name}' added.")

    def clear_shapes(self):
        #clear the shapes
        self.canvas.delete('shape')
        self.shapes.clear()
        self.points.clear()
        self.polygon_points.clear()
        self.current_polygon = None
        self.time_counters.clear()
        print("All shapes cleared.")
    
    def scale_coordinates(self, rois):
        # Get the current video resolution
        video_width = self.app_instance.video_width
        video_height = self.app_instance.video_height
        
        # Fixed canvas dimensions
        canvas_width = 960
        canvas_height = 540
        
        # Calculate the scaling factors
        scale_x = video_width / canvas_width
        scale_y = video_height / canvas_height
        
        # Scale the coordinates
        scaled_rois = {}
        for key, points in rois.items():
            scaled_points = [[x * scale_x, y * scale_y] for x, y in points.exterior.coords]
            scaled_rois[key] = Polygon(scaled_points)
        
        return scaled_rois