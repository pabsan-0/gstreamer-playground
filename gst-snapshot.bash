#! /bin/echo Please-source-if-possible

RTSP_SERVER_PORT=`jq .rtsp_server_port ../settings.json`

SNAPSHOT_PATH="$1"
SNAPSHOT_NAME="$2"
SNAPSHOT_SRC="$3"


mkdir -p "$SNAPSHOT_PATH"

# Use 127.0.0.1 instead of localhost or else 
# https://github.com/aler9/rtsp-simple-server/issues/737#issuecomment-1051225842

gst-launch-1.0                                                                \
    rtspsrc location="rtsp://127.0.0.1:$RTSP_SERVER_PORT/cam$SNAPSHOT_SRC"    \
    ! rtpjpegdepay                                                            \
    ! jpegparse                                                               \
    ! jpegdec                                                                 \
    ! videoconvert                                                            \
    ! pngenc snapshot=true ! filesink location="$SNAPSHOT_PATH$SNAPSHOT_NAME" ;

