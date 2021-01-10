import os
import sys
import numpy as np
import bitstring
from bitstring import ConstBitStream

from utils import *
from config import Config
from Transmitter import Transmitter
from Receiver import Receiver
from Client import Client
from Server import Server
from Pinger import Pinger


def part1():
    pass


def part2ck1():
    # Load configurations
    config = Config(role=0, proto=0)
    sent_data = np.array([])
    # Receiver responsible for receiving data
    if config.is_receiver:
        receiver = Receiver(config, debug_data=sent_data)
        received_data = decodeData(receiver.receive())
        client = Client("10.20.224.147", 9999)      # Node 3 IP
        client.send(received_data)


def part2ck2():
    server = Server("10.20.208.171", 9999)       # Node 2 IP
    f, node3_ip, node3_port = server.receive()
    config = Config(role=1, proto=0)
    data = []
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
        sent_data, sent_time = transmitter.send(node3_ip, node3_port, data)


def part3ck():
    ICMP_ECHO_REQUEST = 8
    ICMP_ECHO_REPLY = 0

    # Load configurations
    config_tran = Config(role=1, proto=1)
    config_tran.TOTAL_FRAMES = 1
    config_tran.robustness = 3
    config_rec = Config(role=0, proto=1)
    config_rec.TOTAL_FRAMES = 1
    config_rec.receive_time = 1

    sent_data = np.array([])
    receiver = Receiver(config_rec, debug_data=sent_data)
    transmitter = Transmitter(config_tran)
    for i in range(10):
        received_data = decodeData(receiver.receive())
        pinger = Pinger(target_host="baidu.com")
        internet_delay, addr, port = pinger.ping()

        packet = generateICMP(ICMP_ECHO_REPLY, addr, os.getpid() & 0xFFFF)
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

        sent_data, sent_time = transmitter.send(addr, port, data)
        # time.sleep(1)


# part2ck1()
# part2ck2()
part3ck()
