from multiprocessing import Process, Queue
import pyaudio
import numpy as np
from Queue import Empty as EmptyException
import matplotlib.pyplot as plt
from options import CHANNELS, CHUNK, SAMPLE_RATE, FORMAT

FORMAT = pyaudio.paFloat32

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels = CHANNELS,
                rate=SAMPLE_RATE,
                output=True,
                frames_per_buffer=CHUNK)

def generate_noise(seconds):
    num_samples = SAMPLE_RATE*CHANNELS*seconds
    noise = np.random.normal(0,1,num_samples)
    return noise

def generate_sinewave(seconds,frequency):
    samples_per_second = SAMPLE_RATE*CHANNELS
    sample = np.array(range(seconds*samples_per_second),dtype=np.float32)
    sin = lambda x: np.sin(2*np.pi*float(frequency)*x/float(samples_per_second))
    return sin(sample)


def play_loop(play_queue, stream):
    while True:
        try:
            arry = play_queue.get_nowait()
            print "Queue had an array: writing data"
        except EmptyException:
            print "Queue was empty: writing zeros"
            arry = np.zeros(CHUNK*CHANNELS,dtype=np.float32)

        # Pack Buffer
        buff = np.zeros(len(arry),dtype=np.float32)
        buff[:] = arry.real[:]

        # Output Buffer
        print "about to write"
        stream.write(buff)
        print "done writing"

def write_to_stream(buff):
    stream.write(envelope(buff).tostring())

def band_pass_filter(buff,low_freq,high_freq,plot=False):
    if plot:
        plt.figure()
        plt.plot(buff)

    spectrum = np.fft.fft(buff)

    if plot:
        plt.figure()
        plt.plot(spectrum)

    num_samples = len(spectrum)
    low_index = (num_samples/2)*low_freq/(SAMPLE_RATE/2)
    high_index = (num_samples/2)*high_freq/(SAMPLE_RATE/2)
    print low_index
    print high_index


    objective = lambda x: x > low_index and x < high_index or x > num_samples-high_index and x<num_samples-low_index
    mask = np.array([float(objective(x)) for x in xrange(len(spectrum))], dtype=np.float32)
    #mask = np.ones(len(spectrum),dtype=np.float32)
    if plot:
        plt.figure()
        plt.plot(mask)

    filtered_spectrum = spectrum*mask

    if plot:
        plt.figure()
        plt.plot(filtered_spectrum)

    filtered = np.fft.ifft(filtered_spectrum)

    if plot:
        plt.figure()
        plt.plot(filtered)
        plt.show()

    return_array = np.zeros(len(buff),dtype=np.float32)
    return_array[:] = np.real(filtered)

    return return_array

def mask_filter(buff,segments):
    num_samples = len(buff)
    index_of = lambda x: (num_samples/2)*x/(SAMPLE_RATE/2)
    def objective(x):
        for low,high in segments:
            if x > index_of(low) and x < index_of(high):
                return True
            if x > num_samples-index_of(high) and x <num_samples-index_of(low):
                return True
        return False
    mask = np.array([float(objective(x)) for x in xrange(num_samples)], dtype=np.float32)

    return_array = np.zeros(num_samples,dtype=np.float32)
    return_array[:] = np.real(np.fft.ifft(np.fft.fft(buff)*mask))

    return return_array

def gain(buff,factor):
    return buff*factor

def envelope(buff):
    num_samples = min([len(buff)/10,4096])
    veloper = np.linspace(0,1,num_samples)
    unveloper = np.linspace(1,0,num_samples)
    buff[:num_samples]*=veloper
    buff[-num_samples:]*=unveloper
    return buff


if __name__ == "__main__":
    buff = generate_noise(15)
    #buff = generate_sinewave(1,440)
    #filtered = band_pass_filter(buff,20000,21000)
    #filtered = mask_filter(buff,((439,441),(513,536),(782,783)))
    filtered = mask_filter(buff,((200,210),(300,500),(1235,1250)))

    write_to_stream(filtered)

