import copy
import numpy as np
import sounddevice as sd
from utils import *


class Receiver:
    def __init__(self, config, debug_data=None):
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
        self.data = debug_data
        self.packet_wo_crc_length = self.header_length + self.data_per_frame
        self.packet_length = self.packet_wo_crc_length + self.crc_length

    def listen(self):
        print("Listening...")
        recording = sd.rec(int(self.receive_time * self.fs), samplerate=self.fs, channels=1)
        status = sd.wait()
        print("Listening Finished.")

        # sd.play(recording)
        # status = sd.wait()

        recording = recording.reshape((recording.size))
        return recording

    def packetSync(self):
        pass

    def decode(self):
        pass

    def checkCRC(self):
        pass

    def receive(self):
        if self.audio_in:
            processing_data = self.listen()
        else:
            processing_data = self.data

        state = 0       # 0 for searching preamble(packet sync), 1 for decoding
        power = 0
        pre_header_index = 0
        sync_power_local_max = 0
        sync_power_sum = np.zeros(processing_data.shape)
        sync_wave_FIFO = np.zeros(self.wave_length_per_bit * 10)
        decode_wave_FIFO = np.array([])
        correct_frame_num = 0
        total_frame_num = 0
        decoded_data = np.array([], dtype=np.uint8)

        output_string = ""

        i = 0
        residue_num = 0

        while i < processing_data.size:
            current_sample = processing_data[i]
            power = power * (1 - 1/64) + current_sample ** 2 / 64

            if state == 0:
                # Packet Sync, search preamble
                sync_wave_FIFO = np.concatenate((sync_wave_FIFO[1:], np.array([current_sample])), axis=0)
                sync_power_sum[i] = np.sum(sync_wave_FIFO * self.preamble_wave, initial=0) / 120            # Correlation

                # Find local max which might be the "true" header start
                if (sync_power_sum[i] > power * 2) and (sync_power_sum[i] > sync_power_local_max) and (sync_power_sum[i] > 0.05):
                    sync_power_local_max = sync_power_sum[i]
                    pre_header_index = i
                # If no new local max is found with 200 wave bits, then recognize it as the true header start
                elif (i - pre_header_index > 150) and (pre_header_index != 0):
                    sync_power_local_max = 0
                    sync_wave_FIFO = np.zeros(self.wave_length_per_bit * 10)
                    state = 1
                    decode_wave_FIFO = processing_data[pre_header_index+1:i]

                i += 1
            else:
                # Preamble found, add data into the decode FIFO
                residue_num = self.wave_length_per_bit * self.packet_length - decode_wave_FIFO.size
                decode_wave_FIFO = np.concatenate((decode_wave_FIFO, np.array(processing_data[i:i+residue_num])), axis=0)
                # decode_wave_FIFO = np.concatenate((decode_wave_FIFO, np.array([current_sample])), axis=0)

                # If FIFO length equals the length of data after modulation
                if decode_wave_FIFO.size == self.wave_length_per_bit * self.packet_length:
                    total_frame_num += 1

                    # decode
                    decode_FIFO_remove_carrier = smooth(decode_wave_FIFO * self.carrier_wave[:decode_wave_FIFO.size], 5)
                    decode_FIFO_power_bit = np.zeros(self.packet_length)
                    for j in range(self.packet_length):
                        decode_FIFO_power_bit[j] = np.sum(decode_FIFO_remove_carrier[8+j*self.wave_length_per_bit:28+j*self.wave_length_per_bit])
                    decode_FIFO_power_bit = (decode_FIFO_power_bit > 0).astype(np.uint8)
                    output_string += arr2str(decode_FIFO_power_bit[self.header_length:self.packet_wo_crc_length])

                    # # crc check
                    # crc_check = generateCRC(decode_FIFO_power_bit[:self.packet_wo_crc_length], mode='crc-'+str(self.crc_length))
                    # if not (dec2arr(int(crc_check, 16), self.crc_length) == decode_FIFO_power_bit[self.packet_wo_crc_length:]).all():
                    #     print("Crc check ERROR", "\t", dec2arr(int(crc_check, 16), self.crc_length), "\t", decode_FIFO_power_bit[self.packet_wo_crc_length:])
                    # else:
                    #     temp_index = 0
                    #     for k in range(self.header_length):
                    #         print(decode_FIFO_power_bit[k], end='')
                    #         temp_index = temp_index + decode_FIFO_power_bit[k] * (2 ** (self.header_length - k - 1))
                    #     print("\t correct, ID:", temp_index)
                    #     correct_frame_num = correct_frame_num + 1
                    decoded_data = np.concatenate((decoded_data, decode_FIFO_power_bit[self.header_length:self.packet_wo_crc_length]), axis=0)

                    # Ready to search the next preamble
                    pre_header_index = 0
                    decode_wave_FIFO = np.array([])
                    state = 0

                i += residue_num

        print("Total Frame Received:", total_frame_num)
        print("CRC Correct Frame Num:", correct_frame_num)

        output_file = open("outputs/OUTPUT.txt", "w")
        output_file.write(output_string)
        output_file.close()

        return decoded_data
