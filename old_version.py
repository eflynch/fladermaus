import math
import struct
import numpy as nm
import matplotlib.pyplot as plt
import binascii
import pyaudio
from multiprocessing import Process, Queue
from Queue import Empty as EmptyException

p = pyaudio.PyAudio()

CHANNELS = 1
CHUNK = 4096
SAMPLE_RATE = 44100
FORMAT = pyaudio.paFloat32
REDUNDANCY = 10
seconds = 1
lowest_frequency = 18000
highest_frequency = 22000



def generate_noise(length):
    noise = nm.random.normal(0,1,length)
    return noise

def get_encoding(b):
    if b == 0:
        return [0,1]*REDUNDANCY
    else:
        return [1,0]*REDUNDANCY

def decode_bit(arry):
    zero = 0
    one = 0
    for i,b in enumerate(arry):
        if i % 2 == b:
            zero+=1
        else:
            one+=1
    if zero > one:
        return 0
    elif one > zero:
        return 1
    else:
        return -1
def get_modulation(bits):
    num_bins = REDUNDANCY*2
    bin_width = (highest_frequency-lowest_frequency)/num_bins
    a = nm.zeros(SAMPLE_RATE*seconds)
    a[0:lowest_frequency] = 0
    a[highest_frequency:] = 0
    position = lowest_frequency
    for b in bits:
        a[position:position+bin_width] = b
        position = position+bin_width
    return a

def encode(s,threshold=0.25):
    generated_noise = generate_noise(SAMPLE_RATE*seconds)
    generated_spectrum = nm.fft.fft(generated_noise)
    high_pass_filter = nm.array([int(x > lowest_frequency and x < highest_frequency) for x in xrange(SAMPLE_RATE*seconds)])
    filtered_spectrum = generated_spectrum * high_pass_filter

    modulation_array = get_modulation(get_encoding(s))
    modulated_spectrum = filtered_spectrum * ((1-threshold) + threshold * modulation_array)

    modulated_signal = nm.fft.ifft(modulated_spectrum)
    return modulated_signal

def decode(signal,threshold=0.25):
    num_bins = REDUNDANCY*2
    spectrum = nm.fft.fft(signal)
    bin_width = (highest_frequency-lowest_frequency)/num_bins
    position = lowest_frequency
    avr = nm.mean(nm.abs(spectrum[lowest_frequency:highest_frequency]))
    bits = []
    for i in range(num_bins):
        s = nm.sum(nm.abs(spectrum[position:position+bin_width]))/bin_width
        if s > (1+threshold)*avr:
            bits.append(1)
        else:
            bits.append(0)
        position += bin_width
    s = decode_bit(bits)
    return s

def add_noise(signal,threshold=0.5):
    return signal*(1-threshold) + generate_noise(SAMPLE_RATE*seconds)*threshold

def play_array(arry,play_queue):
    for i in xrange(len(arry)/(CHUNK*CHANNELS)):
        subarry = arry[i*CHUNK*CHANNELS:(i+1)*CHUNK*CHANNELS]
        play_queue.put(subarry)
        print "Added chunk from %d to %d (%d)" % (i*CHUNK*CHANNELS,(i+1)*CHUNK*CHANNELS,len(subarry))
    remainder = arry[(i+1)*CHUNK*CHANNELS:]
    if len(remainder) > 0:
        subarry = nm.zeros(CHUNK*CHANNELS,dtype=nm.float32)
        subarry[:len(remainder)] = remainder
        play_queue.put(subarry)
        print "Added chunk from %d to %d (%d)" % ((i+1)*CHUNK*CHANNELS,(i+1)*CHUNK*CHANNELS+len(subarry),len(subarry))

def play_loop(play_queue, stream):
    while True:
        try:
            arry = play_queue.get_nowait()
            print "Queue had an array: writing data"
        except EmptyException:
            print "Queue was empty: writing zeros"
            arry = nm.zeros(CHUNK*CHANNELS,dtype=nm.float32)

        # Pack Buffer
        buff = nm.zeros(CHUNK*CHANNELS,dtype=nm.float32)
        buff[:] = arry.real[:]

        # Output Buffer
        print "about to write"
        stream.write(buff)
        print "done writing"


if __name__ == "__main__":
    stream = p.open(format=FORMAT,
                        channels = CHANNELS,
                        rate=SAMPLE_RATE,
                        output=True,
                        frames_per_buffer=CHUNK)

    play_queue = Queue()
    play_process = Process(target=play_loop, args=(play_queue,stream,))

    #num_correct = 0
    #for i in range(100):
    #    c = i % 2
    #    a = encode(c,threshold=1.0)
    #    a_noisy = add_noise(a,0.80)
    #    if decode(a_noisy,threshold=0.0) == c:
    #        num_correct+=1
    #print num_correct
    c = 1
    a = encode(c,threshold=0.9)
    play_array(nm.real(a),play_queue)
    #plt.figure()
    #plt.plot(nm.abs(nm.fft.fft(a)))
    #plt.show()
    #a_noisy = add_noise(a,0.90)
    #print decode(a_noisy,threshold=0.0)
    #a_noisy_spectrum = nm.fft.fft(a_noisy)
    #plt.figure()
    #plt.plot(nm.abs(a_noisy_spectrum))
    #plt.show()
    play_process.start()

    while True:
        pass

