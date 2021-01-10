import os
import sys
import time
import numpy as np
import bitstring
from bitstring import ConstBitStream
from bitarray import bitarray

from utils import *
from config import Config, FTPCmd
from Transmitter import Transmitter
from Receiver import Receiver


def part1():
    # Load configurations
    config_tran = Config(role=1)
    config_rec = Config(role=0)

    ftp_host = input("Input the target FTP host: ")

    # Transmitter to send to Node 2, Receiver to listen from Node 2
    transmitter = Transmitter(config_tran)
    receiver = Receiver(config_rec)

    # Number of commands counting
    cmd_id = 0

    # Tell NAT the target FTP host and connect to it
    transmitter.send("192.168.1.2", 8888, generateSplitBinData(ftp_host), cmd_id, FTPCmd.CONT, type=0)
    type, received_proto, received_data_undecoded = receiver.receive(expect_id=cmd_id, expect_type=0)
    received_data_decoded = decodeBinInfoData(received_data_undecoded)
    # Receive the signal to proceed
    type, received_proto, received_data_undecoded = receiver.receive(expect_id=cmd_id, expect_type=2)
    if type == 2:
        print("{:<40}".format("".join(received_data_decoded)))
    cmd_id += 1

    # Do commands
    while True:
        # Get and send commands to Node 2
        cmd_all = getCmd()
        if len(cmd_all) == 1:
            transmitter.send("192.168.1.2", 8888, generateSplitBinData(""), cmd_id, FTPCmd[cmd_all[0]], type=0)
        elif len(cmd_all) == 2:
            transmitter.send("192.168.1.2", 8888, generateSplitBinData(cmd_all[1]), cmd_id, FTPCmd[cmd_all[0]], type=0)

        # Receive info response from Node 2
        type, received_proto, received_data_undecoded = receiver.receive(expect_id=cmd_id, expect_type=0)
        received_data_decoded = decodeBinInfoData(received_data_undecoded)
        saved_info = received_data_decoded

        # Receive file response from Node 2 if the command is downloading file
        if FTPCmd[cmd_all[0]] == FTPCmd.RETR and ("".join(received_data_decoded))[:3] != "550":
            paths = copy.deepcopy("".join(cmd_all[1]))
            path_list = paths.strip().split()

            type, received_proto, received_data_undecoded = receiver.receive(expect_id=cmd_id, expect_type=1)
            received_data_decoded = decodeBinFileData(received_data_undecoded)

            # Write to file in binary
            bits = bitarray(received_data_decoded)
            output_file = ""
            if len(path_list) == 1:
                output_file = open(path_list[0], "wb+")
            elif len(path_list) == 2:
                output_file = open(path_list[1], "wb+")
            bits.tofile(output_file)
            output_file.close()
        elif FTPCmd[cmd_all[0]] == FTPCmd.QUIT:
            break

        # Receive the signal to proceed
        type, received_proto, received_data_undecoded = receiver.receive(expect_id=cmd_id, expect_type=2)
        if type == 2:
            print("{:<40}".format("".join(saved_info)))

        cmd_id += 1


if __name__ == "__main__":
    part1()
