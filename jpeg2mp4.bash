#! /usr/bin/bash

#
# This script takes a folder with many .jpg files and concatenates 
# them into a mp4 video using gstreamer
#
# Because the gstreamer plugin we will use loops only over 
# integer-sequenced filenames, we'll just create a folder of symlinks
# to the actual target images
#

# Define the glob expression for target images and create temp dir
IMG_GLOB="../images/*.jpg"
mkdir temp && cd temp


# Populate the folder of symlinks with integer names
a=1
for i in "$IMG_GLOB";
do
  new=$(printf "%09d.jpg" "$a")  # 09 pad to length of 9: 0000000000.jpg to 9999999999.jpg 
  ln -s "$i" "$new"
  let a=a+1
done


# The concatenating pipeline, once all symlinks have been created
gst-launch-1.0 -e multifilesrc location="%09d.jpg" index=1 caps="image/jpeg,framerate=(fraction)24/1,width=1280,height=1280" \
    ! jpegdec ! videoconvert  ! videoscale ! video/x-raw,width=1280,height=1280  !  queue ! x264enc ! queue ! mp4mux         \
    ! filesink location=out.mp4


# Clean up yourself! Take out.mp4 and remove temp/
