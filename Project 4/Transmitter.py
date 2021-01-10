import copy
import threading
import numpy as np
from tqdm import tqdm
import sounddevice as sd
from utils import *


class Transmitter:
    def __init__(self, config):
        self.fs = config.fs
        self.fc = config.fc
        self.id_length = config.id_length
        self.seq_num_length = config.seq_num_length
        self.total_seq_length = config.total_seq_length
        self.type_length = config.type_length
        self.data_cnt_length = config.data_cnt_length
        self.ip_length = config.ip_length
        self.port_length = config.port_length
        self.proto_length = config.proto_length
        self.header_length = config.header_length
        self.data_per_frame = config.DATA_PER_FRAME
        self.preamble_wave = config.preamble_wave
        self.carrier_wave = config.carrier_wave
        self.audio_out = config.audio_out
        self.crc_length = config.crc_length
        self.wave_length_per_bit = config.wave_length_per_bit
        self.frame_length = None
        self.robustness = config.robustness
        self.ostream = sd.OutputStream(samplerate=self.fs, channels=1, latency="low")
        # self.ostream.start()

    def addHeaderAndPadding(self, cmd_id, cmd_val, seq, total_seq, type, frame, ip='192.168.1.2', port=8888):
        last_set = 0
        new_frame = np.zeros((self.header_length + self.data_per_frame), dtype=np.uint8)
        new_frame[last_set:last_set+self.id_length] = dec2arr(cmd_id, self.id_length); last_set += self.id_length
        new_frame[last_set:last_set+self.seq_num_length] = dec2arr(seq, self.seq_num_length); last_set += self.seq_num_length
        new_frame[last_set:last_set + self.total_seq_length] = dec2arr(total_seq, self.total_seq_length); last_set += self.total_seq_length
        new_frame[last_set:last_set + self.type_length] = dec2arr(type, self.type_length); last_set += self.type_length
        new_frame[last_set:last_set+self.data_cnt_length] = dec2arr(frame.size, self.data_cnt_length); last_set += self.data_cnt_length
        new_frame[last_set:last_set+self.ip_length] = ip2arr(ip); last_set += self.ip_length;
        new_frame[last_set:last_set+self.port_length] = dec2arr(port, self.port_length); last_set += self.port_length
        new_frame[last_set:last_set+self.proto_length] = dec2arr(cmd_val, self.proto_length)
        new_frame[self.header_length:self.header_length+frame.size] = copy.deepcopy(frame)
        new_frame[self.header_length+frame.size:] = 0
        new_frame[self.header_length+frame.size::2] = 1
        return new_frame

    def addCRC(self, frame):
        ''' Add crc-8 at the tail, calculated from header+frame_data '''
        new_frame = np.zeros((frame.size + self.crc_length), dtype=np.uint8)
        new_frame[:frame.size] = copy.deepcopy(frame)
        new_frame[frame.size:] = dec2arr(int(generateCRC(frame, mode='crc-'+str(self.crc_length)), 16), self.crc_length)
        return new_frame

    def modulate(self, frame):
        frame_wave = np.zeros((frame.size * self.wave_length_per_bit))
        for i in range(frame.size):
            frame_wave[self.wave_length_per_bit*i : self.wave_length_per_bit*(i+1)] = \
                self.carrier_wave[self.wave_length_per_bit*i : self.wave_length_per_bit*(i+1)] * (frame[i] * 2 - 1)
        return frame_wave

    def makeSound(self, wave):
        print("Athernet Sending...       ", end='\r')
        self.ostream.write(wave)
        print("Athernet Sending Finished.", end='\r')

    def pack(self, cmd_id, cmd, i, length, type, frame, ip, port, buffer):
        random_wave = self.modulate(np.random.rand(50))
        header_frame = self.addHeaderAndPadding(cmd_id, cmd.value, i, length, type, frame, ip, port)
        header_frame_crc = self.addCRC(header_frame)
        frame_wave = self.modulate(header_frame_crc)
        part_wave = np.concatenate((random_wave, self.preamble_wave, frame_wave), axis=0)
        buffer[i] = part_wave

    def send(self, ip, port, data, cmd_id, cmd, type):
        self.ostream.start()
        whole_wave = np.array([])
        thread_pool = []
        pack_pool = [None] * len(data)

        # Create modulating threads
        prepare_bar = tqdm(data, desc="Preparing", leave=False)
        for i, frame in enumerate(prepare_bar):
            t = threading.Thread(target=self.pack, args=(cmd_id, cmd, i, len(data), type, frame, ip, port, pack_pool))
            thread_pool.append(t)
            t.start()

        # Waiting for modulating
        modulate_bar = tqdm(thread_pool, desc="Modulating", leave=False)
        for i, t in enumerate(modulate_bar):
            t.join()
            whole_wave = np.concatenate((whole_wave, pack_pool[i]), axis=0)

        random_wave = self.modulate(np.random.rand(50))

        # Add beginning and ending noise
        whole_wave = np.tile(whole_wave, self.robustness)
        whole_wave = np.concatenate((random_wave.repeat(10), whole_wave), axis=0)
        whole_wave = np.concatenate((whole_wave, random_wave.repeat(10)), axis=0)

        if self.audio_out:
            self.makeSound(whole_wave.astype(np.float32))
        send_time = time.time()

        self.ostream.stop()
        return whole_wave, send_time

    def __del__(self):
        self.ostream.close()
