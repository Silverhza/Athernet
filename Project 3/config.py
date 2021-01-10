from utils import *

# Role: 1 for transmitter,
#       0 for receiver

# Proto: 1 for ICMP,
#        0 for data


class Config:
    def __init__(self, role, proto):
        self.fs = 48000
        self.fc = 10 * 1000
        self.id_length = 10
        self.cnt_length = 10
        self.ip_length = 32
        self.port_length = 16
        self.proto_length = 8
        self.header_length = self.id_length + self.cnt_length + self.ip_length + self.port_length + self.proto_length
        self.DATA_PER_FRAME = 320
        self.TOTAL_FRAMES = 30
        self.crc_length = 16
        self.wave_length_per_bit = 5
        self.preamble_wave = generatePreambleWave(self.fs, self.wave_length_per_bit)
        self.carrier_wave = generateCarrierWave(self.fs, self.fc)
        self.robustness = 4
        self.receive_time = 12

        self.audio_in = True
        self.audio_out = True

        self.is_transmitter = role
        self.is_receiver = not self.is_transmitter

        self.proto = proto
