from shapely.geometry import Polygon, MultiPolygon
from tkinter import Toplevel, Label, Entry
import pyautogui
#import math
from utils import center_window
import random


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
        self.color_list = [
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
        self.current_color = self.get_random_color()
        
        
    def shift_press(self, event):
        self.shift_held = True
        #self.mouse_move(event)

    def shift_release(self, event):
        self.shift_held = False
        
    def get_random_color(self):
        color = random.choice(self.color_list)
        return f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}'
    
    def add_point(self, event):
        #add points to the canvas to make a region of interest 
        if self.current_polygon is None: #check if current polygon being drawn
            x, y = event.x, event.y #get mouse click coords
            
            self.points.append((x, y)) #append to points list
            
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill=self.current_color, tags='shape') #plot small ovals where you click
            
            if len(self.points) > 1:
                line_width = 3
                self.canvas.create_line(self.points[-2][0], self.points[-2][1], x, y, fill=self.current_color, tags='shape', width=line_width) #draw lines between points
                
    def complete_rectangle(self, event):
        if len(self.points) != 3:
            self.app.custom_messagebox("Error", "Three points are required to complete the ROI.", "#19232D", "white")
            return

        p1 = self.points[0]
        p2 = self.points[1]
        p3 = self.points[2]
        
        if p1[0] == p2[0]:#p1 and p2 are vertical
            new_x = p3[0]
            new_y = p1[1]
        elif p1[1] == p2[1]:#p1 and p2 are horizontal
            new_x = p1[0]
            new_y = p3[1]
        elif p2[0] == p3[0]:#p2 and p3 are vertical
            new_x = p1[0]
            new_y = p3[1]
        elif p2[1] == p3[1]:#p2 and p3 are horizontal
            new_x = p3[0]
            new_y = p1[1]
        else:#diagonal case
            dx1 = p2[0] - p1[0]
            dy1 = p2[1] - p1[1]

            if abs(dx1) > abs(dy1):#horizontal distance is greater
                new_x = p1[0]
                new_y = p3[1]
            else:#vertical distance is greater
                new_x = p3[0]
                new_y = p1[1]

        self.points.append((new_x, new_y))
        self.canvas.create_oval(new_x-2, new_y-2, new_x+2, new_y+2, fill=self.current_color, tags='shape')
        self.canvas.create_line(p3[0], p3[1], new_x, new_y, tags='shape')
        self.complete_shape(None)
        self.current_color = self.get_random_color()

    def mouse_move(self, event):
        if self.shift_held and self.points:
            self.align_mouse(event)
            
    def align_mouse(self, event):
        if not self.points:
            return

        last_x, last_y = self.points[-1]
        x, y = event.x, event.y

        #determine the primary direction based on the current mouse position
        if abs(x - last_x) > abs(y - last_y):
            #horizontal alignment
            target_x = x
            target_y = last_y
        else:
            #vertical alignment
            target_x = last_x
            target_y = y

        #move the mouse to the aligned position
        pyautogui.moveTo(self.canvas.winfo_rootx() + target_x, self.canvas.winfo_rooty() + target_y)
                
    def complete_shape(self, event):
        #complete the shape and name it
        if len(self.points) > 2: #must have more than 2 points to make a shape
            self.polygon_points = self.points.copy() #copy points from the polygon
            self.canvas.create_polygon(self.points, outline=self.current_color, fill='', width=3, tags='shape') #create the shape using the polygon
            self.current_polygon = Polygon(self.points) #create shapely polygon with the points
            self.points = [] #clear the current points
            self.name_shape_popup() #name the ROI
            self.current_color = self.get_random_color()

    def name_shape_popup(self):
        name_window = Toplevel()
        name_window.title("Region of Interest Name")
        name_window.configure(bg="#19232D")
        name_window.iconbitmap(self.app.icon_path)
        
        #bring the window to the top and focus it
        name_window.lift()
        name_window.focus_force()
        
        name_window.geometry("300x150")
        
        center_window(name_window, 300, 150)
        
        
        Label(name_window, text="Name the Region of Interest", bg="#19232D", fg="white").pack(pady=10)
        
        roi_name = Entry(name_window, width=25, bg="#455364", fg="white", font=8)
        roi_name.pack(pady=10, ipady=2.5)

        def save_name():
            region_name = roi_name.get()
            
            if not region_name:
                self.app.custom_messagebox("Rrror", "Error: Please name ROIs", "#19232D", "white")
                return
            if region_name:
                if region_name in self.shapes:
                    combined_polygon = self.shapes[region_name].union(self.current_polygon)
                    self.shapes[region_name] = combined_polygon
                else:
                    self.shapes[region_name] = self.current_polygon

                if region_name in self.time_counters:
                    self.time_counters[region_name] += 0.0
                else:
                    self.time_counters[region_name] = 0.0

                self.current_polygon = None
                print(f"Region of Interest '{region_name}' added.")
            
            name_window.destroy()

        #create the ok button
        ok_button = self.app.create_rounded_button(name_window, width=130, height=40, corner_radius=15, bg_color='#455364', fg_color='white', text="OK", command=save_name)
        ok_button.pack(pady=10)

        #bind enter key to trigger button
        name_window.bind("<Return>", lambda event: save_name())
        
        def on_close():
            if not roi_name.get():
                self.app.custom_messagebox("Error", "Error: Please name ROIs", "#19232D", "white")
            else:
                name_window.destroy()
                
                
        name_window.protocol("WM_DELETE_WINDOW", on_close)
        

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
        canvas_width = 1056
        canvas_height = 594
        
        #calculate the scaling factors
        scale_x = video_width / canvas_width
        scale_y = video_height / canvas_height
        
        #scale the coordinates
        scaled_rois = {}
        for key, shape in rois.items():
            if isinstance(shape, Polygon):
                #scale the coordinates of a single polygon
                scaled_points = [[x * scale_x, y * scale_y] for x, y in shape.exterior.coords]
                scaled_rois[key] = Polygon(scaled_points)
            elif isinstance(shape, MultiPolygon):
                #if its a multipolygon iterate over each polygon in the multipolygon
                scaled_polygons = []
                for polygon in shape.geoms:
                    scaled_points = [[x * scale_x, y * scale_y] for x, y in polygon.exterior.coords]
                    scaled_polygons.append(Polygon(scaled_points))
                scaled_rois[key] = MultiPolygon(scaled_polygons)
        
        return scaled_rois