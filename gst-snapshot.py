import cv2
from sys import argv
import json
import os
import numpy as np

with open("../settings.json") as file:
    settings = json.load(file)    
    RTSP_SERVER_PORT = settings['rtsp_server_port']


if __name__ == "__main__":

    assert(len(argv) == 4)
    __, dest_path_absolute, dest_fname, cam = argv

    os.makedirs(dest_path_absolute, exist_ok=True)

    gst_pipeline_desc = f'''
        gst-launch-1.0                                                                 \
            rtspsrc location="rtsp://127.0.0.1:{RTSP_SERVER_PORT}/cam{cam}"                \
            ! rtpjpegdepay                                                             \
            ! queue leaky=1 max-size-buffers=100 max-size-time=0 max-size-bytes=0      \
            ! jpegparse                                            \
            ! jpegdec                                                               \
            ! videoconvert                                                             \
            ! decodebin3 ! videoconvert                                                \
            ! appsink               
    '''

    cap = cv2.VideoCapture(gst_pipeline_desc, cv2.CAP_GSTREAMER)
    ret = None 
    while not ret:
        ret, frame = cap.read()
        cv2.imwrite(os.path.join(dest_path_absolute, dest_fname), frame)
