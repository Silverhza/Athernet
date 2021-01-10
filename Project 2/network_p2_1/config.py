from utils import *

class Config:
    def __init__(self, data_size):
        self.fs = 48000
        self.fc = 10 * 1000
        self.id_length = 10
        self.header_length = self.id_length
        self.TOTAL_DATA = data_size
        self.DATA_PER_FRAME = 500
        self.TOTAL_FRAMES = self.TOTAL_DATA // self.DATA_PER_FRAME
        self.crc_length = 8
        self.wave_length_per_bit = 5
        self.preamble_wave = generatePreambleWave(self.fs, self.wave_length_per_bit)
        self.carrier_wave = generateCarrierWave(self.fs, self.fc)
        self.receive_time = 9

        self.audio_in = True
        self.audio_out = False
