import pyaudio
import numpy as np
import matplotlib.pyplot as plt

from purr import read_from_stream
from options import SAMPLE_RATE

def get_spectrum(seconds,low_freq,high_freq):
    buff = read_from_stream(seconds)
    num_samples = len(buff)
    spectrum = np.absolute(np.fft.fft(buff))**2
    index_of = lambda x: (num_samples/2)*x/(SAMPLE_RATE/2)
    return spectrum[index_of(low_freq):index_of(high_freq)]



if __name__ == "__main__":
    plt.figure()
    for i in range(1):
        spectrum = get_spectrum(10,10000,22000)
        plt.plot(spectrum,color='blue')
    print "now turn it on"
    for i in range(1):
        spectrum = get_spectrum(10,10000,22000)
        plt.plot(spectrum,color='red')
    plt.show()


