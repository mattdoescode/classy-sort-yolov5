"""
1. This script grabs data from the postgreSQL DB. 
2. It calculates the 3D location of each fish while flitering out poor detection data (if any)
Each camera only tracks a fish based on a calculated 2D location. Initial pairings are based 
on this. Subsequent pairings (tracking) is done via the ID's given from YOLO output. 
3. Displays each detected fish on a 3D chart
4. drives virtual reality screen 
"""

#camera 0 - front facing camera - captures x,y - globally -> x,z
#camera 1 - top facing camera - captures x,y - globally -> x,y

import argparse
import psycopg2
import sys
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

#db info
from config import config

class detectedObject():
    def __init__(self):
        self.TopX1 = None
        self.TopY1 = None
        self.TopX2 = None
        self.TopY2 = None
        self.FrontX1 = None
        self.FrontY1 = None
        self.FrontX2 = None
        self.FrontY2 = None
        self.TopIDNum = None
        self.FrontIDNum = None
        self.TopFrame = None
        self.FrontFrame = None
        self.Completed = False

def getTableView(tableName):
    if "top" in tableName or "TOP" in tableName or "Top" in tableName:
        return "top"
    elif "front" in tableName or "FRONT" in tableName or "Front" in tableName:
        return "front"
    else:
        print("error detecting camera view")
        print("table name w/ error is: ", tableName)
        sys.exit("check DB table name")

#create temp object + add properties based on camera perspective
def createTrackedObjectFromDBData(tableName, dbRecord):
    currentTemp = detectedObject()
    if "top" in tableName or "TOP" in tableName or "Top" in tableName:
        currentTemp.TopX1 = dbRecord[2]
        currentTemp.TopY1 = dbRecord[3]
        currentTemp.TopX2 = dbRecord[4]
        currentTemp.TopY2 = dbRecord[5]
        currentTemp.TopFrame = dbRecord[1]
        currentTemp.TopIDNum = dbRecord[7]
    elif "front" in tableName or "FRONT" in tableName or "Front" in tableName:
        currentTemp.FrontX1 = dbRecord[2]
        currentTemp.FrontY1 = dbRecord[3]
        currentTemp.FrontX2 = dbRecord[4]
        currentTemp.FrontY2 = dbRecord[5]
        currentTemp.FrontFrame = dbRecord[1]
        currentTemp.FrontIDNum = dbRecord[7]
    else:
        print("ERROR - DB TABLE NAME REQUIRED TO HAVE 'FRONT' or 'TOP' in name")
        sys.exit()
    return currentTemp

def animate(i, para):
    #each detection saved as on object
    tempDetected = []
    
    #get most recent detection data from each camera perspective
    for tableName in tableNames:
        try:
            query = """
                SELECT * FROM "{}"
                WHERE frame = (SELECT MAX(frame) FROM "{}")
            """.format(tableName, tableName)
            cur.execute(query)
            values = cur.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

        # Matching results from the 2 camera feeds is complicated
        # lots of cases to consider (missing detections, fish 
        # all close in apx location, etc) 
        # once pairing is made we can track objects from their
        # id output from YOLO + Sort. -> this makes things really easy

        #each DB record is 
        #recordID, frame#, x1, y1, x2, y2, detected object, sort item ID

        #if both cameras have == number of detections
        if tempDetected and len(tempDetected) == len(values):
            #make temp records for second camera
            #find pairings
            #if valid pairings turn into final detections
            #compare new detections with existing 
            #draw updates
            pass
    
        #when processing first camera
        #turn detections into temp objects
        elif not tempDetected and len(values) > 0:
            for dbRecord in values:
                currentTemp = createTrackedObjectFromDBData(tableName, dbRecord)
                tempDetected.append(currentTemp)
        
        #when len of both detections != 
        elif not tempDetected and len(values) == 0:
            #this will result with an incomplete 3D record. 
            pass

    #COMPARE temp records to existing records
    ##### DO SOMETHING HERE

    # PLOT FISH
    #ax.scatter(x pos, y pos, z pos, s = size of plot point, label for legend)

    #invert axis
    # ax.invert_zaxis()
    # ax.invert_yaxis()
    # ax.invert_zaxis()
    plt.cla()
    ax.axes.set_xlim3d(left=0, right=1000) 
    ax.axes.set_ylim3d(bottom=0, top=1000) 
    ax.axes.set_zlim3d(bottom=0, top=1000)
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')
    plt.legend(loc='upper left')
    plt.tight_layout()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Display location of fish + drive 'vr' display")

    #single object and single camera
    parser.add_argument('--single_object_track', type=bool, default=True, help="Tracking 1 object")
    parser.add_argument('--single_camera_track', type=bool, default=False, help="Tracking from 1 camera")

    parser.add_argument('--video_size', type=list, default=[640,480], help="Video frame dimensions")
    parser.add_argument('--save_results', default=True, help="save results to a .txt file or not")
    parser.add_argument('--fps', default=30, help="fps of camera(s)")

    args = parser.parse_args()

    print("starting with args:")
    print("\t",args)

    # set variables from arguments
    single_object_track, single_camera_track, video_size, save_results, fps = \
        args.single_object_track, args.single_camera_track, args.video_size, args.save_results, args.fps

    # Get table names
    tableNames = []
    conn = None
    try:
        params = config()
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        conn.autocommit = True
        cur = conn.cursor()
        #tracking from 1 camera or two
        if single_camera_track:
            print("getting most recent DB save")
            query = \
                """
                SELECT table_name FROM information_schema.tables
                            WHERE table_schema='public' AND table_name like '%front' or table_name like '%top'
                            ORDER BY table_name DESC LIMIT 1
                """
            print("tracking from 1 camera")
        else:
            print("getting 2 tables from DB")
            query = \
            """
                (SELECT table_name FROM information_schema.tables
                            WHERE table_schema='public' AND table_name like '%front'
                            ORDER BY table_name DESC LIMIT 1) 
                            UNION
                (SELECT table_name FROM information_schema.tables
                            WHERE table_schema='public' AND table_name like '%top'
                            ORDER BY table_name DESC LIMIT 1)
            """
        cur.execute(query)
       
        name = cur.fetchall()
        if(cur.rowcount == 0):
            print("ERROR - NO TABLE FOUND")
            sys.exit()

    except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            sys.exit()

    for item in enumerate(name):
        tableNames.append(item[1][0])

    print("table name(s) are", tableNames)

    # setup init graph 
    fig = plt.figure(figsize=(10,10))
    ax = fig.add_subplot(111, projection='3d')
    ax.view_init(azim = -104, elev = 28)

    #starts main loop of the program -> animate function does it all 
    # ani = FuncAnimation(fig, animate, interval=1000)
    activelyTracked = []
    ani = FuncAnimation(fig, animate, fargs=(tableNames,),interval=100)

    #plt.tight_layout()
    plt.show()
    
    #run_program(args)