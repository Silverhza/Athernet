import os
import re
import copy
import time
import numpy as np
from bitarray import bitarray

import sounddevice as sd
import threading
from utils import *


class Receiver:
    def __init__(self, config, debug_data=None):
        self.fs = config.fs
        self.fc = config.fc
        self.id_length = config.id_length
        self.cnt_length = config.cnt_length
        self.ip_length = config.ip_length
        self.port_length = config.port_length
        self.header_length = config.header_length
        self.data_per_frame = config.DATA_PER_FRAME
        self.frame_num = config.TOTAL_FRAMES
        self.preamble_wave = config.preamble_wave
        self.carrier_wave = config.carrier_wave
        self.crc_length = config.crc_length
        self.wave_length_per_bit = config.wave_length_per_bit
        self.receive_time = config.receive_time
        self.audio_in = config.audio_in
        self.packet_wo_crc_length = self.header_length + self.data_per_frame
        self.packet_length = self.packet_wo_crc_length + self.crc_length
        self.debug_data = debug_data
        self.audio_buffer = np.array([])
        self.data_bit_map = np.zeros((self.frame_num,), dtype=np.uint8)
        self.data_buffer = [""] * self.frame_num
        # self.write_string = ""
        self.proto = config.proto
        self.istream = sd.InputStream(samplerate=self.fs, channels=1, latency="low")
        self.stream_lock = threading.Lock()
        self.audio_buffer_lock = threading.Lock()
        # self.istream = sd.Stream(samplerate=self.fs, channels=1, latency="low")
        # self.istream.start()

    def listen(self):
        print("Athernet Listening...")

        # self.istream.start()
        for _ in range(self.receive_time * 10):
            self.stream_lock.acquire()
            if self.istream.stopped or self.istream.closed:
                print("Athernet Listening Finished.")
                self.stream_lock.release()
                return None
            record = self.istream.read(int(self.fs // 10))[0]
            self.stream_lock.release()

            self.audio_buffer_lock.acquire()
            self.audio_buffer = np.append(self.audio_buffer, record)
            self.audio_buffer_lock.release()

        # self.audio_buffer = self.audio_buffer.reshape((self.audio_buffer.size))
        # print(self.audio_buffer.size)
        print("Athernet Listening Finished.")
        return None

    def packetSync(self):
        power = 0
        timer = time.time()
        pre_header_index = 0
        sync_power_local_max = 0
        sync_power_sum = np.ones(self.fs * self.receive_time)
        sync_wave_FIFO = np.zeros(self.wave_length_per_bit * 128)

        i = 0
        while i < self.fs * self.receive_time:
            if self.istream.stopped or self.istream.closed:
                return
            # if time.time() - timer > 1:
            #     self.istream.close()
            #     print("Link Error!")
            #     os._exit(-1)

            while i >= self.audio_buffer.size:
                if self.istream.stopped or self.istream.closed:
                    return

            current_sample = self.audio_buffer[i]
            power = power * (1 - 1 / 64) + current_sample ** 2 / 64

            # Packet Sync, search preamble
            sync_wave_FIFO = np.concatenate((sync_wave_FIFO[1:], np.array([current_sample])), axis=0)
            # print(current_sample)
            sync_power_sum[i] = np.sum(sync_wave_FIFO * self.preamble_wave, initial=0) / 120  # Correlation

            # Find local max which might be the "true" header start
            # print(sync_power_sum[i], power, sync_power_local_max)
            if (sync_power_sum[i] > power * 2) and (sync_power_sum[i] >= sync_power_local_max) and (
                    sync_power_sum[i] > 0.5):
                sync_power_local_max = sync_power_sum[i]
                pre_header_index = i
            # If no new local max is found with 200 wave bits, then recognize it as the true header start
            elif (i - pre_header_index > 50) and (pre_header_index != 0):
                # timer = time.time()
                # if self.proto == 1:
                #     self.stream_lock.acquire()
                #     self.istream.stop()
                #     self.stream_lock.release()
                #     return

                sync_power_local_max = 0
                sync_wave_FIFO = np.zeros(self.wave_length_per_bit * 128)
                thread_decode = threading.Thread(target=self.decode, args=(pre_header_index, i))
                thread_decode.start()
                thread_decode.join()
                i += self.wave_length_per_bit * self.packet_length - (i - pre_header_index - 1)
                pre_header_index = 0
            i += 1
                # print(i)

        return None

    def decode(self, pre_header_index, i):
        decoded_data = np.array([], dtype=np.uint8)
        output_string = ""
        timer = time.time()

        # Preamble found, add data into the decode FIFO
        residue_num = self.wave_length_per_bit * self.packet_length - (i - pre_header_index - 1)
        while self.audio_buffer.size-i <= residue_num and i <= self.audio_buffer.size:
            if self.istream.stopped or self.istream.closed:
                return
            # if time.time() - timer > 1:
            #     self.istream.close()
            #     print("Link Error!")
            #     os._exit(-1)

        decode_wave_FIFO = np.concatenate((self.audio_buffer[pre_header_index+1:i], np.array(self.audio_buffer[i:i + residue_num])), axis=0)
        # decode_wave_FIFO = np.concatenate((decode_wave_FIFO, np.array([current_sample])), axis=0)

        # If FIFO length equals the length of data after modulation
        if decode_wave_FIFO.size == self.wave_length_per_bit * self.packet_length:
            # decode
            decode_FIFO_remove_carrier = smooth(decode_wave_FIFO * self.carrier_wave[:decode_wave_FIFO.size], 5)
            decode_FIFO_power_bit = np.zeros(self.packet_length)
            for j in range(self.packet_length):
                decode_FIFO_power_bit[j] = np.sum(
                    decode_FIFO_remove_carrier[1+j*self.wave_length_per_bit : 4+j*self.wave_length_per_bit])
            decode_FIFO_power_bit = (decode_FIFO_power_bit > 0).astype(np.uint8)
            output_string += arr2str(decode_FIFO_power_bit[self.header_length:self.packet_wo_crc_length])

            # crc check
            id = self.checkCRC(decode_FIFO_power_bit)

            decoded_data = np.concatenate(
                (decoded_data, decode_FIFO_power_bit[self.header_length:self.packet_wo_crc_length]), axis=0)

        # lock = threading.Lock()
        # lock.acquire()
        # self.write_string += output_string
        # lock.release()
        return decoded_data

    def checkCRC(self, decode_FIFO_power_bit):
        crc_check = generateCRC(decode_FIFO_power_bit[:self.packet_wo_crc_length], mode='crc-' + str(self.crc_length))
        if not (dec2arr(int(crc_check, 16), self.crc_length) == decode_FIFO_power_bit[
                                                                self.packet_wo_crc_length:]).all():
            # print("Crc check ERROR", "\t", dec2arr(int(crc_check, 16), self.crc_length), "\t",
            #       decode_FIFO_power_bit[self.packet_wo_crc_length:])
            return -1
        else:
            index = 0
            for k in range(self.id_length):
                index = index + decode_FIFO_power_bit[k] * (2 ** (self.id_length - k - 1))
            # print("\t", end="")

            count = 0
            for k in range(self.cnt_length):
                count = count + decode_FIFO_power_bit[self.id_length+k] * (2 ** (self.cnt_length - k - 1))

            ip_list = []
            for bin_seg in re.findall(r'.{8}', arr2str(decode_FIFO_power_bit[self.id_length+self.cnt_length:self.id_length+self.cnt_length+self.ip_length])):
                str_seg = str(int(bin_seg, 2))
                ip_list.append(str_seg)
            ip = ".".join(ip_list)

            port = arr2dec(decode_FIFO_power_bit[self.id_length+self.cnt_length+self.ip_length:self.id_length+self.cnt_length+self.ip_length+self.port_length])
            proto = arr2dec(decode_FIFO_power_bit[self.id_length+self.cnt_length+self.ip_length+self.port_length:self.header_length])

            if 0 <= index < self.frame_num and self.data_bit_map[index] != 1:
                print("Correct ID:", index, "\t IP:", ip, "\t port:", port, "\t payload:", count//8, "bytes")
                data_str = arr2str(decode_FIFO_power_bit[self.header_length:self.header_length+count])
                self.data_buffer[index] = data_str
                self.data_bit_map[index] = 1

            if np.sum(self.data_bit_map) == self.frame_num:
                print("All data correctly received!")
                # self.istream.write(np.random.random_sample((self.fs // 10,)))
                if not self.istream.stopped and not self.istream.closed:
                    self.stream_lock.acquire()
                    self.istream.stop()
                    self.stream_lock.release()

            return index

    def receive(self):
        self.audio_buffer = np.array([])
        self.data_bit_map = np.zeros((self.frame_num,), dtype=np.uint8)
        self.data_buffer = [""] * self.frame_num

        self.stream_lock.acquire()
        self.istream.start()
        self.stream_lock.release()

        if self.audio_in:
            thread_listen = threading.Thread(target=self.listen)
            thread_listen.start()
        else:
            self.audio_buffer = self.debug_data

        thread_sync = threading.Thread(target=self.packetSync)
        thread_sync.start()

        if self.audio_in:
            thread_listen.join()

        thread_sync.join()

        # bits = bitarray(self.write_string)
        # output_file = open("outputs/OUTPUT.bin", "wb+")
        # bits.tofile(output_file)
        # output_file.close()

        if self.proto == 0:
            correct_num = 0
            for i in range(self.frame_num):
                if self.data_bit_map[i] == 1:
                    correct_num += 1
                else:
                    print(i, "did not correctly received.")
        # if correct_num == self.frame_num:
        #     print("All data correctly received!")

        if not self.istream.stopped and not self.istream.closed:
            self.stream_lock.acquire()
            self.istream.stop()
            self.stream_lock.release()

        return self.data_buffer

    def __del__(self):
        self.istream.close()
