import socket
from header import Header
import multiprocessing
from lib import logClient, setupLogging
from config import *
from threading import Timer
import threading
import time


class Client:
    def __init__(self, serv_addr='127.0.0.1', serv_port=8000):
        self.sock = socket.socket(family=socket.AF_INET,
                                  type=socket.SOCK_DGRAM)

        self.buf_size = 1024
        self.server_loc = (serv_addr, serv_port)
        self.message = ''
        self.client_ip = None
        self.client_port = None

        self.SEQ_NO = 0
        self.ACK_NO = 1

        self.recv_proc = multiprocessing.Process(
            target=self.receive)

        # Dont start a send unless there is something to send

    def send(self, data=b'Hello, there', connect=False, ACK=False):
        flags = b'\x00'
        if connect:
            flags = bytes([flags[0] | SYN_FLAG[0]])
        if ACK:
            flags = bytes([flags[0] | ACK_FLAG[0]])

        if not connect:
            self.SEQ_NO += len(data)

        req = Header(FLAGS=flags, SEQ=self.SEQ_NO).return_header()+data
        self.sock.settimeout(SOCKET_TIMEOUT)
        self.sock.sendto(req, self.server_loc)

    def receive(self):
        count = 0
        while(True):
            self.sock.settimeout(SOCKET_TIMEOUT)
            self.sock.setblocking(1)
            message = self.sock.recv(self.buf_size)

            self.message, *_ = self.strip_header(message)
            self.ACK_NO += 1
            logClient(f"Receiving Packet #:{self.ACK_NO} from server")

    def strip_header(self, pack):
        # network = big endian
        ACK_NO = int.from_bytes(pack[0:4], byteorder='big')
        SEQ_NO = int.from_bytes(pack[4:8], byteorder='big')
        FLAGS = bytes([pack[8]])
        rwnd_size = int.from_bytes(pack[9:13], byteorder='big', signed=True)
        data = pack[13:]

        return data, ACK_NO, SEQ_NO, FLAGS, rwnd_size

    def initialize_connection(self):
        fails = 0
        while True:
            if fails == 3:
                logClient(f"Failed to connect {fails} times. Giving up.")
                exit(1)

            logClient(f"Sending a connect request to server {self.server_loc}")
            self.send(data=b"", connect=True, ACK=False)
            try:
                self.sock.settimeout(SOCKET_TIMEOUT)
                message = self.sock.recv(self.buf_size)
                _, _, SEQ_NO, FLAGS, _ = self.strip_header(message)
            except socket.timeout as e:
                logClient("Timed out expecting ACK")
                fails += 1
                continue

            if bytes([FLAGS[0] & SYNACK_FLAG[0]]) == SYNACK_FLAG:
                logClient(f"Assigning SEQ_NO {SEQ_NO}")
                self.SEQ_NO = SEQ_NO
                logClient(
                    f"Not Sending a connect ACK to server {self.server_loc}")
                # self.send(data=b"", connect=False, ACK=True)
                break
            else:
                logClient("Invalid connect response. Retrtying.")


def run_client():
    client = Client()
    return client


if __name__ == "__main__":
    setupLogging()
    cli = run_client()
    app_client = cli
    client = app_client
    client.recv_proc.start()
    logClient("Client setup")
    client.initialize_connection()
    client.send()
