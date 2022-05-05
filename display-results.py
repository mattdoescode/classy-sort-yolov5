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
    tempDetected = []
    #how many frames of no detection before we delete
    decayRate = None

    for tableName in tableNames:
        try:
            # get tracking results from newest frame
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

        
        ######## MAKE FIRST INITIAL PAIRINGS

        if tempDetected and len(tempDetected) == len(values):
            #table view
            currentTableView = getTableView(tableName)
    
        #if tempItems is empty and we have results from DB
        if not tempDetected and len(values) > 0:
            #for each value from DB create new object and populate it based on camera perspective 
            for dbRecord in values:
                currentTemp = createTrackedObjectFromDBData(tableName, values)
                tempDetected.append(currentTemp)
        
        #if we have tempitems and results from DB 
        #we need to merge db results with what we have from the other table
        elif tempDetected and len(values) > 0:
            pass
            #match temp detected & current DB results
            #here we have 1 or more record from both cameras
            #similarPosMaxDiff
            if not activelyTracked:
                pass
            else: 
                #merge with regards to atively tracked records
                pass



            #use nearest neighbor algo 


            #combining works (without references to past frames) by comparing the shared deminsion.
            #we find detected objects that have the closest X deminsion location per camera.
            #once objects from each camera are paired on the x we get the item # from the sort algo
            #the item will then be paired by sort algo numbers
            # if currectlyTracked:
            #     #compare x locations
            #     #case where result sets are different sizes
                
            #     #compareCompletedTemps with currectlyTracked
            #     # update CurrentlyTracked
            # else:
            #     # output From combineTemps = currentlyTracked


            # #if we currently have tracked objects we compare existing objects w/ their sort algo items. 
            #     #if we have matching numbers we simply update the objects position
            #     #if we have missmatch by id's
            #         #if 1 missmatch id -> update the missing ID w/ new ID
            #         #if multiple missmatch ids -> compare on shared X and update with saved item values 
            # else:
            #     print("need to combine and check currectly displayed")

        #if tempitems and no results from DB
        elif not tempDetected and len(values) <= 0:
            print("missing information from 1 camera")
        #if no tempitems and no results from DB
        elif tempDetected and len(values) <= 0:
            print("missing information from 1 camera")
        
        else:
            print("something has gone horribly wrong.")
            print("you should never be here")
            sys.exit()

    #find match in global detected objects 
    #if no match can be found make new record

    #cases
    #0 temp records
    #1 incomplete temp record
    #n completed records with m incompleted records
    print(tableName, values)
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