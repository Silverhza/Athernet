import os
import sys
import numpy as np
import bitstring
from bitstring import ConstBitStream
from bitarray import bitarray

from utils import *
from config import Config, FTPCmd
from Transmitter import Transmitter
from Receiver import Receiver
from FTP import FTPClient


def part1():
    # Status
    check_connect = 1
    cmd_id = 0
    resp = None
    ftp = FTPClient()

    # Load configurations
    config_tran = Config(role=1)
    config_tran_ack = Config(role=1); config_tran_ack.robustness = 40
    config_rec = Config(role=0)

    # Transmitter to send to Node 1, Receiver to listen from Node 1
    transmitter = Transmitter(config_tran)
    transmitter_ack = Transmitter(config_tran_ack)
    receiver = Receiver(config_rec)

    # Keep NAT working until QUIT
    while True:
        received_proto = -1
        relay_file_path = "relay/"

        # Listen for command
        type, received_proto, received_data_undecoded = receiver.receive(expect_id=cmd_id, expect_type=0)
        received_data_decoded = decodeBinInfoData(received_data_undecoded)

        # FTP connect
        if received_proto == FTPCmd.CONT.value:
            if check_connect == 0:
                resp = "421 There are too many connections from your internet address."
            else:
                check_connect = 0
                resp = ftp.CONT("".join(received_data_decoded), 21)
        # USER
        elif received_proto == FTPCmd.USER.value:
            if check_connect == 1:
                resp = "Please input FTP connect first."
            else:
                resp = ftp.USER("".join(received_data_decoded))
        # PASS
        elif received_proto == FTPCmd.PASS.value:
            if check_connect == 1:
                resp = "Please input FTP connect first."
            else:
                resp = ftp.PASS("".join(received_data_decoded))
        # PWD
        elif received_proto == FTPCmd.PWD.value:
            if check_connect == 1:
                resp = "Please input FTP connect first."
            else:
                resp = ftp.PWD()
        # CWD
        elif received_proto == FTPCmd.CWD.value:
            if check_connect == 1:
                resp = "Please input FTP connect first."
            else:
                resp = ftp.CWD("".join(received_data_decoded))
        # PASV
        elif received_proto == FTPCmd.PASV.value:
            if check_connect == 1:
                resp = "Please input FTP connect first."
            else:
                resp = ftp.PASV()
        # LIST
        elif received_proto == FTPCmd.LIST.value:
            if check_connect == 1:
                resp = "Please input FTP connect first."
            else:
                resp = ftp.LIST("".join(received_data_decoded))
        # RETR
        elif received_proto == FTPCmd.RETR.value:
            paths = copy.deepcopy("".join(received_data_decoded))
            path_list = paths.strip().split()
            if check_connect == 1:
                resp = "Please input FTP connect first."
            else:
                if len(path_list) == 1:
                    relay_file_path += path_list[0]
                    resp = ftp.RETR(path_list[0], relay_file_path)
                elif len(path_list) == 2:
                    relay_file_path += path_list[1]
                    resp = ftp.RETR(path_list[0], relay_file_path)
        # QUIT
        elif received_proto == FTPCmd.QUIT.value:
            if check_connect == 1:
                resp = "Please input FTP connect first."
            else:
                resp = ftp.QUIT()
                break
        # Retry
        else:
            resp = "Invalid command."

        # Display info response from FTP and send it back to Node 1
        print("{:<40}".format("".join(resp)))
        transmitter.send("192.168.1.1", 8888, generateSplitBinData(resp), cmd_id, FTPCmd.RET, type=0)
            
        # Send file response from FTP to Node 1, if the command is downloading file
        if received_proto == FTPCmd.RETR.value and resp[:3] != "550":
            data_bit_size = os.path.getsize(relay_file_path) * 8
            bit_stream = ConstBitStream(filename=relay_file_path)
            data_str = bit_stream.read(data_bit_size)
            file_data = np.array(list(data_str), dtype=np.uint8)
            transmitter.send("192.168.1.1", 8888, generateSplitBinData(file_data), cmd_id, FTPCmd.RET, type=1)
            if os.path.exists(relay_file_path) and os.path.isfile(relay_file_path):
                try:
                    os.remove(relay_file_path)
                except Exception:
                    pass

        # Okay to receive next command
        transmitter_ack.send("192.168.1.1", 8888, generateSplitBinData(""), cmd_id, FTPCmd.RET, type=2)

        cmd_id += 1

    # For QUIT
    print("{:<40}".format("".join(resp)))
    transmitter.send("192.168.1.1", 8888, generateSplitBinData(resp), cmd_id, FTPCmd.RET, type=0)


if __name__ == "__main__":
    part1()
