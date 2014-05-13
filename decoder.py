import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import time

import Queue as RegQueue
from multiprocessing import Process, Queue
from purr import read_from_stream, start_listening
from purr import string_to_numpy

from options import SAMPLE_RATE,LOW_FREQ,HIGH_FREQ,THRESHOLD,GRAPHIC_MULTIPLIER,MEDIAN_FILTER,DEBUG

import sys


def decode_mask(buff,masks):
    num_samples = len(buff)
    index_of = lambda x: (num_samples/2)*x/(SAMPLE_RATE/2)
    spectrum = np.fft.fft(buff)
    metrics = []
    for m in masks:
        mask,imask = masks[m]

        averages = []
        for low,high in mask:
            width = high-low
            a = np.sum((np.abs(spectrum)**2)[index_of(low):index_of(high)])/width
            averages.append(a)

        iaverages = []
        for low,high in imask:
            width = high-low
            a = np.sum((np.abs(spectrum)**2)[index_of(low):index_of(high)])/width
            iaverages.append(a)

        quality = sum(averages)/len(mask) - sum(iaverages)/len(imask)
        metrics.append((quality*100,m))

    return max(metrics,key=lambda x:x[0])

def call_back(in_data, frame_count, time_info, status):
    buff = string_to_numpy(in_data)
    in_queue.put(buff,False)
    return (in_data, pyaudio.paContinue)


def listen_loop(in_queue,filter_queue):
    while True:
        buff = in_queue.get(True)
        confidence,bit = decode_mask(buff,{0:(zero_mask,one_mask),1:(one_mask,zero_mask)})
        confidence = round(confidence,3)
        graphic = "".join([str(bit)]*int(np.sqrt(min([confidence,THRESHOLD]))*GRAPHIC_MULTIPLIER))+"".join(["+"]*int(np.sqrt(max([0,confidence-THRESHOLD]))*GRAPHIC_MULTIPLIER))


        if confidence > THRESHOLD:
            filter_queue.put(bit,False)
            if bit == 0:
                if DEBUG:
                    print "0               :  ",graphic
            elif bit == 1:
                if DEBUG:
                    print "  1             :  ",graphic
        else:
            if DEBUG:
                print " -              :  ",graphic
            filter_queue.put(-1,False)


def filter_loop(filter_queue,bit_queue):
    window = []

    while True:
        bit = filter_queue.get(True)
        if len(window) < MEDIAN_FILTER:
            window.append(bit)
        else:
            bit_queue.put(sorted(window)[1])
            window.pop(0)
            window.append(bit)

def bit_loop(bit_queue,msg_queue):
    state = -1
    while True:
        bit = bit_queue.get(True)
        if state == -1:
            if bit == 1:
                state = 1
                msg_queue.put(1,False)
            elif bit == 0:
                state = 0
                msg_queue.put(0,False)
        elif state == 0:
            if bit == -1:
                state = -1
            elif bit == 1:
                msg_queue.put(1,False)
                state = 1
        elif state == 1:
            if bit == -1:
                state = -1
            elif bit == 0:
                msg_queue.put(0,False)
                state = 0


def msg_loop(msg_queue):
    string = ""
    bit_string = "0b"
    while True:
        bit = msg_queue.get(True)
        if DEBUG:
            print "                                              ",bit
        bit_string += str(bit)
        if len(bit_string) == 10:
            string += chr(int(bit_string,2))
            if DEBUG:
                print "                                                                                                                                     ---> ",string
            else:
                sys.stdout.write( chr(int(bit_string,2)))
                sys.stdout.flush()

            bit_string = "0b"



if __name__ == "__main__":
    from meow import write_to_stream
    #buff = read_from_stream(5)
    #write_to_stream(buff)

    from encoder import generate_spectrum_mask, generate_inverse_mask, get_bit_encoding
    zero_mask = generate_spectrum_mask(get_bit_encoding(0),LOW_FREQ,HIGH_FREQ)
    one_mask = generate_spectrum_mask(get_bit_encoding(1),LOW_FREQ,HIGH_FREQ)

    in_queue = Queue()
    filter_queue = Queue()
    bit_queue = Queue()
    msg_queue = Queue()

    listen_process = Process(target=listen_loop, args=(in_queue,filter_queue))
    filter_process = Process(target=filter_loop, args=(filter_queue,bit_queue,))
    bit_process = Process(target=bit_loop, args=(bit_queue,msg_queue,))
    msg_process = Process(target=msg_loop, args=(msg_queue,))

    listen_process.start()
    filter_process.start()
    bit_process.start()
    msg_process.start()


    start_listening(call_back)

