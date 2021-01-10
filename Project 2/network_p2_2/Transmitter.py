import copy
import numpy as np
import sounddevice as sd
from utils import *


class Transmitter:
    def __init__(self, config):
        self.data = None
        self.fs = config.fs
        self.fc = config.fc
        self.header_length = config.header_length
        self.preamble_wave = config.preamble_wave
        self.carrier_wave = config.carrier_wave
        self.audio_out = config.audio_out
        self.crc_length = config.crc_length
        self.wave_length_per_bit = config.wave_length_per_bit
        self.frame_num = None
        self.frame_length = None
        self.ostream = sd.OutputStream(samplerate=self.fs, channels=1, latency="low")
        self.ostream.start()

    def addHeader(self, id, frame):
        ''' Add ID for each frame at head'''
        new_frame = np.zeros((frame.size + self.header_length), dtype=np.uint8)
        new_frame[:self.header_length] = dec2arr(id, self.header_length)
        new_frame[self.header_length:] = copy.deepcopy(frame)
        return new_frame

    def addCRC(self, frame):
        ''' Add crc-8 at the tail, calculated from header+frame_data '''
        new_frame = np.zeros((frame.size + self.crc_length), dtype=np.uint8)
        new_frame[:frame.size] = copy.deepcopy(frame)
        new_frame[frame.size:] = dec2arr(int(generateCRC(frame, mode='crc-'+str(self.crc_length)), 16), self.crc_length)
        return new_frame

    def modulate(self, frame):
        frame_wave = np.zeros((frame.size * self.wave_length_per_bit))
        for i in range(frame.size):
            frame_wave[self.wave_length_per_bit*i : self.wave_length_per_bit*(i+1)] = \
                self.carrier_wave[self.wave_length_per_bit*i : self.wave_length_per_bit*(i+1)] * (frame[i] * 2 - 1)
        return frame_wave

    def makeSound(self, wave):
        print("Sending...")
        self.ostream.write(wave)
        print("Sending Finished.")

    def send(self, data):
        self.data = data
        self.frame_num = data.shape[0]
        self.frame_length = data.shape[1]

        # self.ostream.start()
        whole_wave = np.array([])
        for i in range(self.frame_num):
            random_wave = self.modulate(np.random.rand(50))
            header_frame = self.addHeader(i, self.data[i])
            header_frame_crc = self.addCRC(header_frame)
            frame_wave = self.modulate(header_frame_crc)
            whole_wave = np.concatenate((whole_wave, random_wave, self.preamble_wave, frame_wave), axis=0)
        whole_wave = np.concatenate((whole_wave, random_wave.repeat(20)), axis=0)

        if self.audio_out:
            self.makeSound(whole_wave.astype(np.float32))

        return whole_wave

    def __del__(self):
        self.ostream.close()
