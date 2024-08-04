# (Work In Progress)


# DeepLabCut-Region-of-Interest-GUI

This is a GUI based program used to interpret tracking data from DeepLabCut. This program tells the amount of time an animal or object being tracked through DeepLabCut spends in a particular region of interest in the video. This program can drastically lessen the workload of manually tracking the time spent in a particular area of the video. This program also can help introduce a more objective and precise measurment of time an animal spends in a region of interest through using the DeepLabCut tracking data. The main goal of this program is to make it easier for people in research settings with little technical kno

![MainScreen](https://github.com/user-attachments/assets/0e057749-106e-46db-beea-a4d5a11da6ed)

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

### Plotting 

This program also allows the user to plot data using MatLab plots to display the movment in the video of a specific body part. There are options to display the regions of interest over the plot, display the plot over the video, zoom in on the plot to get a clearer picture, and plot a bounding box that is a box around all of the points plotted. 

### Pathing

This feature allows you to load the video and tracking data file and press "Pathing" to see a visual of the path an animal takes during the video. 

## Usage

This program is very easy to use but there are a few different ways to use it. 

### Tracking Time Spent in ROI

This is the main function of this program and this is the workflow of using it.

1. Load the video you want to analyze by using the "Open Video" button (.mp4, .mov, .avi).
2. Use the scroll bar on the bottom to select a frame to load onto the canvas.
   - Make sure that it is a clear view of the regions of interest you want to label.
   ![OpenVideo](https://github.com/user-attachments/assets/1a95a8f4-31bf-42ab-bdbd-ec5db46b05dd)

3. Load the CSV or h5 tracking file from DeepLabCut using the "Open CSV" button.
   ![OpenCSV](https://github.com/user-attachments/assets/19197a77-c271-4fbd-8e31-ae4e67080289)

4. Then, to draw and label the ROI, you need to do a few different things:
   1. Use left-click to plot a point over the video frame (plotting two points will draw a line between them).
   2. Use right-click to complete the region of interest (Once at least three points are plotted, right-click will complete the shape).
   3. After using right-click, a popup will show asking you to name the region of interest.
   4. If a different video has the same ROIs and was filmed at the same angle, you can save the ROI to use again by using the "Save ROI" button.
   ![Draw Shapes](https://github.com/user-attachments/assets/37176c95-da2d-4c94-95ed-98e915cd9f15)

5. In the case that a user already has defined the ROIs, you can load them with the "Load ROI" button to display them on the canvas.
6. Select the segment of the video to analyze (if no segment is selected, it will analyze the whole video).
   ![Video Segment](https://github.com/user-attachments/assets/c21a2e0e-54c0-4775-a221-e4a55acabe53)

7. Switch the mode of the program to the desired mode that you would like to analyze in:
   
   A. Percentage Mode:
   
      1. Percentage mode will be the default mode selected when first loading up the program.
      2. If the program was switched to a different mode, click "Percentage Mode" to switch back to this mode.
      3. Press the "Change Percent" button to change the percentage of body parts that must appear in the region of interest before it starts counting the animal as appearing in the region of interest.
      4. Exclude any body parts that you would like to not analyze using the "Exclude Body Parts" button.
         ![Exclude](https://github.com/user-attachments/assets/103b7e2a-4eba-440f-bede-ceeb0fe1dbe7)

   B. Body Part Mode:
   
      1. Switch to body part mode by pressing the "Body Part Mode" button.
      2. When prompted, click the specific body part that you would like to track.
        
   C. Any Part Mode:

      1. Switch to this mode by pressing "Any Part Mode".
      2. Exclude any body parts that you do not want to analyze.
        
9. Once you have selected all the details and the mode that will be used, there are two different ways to start processing:
   
   A. Pressing the "Process" button:
      1. Once you have all the details selected, you can press the "Process" button to get the output from the current video only.
         ![Process single](https://github.com/user-attachments/assets/ed594e51-bf9c-4149-bf8b-cb48f67138c5)

   B. Saving the details then processing a batch of details at once:
      1. Once the details are selected and it is ready to be processed, click the "Save Details" button.
      2. A popup will appear that will show the list of videos and segments of videos to be processed.
      3. You can use the "Delete" button to select a set of details and delete them from the list so they do not get processed.
      4. Then click "Process Details" to process the whole batch of details.
      5. Save the output to a CSV file using the file dialog popup.
         ![Process Multiple](https://github.com/user-attachments/assets/6fe435f1-881c-48ec-99ce-e7ac8697ac2a)









