#! /bin/echo Please-source-if-possible

RTSP_SERVER_PORT=`jq .rtsp_server_port ../settings.json`


# Move into dir where executable and YAML are
cd ../bin/rtsp-server || cd bin/rtsp-server || cd rtsp-server || echo "Could not find rtsp server path"
./rtsp-simple-server & 
sleep 1;

gst-launch-1.0                                    \
      v4l2src device="/dev/video0"                \
    ! "video/x-raw,width=640,height=480"          \
    ! videoconvert                                \
    ! queue                                       \
    ! tee name=teee                               \
    teee.                                         \
    ! videobalance hue=-0.5                       \
    ! videoconvert ! video/x-raw,format=I420 ! jpegenc ! rtspclientsink payloader=pay0 location=rtsp://localhost:"$RTSP_SERVER_PORT"/cam0 protocols=udp latency=0 sync=false async=false rtpjpegpay name=pay0 \
    teee.                                         \
    ! videobalance hue=+0.0                       \
    ! videoconvert ! video/x-raw,format=I420 ! jpegenc ! rtspclientsink payloader=pay1 location=rtsp://localhost:"$RTSP_SERVER_PORT"/cam1 protocols=udp latency=0 sync=false async=false rtpjpegpay name=pay1 \
    teee.                                         \
    ! videobalance hue=+0.5                       \
    ! videoconvert ! video/x-raw,format=I420 ! jpegenc ! rtspclientsink payloader=pay2 location=rtsp://localhost:"$RTSP_SERVER_PORT"/cam2 protocols=udp latency=0 sync=false async=false rtpjpegpay name=pay2 \
    teee.                                         \
    ! videobalance hue=+1.0                       \
    ! videoconvert ! video/x-raw,format=I420 ! jpegenc ! rtspclientsink payloader=pay3 location=rtsp://localhost:"$RTSP_SERVER_PORT"/cam3 protocols=udp latency=0 sync=false async=false rtpjpegpay name=pay3 \
    
