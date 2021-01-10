import time
import random
import socket


class Client:
    def __init__(self, send_ip, send_port):
        self.ip_port = (send_ip, send_port)
        self.sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)

    def generateRandom(self):
        data = ""
        for _ in range(20):
            data += str(random.randrange(0, 10))
        print(data)
        return data.encode()

    def send(self, data):
        for line in data:
            self.sk.sendto(line.encode(), self.ip_port)

    def __del__(self):
        self.sk.sendto("exit".encode(), self.ip_port)
        self.sk.close()

