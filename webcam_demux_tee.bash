#! /usr/bin/bash

# Adding "" around variables will crash the pipeline

RTSP_SERVER_PORT=8554
CONVERTER_RAW="videoconvert ! video/x-raw,format=I420,fps=10/1"
ENCODER="videoconvert ! x264enc tune=zerolatency b-adapt=0 ! h264parse"
PAYLOADER="rtph264pay"

gst-launch-1.0                                    \
      v4l2src device="/dev/video0"                \
    ! "video/x-raw,width=640,height=480"          \
    ! videoconvert ! queue ! tee name=teee        \
    teee. ! videobalance hue=-0.5 ! $CONVERTER_RAW ! $ENCODER ! rtspclientsink payloader=pay0 location=rtsp://localhost:$RTSP_SERVER_PORT/cam0 protocols=udp latency=0 sync=false async=false  $PAYLOADER name=pay0 \
    teee. ! videobalance hue=+0.0 ! $CONVERTER_RAW ! $ENCODER ! rtspclientsink payloader=pay1 location=rtsp://localhost:$RTSP_SERVER_PORT/cam1 protocols=udp latency=0 sync=false async=false  $PAYLOADER name=pay1 \
    teee. ! videobalance hue=+0.5 ! $CONVERTER_RAW ! $ENCODER ! rtspclientsink payloader=pay2 location=rtsp://localhost:$RTSP_SERVER_PORT/cam2 protocols=udp latency=0 sync=false async=false  $PAYLOADER name=pay2 \
    teee. ! videobalance hue=+1.0 ! $CONVERTER_RAW ! $ENCODER ! rtspclientsink payloader=pay3 location=rtsp://localhost:$RTSP_SERVER_PORT/cam3 protocols=udp latency=0 sync=false async=false  $PAYLOADER name=pay3 ;
