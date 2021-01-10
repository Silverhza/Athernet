import os
import re
import time
import scipy
import socket
import struct
import numpy as np
import crcmod.predefined
from scipy import integrate
import matplotlib.pyplot as plt
# from bitstring import ConstBitStream


def createRandomData(filepath, datasize):
    np.random.seed()
    file = open(filepath, "w")
    data = np.random.randint(2, size=datasize).tolist()
    # print(data)
    for i in range(datasize):
        file.write(str(data[i]))


def dec2arr(dec_value, length):
    ''' Receive a decimal value and transform to a BINARY numpy ARRAY with size of length '''
    bin_str = bin(dec_value)[2:]
    bin_array = np.zeros(length, dtype=np.int)
    bin_array[length-len(bin_str):length] = np.array(list(bin_str))
    return bin_array


def arr2dec(bin_arr):
    ''' Receive a BINARY numpy ARRAY and transform to a decimal value '''
    dec = 0
    factor = 1
    for i in bin_arr[::-1]:
        dec += i * factor
        factor *= 2
    return dec


def arr2str(arr):
    ''' Receive a BINARY numpy ARRAY and transform to a string with 0s and 1s '''
    string = ''.join([str(x) for x in arr])
    return string


def ip2arr(ip_str):
    result = np.array([])
    for seg in ip_str.split('.'):
        result = np.concatenate((result, dec2arr(int(seg), 8)), axis=0)
    return result


def generateCRC(bin_array, mode='crc-16'):
    ''' Crc of ENCODED 16-based BINARY numpy ARRAY data '''
    crc_func = crcmod.predefined.Crc(mode)
    hexData = hex(int(arr2str(bin_array), 2))[2:]
    crc_func.update(hexData.encode())
    crc_result = hex(crc_func.crcValue)
    return crc_result


def generateCarrierWave(fs, fc):
    one_second = np.linspace(0, 1, fs)
    carrier = np.sin(2 * np.pi * fc * one_second)
    return carrier


def generatePreambleWave(fs, wave_len_per_bit):
    one_second = np.linspace(0, 1, fs)
    preamble = np.append(np.linspace(300, 2100, int(wave_len_per_bit / 2 * 128)), np.linspace(2100, 300, int(wave_len_per_bit / 2 * 128)))
    # There's small difference between scipy's cumtrapz and Matlab's cumtrapz
    omega = 2 * np.pi * scipy.integrate.cumtrapz(preamble, one_second[:int(wave_len_per_bit * 128)], initial=0)
    preamble_wave = np.sin(omega)
    # plt.plot(one_second[:440], preamble_wave)
    # plt.show()
    return preamble_wave


def smooth(arr, span):
    '''
    :param arr: NumPy 1-D array
    :param span: smoothing window size needs, which must be odd number
    :return: Smoothed Numpy 1-D array
    '''
    out0 = np.convolve(arr, np.ones(span, dtype=int), 'valid') / span
    r = np.arange(1, span - 1, 2)
    start = np.cumsum(arr[:span - 1])[::2] / r
    stop = (np.cumsum(arr[:-span:-1])[::2] / r)[::-1]
    return np.concatenate((start, out0, stop))


def do_checksum(source_string):
    """  Verify the packet integrity """
    sum = 0
    max_count = (len(source_string)/2)*2
    count = 0
    while count < max_count:
        val = source_string[count + 1]*256 + source_string[count]
        sum = sum + val
        sum = sum & 0xffffffff
        count = count + 2

    if max_count < len(source_string):
        sum = sum + ord(source_string[len(source_string) - 1])
        sum = sum & 0xffffffff

    sum = (sum >> 16)  +  (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def generateICMP(ICMP_ECHO, target_host, ID):
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


def arrDiff(a, b):
    '''
    :param a: NumPy 1-D array
    :param b: NumPy 1-D array
    :return: None, output eh correct rate
    '''
    correct_num = np.sum(a == b)
    print("Correct Rate: ", correct_num / a.size * 100, "%", sep='')


def fileDiff(a, b):
    '''
    :param a: File path for INPUT file
    :param b: File path for OUTPUT file
    :return: None, output teh correct rate
    '''
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


def decodeData(bin_data):
    decoded_data = []
    for line in bin_data:
        temp_line = ""
        for bin_asc in re.findall(r'.{8}', line):
            dec_asc = int(bin_asc, 2)
            ch = chr(dec_asc)
            temp_line += ch
        decoded_data.append(temp_line)
    return decoded_data