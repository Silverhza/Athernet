import copy
import numpy as np
import sounddevice as sd
from utils import *


class Transmitter:
    def __init__(self, config):
        self.fs = config.fs
        self.fc = config.fc
        self.id_length = config.id_length
        self.cnt_length = config.cnt_length
        self.ip_length = config.ip_length
        self.port_length = config.port_length
        self.proto_length = config.proto_length
        self.header_length = config.header_length
        self.data_per_frame = config.DATA_PER_FRAME
        self.preamble_wave = config.preamble_wave
        self.carrier_wave = config.carrier_wave
        self.audio_out = config.audio_out
        self.crc_length = config.crc_length
        self.wave_length_per_bit = config.wave_length_per_bit
        self.frame_num = config.TOTAL_FRAMES
        self.frame_length = None
        self.proto = config.proto
        self.robustness = config.robustness
        self.ostream = sd.OutputStream(samplerate=self.fs, channels=1, latency="low")
        # self.ostream.start()

    def addHeaderAndPadding(self, id, frame, ip='192.168.1.2', port=8888):
        last_set = 0
        new_frame = np.zeros((self.header_length + self.data_per_frame), dtype=np.uint8)
        new_frame[last_set:last_set+self.id_length] = dec2arr(id, self.id_length); last_set += self.id_length
        new_frame[last_set:last_set+self.cnt_length] = dec2arr(frame.size, self.cnt_length); last_set += self.cnt_length
        new_frame[last_set:last_set+self.ip_length] = ip2arr(ip); last_set += self.ip_length;
        new_frame[last_set:last_set+self.port_length] = dec2arr(port, self.port_length); last_set += self.port_length
        new_frame[last_set:last_set+self.proto_length] = dec2arr(self.proto, self.proto_length)
        new_frame[self.header_length:self.header_length+frame.size] = copy.deepcopy(frame)
        new_frame[self.header_length+frame.size:] = 0
        new_frame[self.header_length+frame.size::2] = 1
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
        print("Athernet Sending...")
        self.ostream.write(wave)
        print("Athernet Sending Finished.")

    def send(self, ip, port, data):
        self.ostream.start()
        whole_wave = np.array([])
        random_wave = np.array([])
        for i in range(self.frame_num):
            random_wave = self.modulate(np.random.rand(50))
            header_frame = self.addHeaderAndPadding(i, data[i], ip, port)
            header_frame_crc = self.addCRC(header_frame)
            frame_wave = self.modulate(header_frame_crc)
            whole_wave = np.concatenate((whole_wave, random_wave, self.preamble_wave, frame_wave), axis=0)

        # Add beginning and ending noise
        whole_wave = np.tile(whole_wave, self.robustness)
        whole_wave = np.concatenate((random_wave.repeat(10), whole_wave), axis=0)
        whole_wave = np.concatenate((whole_wave, random_wave.repeat(10)), axis=0)

        if self.audio_out:
            self.makeSound(whole_wave.astype(np.float32))
        send_time = time.time()

        self.ostream.stop()
        return whole_wave, send_time

    def __del__(self):
        self.ostream.close()
