import numpy as np
import threading

from Receiver import Receiver
from Transmitter import Transmitter
from utils import *


class Node(Receiver, Transmitter):
    def __init__(self, role, config):
        self.role = role
        self.mainFunc = None
        Receiver.__init__(self, config)
        Transmitter.__init__(self, config)

    def run(self):
        if self.role == "Transmitter":
            self.mainFunc = self.trySend
        elif self.role == "Receiver":
            self.mainFunc = self.tryReceive
        else:
            raise AssertionError("WRONG ROLE!")

    def trySend(self, data):
        thread_receive = threading.Thread(target=self.receive)
        thread_receive.start()
        frame_num = data.shape[0]

        i = 0
        while i < frame_num:
            self.send(np.array([data[i]]))
            if self.checkAck():
                i += 1

        thread_receive.join()

    def tryReceive(self, data):
        thread_receive = threading.Thread(target=self.receive)
        thread_receive.start()
        frame_num = data.shape[0]

        i = 0
        while i < frame_num:
            self.send(np.array([data[i]]))
            if self.checkAck():
                i += 1

        thread_receive.join()

    def sendAck(self, id):
        random_wave = self.modulate(np.random.rand(50))
        random_data_wave = self.modulate(np.random.rand(490))
        id_wave = self.modulate(dec2arr(id, 10))
        ack_wave = np.concatenate((random_wave, self.preamble_wave, random_data_wave, id_wave), axis=0)

        return ack_wave

    def checkAck(self):
        return True
