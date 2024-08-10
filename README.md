# (Work In Progress)


# DeepLabCut-Region-of-Interest-GUI

This is a GUI based program used to interpret tracking data from DeepLabCut. This program tells the amount of time an animal or object being tracked through DeepLabCut spends in a particular region of interest in the video. This program can drastically lessen the workload of manually tracking the time spent in a particular area of the video. This program also can help introduce a more objective and precise measurment of time an animal spends in a region of interest through using the DeepLabCut tracking data.

![HomeGif](https://github.com/user-attachments/assets/7fb51dee-353a-45db-8319-b2cd3fce7b6a)


## Table of Contents
- [Installation](#installation)
- [Features](#features)
- [Usage](#usage)
- [Contact](#contact)

## Installation

You can download the latest release in .exe form from the release section to the right. Or you can clone the repo using this link https://github.com/JMcGrath2025/DeepLabCut-Region-of-Interest-GUI.git

## Features

The main purpose and feature of this program is to accurately check the amount of time that an animal spends in a specific area of a video.

### Easy to Use GUI

This program comes equipt with a very easy to use GUI that allows anyone that downloads this program to plug in their data from DeepLabCut and get an accurate output.

### Tracking Time Spent in Region of Interest

This is the main purpose of this program and there are a few ways that this is done:
-When you first open the program it will be in percentage mode which is set to 50% by default, this method of tracking the time spent in a region of interest will only start the counting the amount of time spent in the region when 50% or more of the animals body parts appear in the region of interest. You can change the percent of the animal that you would like to change as well through the "Change Percent" button. If you change the mode you can also change it back by pressing the "Percentage Mode" button.

-Another way that you can use this program is by using body part mode. You can switch to that mode by pressing "Body Part Mode". This mode allows for tracking the amount of a time a specific body part spends in a region of interest.

-The final way to track the amount of time spent in a region of interest is through any part mode. You can switch to this mode by pressing "Any Part Mode". This mode tracks the time spent in a region when any part of the animal passes into the zone.

### Plotting 

This program also allows the user to plot data using MatLab plots to display the movment in the video of a specific body part. There are options to display the regions of interest over the plot, display the plot over the video, zoom in on the plot to get a clearer picture, and plot a bounding box that is a box around all of the points plotted. 

### Pathing

This feature allows you to load the video and tracking data file and press "Pathing" to see a visual of the path an animal takes during the video. 

![pathing](https://github.com/user-attachments/assets/28480b56-b5e5-4e4b-b71b-0c2277a34372)

### Batch Processing

This feature allows a user to select all the details of how they would like to analyze a video, for example what body parts to exclude, what regions of interest to use, the video and tracking data to be analyzed, and any other details that the user changes and save them to a list to be processed all at one time. So for example if you want to analyze multiple different segments from multiple different videos or multiple segments from the same video you can select the details to be processed but instead of pressing the "Process" button insetead you can press the "Save Details" button to save the details to a list. Then once you have the details of what you want to process you can process everything in a batch through pressing "Process Details" and when it is done you have the option to save the output of time spent in each region in each of the videos that you saved the details for.

### Excluding Body Parts

Another helpful feature of this program is having the ability to exclude body parts that are not necessary to be tracked. It can also be used to exclude all body parts except for a select few in order to track when a specific portion of the animal enters into the region of interest. For example you might want to exlude tracking data pertaining to a mouse's tail so the it doesn't start tracking the time spent in a region when only the tail is in said region. Another use of this feature could be to exclude all body parts except for the body parts that make up the head of an animal to track when it enters a specific region. 

### Drawing Custom Shapes

What really sets this program apart from the others that are available is the ability to draw custom shapes as the regions of interest. So if the region of interest is not a square or rectangular shape you can still draw a custom shape over the video to represent the region of interest. 

### Saving and Loading Regions of Interest

This program also allows you to easily save and load priorly defined regions of interest to use on videos filmed with at the same angle with the same regions of interest. 

### Get a Specific Video Segment

This feature allows for the selection of a specific segment to analyze. So you could analyze only a portion of the video or shorten the video so a certain part is excluded. 

### Loading of Video and Tracking Data

Through keeping the video and tracking data loaded you can analyze different parts of the same video by changing the segment that will be analyzed, body parts to be excluded or the mode in which it will analyze the tracking data in.

## Usage

This program is very easy to use but there are a few different ways to use it. 

### Tracking Time Spent in ROI

This is the main function of this program and this is the workflow of using it.

#### 1. Load the video you want to analyze by using the "Load Video" button (.mp4, .mov, .avi).
#### 2. Use the scroll bar on the bottom to select a clear frame to load onto the canvas.

   ![load_video](https://github.com/user-attachments/assets/891e34c0-ca5f-47c8-bb9d-a3660c12d602)

#### 3. Load the CSV or h5 tracking file from DeepLabCut using the "Load Tracking" button.

   ![load_tracking](https://github.com/user-attachments/assets/bcd07c86-4288-420b-9847-f11ba0785098)

#### 4. Then, to draw and label the ROI, you need to do a few different things:
   1. Use left-click to plot a point over the video frame (plotting two points will draw a line between them).
   2. (optional) Hold "shift" to align the mouse directly across from last point
   3. Use right-click to complete the region of interest (Once at least three points are plotted, right-click will complete the shape).
   4. (optional) Press "space" to complete a perfect square or rectangle
   5. After using completing the ROI, a popup will show asking you to name the region of interest.
   6. If a different video has the same ROIs and was filmed at the same angle, you can save the ROI to use again by using the "Save ROI" button.
      
   ![draw_roi](https://github.com/user-attachments/assets/02301d54-51d0-49b1-9ee2-5308118afa8f)

#### 7. In the case that a user already has defined the ROIs, you can load them with the "Load ROI" button to display them on the canvas.

   ![load_roi](https://github.com/user-attachments/assets/8d968c32-0451-4576-847e-d1e1d9e19136)

#### 8. Select the segment of the video to analyze (if no segment is selected, it will analyze the whole video).

   ![select_segment](https://github.com/user-attachments/assets/143f0752-c080-4556-9097-557028976eb4)

#### 9. Switch the mode of the program to the desired mode that you would like to analyze in by pressing the "Percentage Mode", "Any Body Part Mode", and "Body Part Mode"

   Percentage Mode:
   
   1. Percentage mode will be the default mode selected when first loading up the program.
   2. If the program was switched to a different mode, click "Percentage Mode" to switch back to this mode.
   3. Press the "Change Percent" button to change the percentage of body parts that must appear in the region of interest before it starts counting the animal as appearing in the region of interest.
   4. Exclude any body parts that you would like to not analyze using the "Exclude Body Parts" button.
      
   ![exclude_body_parts](https://github.com/user-attachments/assets/bfa46a75-5455-4227-a265-e0524061e17a)
   6. Process the video by pressing the "Process" button.
      
   ![process_Percentagemode](https://github.com/user-attachments/assets/2b319dc9-9bc9-4efb-af93-18412c08d601)


   Body Part Mode:
   
   1. Switch to body part mode by pressing the "Body Part Mode" button.
   2. When prompted, click the specific body part that you would like to track.
   3. Process the video by pressing the "Process" button.
      
   ![process_body_part_mode](https://github.com/user-attachments/assets/89f99387-faa9-43e8-b27e-371c81fc8be9)
        
   Any Part Mode:

   1. Switch to this mode by pressing "Any Part Mode".
   2. Exclude any body parts that you do not want to analyze.
   3. Process the video by pressing the "Process" button.
      
   ![process_any_part_mode](https://github.com/user-attachments/assets/0266f08a-2a06-4cbc-9bd0-16edbddfb602)
        
#### 10. Batch Processing:
   1. Select different segments from the same video or from different videos, exclude body parts, and select the mode for processing.
   2. Click the "Save Details" button to bring the details popup.
      
   ![proccessing details](https://github.com/user-attachments/assets/01170368-84c4-4386-9eb0-b0ff399d93fa)
      
   4. (optional) Delete any details that do not need to be processed
   5. Click "Process Details".
   6. Once the processing is finished save to a csv file.
      
   ![process details](https://github.com/user-attachments/assets/664cdcff-1382-4e1f-a2ec-b408452a1c36)


   

### Plotting

This part of the program can show a graph very quickly using the details selected through using the program.

1. Follow steps 1-6 in the instructions for tracking time spent in ROIs selecting the details like the video segment, and ROI's
2. Click the "Plot" button
3. In the popup click the body part that you would like to plot
4. In the next popup click the checkboxes to determine what will be shown in the plot
   A. Select "Show Bounding Box" to show the total area in pixels the points take up.
   B. Select "Show ROIs" to show the ROIs on the plot
   C. Select "Show Area Under Curve (AUC)" to show the area under curve on the plot
   D. Select "Square Graph" to show the data in a square aspect ratio instead of rectangular
   E. Select "Plot Over Video" to plot the data over the video
   C. Select "Zoom In" to zoom in on the plotted data on the video (Zoom Radius is the radius from the middle of the points)
5. Click on "Apply" to see the plot popup window
6. Click download to download a picture of the plot
   
![plotting](https://github.com/user-attachments/assets/45d0cb5d-b597-4d44-81ac-afb98e390bbd)
   

### Pathing

This part of the program is simply a way to show the path an animal takes using the DeepLabCut tracking data

1. Follow steps 1-3 in the first set of instructions
2. Select the segment of the video you would like to view the pathing of
3. Click the "Pathing" button
4. Select one or more of the body parts to show the pathing of
5. Use the "D" key to move the move the slideshow forward
6. Use the "A" key to move the slideshow backwards
7. Use the space bar to pause the slideshow

![pathing](https://github.com/user-attachments/assets/28480b56-b5e5-4e4b-b71b-0c2277a34372)










