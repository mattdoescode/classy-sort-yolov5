from asyncio.windows_events import NULL
import cv2
import numpy as np
import time

cap = cv2.VideoCapture(0)

saved_points = []

def mousePoints(event, x,y,flags,params):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(len(saved_points))
        print(x,y)
        saved_points.append([x,y])
            

ret, frame = cap.read()
cv2.imshow('frame', frame)
cv2.setMouseCallback("frame", mousePoints)

while len(saved_points) != 4: 

    ret, frame = cap.read()

    for points in saved_points: 
        cv2.circle(frame, (points[0],points[1]), 10, (255,0,0),10)

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

    for points in saved_points: 
        cv2.circle(frame, (points[0],points[1]), 10, (255,0,0),10)

    cv2.imshow('frame',frame)  

    if cv2.waitKey(24) == 27:
        break

#stops cv2 from quitting
cv2.waitKey(0)


