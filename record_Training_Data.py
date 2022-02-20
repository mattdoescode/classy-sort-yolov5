import threading
import numpy as np
import os
import cv2
from datetime import datetime
import time

filename = 'video.avi'
frames_per_second = 30
res = '1080p'

# Set resolution for the video capture
# Function adapted from https://kirr.co/0l6qmh
def change_res(cap, width, height):
    cap.set(3, width)
    cap.set(4, height)

# Standard Video Dimensions Sizes
STD_DIMENSIONS =  {
    "480p": (640, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "4k": (3840, 2160),
}

def make_dir(directoryName):
    # Check whether the specified path exists or not
    isExist = os.path.exists(directoryName)

    if not isExist:
        # Create a new directory because it does not exist 
        os.makedirs(directoryName)
        print("Created new directory:", directoryName)


# grab resolution dimensions and set video capture to it.
def get_dims(cap, res='1080p'):
    width, height = STD_DIMENSIONS["480p"]
    if res in STD_DIMENSIONS:
        width,height = STD_DIMENSIONS[res]
    ## change the current caputre device
    ## to the resulting resolution
    change_res(cap, width, height)
    return width, height

def get_perspective_points():
    #point order 
    #TL, TR, BR, BL
    saved_points = []

#draw mouse clicks
def drawPoints(saved_points, frame):
    for points in saved_points: 
        cv2.circle(frame, (points[0],points[1]), 5, (0,255),5)

#draw a box with the points
def connectPoints(saved_points, frame):
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

# Video Encoding, might require additional installs
# Types of Codes: http://www.fourcc.org/codecs.php
VIDEO_TYPE = {
    'avi': cv2.VideoWriter_fourcc(*'XVID'),
    #'mp4': cv2.VideoWriter_fourcc(*'H264'),
    'mp4': cv2.VideoWriter_fourcc(*'XVID'),
}

def get_video_type(filename):
    filename, ext = os.path.splitext(filename)
    if ext in VIDEO_TYPE:
      return  VIDEO_TYPE[ext]
    return VIDEO_TYPE['avi']


class newThread(threading.Thread):
    def __init__(self, name, number, theTime, correction_points):
        threading.Thread.__init__(self)
        self.name = name
        self.number = number
        self.time = theTime
        self.correction_points = correction_points


    def run(self):
        
        basefolder = "RAW-FOOTAGE"
        runfolder = basefolder+"\\" + self.time
        if self.name == "one":
            make_dir(runfolder)
        outPut = runfolder + "\\camera-"+str(self.name) +"-at-"+ str(self.time)
        
        cap = cv2.VideoCapture(self.number)
        out = cv2.VideoWriter(outPut+".avi", get_video_type(filename), 30, get_dims(cap, res))
        width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)   # float `width`
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float `height`
        fps = cap.get(cv2.CAP_PROP_FPS)
        print("is running at resolution:", width, "x", height, "at", fps, "fps")

        #make folder for stills
        make_dir(runfolder+"\\"+"stills-"+str(self.number))
        outputLocation = runfolder+"\\"+"camera-"+str(self.number)

        currentFrame = 0
        while True:
            currentFrame += 1
            ret, frame = cap.read()
            out.write(frame)
            cv2.imwrite(outputLocation+"\\"+str(currentFrame)+".jpg",frame)

            cv2.imshow(self.name,frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cap.release()
                out.release()
                cv2.destroyWindow(self.name)
                break


top_points = []
front_points = []

def getPointsThread(camID, view, save_points):
    
    print('run')
    cap = cv2.VideoCapture(camID)
    ret, frame = cap.read()
    cv2.imshow(view, frame)
    cv2.setMouseCallback(view, save_points)

    #get tank points
    while len(save_points) != 4:

        ret, frame = cap.read()

        drawPoints(save_points, frame)
        cv2.imshow(view,frame)  

        if cv2.waitKey(24) == 27:
            break

    drawPoints(save_points, frame)
    connectPoints(save_points, frame)
    cv2.imshow(view,frame)
    print(save_points)



runTime = str(datetime.today().replace(microsecond=0)).replace(":","-")

# front_correction_points = getPointsThread(0, "front", [])
# top_correction_points = getPointsThread(1, "top", [])
front_correction_points = threading.Thread(target=getPointsThread, args= (0, "front", front_points))
front_correction_points.start()


# front_points = front_correction_points.run()
# top_points = top_correction_points.run()

# one = newThread("Front-facing-Camera",0, runTime, front_points)
# two = newThread("Top-facing-camera",1, runTime, top_points)

# one.start()
# two.start()