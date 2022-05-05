"""
1. This script grabs data from the postgreSQL DB. 
2. It calculates the 3D location of each fish while flitering out poor detection data (if any)
Each camera only tracks a fish based on a calculated 2D location. Initial pairings are based 
on this. Subsequent pairings (tracking) is done via the ID's given from YOLO output. 
3. Displays each detected fish on a 3D chart
4. drives virtual reality screen 
"""

errorAcceptance = 75

#camera 0 - front facing camera - captures x,y - globally -> x,z
#camera 1 - top facing camera - captures x,y - globally -> x,y

import argparse
import psycopg2
import sys
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

#turn off warnings from myplotlib
import logging
logging.getLogger().setLevel(logging.CRITICAL)

#db info
from config import config

class detectedObject():
    def __init__(self):
        self.uniqueID = None
        self.X1 = None
        self.Y1 = None
        self.X2 = None
        self.Y2 = None
        self.frame = None
        self.sortID = None

def getTableView(tableName):
    if "top" in tableName or "TOP" in tableName or "Top" in tableName:
        return "top"
    elif "front" in tableName or "FRONT" in tableName or "Front" in tableName:
        return "front"
    else:
        print("error detecting camera view")
        print("table name w/ error is: ", tableName)
        sys.exit("check DB table name")

#create temp object + add properties based on camera perspective (3d)
def createTrackedObjectFromDBData(tableName, dbRecord):
     #each DB record is 
        #recordID, frame#, x1, y1, x2, y2, detected object, sort item ID
    currentTemp = detectedObject()
    if "top" in tableName or "TOP" in tableName or "Top" in tableName:
        currentTemp.uniqueID = str(dbRecord[0]) +"-top"
    elif "front" in tableName or "FRONT" in tableName or "Front" in tableName:
        currentTemp.uniqueID = str(dbRecord[0]) +"-front"
    else:
        print("ERROR - DB TABLE NAME REQUIRED TO HAVE 'FRONT' or 'TOP' in name")
        sys.exit()
    currentTemp.frame = dbRecord[1]
    currentTemp.X1 = dbRecord[2]
    currentTemp.Y1 = dbRecord[3]
    currentTemp.X2 = dbRecord[4]
    currentTemp.Y2 = dbRecord[5]
    currentTemp.sortID = dbRecord[7]
    return currentTemp

def animate(i, para):
    #each detection saved as on object
    tempDetected = []
    #make temp records for second camera
    secondTempDetected = [] 
    #potential parings
    allPossiblePairs = []
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
            for dbRecord in values:
                secondTempDetected.append(createTrackedObjectFromDBData(tableName, dbRecord))

            #find pairings
            #match on the similar x axis
            for firstItem in sorted(tempDetected, key=lambda detectedObject: ((detectedObject.X1 + detectedObject.X2)/2)):
                for secondItem in sorted(secondTempDetected, key=lambda detectedObject: ((detectedObject.X1 + detectedObject.X2)/2)):
                    if abs((detectedObject.X1 + detectedObject.X2)/2) > errorAcceptance:
                        continue
                    allPossiblePairs.append([firstItem,
                                            secondItem,
                                            abs(
                                                (firstItem.X1 + firstItem.X2)/2 - (secondItem.X1 + secondItem.X2)/2
                                            ), 
                                            None])
            ###FIND THE BEST MATCHES
            #find matches
            finalizedIDs = []
            if (len(allPossiblePairs) > 1):
                counter = 0
                for i in range(len(allPossiblePairs[:-1])):
                    # allPossiblePairs = [x for x in allPossiblePairs if remove(x)]

                    # records might have been processed in the while loop
                    # if so skip
                    if counter > 0:
                        counter = counter - 1
                        continue
                    #if only 1 match per 1 detection it must be a true match
                    if(allPossiblePairs[i][0] != allPossiblePairs[i+1][0]):
                        allPossiblePairs[i][3] = True
                        finalizedIDs.append(allPossiblePairs[i][0].uniqueID)
                        finalizedIDs.append(allPossiblePairs[i][1].uniqueID)   
                    #if we have multiple detections
                    #determine what is best for the current detection
                    else:
                        counter = 1
                        bestDetection = i
                        #check if next index exists (IT ALWAYS WILL ON FIRST LOOP)
                        while len(allPossiblePairs) > i+counter:
                            #check if we need to process (WE ALWAYS WILL FIRST TIME)
                            if(allPossiblePairs[i][0] == allPossiblePairs[i+counter][0]):
                                #if bestDetection is worse update bestDetection
                                if(allPossiblePairs[bestDetection][2] > allPossiblePairs[i+counter][2]):
                                    bestDetection = i+counter
                                counter = counter + 1
                            else:
                                break
                        allPossiblePairs[bestDetection][3] = True
                        finalizedIDs.append(allPossiblePairs[bestDetection][0].uniqueID)
                        finalizedIDs.append(allPossiblePairs[bestDetection][1].uniqueID)
            elif(len(allPossiblePairs) == 1):
                #if only 1 match it must be a true match
                allPossiblePairs[0][3] = True
                finalizedIDs.append(allPossiblePairs[0][0].uniqueID)
                finalizedIDs.append(allPossiblePairs[0][1].uniqueID)   
            else:
                print('nothing to look at')
                pass
            
            #if valid pairings turn into final detections
            validPairs = []
            validDetections = False
            for possiblePair in allPossiblePairs:
                if(possiblePair[3] == True):
                        if len(finalizedIDs) == 0:
                            break
                        setOfElems = set()
                        for elem in finalizedIDs:
                            if elem in setOfElems:
                                break
                            else:
                                setOfElems.add(elem)   
                        #if all checks are passed we have valid detections      
                        validDetections = True
            
            if validDetections:            
                print("Valid detections: ", len(validPairs))
            else:
                print("no valid pairs")
    
            #compare new detections with existing 
            #draw updates
        
        #when processing first camera
        #turn detections into temp objects
        elif not tempDetected and len(values) > 0:
            for dbRecord in values:
                currentTemp = createTrackedObjectFromDBData(tableName, dbRecord)
                tempDetected.append(currentTemp)
        
        #first camera has 0 results
        elif not tempDetected and len(values) == 0:
            #this will result with an incomplete 3D record. 
            pass
        #every other case do nothing
        else:
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