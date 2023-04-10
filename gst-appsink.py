#! /usr/bin/python3

from ctypes import *
import sys
import numpy as np
import cv2
import multiprocessing as mp


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


def on_identity_buffer (pad, info, u_data):
    """ Gstreamer Pad Probe. Attach after decoding to retrieve a frame through
    a queue passed as u_data.
    """
    # Retrieve pad capabilities - needed to sort img bytes later  
    caps = pad.get_current_caps()
    if not caps:
        print("Could not get caps", flush=True)
        return Gst.PadProbeReturn.OK

    # Retrieve image size from caps - needed to sort img bytes later        
    caps_struct = caps.get_structure(0)
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
        # retrieve the bytes from the buffer to the caps image size
        arr = np.ndarray(
            (height, width, 3),
            buffer=buf.extract_dup(0, mapinfo.size),
            dtype=np.uint8
        )
        print(arr.shape)
    except Exception as e:
        print(e, flush=True)

    finally:
        buf.unmap(mapinfo)

    return Gst.PadProbeReturn.OK



def on_appsink_signal(sink, u_data):
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
    depth = fmt_info.depth  # bits per channel

    buffer = sample.get_buffer()
    (result, mapinfo) = buffer.map(Gst.MapFlags.READ)
    if not result:
        print("Could not map buffer!", flush=True)
        return Gst.FlowReturn.OK    
        
    print("----------------")
    print("Using %s format" % fmt_info.name)
    print("Pixel bits: %d, Per-channel depth: %s" % (bits, depth))
    print("Image dimensions:", h, w, c)  
    print("Need to allocate %d incoming bytes" % mapinfo.size)
    print("        This is: %d = 480 * 640 * (depth[0] + depth[1] + depth[2] + depth[3]) / 8" %
                                (480 * 640 * (depth[0] + depth[1] + depth[2] + depth[3]) / 8 )
    )
    print("Theoretical buffer bytes : %d" % (h * w * np.sum(depth) / 8))  
    print()
    print("A single pixel needs %d bytes per channel" % int(mapinfo.size / 480 / 640 * 8 / c))
    print("Using dtype %s" % dtype) 

    # mapinfo.size [bytes]= 480 * 640 * (c * bits_per_channel) / 8
    # RGB: three channels, each channel needs one byte -> array has 3ch np.uint8

    array = np.ndarray(
        shape=(h, w, c),
        buffer=buffer.extract_dup(0, mapinfo.size),
        dtype=dtype
    )
    
    array = cv2.cvtColor(array, cv2.COLOR_RGB2BGR);
    print(array.shape)
    cv2.imwrite("echo.jpeg", array)

    return Gst.FlowReturn.OK




if __name__ == "__main__":
    
    Gst.init(sys.argv[1:])
    loop = GLib.MainLoop()
    
    
    pipe_desc = f"""
        videotestsrc 
            ! videoconvert ! video/x-raw,format=RGB,width=640,height=480
            ! identity name=my_identity
            ! appsink emit-signals=true name=my_appsink
        """

    # Parsing and setting stuff up
    pipeline = Gst.parse_launch(pipe_desc)

    # Listening to the bus for events and errors
    bus = pipeline.get_bus()    
    bus.add_signal_watch()
    bus.connect("message", on_bus_message, loop)

    # Probing a pad for custom applications
    element = pipeline.get_by_name("my_appsink")
    element.connect("new-sample", on_appsink_signal, None)

    # element = pipeline.get_by_name("my_identity")
    # pad = element.get_static_pad('src')
    # pad.add_probe(Gst.PadProbeType.BUFFER, on_identity_buffer, None)



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
