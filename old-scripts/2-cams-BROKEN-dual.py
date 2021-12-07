# Script shell from here https://stackoverflow.com/questions/29664399/capturing-video-from-two-cameras-in-opencv-at-once
# modified to take in parameters for recording, to record, and to process data 

# see https://www.codingforentrepreneurs.com/blog/how-to-record-video-in-opencv-python
# for more examples on how to modify camera feed

import cv2
import numpy as np
import threading
import os
from datetime import datetime


outputLocation = ""

VIDEO_TYPE = {
    'avi': cv2.VideoWriter_fourcc(*'XVID'),
    #'mp4': cv2.VideoWriter_fourcc(*'H264'),
    'mp4': cv2.VideoWriter_fourcc(*'XVID'),
}

def make_dir(directoryName):
    # Check whether the specified path exists or not
    isExist = os.path.exists(directoryName)

    if not isExist:
        # Create a new directory because it does not exist 
        os.makedirs(directoryName)
        print("The new directory is created!", directoryName)


def get_video_type(filename):
    filename, ext = os.path.splitext(filename)
    if ext in VIDEO_TYPE:
      return  VIDEO_TYPE[ext]
    return VIDEO_TYPE['mp4']

class camThread(threading.Thread):
    def __init__(self, previewName, camID, runTime):
        threading.Thread.__init__(self)
        self.previewName = previewName
        self.camID = camID
        self.runTime = runTime
    def run(self):
        print ("Starting " + self.previewName)
        camPreview(self.previewName, self.camID, self.runTime)

def camPreview(previewName, camID, runTime):
    cv2.namedWindow(previewName)
    cam = cv2.VideoCapture(camID)

    if cam.isOpened():  # try to get the first frame

        rval, frame = cam.read()

        width  = cam.get(cv2.CAP_PROP_FRAME_WIDTH)   # float `width`
        height = cam.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float `height`
        fps = cam.get(cv2.CAP_PROP_FPS)

        basefolder = "RAW-FOOTAGE"
        runfolder = basefolder+"\\" + runTime


        print("camera", camID, "is running at resolution:", width, "x", height, "at", fps, "fps")
        outPut = runfolder + "\\camera-"+str(camID) +"-at-"+ str(runTime)

        # makes directory if needed. 
        # openCV will not record anything if directory does not exist. 
        # REALLY STUPID of openCV
        make_dir(runfolder)
        out = cv2.VideoWriter(outPut+".mp4", get_video_type(filename), 30, (int(width),int(height)))

        #make folder for stills
        make_dir(runfolder+"\\"+"stills-camera-"+str(camID))
        outputLocation = runfolder+"\\"+"stills-camera-"+str(camID)

    else:
        rval = False

    currentFrame = 0
    while rval:
        currentFrame = currentFrame + 1
        # record video + record image stills.
        # recorded video can be used for analysis later
        # stills will be grabbed by YOLO and processed. 
        cv2.imshow(previewName, frame)

        # print("attemping to save," + outputLocation+"\\"+str(currentFrame)+".jpg")
        cv2.imwrite(outputLocation+"\\"+str(currentFrame)+".jpg",frame)

        rval, frame = cam.read()
        out.write(frame) 

        key = cv2.waitKey(20)

        if key == 27:  # exit on ESC
            # cam.release()
            # out.release()
            cv2.destroyWindow(previewName)
            cam.release()
            out.release()
            break

# Create two threads as follows

runTime = str(datetime.today().replace(microsecond=0)).replace(":","-")
filename = "file.avi"

thread1 = camThread("Camera 1", 0, runTime)
thread2 = camThread("Camera 2", 1, runTime)
thread1.start()
thread2.start()