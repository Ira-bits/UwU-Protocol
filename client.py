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

        self.connectionState: ConnState = ConnState.NO_CONNECT
        self.packet_buffer = deque([])

        self.has_packet_buffer = threading.Event()
        self.ack_packet_fails = 0

        self.SEQ_NO = 0
        self.ACK_NO = 1

        self.process_packet_thread = threading.Thread(
            target=self.processPacketLoop)

        self.process_packet_thread.start()

        self.sendConnection()
        self.receiveLoop()

    def sendConnection(self):
        '''
        Send a SYN packet to server
        '''
        logClient("Starting client!")
        initialSynPacket = Packet(Header(1, 1, FLAGS=SYN_FLAG))
        self.connectionState = ConnState.SYN
        self.sock.sendto(initialSynPacket.as_bytes(), self.server_loc)

    def tryConnect(self, packet):
        '''
            Try to establish a connection or move across a connection state
        '''
        if self.connectionState is ConnState.NO_CONNECT:  # WTF
            logClient(f"Invalid state: Not connected!\n Exitting!")
            exit(1)

        elif self.connectionState is ConnState.SYN:
            if packet.header.has_flag(SYNACK_FLAG):

                self.SEQ_NO = packet.header.SEQ_NO
                self.connectionState = ConnState.SYNACK

                ackPacket = Packet(Header(1, self.SEQ_NO, ACK_FLAG))

                self.sock.sendto(ackPacket.as_bytes(), self.server_loc)
                self.connectionState = ConnState.CONNECTED

                logClient("Connection established (hopefully)")
            elif packet.header.has_flag(SYN_FLAG):

                logClient("Resending SYN Packet to server")
                initialSynPacket = Packet(Header(1, 1, FLAGS=SYN_FLAG))
                self.connectionState = ConnState.SYN
                self.sock.sendto(initialSynPacket.as_bytes(), self.server_loc)
        else:
            logClient(
                f"Expecting SYNACK flag at state SYN, got {packet.header.FLAGS}")

    def pushPacketToBuffer(self, packet: Packet):
        logClient(
            f"found packet in buffer, with flags: {bytearray(packet.header.FLAGS).hex()}")
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

                if self.ack_packet_fails >= MAX_FAIL_COUNT:
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
                message = self.sock.recv(
                    self.buf_size)
                if(message is not None):
                    packet = Packet(message)
                    message = None
                self.pushPacketToBuffer(packet)
            except socket.timeout as e:
                self.handleTimeout()


if __name__ == "__main__":
    setupLogging()
    Client()
