from pyaudio import paFloat32

SAMPLE_RATE = 44100
FORMAT = paFloat32 
BITS_PER_SECOND = 1
LOW_FREQ = 0
HIGH_FREQ = 24000
CHUNK = 1024
CHANNELS = 1
CHUNKS_PER_BUFFER = 6
THRESHOLD = 0.03
GRAPHIC_MULTIPLIER = 100
MEDIAN_FILTER = 5
DEBUG = True
