#! /usr/bin/python3

import sys
import threading
import time

import gi
import numpy as np

gi.require_version("Gst", "1.0")
gi.require_version("GstRtp", "1.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import GLib, Gst, GstVideo


def threaded(func):
    """Decorator to run class methods on a different thread"""

    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args)
        thread.start()
        return thread

    return wrapper


class FPSCounter:
    """Simple class to measure call frequency"""

    def __init__(self):
        self.last_time = time.time()
        self.frame_count = 0

    def tick(self):
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_time

        if elapsed >= 1.0:
            print("FPS: %s" % self.frame_count)
            self.frame_count = 0
            self.last_time = time.time()


class GstLiveSource:
    def __init__(self):

        Gst.init(sys.argv[1:])

        # FIXME
        pipe_desc = f"""
            rtspsrc                                                                
                location=rtsp://localhost:8554/test
                latency=1                                                          
                drop-on-latency=1                                                  
            ! rtph264depay                                                         
            ! queue leaky=1 max-size-buffers=10 max-size-time=0 max-size-bytes=0
            ! avdec_h264                                                           
            ! videoconvert ! queue
            ! videorate    ! video/x-raw,framerate=30/1
            ! videoconvert ! video/x-raw,format=BGR
            ! appsink emit-signals=true name=my_appsink caps="video/x-raw,format=BGR"
            """

        # Frame data and ready-to-read flag
        self.frame_array = None  # can be Array or None
        self.frame_ready = False

        # Thread-stop event and very thread
        self.thread_stop = threading.Event()
        self.thread = self._start_pipeline(pipe_desc)

    def appsink_user_cb(self, frame):
        self.frame_array = frame
        self.frame_ready = True

    def read(self):
        if self.frame_ready:
            self.frame_ready = False
            return True, self.frame_array
        return False, []

    def release(self):
        self.thread_stop.set()
        self.thread.join()

    @threaded
    def _start_pipeline(self, pipe_desc):

        # Parsing and setting stuff up
        pipeline = Gst.parse_launch(pipe_desc)
        loop = GLib.MainLoop()
        context = loop.get_context()

        # Listening to the bus for events and errors
        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_bus_message, loop)

        # Using the appsink
        element = pipeline.get_by_name("my_appsink")
        element.connect("new-sample", self._appsink_cb, self.appsink_user_cb)

        # Start and run pipeline until stop event
        try:
            pipeline.set_state(Gst.State.PLAYING)
            while True:
                context.iteration(may_block=True)
                if self.thread_stop.is_set():
                    break
        except Exception as err:
            print(err)
        finally:
            loop.quit()
            pipeline.set_state(Gst.State.NULL)

    @staticmethod
    def _on_bus_message(bus: Gst.Bus, message: Gst.Message, loop: GLib.MainLoop):
        """Default GStreamer GstBus message handler"""
        mtype = message.type

        if mtype == Gst.MessageType.EOS:
            print("End of stream")
            loop.quit()

        elif mtype == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(err, debug)
            loop.quit()

        elif mtype == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            print(err, debug)

        return True

    @staticmethod
    def _appsink_cb(sink, u_data):
        """Get Numpy array from BGR buffers via appsink.

        This is simple for BGR but a hairkiller if YUY. Just set the caps to BGR
        and place a videoconvert to let gstreamer do the conversion.
        """
        # Lots of lines to parse GstBuffer img into numpy array
        sample = sink.emit("pull-sample")

        caps = sample.get_caps().get_structure(0)  # Gst.Structure
        rc, w = caps.get_int("width")
        rc, h = caps.get_int("height")
        fmt_str = caps.get_value("format")

        fmt_enum = GstVideo.VideoFormat.from_string(fmt_str)
        fmt_info = GstVideo.VideoFormat.get_info(fmt_enum)

        c = int(fmt_info.n_components)
        bits = fmt_info.bits
        dtype = np.uint8 if bits != 16 else np.int16
        # depth = fmt_info.depth  # bits per channel

        buffer = sample.get_buffer()
        (result, mapinfo) = buffer.map(Gst.MapFlags.READ)
        if not result:
            print("Could not map buffer!", flush=True)
            return Gst.FlowReturn.OK

        array = np.ndarray(
            shape=(h, w, c), buffer=buffer.extract_dup(0, mapinfo.size), dtype=dtype
        )

        # Non-gstreamer features go here
        appsink_user_cb = u_data
        appsink_user_cb(array)

        # Memory cleanup
        buffer.unmap(mapinfo)
        
        return Gst.FlowReturn.OK


if __name__ == "__main__":

    # This for drawing frames with opencv, if x11 crashes
    # fmt: off
    # import ctypes
    # ctypes.cdll.LoadLibrary("libX11.so.6").XInitThreads()
    # import cv2
    # cv2.startWindowThread()
    # fmt: on

    cap = GstLiveSource()
    fps = FPSCounter()

    count = 0

    try:
        while True:
            ret, frame = cap.read()
            if ret:
                print(time.time(), frame.shape, np.mean(frame))
                fps.tick()

                # cv2.imshow("f", cv2.pyrDown(cv2.pyrDown(frame)))
                # cv2.waitKey(5)

    except KeyboardInterrupt:
        cap.release()
