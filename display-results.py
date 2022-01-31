import argparse
import psycopg2
import sys
import time

import random
from itertools import count
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation


from config import config

# this script gets the information from postgres about both cameras
# it them combines the data and makes a 3d map that follows the fish
# this script is also the VR screen for the fish

# """ Connect to the PostgreSQL database server """


#def run_program(opt, *args):

def animate(i, para):

    # print(i)
    # print(tableNames)
    # GET INFO FROM DB
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
            print("Error with the camera")
    
        print("global location is (x,y,z):", locationGlobal['x'], locationGlobal['y'], locationGlobal['z'])
 

    # NOW LETS DRAW THIS INFO
    plt.cla()

    ax.axes.set_xlim3d(left=0, right=600) 
    ax.axes.set_ylim3d(bottom=0, top=600) 
    ax.axes.set_zlim3d(bottom=0, top=600)

    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')

    #scatter(x pos, y pos, z pos, s = size of plot point, label for legend)
    ax.scatter(int(locationGlobal['x']),int(locationGlobal['y']),int(locationGlobal['z']), s = 500, label = "Fish 1")

    plt.legend(loc='upper left')
    plt.tight_layout()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Object location determination")
    parser.add_argument('--single_object_track', type=bool, default=True, help="Tracking 1 object")
    parser.add_argument('--single_camera_track', type=bool, default=False, help="Tracking from 2 cameras")
    parser.add_argument('--video_size', type=list, default=[640,480], help="Video frame dimensions")
    parser.add_argument('--save_results', default=True, help="save results to a .txt file or not")
    parser.add_argument('--fps', default=30, help="fps of camera(s)")

    args = parser.parse_args()

    print("RUNNING VISUALS with args:")
    print(args)

    # DO THE SETUP STUFF 
    single_object_track, single_camera_track, video_size, save_results, fps = \
        args.single_object_track, args.single_camera_track, args.video_size, args.save_results, args.fps

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

    # we could start tread(s) here? 

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
    # CONFIRM THIS INFO ^^^^ 1/26/21
    locationGlobal['x'] = locationGlobal['y'] = locationGlobal['z'] = 0

    # setup init graph 
    fig = plt.figure(figsize=(10,10))
    ax = fig.add_subplot(111, projection='3d')
    ax.view_init(azim = -104, elev = 28)

    #starts main loop of the program -> animate function does it all 
    # ani = FuncAnimation(fig, animate, interval=1000)
    ani = FuncAnimation(fig, animate, fargs=(tableNames,),interval=100)

    #plt.tight_layout()
    plt.show()
    
    #run_program(args)