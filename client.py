import socket
from header import Header
import multiprocessing
from lib import logClient, setupLogging
from config import *
from threading import Timer
import threading
import time
from header import Header, Packet
from collections import deque


class Client:
    def __init__(self, serv_addr='127.0.0.1', serv_port=8000):
        self.sock = socket.socket(family=socket.AF_INET,
                                  type=socket.SOCK_DGRAM)

        self.buf_size = 1024
        self.server_loc = (serv_addr, serv_port)
        self.message = ''
        self.client_ip = None
        self.client_port = None
        self.connectionState: ConnState = ConnState.NO_CONNECT
        self.packet_buffer = deque([])
        self.has_packet_buffer = threading.Event()
        self.ack_packet_fails = 0
        self.SEQ_NO = 0
        self.ACK_NO = 1

        self.process_packet_thread = threading.Thread(
            target=self.processPacketLoop)
        self.process_packet_thread.start()
        self.start()
        self.receiveLoop()

    def start(self):
        logClient("Starting client!")
        initialSynPacket = Packet(Header(1, 1, FLAGS=SYN_FLAG))
        self.connectionState = ConnState.SYN
        self.sock.sendto(initialSynPacket.as_bytes(), self.server_loc)

    def tryConnect(self, packet):
        if self.connectionState is ConnState.NO_CONNECT:  # WTF
            logClient(f"Invalid state: Not connected!")
            exit(1)

        elif self.connectionState is ConnState.SYN:
            if packet.header.has_flag(SYNACK_FLAG):

                self.SEQ_NO = packet.header.SEQ_NO
                self.connectionState = ConnState.SYNACK

                ackPacket = Packet(Header(1, self.SEQ_NO, ACK_FLAG))

                self.sock.sendto(ackPacket.as_bytes(), self.server_loc)
                self.connectionState = ConnState.CONNECTED

                logClient("Connection establisheds")
            else:
                logClient(
                    f"Expecting SYNACK flag at state SYN, got {packet.header.FLAGS}")

    def pushPacketToBuffer(self, packet: Packet):
        self.packet_buffer.append(packet)
        self.has_packet_buffer.set()

    def processSinglePacket(self, packet: Packet):
        if self.connectionState is not ConnState.CONNECTED:
            self.tryConnect(packet)
        else:
            self.processData(packet)

    def processPacketLoop(self):
        while True:
            self.has_packet_buffer.wait()
            if len(self.packet_buffer) != 0:
                self.processSinglePacket(self.packet_buffer.popleft())
                self.has_packet_buffer.clear()

    def processData(self, packet):
        logClient(packet.data)
        pass

    def handleTimeout(self):
        if self.connectionState is not ConnState.CONNECTED:
            if self.connectionState == ConnState.SYN:
                logClient(f"Timed out recv , cur state {self.connectionState}")
                self.ack_packet_fails += 1

                if self.ack_packet_fails >= 3:
                    logClient(
                        f"Timed out recv when in state {self.connectionState}, expecting SYN_ACK. Giving up")
                    exit(1)
                else:
                    synPacket = Packet(Header(ACK=1, SEQ=1, FLAGS=SYN_FLAG))
                    self.pushPacketToBuffer(synPacket)
            else:
                logClient(f"Invalid state: {self.connectionState}")
                exit(1)
        else:
            # Data RDP ...
            pass

    def receiveLoop(self):
        while True:
            try:
                self.sock.settimeout(SOCKET_TIMEOUT)
                message = self.sock.recv(self.buf_size)
                packet = Packet(message)
                self.pushPacketToBuffer(packet)
            except socket.timeout as e:
                self.handleTimeout()

        # Dont start a send unless there is something to send

    # def send(self, data=b'Hello, there', connect=False, ACK=False):
    #     flags = b'\x00'
    #     if connect:
    #         flags = bytes([flags[0] | SYN_FLAG[0]])
    #     if ACK:
    #         flags = bytes([flags[0] | ACK_FLAG[0]])

    #     if not connect:
    #         self.SEQ_NO += len(data)

    #     logClient(f"Flags: {bytearray(flags).hex()}")
    #     req = Header(FLAGS=flags, SEQ=self.SEQ_NO).return_header()+data
    #     self.sock.settimeout(SOCKET_TIMEOUT)
    #     self.sock.sendto(req, self.server_loc)

    # def receive(self):
    #     count = 0
    #     while(True):
    #         self.sock.settimeout(SOCKET_TIMEOUT)
    #         self.sock.setblocking(1)
    #         message = self.sock.recv(self.buf_size)

    #         self.message, *_ = self.strip_header(message)
    #         self.ACK_NO += 1
    #         logClient(f"Receiving Packet #:{self.ACK_NO} from server")

    # def strip_header(self, pack):
    #     # network = big endian
    #     ACK_NO = int.from_bytes(pack[0:4], byteorder='big')
    #     SEQ_NO = int.from_bytes(pack[4:8], byteorder='big')
    #     FLAGS = bytes([pack[8]])
    #     rwnd_size = int.from_bytes(pack[9:13], byteorder='big', signed=True)
    #     data = pack[13:]

    #     return data, ACK_NO, SEQ_NO, FLAGS, rwnd_size

    # def initialize_connection(self):
    #     fails = 0
    #     while True:
    #         if fails == 3:
    #             logClient(f"Failed to connect {fails} times. Giving up.")
    #             exit(1)

    #         logClient(f"Sending a connect request to server {self.server_loc}")
    #         self.send(data=b"", connect=True, ACK=False)
    #         try:
    #             self.sock.settimeout(SOCKET_TIMEOUT)
    #             message = self.sock.recv(self.buf_size)
    #             _, _, SEQ_NO, FLAGS, _ = self.strip_header(message)
    #         except socket.timeout as e:
    #             logClient("Timed out expecting ACK")
    #             fails += 1
    #             continue

    #         if bytes([FLAGS[0] & SYNACK_FLAG[0]]) == SYNACK_FLAG:
    #             logClient(f"Assigning SEQ_NO {SEQ_NO}")
    #             self.SEQ_NO = SEQ_NO
    #             logClient(f"Sending a connect ACK to server {self.server_loc}")
    #             logClient("Connection established")
    #             self.send(data=b"", connect=False, ACK=True)
    #             break
    #         else:
    #             logClient("Invalid connect response. Retrtying.")


if __name__ == "__main__":
    setupLogging()
    Client()
