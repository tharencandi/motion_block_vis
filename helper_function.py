import math
import cv2
import numpy as np
import sys
import os
from numpy.core.numeric import Infinity
from IPython.display import clear_output

"""CONFIGURABLE PARAMATERS"""
#(k=4, ssd threshold=[150,200]
VIDEO_FILE = 'monkey2.mp4'
DOWNGRADE = False
T_MAX = 200
T_MIN = 100
K_VALUE = 3
SEARCH_RANGE = 2
DEBUG = False

""" END OF CONFIGURABLE PARAMATERS"""
block_size = (2*K_VALUE) + 1 

#allow command line argument choice of video file
if (len(sys.argv) > 1):
    VIDEO_FILE = sys.argv[1]

video_name = VIDEO_FILE.rpartition('.')[0]
output_folder = video_name + "_processed_frames"

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

if not os.path.exists("videos"):
    os.makedirs("videos")

"""
    OPTIONAL PAD FUNCTION TO GET COMPLETE COVERAGE OF BLOCKS ACROSS IMAGE
        - used to make width and height divisible by the block width and height
"""
def Pad_frame(frame, x_pad, y_pad):
    if (x_pad == 0 and y_pad == 0):
        return frame
    image = cv2.copyMakeBorder(frame, 0, int(y_pad), 0, int(x_pad), cv2.BORDER_CONSTANT)
    return image

"""
    calculates ssd for source block given (x, y) and target block given (x_prime, y_prime)
"""
def Block_ssd(frame, next_frame, x, y, x_prime, y_prime):
    #print("({},{}), ({},{})".format(x,y,x_prime, y_prime))
    value = 0
    for block_y in range(-K_VALUE, K_VALUE):
        for block_x in range(-K_VALUE, K_VALUE):
            for col_val in range(3):
                #print("\t",x_prime + block_x,y_prime + block_y)
                frame_val = frame[y+ block_y][x + block_x][col_val]
                next_frame_val = next_frame[y_prime + block_y][x_prime + block_x][col_val]
                value += math.pow((int(frame_val) - int(next_frame_val)), 2)
    
    res = math.sqrt(value)
    return res
    

# get frames of video
original_video = cv2.VideoCapture(VIDEO_FILE)
frame_height = int(original_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
frame_width = int(original_video.get(cv2.CAP_PROP_FRAME_WIDTH))
fps = original_video.get(cv2.CAP_PROP_FPS)

#padding calucation
blocks = ( frame_height * frame_width ) / ( math.pow(block_size,2) )
modulo_width = (frame_width % block_size)
modulo_height = (frame_height % block_size)
width_pad = 0
height_pad = 0

width_pad = block_size - modulo_width
height_pad = block_size - modulo_height

print("wxh = {}x{}\nblock_size = {}\n blocks = {}".format(frame_width, frame_height, block_size,blocks))

"""PROCESSING ALL FRAMES WITH ALGORITHM"""
ctr = 0
prev_frame = None
while True:
    ret, frame = original_video.read()
    
    if not ret:
        break
    if DOWNGRADE:
        frame = cv2.resize(frame, (213*2, 120*2),fx=0,fy=0, interpolation = cv2.INTER_CUBIC)
        
    if (ctr == 0):
        print("frame size: {} ".format(frame.shape))
        prev_frame = frame
        ctr += 1 
        continue

    
    #padded_frame = Pad_frame(frame, width_pad, height_pad)
    padded_frame = frame.copy()
    
    output_frame = prev_frame.copy()
    
    height = padded_frame.shape[0]
    width = padded_frame.shape[1]

    #loop through all blocks in the current frame 
    # (x_pos, y_pos) is block center position. 
    for i in range(0,int(height/block_size)-1):
        for j in range(0,int(width/block_size)-1):

            y_pos = int(i*block_size + K_VALUE)
            x_pos = int(j*block_size + K_VALUE)
            
            if DEBUG:
                output_frame = cv2.rectangle(output_frame, (x_pos-K_VALUE, y_pos-K_VALUE), (x_pos + K_VALUE,y_pos + K_VALUE), color=(0, 0, 255), thickness=1)
                    
            min_x = Infinity
            min_y = Infinity
            min_ssd = Infinity
          
            #loop through limited search space of blocks in the next frame   
            for i_prime in range(max(0, i - SEARCH_RANGE), min(i + SEARCH_RANGE +1, (int(height/block_size)-1))):
                for j_prime in range(max(0, j - SEARCH_RANGE),min(j + SEARCH_RANGE +1, (int(width/block_size)-1))):

                    y_prime_pos = int(i_prime*block_size + K_VALUE)
                    x_prime_pos = int(j_prime*block_size + K_VALUE)
                               
                    #calculate the SSD 
                    ssd = Block_ssd(prev_frame, padded_frame, x_pos, y_pos, x_prime_pos, y_prime_pos)

                    #update min SSD and associated block coordinates
                    if ssd < min_ssd:
                        min_ssd = ssd
                        min_x = x_prime_pos
                        min_y = y_prime_pos
            
            #print arrow to block in next frame with min SSD
            if min_ssd >= T_MIN and min_ssd <= T_MAX and (min_x != x_pos and min_y != y_pos) :
                output_frame = cv2.line(output_frame, (x_pos,y_pos), (min_x, min_y), (0, 255, 0), 1)
                output_frame = cv2.circle(output_frame, (min_x, min_y),radius=0, color=(0, 255, 0), thickness=2)
    
    print(str(ctr)+"/300")
    
    if DOWNGRADE:
        output_frame = cv2.resize(output_frame, (frame_width, frame_height),fx=0,fy=0, interpolation = cv2.INTER_CUBIC)

    cv2.imwrite('{}/frame{}.tif'.format(output_folder, ctr-1), output_frame) 
    prev_frame = padded_frame

    if (ctr > 300):
        break
    ctr += 1

original_video.release()

"""OUTPUTTING PROCESSED FRAMES TO A VIDEO FILE"""
count = 0
out = cv2.VideoWriter('videos/{}_k{}_min{}_max{}_downgrade_{}.mov'.format(video_name, K_VALUE, T_MIN, T_MAX, DOWNGRADE), cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), fps, (int(frame_width), int(frame_height)))
while(1):
    img = cv2.imread('{}/frame{}.tif'.format(output_folder, count))
    if img is None:
        print('No more frames to be loaded')
        break
    clear_output(wait=True)
    out.write(img)
    count += 1
    
out.release()
cv2.destroyAllWindows()
