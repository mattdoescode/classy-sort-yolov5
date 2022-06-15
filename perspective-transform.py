"""
    NEED TO MODIFY FOR DIFFERENT PERSPECTIVES 5/30

"""

"""
Takes raw video footage or saved file and applies a manual Perspective Transformation 
such that the output is (1) scaled to a format that can be used pixels to real world units. 
                    and (2) corrects for distoration / improperly positioned camera

Currently this file is setup to map a 640 x 480p camera to a standard 10 gallon fish tank

Matthew Loewen
2/13/2022
"""

""" "output resolution"

tank measures 10 gal are

20.25" length
12.625" height
10.5" width

for a 640 x 480

    640
-------------
|           |
|           | 480 
|           |
-------------

assuming everything is perfect 
mapping largest dimensions 
640px = 20.25"

1 pixel = 0.031640625 inches
conversely 
31.6049382716 pixels = 1 inch

we will base all tracking results off of this conversion
NEED TO MAKE SURE THIS SCALE IS KEPT FOR ALL CONVERSIONS

SO....

20.25 x 31.6049382716 = 640 -> Our X will be 640 pixels
12.625 X 31.6049382716 = 399.012345679 -> Our Y for video will be 399 pixels 
10.5 x 31.6049382716 = 331.851851852 -> Our Z will be 332 pixels

As we track the fish we can use these coordinates to translte to real world location

new 

    1920
------------
|          | 1080
|          |
|          |
------------

1920 = 20.25

1 pixel = 0.010546875 inch
94.8148148148 pixels = 1 inch 


x = 1920 pixels
y = 12.625 x 94.8148148148 = 1197.03703704
z = 10.5 x 94.8148148148 = 995


20.25" length
12.625" height
10.5" width

---------------

1280 x 720
1280px = 20.25"
x = 1280
1 px = 0.0158203125 in
63.2098765432px = 1 inch
y = 12.625 x 63.2098765432 = 798.024691358
z = 10.5 x 63.2098765432 = 663.703703704

"""

import cv2
import numpy as np
from os.path import exists
import sys


convertvideo = False
conversionFile = r"C:\Users\matt2\Desktop\Fish videos - final cuts\1 yellow zebra fish\1-front-30-second-clip.mp4"
saveVideo = True

#point order 
#TL, TR, BR, BL
saved_points = []
# To do... cam 1 cords, cam 2 cords
tank_points = [[0,0],[640,0],[640,399],[0,399]]
# X, Y, Z
scaledResolution = [640, 399, 332]
# TO DO: write conversion function for dynamic tank size + camera resolution

#record mouse clicks
def mousePoints(event,x,y,flags,params):
    if event == cv2.EVENT_LBUTTONDOWN:
        saved_points.append([x,y])

#draw mouse clicks
def drawPoints():
    for points in saved_points: 
        cv2.circle(frame, (points[0],points[1]), 5, (0,255),5)

#make a box around points
def connectPoints():
    if len(saved_points) < 2: return
    previous = []
    first = []
    for point in saved_points:
        if not previous and not first:
            first = point
            previous = point
            continue
        
        #last point draws to the first 
        #last point draws to second last visited
        if saved_points[-1] == point:
            cv2.line(frame,[point[0],point[1]],[first[0],first[1]],(0,200,0),3)
            cv2.line(frame,[previous[0],previous[1]],[point[0],point[1]],(0,200,0),3)
        else:
            cv2.line(frame,[previous[0],previous[1]],[point[0],point[1]],(0,200,0),3)
        previous = point
    previous = []

if convertvideo and not exists(conversionFile):
    print("Invalid path to file")
    sys.exit()

if convertvideo:
    cap = cv2.VideoCapture(conversionFile)
else:
    cap = cv2.VideoCapture(0)

ret, frame = cap.read()
cv2.imshow('frame', frame)
cv2.setMouseCallback("frame", mousePoints)

#get tank points
while len(saved_points) != 4:

    if not convertvideo:
        ret, frame = cap.read()

    drawPoints()
    cv2.imshow('frame',frame)  

    if cv2.waitKey(24) == 27:
        break

#stop recording mouse clicks
cv2.setMouseCallback("frame",lambda *args : None)

#calculate matrix for warping 
print(saved_points)
print(tank_points)
matrix = cv2.getPerspectiveTransform(np.float32(saved_points), np.float32(tank_points))

base = "corrected-video"
filename = ""
if convertvideo:
    #get filename and remove .avi
    lastDir = conversionFile.rfind("\\")
    # print(lastDir)
    # lastDir = lastDir[lastDir+1:-4]
    lastDir = "Converted-" + str(lastDir) + ".avi"
else:
    lastDir = "file.avi"

if saveVideo:
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    fps = cap.get(cv2.CAP_PROP_FPS)
    video_writer = cv2.VideoWriterD(lastDir,fourcc, fps, (scaledResolution[0],scaledResolution[1]))


while cap.isOpened():
    ret, frame = cap.read()
    
    if not ret and saveVideo:
        video_writer.release()
        print("end of processing")
        sys.exit()

    #apply matrix to new frame
    result = cv2.warpPerspective(frame, matrix,(scaledResolution[0],scaledResolution[1]))

    #still draw bounding box on raw video capture
    drawPoints()
    connectPoints()

    cv2.imshow('frame',frame)
    cv2.imshow('conversion', result) # Transformed Capture

    if saveVideo:
        video_writer.write(result)

    if cv2.waitKey(24) == 27:
        break

print("converted file")