import socket


class Server:
    def __init__(self, server_ip, port):
        self.ip_port = (server_ip, port)
        self.sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.sk.bind(self.ip_port)

    def receive(self):
        all_lines = []
        print("Server listening...")
        while True:
            raw_data, addr = self.sk.recvfrom(1024)
            data = raw_data.decode()
            if data == "exit":
                print("Exit.")
                break
            print("Data:", data, "IP:", addr[0], "Port:", addr[1], "Payload:", len(data))
            all_lines.append(data)
        return all_lines, addr[0], addr[1]

    def __del__(self):
        self.sk.close()
