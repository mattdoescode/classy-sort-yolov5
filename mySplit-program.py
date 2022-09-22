import os
import random
import shutil


#start program at root directory

"""

Set up file structure as such:

root
    images
        train
    
    labels
        train
"""

if not os.path.exists('C:\\Users\\matt2\Desktop\\training-data-split\\images\\val'):
    os.makedirs('C:\\Users\\matt2\\Desktop\\training-data-split\\images\\val')

if not os.path.exists('C:\\Users\\matt2\Desktop\\training-data-split\\labels\\val'):
    os.makedirs('C:\\Users\\matt2\\Desktop\\training-data-split\\labels\\val')

src = "C:/Users/matt2/Desktop/training-data-split/"
dest = "C:/Users/matt2/Desktop/training-data-split/"

counter = 0
for file in os.listdir("C:/Users/matt2/Desktop/training-data-split/images/train"):
    print(file)
    if( 0.82 < random.uniform(0, 1) ):
        shutil.move(src+"/images/train/"+file,dest+"images/val/"+file)
        file = file[:-3] + "txt"
        shutil.move(src+"/labels/train/"+file,dest+"labels/val/"+file)
