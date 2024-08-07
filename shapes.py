from shapely.geometry import Polygon
from tkinter import simpledialog
import pyautogui


class ShapeDrawer:
    '''
    This class is used to manage and draw shapes on a tkinter canvas
    '''
    def __init__(self, canvas, app):
        #initialize the shapedrawer withe a tkinter canvas
        self.canvas = canvas 
        self.points = [] #list to store points for current polygon to be cleared after completed shape
        self.shapes = {} #dictionary to store named shapes
        self.polygon_points = [] #list to store points for current polygon
        self.current_polygon = None #shapely object for the current polygon
        self.time_counters = {} #Dictionary to keep track of time
        self.app = app
        self.shift_held = False
        
        
    def shift_press(self, event):
        self.shift_held = True

    def shift_release(self, event):
        self.shift_held = False
        
    def add_point(self, event):
        #add points to the canvas to make a region of interest 
        if self.current_polygon is None: #check if current polygon being drawn
            x, y = event.x, event.y #get mouse click coords
            
            self.points.append((x, y)) #append to points list
            self.canvas.create_oval(x-2, y-2, x+2, y+2, fill='black', tags='shape') #plot small ovals where you click
            
            if len(self.points) > 1:
                self.canvas.create_line(self.points[-2][0], self.points[-2][1], x, y, tags='shape') #draw lines between points
                
    def mouse_move(self, event):
        if self.shift_held and self.points:
            self.align_mouse(event)
            
    def align_mouse(self, event):
        if not self.points:
            return

        last_x, last_y = self.points[-1]
        x, y = event.x, event.y

        #determine the primary direction
        delta_x = abs(x - last_x)
        delta_y = abs(y - last_y)

        if delta_x > delta_y:
            #horizontal or vertical alignment
            pyautogui.moveTo(self.canvas.winfo_rootx() + x, self.canvas.winfo_rooty() + last_y)
        elif delta_y > delta_x:
            #vertical alignment
            pyautogui.moveTo(self.canvas.winfo_rootx() + last_x, self.canvas.winfo_rooty() + y)
        else:
            #corner case for making a perfect square
            side_length = min(delta_x, delta_y)
            if x > last_x and y > last_y:
                pyautogui.moveTo(self.canvas.winfo_rootx() + last_x + side_length, self.canvas.winfo_rooty() + last_y + side_length)
            elif x > last_x and y < last_y:
                pyautogui.moveTo(self.canvas.winfo_rootx() + last_x + side_length, self.canvas.winfo_rooty() + last_y - side_length)
            elif x < last_x and y > last_y:
                pyautogui.moveTo(self.canvas.winfo_rootx() + last_x - side_length, self.canvas.winfo_rooty() + last_y + side_length)
            elif x < last_x and y < last_y:
                pyautogui.moveTo(self.canvas.winfo_rootx() + last_x - side_length, self.canvas.winfo_rooty() + last_y - side_length)
                
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
        #get the current video resolution
        video_width = self.app.video_width
        video_height = self.app.video_height
        
        #fixed canvas dimensions
        canvas_width = 960
        canvas_height = 540
        
        #calculate the scaling factors
        scale_x = video_width / canvas_width
        scale_y = video_height / canvas_height
        
        #scale the coordinates
        scaled_rois = {}
        for key, points in rois.items():
            scaled_points = [[x * scale_x, y * scale_y] for x, y in points.exterior.coords]
            scaled_rois[key] = Polygon(scaled_points)
        
        return scaled_rois