import sys
import numpy as np

from utils import *
import config as config
from Transmitter import Transmitter
from Receiver import Receiver

if __name__ == "__main__":

    # Load configurations
    config = config.Config()

    # Create random data
    # createRandomData("inputs/INPUT3.txt", config.TOTAL_DATA)

    # Read data from INPUT.txt and reorganize to data
    input_file_path = "inputs/INPUT.txt"
    input_file = open(input_file_path, "r")
    data_str = input_file.read()
    data = np.array(list(data_str), dtype=np.uint8)
    data = data.reshape((config.TOTAL_FRAMES, config.DATA_PER_FRAME))
    # for i in range(TOTAL_FRAMES):
    #     for j in range(DATA_PER_FRAME):
    #         print(data[i, j], end='')
    #     print('\n')

    sent_data = np.array([])

    # # # Transmitter responsible for sending data
    # transmitter = Transmitter(data, config)
    # sent_data = transmitter.send()

    # Receiver responsible for receiving data
    receiver = Receiver(config, debug_data=sent_data)
    received_data = receiver.receive()

    # arrDiff(np.array(list(data_str), dtype=np.uint8), received_data)
    fileDiff(input_file_path, "outputs/OUTPUT.txt")
