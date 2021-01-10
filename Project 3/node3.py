import os
import sys
import numpy as np

from utils import *
from Client import Client
from Server import Server


def part1():
    pass


def part2ck1():
    server = Server("10.20.236.135", 9999)       # Node 3 IP
    all_lines, addr, port = server.receive()
    with open('./outputs/OUTPUT.txt', 'w+') as f:
        for line in all_lines:
            f.write(line)


def part2ck2():
    # Set path
    input_file_path = "inputs/INPUT.txt"
    client = Client("10.20.238.233", 9999)       # Node 2 IP
    # Read data
    data = []
    with open(input_file_path) as f:
        for line in f:
            data.append(line)
    client.send(data)


part2ck1()
part2ck2()
