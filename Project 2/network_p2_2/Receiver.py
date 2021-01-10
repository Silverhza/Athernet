import os
import copy
import time
import numpy as np
from bitarray import bitarray

import sounddevice as sd
import threading
from utils import *


class Receiver:
    def __init__(self, config):
        self.fs = config.fs
        self.fc = config.fc
        self.header_length = config.header_length
        self.data_per_frame = config.DATA_PER_FRAME
        self.preamble_wave = config.preamble_wave
        self.carrier_wave = config.carrier_wave
        self.crc_length = config.crc_length
        self.wave_length_per_bit = config.wave_length_per_bit
        self.receive_time = config.receive_time
        self.audio_in = config.audio_in
        self.packet_wo_crc_length = self.header_length + self.data_per_frame
        self.packet_length = self.packet_wo_crc_length + self.crc_length
        self.buffer = np.array([])
        self.write_string = ""
        self.istream = sd.InputStream(samplerate=self.fs, channels=1, latency="low")
        self.istream.start()

    def listen(self):
        print("Listening...")
        i = 0

        # self.istream.start()
        for _ in range(self.receive_time * 10):
            record = self.istream.read(int(self.fs // 10))[0]
            lock = threading.Lock()
            lock.acquire()
            self.buffer = np.append(self.buffer, record)
            lock.release()

        # self.buffer = self.buffer.reshape((self.buffer.size))
        # print(self.buffer.size)
        print("Listening Finished.")
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
            if time.time() - timer > 1:
                self.istream.close()
                print("Link Error!")
                os._exit(-1)

            while i >= self.buffer.size:
                pass

            current_sample = self.buffer[i]
            power = power * (1 - 1 / 64) + current_sample ** 2 / 64

            # Packet Sync, search preamble
            sync_wave_FIFO = np.concatenate((sync_wave_FIFO[1:], np.array([current_sample])), axis=0)
            # print(current_sample)
            sync_power_sum[i] = np.sum(sync_wave_FIFO * self.preamble_wave, initial=0) / 20  # Correlation

            # Find local max which might be the "true" header start
            # print(sync_power_sum[i], power, sync_power_local_max)
            if (sync_power_sum[i] > power * 2) and (sync_power_sum[i] >= sync_power_local_max) and (
                    sync_power_sum[i] > 1.6):
                sync_power_local_max = sync_power_sum[i]
                pre_header_index = i
            # If no new local max is found with 200 wave bits, then recognize it as the true header start
            elif (i - pre_header_index > 50) and (pre_header_index != 0):
                timer = time.time()
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

        # Preamble found, add data into the decode FIFO
        residue_num = self.wave_length_per_bit * self.packet_length - (i - pre_header_index - 1)
        while (self.buffer.size-i <= residue_num and i <= self.buffer.size):
            pass
        decode_wave_FIFO = np.concatenate((self.buffer[pre_header_index+1:i], np.array(self.buffer[i:i + residue_num])), axis=0)
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

        lock = threading.Lock()
        lock.acquire()
        self.write_string += output_string
        lock.release()
        return decoded_data

    def checkCRC(self, decode_FIFO_power_bit):
        crc_check = generateCRC(decode_FIFO_power_bit[:self.packet_wo_crc_length], mode='crc-' + str(self.crc_length))
        if not (dec2arr(int(crc_check, 16), self.crc_length) == decode_FIFO_power_bit[
                                                                self.packet_wo_crc_length:]).all():
            print("Crc check ERROR", "\t", dec2arr(int(crc_check, 16), self.crc_length), "\t",
                  decode_FIFO_power_bit[self.packet_wo_crc_length:])
            return -1
        else:
            temp_index = 0
            for k in range(self.header_length):
                print(decode_FIFO_power_bit[k], end='')
                temp_index = temp_index + decode_FIFO_power_bit[k] * (2 ** (self.header_length - k - 1))
            print("\t correct, ID:", temp_index)
            return temp_index

    def receive(self):
        thread_listen = threading.Thread(target=self.listen)
        thread_listen.start()
        thread_sync = threading.Thread(target=self.packetSync)
        thread_sync.start()

        thread_listen.join()
        thread_sync.join()

        bits = bitarray(self.write_string)
        output_file = open("outputs/OUTPUT.bin", "wb+")
        bits.tofile(output_file)
        output_file.close()

        return self.write_string

    def __del__(self):
        self.istream.close()
