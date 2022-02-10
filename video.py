import cv2
import numpy as np

""" "output resolution"

tank measures 10 gal are

20.25" length
12.625" height
10.5" width

Used webcam records at 640 x 480

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
"""

cap = cv2.VideoCapture(0)


#point order 
#TL, TR, BR, BL
saved_points = []
tank_points = [[0,0],[640,0],[640,399],[0,399]]
# X, Y, Z
scaledResolution = [640, 399, 332]
# TO DO: write conversion function for dynamic tank size + camera resolution

#record mouse clicks to create box for perspective mapping
def mousePoints(event,x,y,flags,params):
    if event == cv2.EVENT_LBUTTONDOWN:
        saved_points.append([x,y])

#draw mouse clicks
def drawPoints():
    for points in saved_points: 
        cv2.circle(frame, (points[0],points[1]), 5, (0,255),5)

#make a box around points
def connectPoints():
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

#start video capture
ret, frame = cap.read()
cv2.imshow('frame', frame)
cv2.setMouseCallback("frame", mousePoints)

#get tank points
while len(saved_points) != 4: 
    ret, frame = cap.read()
    drawPoints()
    cv2.imshow('frame',frame)  

    if len(saved_points) == 4:
        print("saved points is 4")
        for item in saved_points:
            print(item)

    if cv2.waitKey(24) == 27:
        break

#stop recording mouse clicks
cv2.setMouseCallback("frame",lambda *args : None)

#calculate matrix for warping 
print(saved_points)
print(tank_points)
matrix = cv2.getPerspectiveTransform(np.float32(saved_points), np.float32(tank_points))

while 1:
    ret, frame = cap.read()

    #apply matrix to new frame
    result = cv2.warpPerspective(frame, matrix,(640,399))

    #still draw bounding box on raw video capture
    drawPoints()
    connectPoints()

    cv2.imshow('frame',frame)
    cv2.imshow('conversion', result) # Transformed Capture
    if cv2.waitKey(24) == 27:
        break

#stops cv2 from quitting
cv2.waitKey(0)


