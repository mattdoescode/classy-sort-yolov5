"""
1. This script grabs data from the postgreSQL DB. 
2. It calculates the 3D location of each fish while flitering out poor detection data (if any)
Each camera only tracks a fish based on a calculated 2D location. Initial pairings are based 
on this. Subsequent pairings (tracking) is done via the ID's given from YOLO output. 
3. Displays each detected fish on a 3D chart
4. drives virtual reality screen 
"""

"""
    32 px = 1 inch
"""

errorAcceptance = 1000
activelyTracked = []
sortAlgoMaxFrameAge = 60

#camera 0 - front facing camera - captures x,y - globally -> x,z
#camera 1 - top facing camera - captures x,y - globally -> x,y

import time

import argparse
import psycopg2
import sys
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from mpl_toolkits.mplot3d import Axes3D


#turn off warnings from myplotlib
import logging
logging.getLogger().setLevel(logging.CRITICAL)

#db info
from config import config

class detectedObject():
    def __init__(self):
        self.uniqueID = None
        self.perspective = None
        self.X1 = None
        self.Y1 = None
        self.X2 = None
        self.Y2 = None
        self.frame = None
        self.sortID = None
        self.correctedX = None
        self.correctedY = None

class finalObject():
    def __init__(self):
        self.uniqueID = None
        self.sideID = None
        self.frontID = None
        self.frontFrame = None
        self.sideFrame = None
        self.X1 = None
        self.X2 = None
        self.Y1 = None
        self.Y2 = None
        self.Z1 = None
        self.Z2 = None
        self.sideSortID = None
        self.frontSortID = None
        # self.correctedX = None
        self.correctedY = None
        self.correctedZ = None
        self.correctedAverageX = None
        self.age = 0

#take 2 matched perspectives for a fish 2 detectedObject
#return finalobject object
def mergeCameraDetections(view1,view2):
    mergedObj = finalObject()
    views = [view1,view2]
    x1 = x2 = 0
    for view in views:
        if view.perspective == 'side':
            mergedObj.Y1 = view.Y1
            mergedObj.Y2 = view.Y2
            mergedObj.sideFrame = view.frame
            mergedObj.sideID = view.uniqueID
            mergedObj.sideSortID = view.sortID
            mergedObj.correctedY = view.correctedY
        elif view.perspective == 'front':
            mergedObj.Z1 = view.Y1
            mergedObj.Z2 = view.Y2
            mergedObj.frontFrame = view.frame
            mergedObj.frontID = view.uniqueID
            mergedObj.frontSortID = view.sortID
            #caputed Y is global Z
            mergedObj.correctedZ = view.correctedY

    mergedObj.correctedAverageX = (view1.correctedX + view2.correctedX)/2

    print(mergedObj.correctedY, mergedObj.correctedZ, mergedObj.correctedAverageX)

        # x1 = x1 + view.X1
        # x2 = x2 + view.X2

    # mergedObj.X1 = x1/2
    # mergedObj.X2 = x2/2

    mergedObj.uniqueID = "Side: " + str(mergedObj.sideSortID) + " Front: ", str(mergedObj.frontSortID)

    # mergedObj.uniqueID = str(views[0].sortID) + " " + str(views[1].sortID)

    return mergedObj

#create temp object + add properties based on camera perspective (3d)
def createTrackedObjectFromDBData(tableName, dbRecord):
     #each DB record is 
        #recordID, frame#, x1, y1, x2, y2, detected object, sort item ID
    currentTemp = detectedObject()
    if "side" in tableName or "SIDE" in tableName or "Side" in tableName:
        currentTemp.uniqueID = str(dbRecord[0]) +"-side"
        currentTemp.perspective = 'side'
    elif "front" in tableName or "FRONT" in tableName or "Front" in tableName:
        currentTemp.uniqueID = str(dbRecord[0]) +"-front"
        currentTemp.perspective = 'front'
    else:
        print("ERROR - DB TABLE NAME REQUIRED TO HAVE 'FRONT' or 'TOP' in name")
        sys.exit()
    currentTemp.frame = dbRecord[1]
    currentTemp.X1 = dbRecord[2]
    currentTemp.Y1 = dbRecord[3]
    currentTemp.X2 = dbRecord[4]
    currentTemp.Y2 = dbRecord[5]
    currentTemp.sortID = dbRecord[7]
    currentTemp.correctedX = dbRecord[8]
    currentTemp.correctedY = dbRecord[9] 
    return currentTemp

def animate(i, para):
    screen.fill((255,255,255))
    pygame.display.flip()
    #each detection saved as on object
    tempDetected = []
    #make temp records for second camera
    secondTempDetected = [] 
    #potential parings
    allPossiblePairs = []
    #do we have something?
    validDetections = False
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

        #print DB results
        # for result in values:
        #     print(result)

        #if both cameras have == number of detections
        if tempDetected and len(tempDetected) == len(values):
            for dbRecord in values:
                secondTempDetected.append(createTrackedObjectFromDBData(tableName, dbRecord))
            
            #find pairings
            #match on the similar x axis
            for firstItem in sorted(tempDetected, key=lambda detectedObject: detectedObject.correctedX):
                for secondItem in sorted(secondTempDetected, key=lambda detectedObject: detectedObject.correctedX):
                    distance = abs(
                                    firstItem.correctedX - secondItem.correctedX
                                  )
                    if distance > errorAcceptance:
                        continue
                    # print('adding to all possible pairs')
                    allPossiblePairs.append([firstItem,
                                            secondItem,
                                            distance, 
                                            None])
            
            # print('all possible pairs are')
            # for pp in allPossiblePairs:
            #     print(pp[0].uniqueID,pp[1].uniqueID,pp[2])

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

                #do something with the last result
                # DOUBLE CHECK IF IS ACTAULLY THE SOULUTION
                if allPossiblePairs[-1][0].uniqueID != allPossiblePairs[-2][0].uniqueID:
                        allPossiblePairs[-1][3] = True
                        finalizedIDs.append(allPossiblePairs[-1][0].uniqueID)
                        finalizedIDs.append(allPossiblePairs[-1][1].uniqueID)   

            elif(len(allPossiblePairs) == 1):
                #if only 1 match it must be a true match
                allPossiblePairs[0][3] = True
                finalizedIDs.append(allPossiblePairs[0][0].uniqueID)
                finalizedIDs.append(allPossiblePairs[0][1].uniqueID)   
                # print("looking at the 1 case stuff")
            #all possible pairs = 0
            else:
                pass
            
            #detect if detections have any duplictes
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
            
            #if we have valid detections
            mergedRecordsToCompareToActivelyTracked = []  
            if validDetections:
                for possiblePair in allPossiblePairs:
                    if(possiblePair[3] == True):
                        #combine results
                        mergedRecordsToCompareToActivelyTracked.append(mergeCameraDetections(possiblePair[0],possiblePair[1]))
                mergedRecordsToCompareToActivelyTracked = sorted(mergedRecordsToCompareToActivelyTracked, key=lambda x: x.sideSortID)
                #compare new records with previously existing records
                #compare existing ID's to 
    
                """
                    ALL RECORDS AT THIS POINT ARE PAIRED BASED ON AN AVERAGED SHARED X

                    # TO DO AGE RECORDS AND DELETE WHEN TOO OLD
                """
                #compare new records to records from the last frame
                #pair records based on their SORTID 
                if 'activelyTracked' in vars():
                    list1Pointer = list2Pointer = 0
                    #temp records are sorted by sideSortID
                    #adding directly to perm storage should always result in a sorted record? (double check this)
                    while len(mergedRecordsToCompareToActivelyTracked) != list1Pointer and len(activelyTracked) != list2Pointer:
                        if(mergedRecordsToCompareToActivelyTracked[list1Pointer].sideSortID == activelyTracked[list2Pointer].sideSortID and mergedRecordsToCompareToActivelyTracked[list1Pointer].frontSortID == activelyTracked[list2Pointer].frontSortID):
                            activelyTracked[list2Pointer] = mergedRecordsToCompareToActivelyTracked[list1Pointer]
                            # print("match")
                            list2Pointer = list2Pointer + 1
                            mergedRecordsToCompareToActivelyTracked.pop(list1Pointer)
                            continue
                        #check which pointer has highest value
                        #increment the other
                        if mergedRecordsToCompareToActivelyTracked[list1Pointer].sideSortID < activelyTracked[list2Pointer].sideSortID:
                            list1Pointer = list1Pointer + 1
                        else:
                            list2Pointer = list2Pointer + 1
                    
                    list1Pointer = 0
                    partMatchPointerNum = 0
                    while len(mergedRecordsToCompareToActivelyTracked) >= list1Pointer:
                        view1Match = view2Match = False
                        for i in range(len(activelyTracked)):
                            if(mergedRecordsToCompareToActivelyTracked[list1Pointer].sideSortID == activelyTracked[i].sideSortID):
                                view1Match = True
                                partMatchPointerNum = i
                            elif(mergedRecordsToCompareToActivelyTracked[list1Pointer].frontSortID == activelyTracked[i].frontSortID):
                                view2Match = True
                                partMatchPointerNum = i
                        if(view1Match == False and view2Match == False):
                            activelyTracked.append(mergedRecordsToCompareToActivelyTracked.pop(list1Pointer))
                            continue
                        if(view1Match or view2Match):
                            activelyTracked[partMatchPointerNum] = mergedRecordsToCompareToActivelyTracked.pop(list1Pointer)
                        
                        list1Pointer = list1Pointer + 1
                    
                    listPointer = 0
                    while(len(activelyTracked) != listPointer):
                        if(activelyTracked.age >= sortAlgoMaxFrameAge):
                            activelyTracked[listPointer].pop()
                            print("deleted record without match for", sortAlgoMaxFrameAge, "frames")
                        else:
                            listPointer = listPointer + 1
                else:
                    activelyTracked = mergedRecordsToCompareToActivelyTracked
            else:
                print("something is wrong with detection data")

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
            #we could update with just a single record... but we won't
            pass
        #every other case do nothing
        else:
            pass

    #clear anything on the plot
    plt.cla()

    #PLOT FISH
    #ax.scatter(x pos, y pos, z pos, s = size of plot point, label for legend)
    if 'activelyTracked' in vars():
        # print(len(activelyTracked), "records")
        for permTracked in activelyTracked:
            #average this out (2 points per cord)
            ax.scatter(float(permTracked.correctedAverageX), 320 - float(permTracked.correctedY), 384 - float(permTracked.correctedZ), s = 400, label = permTracked.uniqueID)

    
    ax.axes.set_xlim3d(left=0, right=640) 
    ax.axes.set_ylim3d(bottom=0, top=320) 
    ax.axes.set_zlim3d(bottom=0, top=384)
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')
    plt.legend(loc='upper left')
    # plt.tight_layout()

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
                            WHERE table_schema='public' AND table_name like '%front' or table_name like '%side'
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
                            WHERE table_schema='public' AND table_name like '%side'
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
    fig = plt.figure(figsize=(8,8))
    
    ax = fig.add_subplot(111, projection='3d')
    ax.view_init(azim = -104, elev = 28)
    #scale tank 
                                                                #x, y, z
    ax.get_proj = lambda: np.dot(Axes3D.get_proj(ax), np.diag([1, .5, .6, .8]))

    import pygame
    pygame.init()
    screen = pygame.display.set_mode((2560,1440))

    #starts main loop of the program -> animate function does it all 
    # ani = FuncAnimation(fig, animate, interval=1000)
    ani = FuncAnimation(fig, animate, fargs=(tableNames,),interval=100)

    #plt.tight_layout()
    plt.show()
    
    #run_program(args)