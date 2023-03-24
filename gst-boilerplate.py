#! /usr/bin/python3

from ctypes import *
import sys

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtp', '1.0')
gi.require_version('GObject', '2.0')
from gi.repository import Gst, GObject, GLib, GstRtp


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


def probe_on_data(pad, info, u_data):
    gst_buffer = info.get_buffer()
    assert(gst_buffer), "Unable to get GstBuffer"
    
    #  Do the shit

    return Gst.PadProbeReturn.OK



if __name__ == "__main__":
    
    Gst.init(sys.argv[1:])
    loop = GLib.MainLoop()
    
    
    pipe_desc = f"""
        videotestsrc 
            ! videoconvert ! video/x-raw,width=480,height=640
            ! xvimagesink
        videotestsrc 
            ! videoconvert ! video/x-raw,width=640,height=480
            ! identity name=probe_me
            ! xvimagesink
        """

    # Parsing and setting stuff up
    pipeline = Gst.parse_launch(pipe_desc)

    # Listening to the bus for events and errors
    bus = pipeline.get_bus()    
    bus.add_signal_watch()
    bus.connect("message", on_bus_message, loop)

    # Probing a pad for custom applications
    element = pipeline.get_by_name("probe_me")
    pad = element.get_static_pad('src')
    pad.add_probe(Gst.PadProbeType.BUFFER, probe_on_data, None)


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
