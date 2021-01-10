from enum import Enum, unique

from utils import *


@unique
class FTPCmd(Enum):
    CONT = 0    # Connect
    USER = 1
    PASS = 2
    PWD = 3
    CWD = 4
    PASV = 5
    LIST = 6
    RETR = 7    # Download
    RET = 8     # Node 2 to node 1
    QUIT = 9


class Config:
    def __init__(self, role):
        # Length of the "fs" field
        self.fs = 48000

        # Length of the "fc" field
        self.fc = 10 * 1000

        # Length of the "command id" field, records which command this packet belongs
        self.id_length = 10

        # Length of the "# sequence" field, records which sequence of a command this packet belongs
        self.seq_num_length = 20

        # Length of the "total sequence amount" field, records how many sequences a command possess
        self.total_seq_length = 20

        # Length of the "type" field, 0 for info, 1 for file data, 2 for "ready for next command"
        self.type_length = 8

        # Length for "data count" field, record how many valid bits this packet contain
        self.data_cnt_length = 10

        # Length for "ip" field
        self.ip_length = 32

        # Length for "port" field
        self.port_length = 16

        # Length for "protocol" field, each protocol corresponds to one FTPCmd
        self.proto_length = 8

        # Total length for the header
        self.header_length = self.id_length + self.seq_num_length + self.total_seq_length + self.type_length \
                             + self.data_cnt_length + self.ip_length + self.port_length + self.proto_length

        # Length for the "crc" field
        self.crc_length = 16

        # How long a bit is modulated
        self.wave_length_per_bit = 5

        # The preset preamble wave
        self.preamble_wave = generatePreambleWave(self.fs, self.wave_length_per_bit)

        # The preset carrier wave
        self.carrier_wave = generateCarrierWave(self.fs, self.fc)

        # Amount of data per frame
        self.DATA_PER_FRAME = 320

        # Robustness level of transmitting
        self.robustness = 5

        # How long does the receiver keep listening
        self.receive_time = 10800

        # False for debug
        self.audio_in = True
        self.audio_out = True

        # Role: 1 for transmitter, 0 for receiver
        self.is_transmitter = role
        self.is_receiver = not self.is_transmitter
