import os
import sys
import numpy as np
import bitstring
from bitstring import ConstBitStream
import time

from utils import *
from config import Config
from Transmitter import Transmitter
from Receiver import Receiver
from Client import Client


def part1():
    pass


def part2ck1():
    # Set path
    input_file_path = "inputs/INPUT.txt"
    # Load configurations
    config = Config(role=1, proto=0)
    # Read data
    data = []
    with open(input_file_path) as f:
        for line in f:
            binary_line = np.array([])
            for i in line:
                binary = dec2arr(ord(i), 8)
                binary_line = np.concatenate((binary_line, binary), axis=0)
            data.append(binary_line.astype(np.uint8))
    # print(data)
    sent_data = np.array([])
    # Transmitter responsible for sending data
    if config.is_transmitter:
        transmitter = Transmitter(config)
        sent_data, sent_time = transmitter.send("192.168.1.2", 8888, data)


def part2ck2():
    # Load configurations
    config = Config(role=0, proto=0)
    sent_data = np.array([])
    # Receiver responsible for receiving data
    if config.is_receiver:
        receiver = Receiver(config, debug_data=sent_data)
        received_data = decodeData(receiver.receive())
        print(received_data)
        with open('./outputs/OUTPUT.txt', 'w+') as f:
            for line in received_data:
                f.write(line)


def part3ck():
    ICMP_ECHO_REQUEST = 8

    # Load configurations
    config_tran = Config(role=1, proto=1)
    config_tran.TOTAL_FRAMES = 1
    config_tran.robustness = 3
    config_rec = Config(role=0, proto=1)
    config_rec.TOTAL_FRAMES = 1
    config_rec.receive_time = 1

    sent_data = np.array([])
    transmitter = Transmitter(config_tran)
    receiver = Receiver(config_rec)
    for i in range(10):
        packet = generateICMP(ICMP_ECHO_REQUEST, "baidu.com", os.getpid() & 0xFFFF)
        unpacked_packet = struct.unpack_from("bbHHhd", packet)
        packet_str = "".join([str(x) for x in unpacked_packet])
        while len(packet_str) < 32:
            packet_str += "Q"
        data = []
        binary_line = np.array([])
        for i in packet_str:
            binary = dec2arr(ord(i), 8)
            binary_line = np.concatenate((binary_line, binary), axis=0)
        data.append(binary_line.astype(np.uint8))
        # print(data)

        sent_data, sent_time = transmitter.send("192.168.1.2", 8888, data)
        received_data = decodeData(receiver.receive())
        print("Latency: ", time.time()-sent_time)
        # time.sleep(0.0)                 # Sleep argument to offset time spent on sending preparations

# part2ck1()
# part2ck2()
part3ck()
