import gi

gi.require_version("Gst", "1.0")
import matplotlib.pyplot as plt
import numpy as np
from gi.repository import GObject, Gst

Gst.init(None)

PIPELINE = """
alsasrc ! audioconvert ! audioresample !
spectrum interval=100000000 bands=128 threshold=-80 post-messages=true !
fakesink
"""

pipeline = Gst.parse_launch(PIPELINE)
bus = pipeline.get_bus()
bus.add_signal_watch()

BUFFER_SIZE = 100  # how many frames to store
spectrogram_data = []


def on_message(bus, message):
    global spectrogram_data

    if (
        message.type == Gst.MessageType.ELEMENT
        and message.get_structure().get_name() == "spectrum"
    ):
        magnitudes = message.get_structure().get_value("magnitude")
        freqs = np.array(magnitudes)

        spectrogram_data.append(freqs)
        if len(spectrogram_data) > BUFFER_SIZE:
            spectrogram_data.pop(0)

        # Visualize as rolling spectrogram with time on vertical axis
        plt.clf()
        plt.imshow(
            np.flipud(np.array(spectrogram_data)),  # flip so time goes up
            aspect="auto",
            extent=[0, len(freqs), 0, BUFFER_SIZE],
            cmap="viridis",
        )
        plt.xlabel("Frequency Band")
        plt.ylabel("Time (old → new ↑)")
        plt.pause(0.01)


bus.connect("message", on_message)

pipeline.set_state(Gst.State.PLAYING)

try:
    plt.figure(figsize=(6, 6))
    plt.ion()
    plt.show()
    loop = GObject.MainLoop()
    loop.run()
except KeyboardInterrupt:
    pass
finally:
    pipeline.set_state(Gst.State.NULL)
