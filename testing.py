import random
from itertools import count
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation


plt.style.use('fivethirtyeight')

x_vals = [4]
y_vals = [4]

index = count()

def animate(i):

    #data = pd.read_csv('data.csv')
    
    x = [0,0]
    y1 = [3,random.randrange(10,20)]
    y2 = [6,random.randrange(10,20)]

    # clears everything gets ready to plot next data point
    plt.cla()

    ax.axes.set_xlim3d(left=0, right=50) 
    ax.axes.set_ylim3d(bottom=0, top=50) 
    ax.axes.set_zlim3d(bottom=0, top=50) 
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')

    ax.scatter(2,3,40, s = 500)
    plt.plot(x, y1, 20, label='Channel 1')
    plt.plot(x, y2, 20, label='Channel 2')

    plt.legend(loc='upper left')
    plt.tight_layout()


fig = plt.figure(figsize=(10,10))
ax = fig.add_subplot(111, projection='3d')

ani = FuncAnimation(fig, animate, interval=1000)

#plt.tight_layout()
plt.show()