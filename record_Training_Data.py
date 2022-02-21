import threading
import numpy as np
import os
import cv2
from datetime import datetime
import time
import random

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

class captureThread(threading.Thread):
    def __init__(self, name, cameraID, theTime, correction_points):
        threading.Thread.__init__(self)
        self.name = name
        self.cameraID = cameraID
        self.time = theTime
        self.correction_points = correction_points
        #scaled output points in the order of TL,TR,BR,BL
        self.tank_points = [[0,0],[1920,0],[1920, 1197], [0,1197]] 
        #calculation for correction-matrix
        self.correction_matrix = cv2.getPerspectiveTransform(np.float32(self.correction_points), 
                                                            np.float32(self.tank_points))

    def run(self):
        basefolder = "RAW-FOOTAGE"
        runfolder = basefolder+"\\" + self.time
        if self.name == "Top-facing-Camera":
            make_dir(runfolder)
        outPut = runfolder + "\\camera-"+str(self.name) +"-at-"+ str(self.time)
        outPutConverted = runfolder + "\\converted-"+str(self.name) +"-at-"+ str(self.time)

        cap = cv2.VideoCapture(self.cameraID)

        out = cv2.VideoWriter(outPut+".avi", get_video_type(filename), 30, get_dims(cap, res))
        outConverted = cv2.VideoWriter(outPutConverted+".avi", get_video_type(filename), 30, (1920,1197))

        # width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)   # float `width`
        # height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float `height`
        # fps = cap.get(cv2.CAP_PROP_FPS)
        # print("is running at resolution:", width, "x", height, "at", fps, "fps")

        #make folder for stills
        make_dir(runfolder+"\\"+"stills-"+str(self.cameraID))
        outputLocation = runfolder+"\\"+"camera-"+str(self.cameraID)

        currentFrame = 0
        while True:
            currentFrame += 1
            ret, frame = cap.read()
            out.write(frame)
            cv2.imwrite(outputLocation+"\\"+str(currentFrame)+".jpg",frame)

            #apply matrix to new frame
            result = cv2.warpPerspective(frame, self.correction_matrix,(1920,1197))
            
            outConverted.write(result)
            #show frames
            cv2.imshow('conversion-'+self.name, result) # Transformed Capture
            cv2.imshow(self.name,frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cap.release()
                out.release()
                cv2.destroyWindow(self.name)
                break

class getPoints(threading.Thread):
    def __init__(self, name, camID):
        threading.Thread.__init__(self)
        #each point is [x,y]
        self.saved_points = []
        self.name = name
        self.camID = camID

    def mousePoints(self, event,x,y,flags,params):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.saved_points.append([x,y])

    #draw mouse clicks
    def drawPoints(self,frame):
        for points in self.saved_points: 
            cv2.circle(frame, (points[0],points[1]), 5, (0,255),5)

    def run(self):
        cap = cv2.VideoCapture(self.camID)

        #manually set 1080p @ 30fps
        cap.set(3, 1920)
        cap.set(4, 1080)
        cap.set(5, 30)

        ret, frame = cap.read()
        cv2.imshow(self.name,frame)  

        cv2.setMouseCallback(self.name, self.mousePoints)

        while len(self.saved_points) != 4:
       
            ret, frame = cap.read()

            self.drawPoints(frame)
            cv2.imshow(self.name,frame)  

            if cv2.waitKey(24) == 27:
                break
        
        print(self.name, "saved", self.saved_points)

    def returnPoints(self):
        return self.saved_points

    def returnCameraID(self):
        return self.camID

runTime = str(datetime.today().replace(microsecond=0)).replace(":","-")

front_points_tread = getPoints("front", 0)
top_points_thread = getPoints("top", 1)

front_points_tread.start()
top_points_thread.start()

#wait for collection of all points 
front_points_tread.join()
top_points_thread.join()

#once we have all points start recording 
#we are recording 2 raw captures, 2 edited captures, series of stills
front_capture_thread = captureThread("Front-facing-Camera", front_points_tread.returnCameraID(), 
                                runTime, front_points_tread.returnPoints())
top_capture_thread = captureThread("Top-facing-Camera", top_points_thread.returnCameraID(), 
                                runTime, top_points_thread.returnPoints())

front_capture_thread.start()
top_capture_thread.start()