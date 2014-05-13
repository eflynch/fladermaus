import pyaudio
import time
import numpy as np
import matplotlib.pyplot as plt
from options import CHANNELS, CHUNK, SAMPLE_RATE, FORMAT, CHUNKS_PER_BUFFER


def read_from_stream(seconds):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                channels = CHANNELS,
                rate = SAMPLE_RATE,
                input = True,
                output = False,
                frames_per_buffer = CHUNK)
    buff = string_to_numpy(stream.read(SAMPLE_RATE*seconds))
    return buff

def string_to_numpy(string):
    buff = np.zeros(len(string)/4,dtype=np.float32)
    buff[:] = np.fromstring(string,dtype=np.float32)
    return buff


def start_listening(callback):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels = CHANNELS,
                    rate = SAMPLE_RATE,
                    input = True,
                    output = False,
                    frames_per_buffer = CHUNK*CHUNKS_PER_BUFFER,
                    stream_callback=callback)
    stream.start_stream()
    while stream.is_active():
        time.sleep(0.1)


if __name__ == "__main__":
    from meow import write_to_stream
    buff = read_from_stream(5)
    write_to_stream(buff)

