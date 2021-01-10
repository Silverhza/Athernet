import os
import re
import time
import copy
import scipy
import socket
import struct
from typing import List, Tuple
import numpy as np
import crcmod.predefined
from scipy import integrate
import matplotlib.pyplot as plt
from bitstring import ConstBitStream


def createRandomData(filepath: str, datasize: int) -> None:
    """ Create random data of size DATASIZE and store it in FILEPATH """
    np.random.seed()
    file = open(filepath, "w")
    data = np.random.randint(2, size=datasize).tolist()
    # print(data)
    for i in range(datasize):
        file.write(str(data[i]))


def dec2arr(dec_value: int, length: int) -> np.ndarray:
    """ Receive a decimal DEC_VALUE and transform it to a binary ndarray with size of LENGTH """
    bin_str = bin(dec_value)[2:]
    # print(bin_str)
    bin_array = np.zeros(length, dtype=np.int)
    bin_array[length-len(bin_str):length] = np.array(list(bin_str))
    return bin_array


def arr2dec(bin_arr: np.ndarray) -> int:
    """ Receive a binary ndarray BIN_ARR and transform to a decimal value """
    dec = 0
    factor = 1
    for i in bin_arr[::-1]:
        dec += i * factor
        factor *= 2
    return dec


def arr2str(bin_arr: np.ndarray) -> str:
    """ Receive a binary ndarray BIN_ARR and transform it to a binary string """
    string = ''.join([str(x) for x in bin_arr])
    return string


def ip2arr(ip_str: str) -> np.ndarray:
    """ Receive a string of IP address and transform it to a binary ndarray """
    result = np.array([])
    for seg in ip_str.split('.'):
        result = np.concatenate((result, dec2arr(int(seg), 8)), axis=0)
    return result


def generateSplitBinData(raw_data) -> List[np.ndarray]:
    """ Receive a string or a ndarray of RAW_DATA, split it according to a fixed size """
    bin_data_list = []
    raw_copy = copy.deepcopy(raw_data)

    if isinstance(raw_data, str):
        str_data_list = []
        while len(raw_copy) > 40:
            str_data_list.append(raw_copy[:40])
            raw_copy = raw_copy[40:]
        else:
            str_data_list.append(raw_copy)

        for line in str_data_list:
            binary_line = np.array([])
            for i in line:
                binary = dec2arr(ord(i), 8)
                binary_line = np.concatenate((binary_line, binary), axis=0)
            bin_data_list.append(binary_line.astype(np.uint8))
    elif isinstance(raw_data, np.ndarray):
        raw_copy = raw_copy.reshape((-1, ))
        while raw_copy.size > 40:
            bin_data_list.append(raw_copy[:40])
            raw_copy = raw_copy[40:]
        else:
            bin_data_list.append(raw_copy)
    else:
        raise AssertionError("Unsupported data type to split!")

    return bin_data_list


def generateCRC(bin_arr: np.ndarray, mode: str = 'crc-16') -> str:
    """ Calculate crc with given MODE of an encoded 16-based binary ndarray BIN_ARR """
    crc_func = crcmod.predefined.Crc(mode)
    hexData = hex(int(arr2str(bin_arr), 2))[2:]
    crc_func.update(hexData.encode())
    crc_result = hex(crc_func.crcValue)
    return crc_result


def generateCarrierWave(fs: int, fc: int) -> np.ndarray:
    """ Generate carrier wave with given FS and FC """
    one_second = np.linspace(0, 1, fs)
    carrier = np.sin(2 * np.pi * fc * one_second)
    return carrier


def generatePreambleWave(fs: int, wave_len_per_bit: int) -> np.ndarray:
    """ Generate carrier wave with given FS and WAVE_LEN_PER_BIT """
    one_second = np.linspace(0, 1, fs)
    preamble = np.append(np.linspace(300, 2100, int(wave_len_per_bit / 2 * 128)), np.linspace(2100, 300, int(wave_len_per_bit / 2 * 128)))
    # There's small difference between scipy's cumtrapz and Matlab's cumtrapz
    omega = 2 * np.pi * scipy.integrate.cumtrapz(preamble, one_second[:int(wave_len_per_bit * 128)], initial=0)
    preamble_wave = np.sin(omega)
    # plt.plot(one_second[:440], preamble_wave)
    # plt.show()
    return preamble_wave


def smooth(arr: np.ndarray, span: int) -> np.ndarray:
    """ Smooth the ndarray ARR with the given window size SPAN """
    out0 = np.convolve(arr, np.ones(span, dtype=int), 'valid') / span
    r = np.arange(1, span - 1, 2)
    start = np.cumsum(arr[:span - 1])[::2] / r
    stop = (np.cumsum(arr[:-span:-1])[::2] / r)[::-1]
    return np.concatenate((start, out0, stop))


def do_checksum(source_string: bytes) -> int:
    """ Verify the packet integrity with SOURCE_STRING """
    sum = 0
    max_count = (len(source_string) / 2) * 2
    count = 0
    while count < max_count:
        val = source_string[count + 1] * 256 + source_string[count]
        sum = sum + val
        sum = sum & 0xffffffff
        count = count + 2

    if max_count < len(source_string):
        sum = sum + ord(source_string[len(source_string) - 1])
        sum = sum & 0xffffffff

    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def generateICMP(ICMP_ECHO: int, target_host: str, ID: int) -> bytes:
    """ Gnenrate ICMP packet with ICMP_ECHO type, TARGET_HOST, ID """
    target_addr = socket.gethostbyname(target_host)
    my_checksum = 0
    # Create a dummy heder with a 0 checksum.
    header = struct.pack("bbHHh", ICMP_ECHO, 0, my_checksum, ID, 1)
    bytes_In_double = struct.calcsize("d")
    data = (192 - bytes_In_double) * "Q"
    data = struct.pack("d", time.time()) + bytes(data.encode('utf-8'))
    # Get the checksum on the data and the dummy header.
    my_checksum = do_checksum(header + data)
    header = struct.pack(
        "bbHHh", ICMP_ECHO, 0, socket.htons(my_checksum), ID, 1
    )
    packet = header + data
    return packet


def arrDiff(a: np.ndarray, b: np.ndarray) -> None:
    """ Output the correct rate between two ndarrays A and B """
    correct_num = np.sum(a == b)
    print("Correct Rate: ", correct_num / a.size * 100, "%", sep='')


def fileDiff(a: np.ndarray, b: np.ndarray) -> None:
    """ Output the correct rate between two binary files A and B """
    print("Diffing...")
    input_size, output_size = os.path.getsize(a) * 8, os.path.getsize(b) * 8
    if output_size <= 0:
        print(">> OUTPUT.bin is EMPTY, Accuracy: 0%")
        return
    elif output_size < input_size:
        print(">> Partial Data Received, received: ", output_size)

    compare_size = min(input_size, output_size)
    input_stream, output_stream = ConstBitStream(filename=a), ConstBitStream(filename=b)
    input_bits, output_bits = input_stream.read(compare_size), output_stream.read(compare_size)
    input_arr, output_arr = np.array(list(input_bits), dtype=np.uint8), np.array(list(output_bits), dtype=np.uint8)

    correct_num = np.sum(input_arr == output_arr)
    print(">> Received Data Accuracy: ", correct_num / input_arr.size * 100, "%", sep='')


def decodeBinInfoData(bin_data: List[str]) -> List[str]:
    """ Decode information data from BIN_DATA """
    decoded_data = []
    for line in bin_data:
        temp_line = ""
        for bin_asc in re.findall(r'.{8}', line):
            dec_asc = int(bin_asc, 2)
            ch = chr(dec_asc)
            temp_line += ch
        decoded_data.append(temp_line)
    return decoded_data


def decodeBinFileData(bin_data: List[str]) -> str:
    """ Decode file data from BIN_DATA """
    return "".join(bin_data)


def getCmd() -> Tuple[str]:
    """ Parse user's commands """
    while True:
        cmdline = input("ftp> ")
        cmdline = cmdline.strip()
        cmd_stack = cmdline.split()
        if len(cmd_stack) == 0:
            continue

        cmd = cmd_stack[0].upper()

        if cmd == "USER":
            if len(cmd_stack) > 1:
                user = cmd_stack[1]
            else:
                user = "anonymous"
            return cmd, user

        elif cmd == "PASS":
            if len(cmd_stack) > 1:
                passwd = cmd_stack[1]
            else:
                passwd = ""
            return cmd, passwd

        elif cmd == "PWD":
            return (cmd, )

        elif cmd == "CWD":
            if len(cmd_stack) > 1:
                dir = cmd_stack[1]
                return cmd, dir
            else:
                print("You should provide the remote-directory")

        elif cmd == "PASV":
            return (cmd, )

        elif cmd == "LIST":
            if len(cmd_stack) > 1:
                dir = cmd_stack[1]
            else:
                dir = ""
            return cmd, dir

        elif cmd == "RETR":
            if len(cmd_stack) == 2:
                remote_file = cmd_stack[1]
                return cmd, remote_file
            elif len(cmd_stack) == 3:
                remote_file = cmd_stack[1]
                local_file = cmd_stack[2]
                return cmd, remote_file + " " + local_file
            else:
                print("You should provide the remote-file (and maybe local-file)")

        elif cmd == "QUIT":
            return (cmd, )

        else:
            print("Wrong Command! Try Again!")
