Scripts & Data flow

1. Data collection -> record_Training_Data.py
<p>This script records training data in the form of 4 video feeds and image stills. 2 for the top and front view of the fish tank, and 2 in which a perspective transformation has been applied to fill the frame. Image stills are saved from each video feed of the untransformed video.</p>

2. Train Network -> yolov5/train.py
<p>To train the network we need to label training data and set aside testing data. Copy over instructions from other github</p>
<p>Talk about picking a network model - steps to train </p>
<p>Talk about selecting training data</p>

3. Run network w/ classy sort -> class_track.py
<p>Take trained weights file and run the network</p>
<p>Running two instances of the YOLO network using webcam footage. One per live video feed. This script does object detection, object classification, saves a raw video capture, saves a video capture with detection data, and saves all information to a local PostgreSQL database. I've achieved 97% accuracy for detection at 75 fps for 1 camera and 35 fps x 2 for 2 cameras. With a GTX 3080 10gb card.</p>
<p>This script can run with SORT (object tracking with an ID across a series of frames) or without SORT where it just detects objects present in a given frame.</p>
<p>Saved detections to postgresql database and .txt file, outputs raw video capture</p>

4. Display 3D locations + virtual background -> display-results.py
<p> Pulls information from the database and calculates a 3D location in real time, displays this location. </p>
<p> Can be run on saved runs from the database </p>
<p> Generates a virtual background and displays this</p>

<p> talk about $ funding problem </p>
<p> reflections problems </p>

## Additional files

Original stuff in the repo

# Classysort

ClassySORT is a simple real-time multi-object tracker (MOT) that works for any kind of object class (not just people).

This is a one-person free time project. I will try to respond to Issues, but can't make any promises about support. In the open source community, 'please' and 'thank you' go a long way.

**I am curious to find out what you're using `classy-sort-yolov5` for, so please tell me if you end up using this repository!**

by Jason Sohn

![demo-footage](assets/velon-2019-creds.gif)

## Introduction

ClassySORT is designed to be a state-of-the-art (SOTA) multi-object tracker (MOT) for use on your own projects. And bcause the You-only-look-once algorithm (YOLO) detector is pretrained on COCO dataset, ClassySORT can detect and count and track 80 different kinds of common objects 'out of the box'.

My development platform is Pop_OS! 20.04 (a fork of Ubuntu) and NVIDIA RTX2070S.

Modifying it is exactly the same process as training YOLO with your own dataset. [How do I do that?](https://github.com/ultralytics/yolov5/wiki/Train-Custom-Data)

**ClassySORT implements**

- [ultralytics/YOLOv5](https://github.com/ultralytics/yolov5/wiki) with no modifications
- [abewley/SORT](https://github.com/abewley/sort) with minor modifications

This repository uses a fixed version of YOLOv5 to ensure compatbility. Replacing the YOLOv5 code to the updated ultralytics/YOLOv5 code may result in breaking changes. If you are able to this without issues, please submit a pull request.

If you only need to track people, or have the resources to train a model from scratch with your own dataset, see 'More Complex MOTs' section below.

## Using ClassySORT

Clone this repository

```bash
git clone https://github.com/tensorturtle/classy-sort-yolov5.git
cd classy-sort-yolov5
```

### Install Requirements

Python 3.8 or later with all requirements.txt. To install run:

```bash
pip install -r requirements.txt
```

### Download YOLOv5 weights

```bash
./download_weights.sh
```

This script will save yolov5 weights to `yolov5/weights/` directory.

### Run Tracking

To run the tracker on your own video and view the tracked bounding boxes, run:

```bash
python classy_track.py --source /path/to/video.mp4 --view-img
```

To get a summary of arguments run:

```bash
python classy_track.py -h
```

The text results are saved to `/inference/output/` from the array above in the following format. That location in the script is also a good point to plug your own programs into.

The saved text file contains the following information:

```bash
[frame_index, x_left_top, y_left_top, x_right_bottom, y_right_bottom, object_category, u_dot, v_dot, s_dot, object_id]
```

where

- u_dot: time derivative of x_center in pixels
- v_dot: time derivative of y_center in pixels
- s_dot: time derivative of scale (area of bbox) in pixels

## Implementation Details

### Modifications to SORT

#### 1. Class-aware Tracking

The original implementation of SORT threw away YOLO's object class information (0: person, 1: bike, etc.).
I wanted to keep that information, so I added a `detclass` attribute to `KalmanBoxTracker` object in `sort.py`:

![modifications_to_sort_schematic](assets/sort-mod.png)

#### 2. Kalman Filter parameters

I found that for my own dataset in which bounding boxes change size fairly quickly, the default Q value (process covariance) was too low. I recommend you try experimenting with them.

## More Complex MOTs

If you only need to track people, or have the resources to train a model from scratch with your own dataset, then I recommend [bostom/Yolov5_DeepSort_PyTorch](https://github.com/mikel-brostrom/Yolov5_DeepSort_Pytorch).
DeepSORT adds a separately trained neural network on top of SORT, which increases accuracy for human detections but slightly decreases performance.
It also means that using your custom dataset involves training both YOLO and DeepSORT's 'deep association metric'

For a 'bag of tricks' optimized version of YOLOv5 + DeepSORT, see [GeekAlexis/FastMOT](https://github.com/GeekAlexis/FastMOT)

## License

ClassySORT is released under the GPL License version 3 to promote the open use of the tracker and future improvements.
This means that code from this repository cannot be used for closed source distributions,
and you must license any derived code as GPL3 as well.
