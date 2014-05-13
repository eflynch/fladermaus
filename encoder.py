import meow
import time
from options import BITS_PER_SECOND,LOW_FREQ,HIGH_FREQ

REDUNDANCY = 20

def get_bit_encoding(b):
    if b == 0:
        return [0,1]*REDUNDANCY
    else:
        return [1,0]*REDUNDANCY


def generate_spectrum_mask(bits,low,high):
    num_bins = len(bits)
    bin_width = (high-low)/num_bins
    segments = []

    inSegment = False
    low_point = low
    for i,b in enumerate(bits):
        position = i*bin_width+low
        if inSegment:
            if b==0:
                segments.append((low_point,position))
                inSegment = False
        else:
            if b==1:
                low_point = position
                inSegment = True

    if inSegment:
        segments.append((low_point,high))

    return segments

def generate_inverse_mask(bits,low,high):
    return generate_spectrum_mask([int(not b) for b in bits],low,high)


def encode_bit(b,seconds):
    bits = get_bit_encoding(b)
    segments = generate_spectrum_mask(bits,LOW_FREQ,HIGH_FREQ)

    noise = meow.generate_noise(seconds)
    filtered_noise = meow.mask_filter(noise,segments)
    return filtered_noise

def encode_null(seconds):
    bits = [0,0]*REDUNDANCY
    segments = generate_spectrum_mask(bits,LOW_FREQ,HIGH_FREQ)

    noise = meow.generate_noise(seconds)
    filtered_noise = meow.mask_filter(noise,segments)
    return filtered_noise

string_to_bits = lambda x: "".join(['00000000'[len(bin(ord(c))[2:]):]+bin(ord(c))[2:] for c in x])

def send_message(s):

    #send_calibration()

    bits = string_to_bits(s)
    for b in bits:
        buff = encode_bit(int(b),1./BITS_PER_SECOND)
        meow.write_to_stream(buff)
        buff = encode_null(1./BITS_PER_SECOND)
        meow.write_to_stream(buff)

if __name__ == "__main__":
    while True:
        message = raw_input(">")
        send_message(message)



