import os
import argparse
import socket
import struct
import select
import time
import copy
import numpy as np
from utils import *


ICMP_ECHO_REQUEST = 8 # Platform specific
DEFAULT_TIMEOUT = 1
DEFAULT_COUNT = 1


class Pinger(object):
    """ Pings to a host -- the Pythonic way"""

    def __init__(self, target_host, count=DEFAULT_COUNT, timeout=DEFAULT_TIMEOUT):
        self.target_host = target_host
        self.count = count
        self.timeout = timeout
        self.addr = "192.168.1.1"
        self.port = 8888
        self.delay = 0.0

    def receive_pong(self, sock, ID, timeout):
        """
        Receive ping from the socket.
        """
        time_remaining = timeout
        while True:
            start_time = time.time()
            readable = select.select([sock], [], [], time_remaining)
            time_spent = (time.time() - start_time)
            if readable[0] == []: # Timeout
                return None

            time_received = time.time()
            recv_packet, addr = sock.recvfrom(1024)
            self.addr = addr[0]
            self.port = addr[1]
            #print(self.addr)
            icmp_header = recv_packet[20:28]
            type, code, checksum, packet_ID, sequence = struct.unpack("bbHHh", icmp_header)
            if packet_ID == ID:
                bytes_In_double = struct.calcsize("d")
                time_sent = struct.unpack("d", recv_packet[28:28 + bytes_In_double])[0]
                return time_received - time_sent

            time_remaining = time_remaining - time_spent
            if time_remaining <= 0:
                return None

    def send_ping(self, sock, ID):
        """
        Send ping to the target host
        """
        target_addr = socket.gethostbyname(self.target_host)
        packet = generateICMP(ICMP_ECHO_REQUEST, self.target_host, ID)
        sock.sendto(packet, (target_addr, 1))

    def ping_once(self):
        """
        Returns the delay (in seconds) or none on timeout.
        """
        icmp = socket.getprotobyname("icmp")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        except socket.error as e:
            if e.errno == 1:
                # Not superuser, so operation not permitted
                e.msg += "ICMP messages can only be sent from root user processes"
                raise socket.error(e.msg)
        except Exception as e:
            print("Exception: %s" %(e))

        my_ID = os.getpid() & 0xFFFF

        self.send_ping(sock, my_ID)
        delay = self.receive_pong(sock, my_ID, self.timeout)
        sock.close()
        self.delay = delay
        return delay

    def ping(self):
        """
        Run the ping process
        """
        for i in range(self.count):
            print("Ping to %s..." % self.target_host,)
            try:
                delay = self.ping_once()
            except socket.gaieror as e:
                print("Ping failed. (socket error: '%s')" % e[1])
                break

            if delay == None:
                print("Ping failed. (timeout within %ssec.)" % self.timeout)
            else:
                self.delay = self.delay * 1000
                print("Get pong from", self.addr, "in %0.4fms" % self.delay)

        return delay, self.addr, self.port


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Python ping')
    parser.add_argument('host', action="store", help=u'主机名')
    given_args = parser.parse_args()
    target_host = given_args.host
    pinger = Pinger(target_host=target_host)
    pinger.ping()
