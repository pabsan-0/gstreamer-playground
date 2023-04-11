#! /usr/bin/python3

from ctypes import *
import sys
import numpy as np

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtp', '1.0')
from gi.repository import Gst, GLib


def on_bus_message(bus: Gst.Bus, message: Gst.Message, loop: GLib.MainLoop):
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


_pts = 0  # buffers presentation timestamp
_duration = 10**9 / 30  # frame duration

def on_need_data_cb (appsrc, length, u_data):
    global _pts
    global _duration


    array = np.random.randint(
        low=0, high=255,
        size=(480, 640, 3),
        dtype=np.uint8
    )
    
    buffer = Gst.Buffer.new_wrapped(array.tobytes())
    _pts += _duration
    buffer.pts = _pts
    buffer.duration = _duration

    appsrc.emit("push-buffer", buffer)

    return None


if __name__ == "__main__":
    
    Gst.init(sys.argv[1:])
    loop = GLib.MainLoop()
    
    pipe_desc = f"""
        appsrc  emit-signals=true 
                is-live=true
                name=my_appsrc
                caps=video/x-raw,format=RGB,width=640,height=480,framerate=30/1
                format=GST_FORMAT_TIME
                block=true
            ! queue max-size-buffers=4 
            ! videoconvert 
            ! fpsdisplaysink
        """

    # Parsing and setting stuff up
    pipeline = Gst.parse_launch(pipe_desc)

    # Listening to the bus for events and errors
    bus = pipeline.get_bus()    
    bus.add_signal_watch()
    bus.connect("message", on_bus_message, loop)

    # Using the appsrc
    element = pipeline.get_by_name("my_appsrc")
    element.connect("need-data", on_need_data_cb, None)


    # Start the pipeline
    pipeline.set_state(Gst.State.PLAYING)
    try:
        # Blocking run call 
        loop.run()
    except Exception as e:
        print(e)
        loop.quit()

    # Python has a garbage collector, but normally we'd clean up here
    pipeline.set_state(Gst.State.NULL)
    del pipeline
