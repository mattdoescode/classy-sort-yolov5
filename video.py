from asyncio.windows_events import NULL
import cv2
import numpy as np

cap = cv2.VideoCapture(0)

saved_points = []

def mousePoints(event, x,y,flags,params):
    if event == cv2.EVENT_LBUTTONDOWN:
        # print(len(saved_points))
        # print(x,y)
        saved_points.append([x,y])
        # print(saved_points)

def drawPoints():
    for points in saved_points: 
        cv2.circle(frame, (points[0],points[1]), 5, (0,255),5)

def connectPoints():
    previous = []
    first = []
    for point in saved_points:
        if not previous and not first:
            first = point
            previous = point
            continue
        
        #last point draws to the first 
        #last point dears to second last visited
        if saved_points[-1] == point:
            cv2.line(frame,[point[0],point[1]],[first[0],first[1]],(0,200,0),3)
            cv2.line(frame,[previous[0],previous[1]],[point[0],point[1]],(0,200,0),3)
        else:
            cv2.line(frame,[previous[0],previous[1]],[point[0],point[1]],(0,200,0),3)
        previous = point

    previous = []
            
ret, frame = cap.read()
cv2.imshow('frame', frame)
cv2.setMouseCallback("frame", mousePoints)

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

#remove callback
cv2.setMouseCallback("frame",lambda *args : None)

while 1:
    ret, frame = cap.read()

    drawPoints()
    connectPoints()

    cv2.imshow('frame',frame)  
    if cv2.waitKey(24) == 27:
        break

#stops cv2 from quitting
cv2.waitKey(0)


