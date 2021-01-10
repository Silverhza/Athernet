import os
import sys
import numpy as np
import bitstring
from bitstring import ConstBitStream

from utils import *
import config as config
from Transmitter import Transmitter
from Receiver import Receiver

if __name__ == "__main__":

    # Create random data
    # createRandomData("inputs/INPUT3.txt", config.TOTAL_DATA)

    # Set path
    input_file_path = "inputs/INPUT.bin"
    data_bit_size = os.path.getsize(input_file_path) * 8

    # Load configurations
    config = config.Config(data_bit_size)

    # Read data
    bit_stream = ConstBitStream(filename=input_file_path)
    data_str = bit_stream.read(data_bit_size)
    data = np.array(list(data_str), dtype=np.uint8)
    data = data.reshape((config.TOTAL_FRAMES, config.DATA_PER_FRAME))
    # for i in range(TOTAL_FRAMES):
    #     for j in range(DATA_PER_FRAME):
    #         print(data[i, j], end='')
    #     print('\n')

    sent_data = np.array([])

    # # Transmitter responsible for sending data
    # transmitter = Transmitter(data, config)
    # sent_data = transmitter.send()

    # Receiver responsible for receiving data
    receiver = Receiver(config, debug_data=sent_data)
    received_data = receiver.receive()

    fileDiff(input_file_path, "outputs/OUTPUT.bin")
