import Queue
import threading
import time
import pyaudio
import numpy as np
import options
import sys
import psk
import struct

FORMAT = pyaudio.paInt16
frame_length = 3
chunk = 1024
rate = 44100
#frames_per_buffer = chunk * 10
frames_per_buffer = chunk 

in_length = 10000
# raw audio frames
in_frames = Queue.Queue(in_length)

sigil = [int(x) for x in options.sigil]

wait_for_sample_timeout = 0.1
wait_for_frames_timeout = 0.1


bottom_threshold = 8000
def process_frames():
    while True:
        try:
            frame = in_frames.get(False)
            
            #code from http://stackoverflow.com/questions/2648151/python-frequency-detection
            # Take the fft and square each value
            fftData=abs(np.fft.rfft(frame))**2
            # find the maximum
            which = fftData[1:].argmax() + 1
            # use quadratic interpolation around the max
            if which != len(fftData)-1:
                y0,y1,y2 = np.log(fftData[which-1:which+2:])
                x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
                # find the frequency and output it
                thefreq = (which+x1)*rate/chunk
                if thefreq>bottom_threshold:
                    print str(fftData[which])+".  The freq is " +str(thefreq)+ " Hz"
            else:
                thefreq = which*rate/chunk
                print "The freq is %f Hz." % (thefreq)
        except Queue.Empty:
                time.sleep(wait_for_frames_timeout)
          


processes = [process_frames]
threads = []

for process in processes:
    thread = threading.Thread(target=process)
    thread.daemon = True
    thread.start()        

# split something into chunks
def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def unpack(buffer):
    return unpack_buffer(list(chunks(buffer, 2)))

def unpack_buffer(buffer):
    return [struct.unpack('h', frame)[0] for frame in buffer]

def callback(in_data, frame_count, time_info, status):
    frames = list(chunks(unpack(in_data), chunk))
    for frame in frames:
        if not in_frames.full():
            in_frames.put(frame, False)
    return (in_data, pyaudio.paContinue)

def start_analysing_stream():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=options.channels, rate=options.rate,
        input=True, frames_per_buffer=frames_per_buffer, stream_callback=callback)
    stream.start_stream()
    while stream.is_active():
        time.sleep(wait_for_sample_timeout)

start_analysing_stream()


