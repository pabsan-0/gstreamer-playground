#! /usr/bin/python3

import sys
import threading

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


class GstLiveSource:

    def __init__(self):

        Gst.init(sys.argv[1:])

        pipe_desc = f"""
            v4l2src device=/dev/video0
                ! videoconvert ! video/x-raw,format=I420,width=640,height=480
                ! videoconvert ! video/x-raw,format=BGR,width=640,height=480
                ! appsink emit-signals=true name=my_appsink caps="video/x-raw,format=BGR"
            """

        self.last_frame = None  # can be Array or None
        self.thread = self._start_pipeline(pipe_desc)

    def appsink_user_cb(self, frame):
        self.last_frame = frame

    def read(self):
        return (self.last_frame is not None), self.last_frame

    def release(self):
        self.thread.raise_exception()
        self.thread.join()

    @threaded
    def _start_pipeline(self, pipe_desc):

        # Parsing and setting stuff up
        pipeline = Gst.parse_launch(pipe_desc)
        loop = GLib.MainLoop()

        # Listening to the bus for events and errors
        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_bus_message, loop)

        # Using the appsink
        element = pipeline.get_by_name("my_appsink")
        element.connect("new-sample", self._appsink_cb, self.appsink_user_cb)

        pipeline.set_state(Gst.State.PLAYING)
        try:
            # Blocking run call
            loop.run()
        except Exception as e:
            print(e)
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

        return Gst.FlowReturn.OK


if __name__ == "__main__":
    # Tweaks to avoid X11 errors if using cv2.imshow in multithread contexts
    # fmt: off
    import ctypes  
    ctypes.cdll.LoadLibrary("libX11.so").XInitThreads()
    import cv2
    cv2.startWindowThread()
    # fmt: on

    cap = GstLiveSource()

    while True:
        ret, frame = cap.read()
        if ret:
            # cv2.imwrite("frame.png", frame)
            cv2.imshow("frame", frame)
            cv2.waitKey(5)
