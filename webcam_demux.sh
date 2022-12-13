#! /usr/bin/bash

# 
# This bash script will take your webcam's input and demux it to 4 streams with
# modified hue, in order to simulate 4 input cameras.
# 

## Set up dummy loopback devices
# sudo apt install v4l2loopback-dkms
sudo modprobe -r v4l2loopback
sudo modprobe v4l2loopback max_buffers=2 devices=4
v4l2-ctl --list-devices
# sudo modprobe -r v4l2loopback


## Sender
gst-launch-1.0                                    \
      v4l2src device="/dev/video0"                \
    ! "video/x-raw,width=640,height=480"          \
    ! videoconvert                                \
    ! tee name=teee                               \
    teee.                                         \
    ! videobalance hue=-0.5                       \
    ! v4l2sink device=/dev/video2 sync=0 async=0  \
    teee.                                         \
    ! videobalance hue=+0.0                       \
    ! v4l2sink device=/dev/video3 sync=0 async=0  \
    teee.                                         \
    ! videobalance hue=+0.5                       \
    ! v4l2sink device=/dev/video4 sync=0 async=0  \
    teee.                                         \
    ! videobalance hue=+1.0                       \
    ! v4l2sink device=/dev/video5 sync=0 async=0  ;



## Receiver pipelines - all
# gst-launch-1.0                                                              \
#     v4l2src device=/dev/video2 ! queue ! videoconvert ! queue ! xvimagesink \
#     v4l2src device=/dev/video3 ! queue ! videoconvert ! queue ! xvimagesink \
#     v4l2src device=/dev/video4 ! queue ! videoconvert ! queue ! xvimagesink \
#     v4l2src device=/dev/video5 ! queue ! videoconvert ! queue ! xvimagesink ;


##  Debugging
# Failed to allocate buffer: https://stackoverflow.com/questions/68029291/gstreamer-v4l2src-failed-to-allocate-buffer-when-run-on-a-jetson-nano