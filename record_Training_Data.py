import threading
import numpy as np
import os
import cv2
from datetime import datetime

filename = 'video.avi'
frames_per_second = 30
res = '480p'

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
    def __init__(self, name, number, theTime):
        threading.Thread.__init__(self)
        self.name = name
        self.number = number
        self.time = theTime

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
        make_dir(runfolder+"\\"+"stills-camera-"+str(self.number))
        outputLocation = runfolder+"\\"+"stills-camera-"+str(self.number)

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


runTime = str(datetime.today().replace(microsecond=0)).replace(":","-")
filename = "file.avi"

one = newThread("one",0, runTime)
two = newThread("two",1, runTime)

one.start()
two.start()