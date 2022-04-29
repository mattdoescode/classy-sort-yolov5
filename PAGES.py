# with open('file.txt') as f:
#     lines = f.readlines()


# for line in lines:
#     # line = line.split('\t')
    
#     print(line, end="")

#     print(line[:-1], "(JPN ALT ART)")

    
#     # line = line.split(':')
#     # print(line[1][1:], end="")

# from numpy import empty


# tempDetected = None
# print(tempDetected is not empty)

# class detectedObject():
#     def __init__(self):
#         self.frontX = None
#         self.frontY = None
#         self.topX = None
#         self.topY = None
#         self.topID = None
#         self.frontID = None
#         self.lastFrameTop = None
#         self.lastFrameFront = None

# temp = detectedObject()

# temp.frontID = "bing"

# print(temp.frontID)

# import psycopg2 
# from config import config
# import sys

# tableNames = []
# single_camera_track = False
# params = config()
# print('Connecting to the PostgreSQL database...')
# conn = psycopg2.connect(**params)
# conn.autocommit = True
# cur = conn.cursor()
# #tracking from 1 camera or two
# if single_camera_track:
#     print("getting most recent DB save")
#     query = \
#         """
#         SELECT table_name FROM information_schema.tables
#                     WHERE table_schema='public' AND table_name like '%front' or table_name like '%top'
#                     ORDER BY table_name DESC LIMIT 1
#         """
#     print("tracking from 1 camera")
# else:
#     print("getting 2 tables from DB")
#     query = \
#     """
#         (SELECT table_name FROM information_schema.tables
#                     WHERE table_schema='public' AND table_name like '%front'
#                     ORDER BY table_name DESC LIMIT 1) 
#                     UNION
#         (SELECT table_name FROM information_schema.tables
#                     WHERE table_schema='public' AND table_name like '%top'
#                     ORDER BY table_name DESC LIMIT 1)
#     """
# cur.execute(query)

# name = cur.fetchall()
# if(cur.rowcount == 0):
#     print("ERROR - NO TABLE FOUND")
#     sys.exit()

# for item in enumerate(name):
#     tableNames.append(item[1][0])

# for tableName in tableNames:
#     try:
#         # get tracking results from newest frame
#         query = """
#             SELECT * FROM "{}"
#             WHERE frame = (SELECT MAX(frame) FROM "{}")
#         """.format(tableName, tableName)
#         cur.execute(query)
#         values = cur.fetchall()
#     except (Exception, psycopg2.DatabaseError) as error:
#         print(error)

#     print(len(values))
#     for dbRecord in values:
#         print("from", tableName, dbRecord)
#         #print(dbRecord['bbox_x1'])

# myString = "3983--5830-49-front"

# if "front" in myString:
#     print("hey")

# class detectedObject():
#     def __init__(self):
#         self.TopX1 = None
#         self.TopY1 = None
#         self.TopX2 = None
#         self.TopY2 = None
#         self.FrontX1 = None
#         self.FrontY1 = None
#         self.FrontX2 = None
#         self.FrontY2 = None
#         self.TopIDNum = None
#         self.FrontIDNum = None
#         self.TopFrame = None
#         self.FrontFrame = None

# myObjs = []

# temp = detectedObject()
# temp.TopX1 = 100
# myObjs.append(temp)

# temp = detectedObject()
# temp.TopX1 = 110
# myObjs.append(temp)
# temp = detectedObject()
# temp.TopX1 = 90
# myObjs.append(temp)

# temp = detectedObject()
# temp.TopX1 = 155
# myObjs.append(temp)

# temp = detectedObject()
# temp.TopX1 = 399
# myObjs.append(temp)

# myObjs = sorted(myObjs, key=lambda detectedObject: detectedObject.TopX1)

# for obj in myObjs:
#     print(obj.TopX1)

# for objects in myObjs:
#     print(objects.TopX1)


# Python program to illustrate 
# *kwargs for variable number of keyword arguments
 
# def myFun(**kwargs):
#     for key, value in kwargs.items():
#         print ("%s == %s" %(key, value))
 
# # Driver code
# myFun(first ='Geeks', mid ='for', last='Geeks')   


# Python program to illustrate 
# *kwargs for variable number of keyword arguments



# def myFun(*args,**kwargs):
#     print("args: ", args)
#     print("kwargs: ", kwargs)
 
 
# # Now we can use both *args ,**kwargs
# # to pass arguments to this function :
# myFun('geeks','for','geeks',first="Geeks",mid="for",last="Geeks")

# def makePairs(list1, list2):
#     if len(list1) >= len(list2):
        
#     else:


# from cv2 import sort

####################

# list1 = [90]
# list2 = [90]

list1 = [10,100,110,120]
list2 = [10,100,110,120]

class detectedObject():
    def __init__(self):
        self.uniqueID = "Whatever"
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

listID = []
listID.extend(range(len(list1),0,-1))

frontList = []
for item in list1:
    new = detectedObject()
    new.FrontIDNum = listID[-1]
    new.FrontX1 = item
    listID.pop()
    frontList.append(new)

listID2 = []
listID2.extend(range(0,80,1))

topList = []
for item in list2:
    new = detectedObject()
    new.TopIDNum = listID2[-1]
    new.TopX1 = item
    listID2.pop()
    topList.append(new)

# for item in list1Obj:
#     print(item.TopX1, item.TopIDNum)
# for item in list2Obj:
#     print(item.TopX1, item.TopIDNum)

# #####################################

finalizedIDs = []
multiMatch = False

def trackUniqueMatchedID(idToAdd):
    finalizedIDs.append(idToAdd)

def checkIfDuplicates():
    setOfElems = set()
    for elem in finalizedIDs:
        if elem in setOfElems:
            return True
        else:
            setOfElems.add(elem)         
    return False

#get all possible matches
errorAcceptance = 75

#collection of all possible matches with distances
allPossiblePairs = []

#ignore all cases 
if(len(topList) == len(frontList)):
    #does it matter how we match? More results vs fewer
    for topItem in sorted(topList, key=lambda detectedObject: detectedObject.TopX1):
        for frontItem in sorted(frontList, key=lambda detectedObject: detectedObject.FrontX1):
            if abs(topItem.TopX1-frontItem.FrontX1) > errorAcceptance:
                continue
            allPossiblePairs.append([topItem,frontItem,abs(topItem.TopX1-frontItem.FrontX1), None])
    # print("pairs are:")
    # for possiblePair in allPossiblePairs:
    #     print(possiblePair[0].TopX1,possiblePair[1].FrontX1, possiblePair[2], possiblePair[3])

    #find matches
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
            trackUniqueMatchedID(allPossiblePairs[i][0].TopIDNum)
            trackUniqueMatchedID(allPossiblePairs[i][1].FrontIDNum)   
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
            trackUniqueMatchedID(allPossiblePairs[bestDetection][0].TopIDNum)
            trackUniqueMatchedID(allPossiblePairs[bestDetection][1].FrontIDNum)
            
    print("updated pairs are:")
    for possiblePair in allPossiblePairs:
        print(possiblePair[0].TopX1,possiblePair[1].FrontX1, possiblePair[2], possiblePair[3])
    
    print("unique items are")
    for item in finalizedIDs:
        print(item)

else:
    print("non matching # of detections.... waiting....")


if(checkIfDuplicates()):
    print("try again later")
else:
    print("all good hoss")


# # # visitedPoints = []
# # # bestMatches = []
# # # for pair in allPossiblePairs:
# # #     print(pair)