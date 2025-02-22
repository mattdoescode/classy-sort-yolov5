# https://stackoverflow.com/questions/57399915/how-do-i-determine-the-locations-of-the-points-after-perspective-transform-in-t

"""
    IMPORTANT THINGS:

# NOTES: When running on saved videos - playback is not in realtime but rather it's as fast as the computer can process 
    # this is approxmately 100 frames person second with a rtx 3080 (~3x real time speed @ 30 fps footage)

Params to triple check for corectness:
    #Weights -> make sure correct weights for the dataset
    #Source -> don't process the wrong video feed
"""



"""
Code base started from https://github.com/tensorturtle/classy-sort-yolov5 this author 
implemented sort as outlined here https://github.com/abewley/sort into YoloV5. 

I have heavily modified this codebase. I fixed several bugs and added the following:
    Changed code to report detection location
    PostgreSQL recording
    Multiple labels 
    Multiple Video recording / saving
    Frame saving
    .txt file saving
    Video output
    PerspectiveTransform code
"""

# python interpreter searchs these subdirectories for modules
import sys

from cv2 import getPerspectiveTransform
sys.path.insert(0, './yolov5')
sys.path.insert(0, './sort')

import argparse
import os
import platform
import shutil
import time
from pathlib import Path
import cv2
import torch
import torch.backends.cudnn as cudnn
from datetime import datetime
import numpy as np

#yolov5
from yolov5.utils.datasets import LoadImages, LoadStreams
from yolov5.utils.general import check_img_size, non_max_suppression, scale_coords
from yolov5.utils.torch_utils import select_device, time_synchronized

#SORT
import skimage
from sort import *

#DB stuff
import psycopg2
from config import config

torch.set_printoptions(precision=3)

def connect(tableName):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        conn.autocommit = True

        # create a cursor
        cur = conn.cursor()

        #Create TABLE
        createTable = """CREATE TABLE "{}" ( 
            recordID BIGSERIAL PRIMARY KEY,
            frame INTEGER NOT NULL,
            bbox_x1 decimal	NOT NULL,
            bbox_y1 decimal	NOT NULL,
            bbox_x2 decimal	NOT NULL,
            bbox_y2 decimal	NOT NULL,
            category CHARACTER VARYING(50) NOT NULL, 
            identityNum INTEGER NOT NULL,
            scaledX decimal NOT NULL,
            scaledY decimal NOT NULL
        )""".format(str(tableName))

        cur.execute(createTable)
        print("Created new DB table", tableName)

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        sys.exit()
    return cur
    
def insertRecordDB(cur, tableName, data):
    statement = """INSERT INTO "{}"
    (frame, bbox_x1,
            bbox_y1,
            bbox_x2,
            bbox_y2,
            category,
            identityNum,
            scaledX,
            scaledY
    ) VALUES ({},{},{},{},{},{},{},{},{})
    """.format(str(tableName), data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8] )

    print(statement)

    cur.execute(statement)
    
palette = (2 ** 11 - 1, 2 ** 15 - 1, 2 ** 20 - 1)

def bbox_rel(*xyxy):
    """" Calculates the relative bounding box from absolute pixel values. """
    bbox_left = min([xyxy[0].item(), xyxy[2].item()])
    bbox_top = min([xyxy[1].item(), xyxy[3].item()])
    bbox_w = abs(xyxy[0].item() - xyxy[2].item())
    bbox_h = abs(xyxy[1].item() - xyxy[3].item())
    x_c = (bbox_left + bbox_w / 2)
    y_c = (bbox_top + bbox_h / 2)
    w = bbox_w
    h = bbox_h
    return x_c, y_c, w, h


def compute_color_for_labels(label):
    """
    Simple function that adds fixed color depending on the class
    """
    color = [int((p * (label ** 2 - label + 1)) % 255) for p in palette]
    return tuple(color)


def draw_boxes(img, bbox, identities=None, categories=None, names=None, offset=(0, 0)):
    for i, box in enumerate(bbox):
        x1, y1, x2, y2 = [int(i) for i in box]
        x1 += offset[0]
        x2 += offset[0]
        y1 += offset[1]
        y2 += offset[1]
        # box text and bar
        cat = int(categories[i]) if categories is not None else 0
        
        id = int(identities[i]) if identities is not None else 0
        
        color = compute_color_for_labels(id)
        
        label = f'{id} | {names[cat]}'
        t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_PLAIN, 1, 1)[0]
        #Rect around detected object
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)

        #Rect background for text
        cv2.rectangle(
            img, (x1, y1+(y2-y1)), (x1 + t_size[0] + 3, y1 + t_size[1] + 4 + (y2-y1)), color, -1)
        #
        cv2.putText(img, label, (x1, y1 +
                                    t_size[1] + 4 + (y2-y1)), cv2.FONT_HERSHEY_PLAIN, 1, [255, 255, 255], 1)
    return img

def drawPoints(saved_points,frame):
    for points in saved_points: 
        cv2.circle(frame, (points[0],points[1]), 5, (0,255),5)

def connectPoints(saved_points, frame):
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

savedMousePoints = []
def mousePoints(event,x,y,flags,params):
    if event == cv2.EVENT_LBUTTONDOWN:
        savedMousePoints.append([x,y])


def detect(opt, *args):
    out, source, weights, view_img, save_txt, imgsz, save_img, sort_max_age, sort_min_hits, sort_iou_thresh, perspective_transformation = \
        opt.output, opt.source, opt.weights, opt.view_img, opt.save_txt, opt.img_size, opt.save_img, opt.sort_max_age, opt.sort_min_hits, opt.sort_iou_thresh, opt.perspective_transformation
    
    webcam = source == '0' or source == '1' or source.startswith(
        'rtsp') or source.startswith('http') or source.endswith('.txt')
    # Initialize SORT
    sort_tracker = Sort(max_age=sort_max_age,
                       min_hits=sort_min_hits,
                       iou_threshold=sort_iou_thresh) # {plug into parser}
    
    
    # Directory and CUDA settings for yolov5
    device = select_device(opt.device)
    if os.path.exists(out):
        shutil.rmtree(out)  # delete output folder
    os.makedirs(out)  # make new output folder
    half = device.type != 'cpu'  # half precision only supported on CUDA

    # Load yolov5 model
    model = torch.load(weights, map_location=device)['model'].float() #load to FP32. yolov5s.pt file is a dictionary, so we retrieve the model by indexing its key
    model.to(device).eval()
    if half:
        model.half() #to FP16

    # Set DataLoader
    vid_path, vid_writer = None, None
    
    if webcam:
        #collect correction points
        cap = cv2.VideoCapture(0)
        cap.set(3, 640)
        cap.set(4, 480)
        cap.set(5, 30)
        ret, frame = cap.read()
        name = "collect"
        cv2.imshow(name,frame)
        cv2.setMouseCallback(name, mousePoints)

        while len(savedMousePoints) != 4:
            ret, frame = cap.read()
            drawPoints(savedMousePoints, frame)
            cv2.imshow(name,frame)
            if cv2.waitKey(24) == 27:
                    break
        cv2.destroyAllWindows()
        cap.release #might not need this line

        view_img = True
        cudnn.benchmark = True  # set True to speed up constant image size inference
        dataset = LoadStreams(source, img_size=imgsz)
        perspectiveName = "front" #if '0' == source else "side"
        tableName = os.path.split(out)[1] + "-" + perspectiveName
        print("table name is", tableName)
        print("source is ", source)
    else:
        dataset = LoadImages(source, img_size=imgsz)

        # get filename
        lastDir = source.rfind("\\")
        # source = filename without .avi 
        source = source[lastDir+1:-4]

        print("source is ", source)
        print("PROCESSING SAVED FILE")
        # source = "FROM-FILE-" + source

        tableName = os.path.split(out)[1] + "-" + source

        print("VIDEO FILE SOURCE IS: ", os.path.abspath(source))
    
    # get names of object categories from yolov5.pt model
    names = model.module.names if hasattr(model, 'module') else model.names 

    # Run inference
    t0 = time.time()
    img = torch.zeros((1,3,imgsz,imgsz), device=device) #init img
    
    # Run once (throwaway)
    _ = model(img.half() if half else img) if device.type != 'cpu' else None
    
    save_path = str(Path(out))
    txt_path = str(Path(out))+'/results.txt'
    print("OUTPUT FILES WILL BE SAVED TO: ", os.path.abspath(save_path))

    cur = connect(tableName)

    
    ######
        #PROCESSING EACH FRAME HERE
    #####
    imgRaw = ""
    for frame_idx, (path, img, im0s, vid_cap) in enumerate(dataset): #for every frame
        img= torch.from_numpy(img).to(device)
        img = img.half() if half else img.float() #unint8 to fp16 or fp32
        img /= 255.0 #normalize to between 0 and 1.
        if img.ndimension()==3:
            img = img.unsqueeze(0)

        # Inference
        t1 = time_synchronized()
        pred = model(img, augment=opt.augment)[0] 

        # Apply NMS
        # multiple detections at same location -> combine to become one
        pred = non_max_suppression(
            pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=opt.agnostic_nms)
        t2 = time_synchronized()

        imgRaw = im0s[0].copy()
        # Process detections
        for i, det in enumerate(pred): #for each detection in this frame
            if webcam:  # batch_size >= 1
                p, s, im0 = path[i], '%g: ' % i, im0s[i].copy()
            else:
                p, s, im0 = path, '', im0s
            
            s += f'{img.shape[2:]}' #print image size and detection report
            save_path = str(Path(out) / Path(p).name)

            # Rescale boxes from img_size (temporarily downscaled size) to im0 (native) size
            det[:, :4] = scale_coords(
                img.shape[2:], det[:, :4], im0.shape).round()
            
            for c in det[:, -1].unique(): #for each unique object category
                n = (det[:, -1] ==c).sum() #number of detections per class
                s += f' - {n} {names[int(c)]}'

            dets_to_sort = np.empty((0,6))

            # Pass detections to SORT
            # NOTE: We send in detected object class too
            for x1,y1,x2,y2,conf,detclass in det.cpu().detach().numpy():
                dets_to_sort = np.vstack((dets_to_sort, np.array([x1, y1, x2, y2, conf, detclass])))
            print('\n')
            print('Input into SORT:\n',dets_to_sort,'\n')

            # Run SORT
            tracked_dets = sort_tracker.update(dets_to_sort)

            print('Output from SORT:\n',tracked_dets,'\n')
            
            # draw boxes for visualization
            if len(tracked_dets)>0:
                bbox_xyxy = tracked_dets[:,:4]
                identities = tracked_dets[:, 8]
                categories = tracked_dets[:, 4]
                draw_boxes(im0, bbox_xyxy, identities, categories, names)
                
            # Write detections to file. NOTE: Not MOT-compliant format.
            if save_txt and len(tracked_dets) != 0:
                for j, tracked_dets in enumerate(tracked_dets):
                    bbox_x1 = tracked_dets[0]
                    bbox_y1 = tracked_dets[1]
                    bbox_x2 = tracked_dets[2]
                    bbox_y2 = tracked_dets[3]
                    category = tracked_dets[4]
                    u_overdot = tracked_dets[5]
                    v_overdot = tracked_dets[6]
                    s_overdot = tracked_dets[7]
                    identity = tracked_dets[8]
                    
                    #bounds of transformation
                #top view
                    #normalPoints = [[0,0],[640,0],[640,320],[0,320]]
                #front view
                    normalPoints = [[0,0],[640,0],[640,384],[0,384]]

                    #calculate the transformation
                    # matrix=cv2.getPerspectiveTransform(np.array(normalPoints),np.array(savedMousePoints)) #move this out of loop later
                    convertedNormalPoints = np.array([[normalPoints[0]],[normalPoints[1]],[normalPoints[2]],[normalPoints[3]]],np.float32)
                    convertedSavedMousePoints = np.array([[savedMousePoints[0]],[savedMousePoints[1]],[savedMousePoints[2]],[savedMousePoints[3]]],np.float32)

                    matrix = getPerspectiveTransform(convertedSavedMousePoints,convertedNormalPoints)#move this outside of loop
                    
                    #Existing center point of detected object
                    p = [(bbox_x1+bbox_x2)/2, (bbox_y1+bbox_y2)/2]
                    #convert the point
                    px = (matrix[0][0]*p[0] + matrix[0][1]*p[1] + matrix[0][2]) / ((matrix[2][0]*p[0] + matrix[2][1]*p[1] + matrix[2][2]))
                    py = (matrix[1][0]*p[0] + matrix[1][1]*p[1] + matrix[1][2]) / ((matrix[2][0]*p[0] + matrix[2][1]*p[1] + matrix[2][2]))
                    
                    with open(txt_path, 'a') as f:
                        f.write(f'{frame_idx},{bbox_x1},{bbox_y1},{bbox_x2},{bbox_y2},{category},{u_overdot},{v_overdot},{s_overdot},{identity},{px},{py}')
                    
                    insertRecordDB(cur, tableName, [frame_idx, bbox_x1,bbox_y1,bbox_x2,bbox_y2,category,identity, px, py])

            print(f'{s} Done. ({t2-t1})')    
            # Stream image results(opencv)
            if view_img:
                drawPoints(savedMousePoints, im0)
                connectPoints(savedMousePoints, im0)
                cv2.imshow('0',im0) #default value is p, im0 #p stopped working
            if view_img or save_img:
                if cv2.waitKey(1)==ord('q'): #q to quit
                    raise StopIteration
            # Save video results
            if save_img:
                if dataset.mode == 'images':
                    # print('saving img!')
                    cv2.imwrite(save_path, im0)
                else:
                    # print('saving video!')
                    print("vid path is", vid_path)
                    print("save_path is", save_path)
                    if vid_path != save_path:  # new video
                        vid_path = save_path
                        if isinstance(vid_writer, cv2.VideoWriter):
                            vid_writer.release()  # release previous video writer

                        fps = vid_cap.get(cv2.CAP_PROP_FPS)
                        w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        vid_writer = cv2.VideoWriter(
                            save_path+".avi", cv2.VideoWriter_fourcc(*opt.fourcc), fps, (w, h))
                        vid_writer_RAW = cv2.VideoWriter(
                            save_path+"RAW.avi", cv2.VideoWriter_fourcc(*opt.fourcc), fps, (w, h))
                        print("video writer started")
                    vid_writer.write(im0)
                    vid_writer_RAW.write(imgRaw)
    if save_txt or save_img:
        print('Results saved to %s' % os.getcwd() + os.sep + out)
        if platform == 'darwin':  # MacOS
            os.system('open ' + save_path)

    print('Done. (%.3fs)' % (time.time() - t0))
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', type=str,
                        default='C:\\Users\\matt2\\Desktop\\classy-sort-yolov5-MINE\\white-sub\\exp10\\weights\\best.pt', help='model.pt path')
    # file/folder, 0 for webcama
    # file_location = "C:\Users\matt2\Desktop\working-camera\RAW-FOOTAGE\2021-12-07 16-07-34\camera-one-at-2021-12-07 16-07-34.avi"
    # file_location = file_location.replace('\\','/')q

    #parser.add_argument('--source', type=str, default='C:\\Users\\matt2\\Desktop\\Fish videos - final cuts\\1 yellow zebra fish\\1-front.avi', help='source')
    parser.add_argument('--source', type=str,
                        default="0", help='source')

    parser.add_argument('--output', type=str, default='inference/processed-videos/'+str(datetime.today().replace(microsecond=0)).replace(":","_").replace(" ","_"),
                        help='output folder')  # output folder

    print("STARTING SCRIPT AT:",str(datetime.today().replace(microsecond=0)).replace(":","_").replace(" ","_"))
    parser.add_argument('--img-size', type=int, default=640,
                        help='inference size (pixels)')
    parser.add_argument('--conf-thres', type=float,
                        default=0.2, help='object confidence threshold')
    parser.add_argument('--iou-thres', type=float,
                        default=0.4, help='IOU threshold for NMS')
    parser.add_argument('--fourcc', type=str, default='mp4v',
                        help='output video codec (verify ffmpeg support)')
    parser.add_argument('--device', default='',
                        help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true',
                        help='display results', default="True")
    parser.add_argument('--save-img', action='store_true',
                        default="True", help='save video file to output folder (disable for speed)')
    parser.add_argument('--save-txt', action='store_true',
                        help='save results to *.txt', default="True")
    # for number of classes trained with 
    parser.add_argument('--classes', nargs='+', type=int,
                        default=[i for i in range(2)], help='filter by class') #80 classes in COCO dataset
    parser.add_argument('--agnostic-nms', action='store_true',
                        help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true',
                        help='augmented inference')
    parser.add_argument('--perspective-transformation', default="True")

    #SORT params
    parser.add_argument('--sort-max-age', type=int, default=60,
                        help='keep track of object even if object is occluded or not detected in n frames')
    parser.add_argument('--sort-min-hits', type=int, default=2,
                        help='start tracking only after n number of objects detected')
    parser.add_argument('--sort-iou-thresh', type=float, default=0.2,
                        help='intersection-over-union threshold between two frames for association')
    
    args = parser.parse_args()
    args.img_size = check_img_size(args.img_size)
    print("arguments for this script are:".upper(), args)

    with torch.no_grad():
        detect(args)