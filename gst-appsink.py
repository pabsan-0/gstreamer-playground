#! /usr/bin/python3

from ctypes import *
import sys
import numpy as np
import cv2

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtp', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GLib, GstVideo


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


def probe_cb (pad, info, u_data):
    """ Get Numpy array from BGR buffers via pad probe. Enforcing caps is cheaty
    """
    # Retrieve pad capabilities - needed to sort img bytes later  
    caps = pad.get_current_caps()
    caps_struct = caps.get_structure(0)
    if not caps:
        print("Could not get caps", flush=True)
        return Gst.PadProbeReturn.OK

    # Assert incoming video format
    fmt_str = caps_struct.get_value('format')
    if fmt_str != "BGR":
        print("Uncompatible caps! Identity element NEEDS to receive BGR.", flush=True)
        return Gst.PadProbeReturn.OK

    # Retrieve image size from caps - needed to sort img bytes later        
    ret_h, height = caps_struct.get_int('height')
    ret_w, width  = caps_struct.get_int('width')
    if not (ret_h and ret_w):
        print("Could not get height and width of image", flush=True)
        return Gst.PadProbeReturn.OK

    # Go for the actual image once we have its size
    buf = info.get_buffer()
    (result, mapinfo) = buf.map(Gst.MapFlags.READ)
    if not result:
        print("Could not map buffer!", flush=True)
        return Gst.PadProbeReturn.OK

    try:
        array = np.ndarray(
            (height, width, 3), # CHEATY because I make up the 3-channel part
            buffer=buf.extract_dup(0, mapinfo.size),
            dtype=np.uint8
        )
        cv2.imwrite("probe.jpeg", array)

    except Exception as e:
        print(e, flush=True)

    finally:
        buf.unmap(mapinfo)

    return Gst.PadProbeReturn.OK



def appsink_cb (sink, u_data):
    """ Get Numpy array from BGR buffers via appsink.

    This is simple for BGR but a hairkiller if YUY. Just set the caps to BGR 
    and place a videoconvert to let gstreamer do the conversion.
    """
    sample = sink.emit("pull-sample")
    caps = sample.get_caps().get_structure(0)  # Gst.Structure
    rc, w = caps.get_int('width')
    rc, h = caps.get_int('height')
    fmt_str = caps.get_value('format')
    
    fmt_enum = GstVideo.VideoFormat.from_string(fmt_str)
    fmt_info = GstVideo.VideoFormat.get_info(fmt_enum)

    c = int(fmt_info.n_components)
    bits = fmt_info.bits
    dtype = np.uint8 if bits!=16 else np.int16
    # depth = fmt_info.depth  # bits per channel

    buffer = sample.get_buffer()
    (result, mapinfo) = buffer.map(Gst.MapFlags.READ)
    if not result:
        print("Could not map buffer!", flush=True)
        return Gst.FlowReturn.OK    
        
    array = np.ndarray(
        shape=(h, w, c),
        buffer=buffer.extract_dup(0, mapinfo.size),
        dtype=dtype
    )

    cv2.imwrite("appsink.jpeg", array)
    
    buffer.unmap(mapinfo)

    return Gst.FlowReturn.OK



if __name__ == "__main__":
    
    Gst.init(sys.argv[1:])
    loop = GLib.MainLoop()
    
    
    pipe_desc = f"""
        videotestsrc 
            ! videoconvert ! video/x-raw,format=I420,width=640,height=480
            ! videoconvert ! video/x-raw,format=BGR,width=640,height=480
            ! identity name=my_identity 
            ! appsink emit-signals=true name=my_appsink caps="video/x-raw,format=BGR"
        """

    # Parsing and setting stuff up
    pipeline = Gst.parse_launch(pipe_desc)

    # Listening to the bus for events and errors
    bus = pipeline.get_bus()    
    bus.add_signal_watch()
    bus.connect("message", on_bus_message, loop)

    # Using the appsink
    element = pipeline.get_by_name("my_appsink")
    element.connect("new-sample", appsink_cb, None)

    # Probing a pad
    element = pipeline.get_by_name("my_identity") 
    pad = element.get_static_pad('src')
    pad.add_probe(Gst.PadProbeType.BUFFER, probe_cb, None)


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
