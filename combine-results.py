import argparse
import psycopg2
import sys
import time

import matplotlib.pyplot as plt

from mpl_toolkits.mplot3d import Axes3D
import numpy as np


from config import config

# this script gets the information from postgres about both cameras
# it them combines the data and makes a 3d map that follows the fish
# this script is also the VR screen for the fish

# """ Connect to the PostgreSQL database server """

def run_program(opt, *args):
    single_object_track, single_camera_track, video_size, save_results = \
        opt.single_object_track, opt.single_camera_track, opt.video_size, opt.save_results

    conn = None
    try:
        params = config()
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        conn.autocommit = True
        cur = conn.cursor()
        if single_camera_track:
            query = \
                """
                SELECT table_name FROM information_schema.tables
                            WHERE table_schema='public' AND table_name like '%0'
                            ORDER BY table_name DESC LIMIT 1
                """
            print("tracking from 1 camera")
        else:
            query = \
            """
                (SELECT table_name FROM information_schema.tables
                            WHERE table_schema='public' AND table_name like '%0'
                            ORDER BY table_name DESC LIMIT 1) 
                            UNION
                (SELECT table_name FROM information_schema.tables
                            WHERE table_schema='public' AND table_name like '%1'
                            ORDER BY table_name DESC LIMIT 1)
            """
            print("getting 2 most recent captures")
        cur.execute(query)
        name = cur.fetchall()

    except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            sys.exit()

    # we could start treading here... 
    # for item in name:

    tableNames = []    
    for item in enumerate(name):
        tableNames.append(item[1][0])
        print(item[1][0])

    #make 2D array to hold each item
    #locations = [0*[2]] * len(tableNames) 
    # locations = [[]]
    locationGlobal = {'x':0, 'y':0, 'z':0}

    #when we have 2 cameras
    #camera 0 captures x,y - globally -> x,z
    #camera 1 captures x,y - globally -> x,y

    while True:
        locationGlobal['x'] = locationGlobal['y'] = locationGlobal['z'] = 0
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

            centerPointX = (values[0][2] + values[0][4]) / 2
            centerPointY = (values[0][3] + values[0][5]) / 2

            #convert from 2d camera perspective to 3d point
            if tableName[-1] == "0":
                locationGlobal['x'] = centerPointX
                locationGlobal['z'] = centerPointY
            elif tableName[-1] == "1":
                locationGlobal['x'] = (locationGlobal['x'] + centerPointX) / 2
                locationGlobal['y'] = centerPointY
            else:
                print("Not sure how'd you ever end up here")
            
        print("global location is (x,y,z):", locationGlobal['x'], locationGlobal['y'], locationGlobal['z'])

    # eventually thread getting the locations
    # eventually thread updating visual 3D location of the fish 
    # eventually thread updating VR screen for the fish
    # while True:

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Object location determination")
    parser.add_argument('--single-object-track', type=bool, default=True, help="Tracking 1 object")
    parser.add_argument('--single-camera-track', type=bool, default=False, help="Tracking from 2 cameras")
    parser.add_argument('--video-size', type=list, default=[640,480], help="Video frame dimensions")
    parser.add_argument('--save-results', default=True, help="save results to a .txt file or not")

    args = parser.parse_args()

    print("RUNNING VISUALS with args:")
    print(args)

    run_program(args)