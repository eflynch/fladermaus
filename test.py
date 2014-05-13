import numpy as nm
import matplotlib.pyplot as plt
import binascii
import zfec

SAMPLE_RATE = 44100
REDUNDANCY = 3
BITS_PER_CHR = 16
seconds = 2
lowest_frequency = 18000
highest_frequency = 21000

def chr_to_bits(string):
    bits = [int(b) for b in bin(ord(string))[2:]]
    if len(bits) % 2 == 1:
        bits.insert(0,0)
    return bits


def bits_to_chr(bits):
    n = int("0b"+"".join([str(b) for b in bits]),2)
    return chr(n)

def generate_noise(length):
    noise = nm.random.normal(0,1,length)
    return noise

def get_encoding(c):
    bits = chr_to_bits(c)
    pbits = [(b+1)%2 for b in bits]
    bits.extend(pbits)
    return bits

def get_string_encoding(string):
    ecc = zfec.Encoder(len(string),len(string)*REDUNDANCY).encode([c for c in string])
    bits = []
    for c in ecc:
        bits.extend(get_encoding(c))
    return bits

def decode_bits(bits):
    num_chrs = len(bits)/BITS_PER_CHR/REDUNDANCY
    blocks = []
    indices = []
    for i in xrange(num_chrs*REDUNDANCY):
        frame = bits[i*BITS_PER_CHR:(i+1)*BITS_PER_CHR]
        if sum(frame) != BITS_PER_CHR/2:
            continue
        c = bits_to_chr(frame[:8])
        blocks.append(c)
        indices.append(i)
    if len(blocks) < num_chrs:
        raise Exception("Didn't get enough good blocks, got %d" % len(blocks))
   
    chrs = zfec.Decoder(num_chrs,num_chrs*REDUNDANCY).decode(blocks[:num_chrs],indices[:num_chrs])[:num_chrs]
    return "".join(chrs)

def get_modulation(bits):
    num_bins = len(bits)
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

    modulation_array = get_modulation(get_string_encoding(s))
    modulated_spectrum = filtered_spectrum * ((1-threshold) + threshold * modulation_array)

    modulated_signal = nm.fft.ifft(modulated_spectrum)
    return modulated_signal

def decode(signal,num_chrs,threshold=0.25):
    num_bits = num_chrs*BITS_PER_CHR*REDUNDANCY
    spectrum = nm.fft.fft(signal)
    bin_width = (highest_frequency-lowest_frequency)/num_bits
    position = lowest_frequency
    avr = nm.mean(nm.abs(spectrum[lowest_frequency:highest_frequency]))
    bits = []
    for i in range(num_bits):
        s = nm.sum(nm.abs(spectrum[position:position+bin_width]))/bin_width
        if s > (1+threshold)*avr:
            bits.append(1)
        else:
            bits.append(0)
        position += bin_width
    
    s = decode_bits(bits)
    return s

def add_noise(signal,threshold=0.5):
    return signal*(1-threshold) + generate_noise(SAMPLE_RATE*seconds)*threshold

c = "abcd"
a = encode(c,threshold=1.0)
a_noisy = add_noise(a,0.60)
print decode(a_noisy,len(c),threshold=0.0)
a_noisy_spectrum = nm.fft.fft(a_noisy)

#plt.figure()
#plt.plot(a)
#plt.figure()
#plt.plot(a_noisy_spectrum)
#plt.show()

