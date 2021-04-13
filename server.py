
import socket
import select
import threading
from threading import Timer

from header import Header, Packet
from lib import logServer, setupLogging
from config import *
from collections import deque


class Server:
    def __init__(self, addr="127.0.0.1", port=8000, r_wnd_size=4):
        self.buf_size = 1024
        self.sock = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.sock.bind((addr, port))

        self.addr = addr
        self.port = port
        self.connectionState: ConnState = ConnState.NO_CONNECT
        self.receive_wind = set()

        # For send()
        self.has_packet_buffer = threading.Event()
        self.packet_buffer = deque([])
        # self.send_buffer: None | Packet = None

        self.client_loc: None

        self.recv_thread = threading.Thread(
            target=self.receive)

        # start a receive process
        self.recv_thread.start()
        self.processPacketLoop()

    def pushPacketToBuffer(self, packet: Packet, location: tuple):
        '''
            Fills the buffer to send the packet
        '''
        self.packet_buffer.append((packet, location))
        self.has_packet_buffer.set()

    def processSinglePacket(self, packet: Packet, location: tuple):
        if self.connectionState is not ConnState.CONNECTED:
            self.tryConnect(packet, location)
        else:
            self.processRequest(packet, location)

    def processRequest(self, packet: Packet, location: tuple):
        pass

    def processPacketLoop(self):
        """
        Sends a packet
        """
        while True:
            self.has_packet_buffer.wait()

            # Sanity check
            if self.packet_buffer is None:
                logServer(
                    f"Execption: send() tried with empty send_buffer or client_loc")
                exit(1)

            packet, location = self.packet_buffer.popleft()
            logServer(
                f"Sending packet number: {0} of size {len(packet.data)} bytes.")

            self.processSinglePacket(packet, location)
            self.has_packet_buffer.clear()

    def tryConnect(self, packet: Packet, location: tuple):
        if self.connectionState is ConnState.NO_CONNECT:

            if packet.header.has_flag(SYN_FLAG):
                self.connectionState = ConnState.SYN
                logServer(
                    f"SYN_ACK being sent to client at {location}")

                synAckPacket = Packet(Header(1, 3000, SYNACK_FLAG))
                self.sock.sendto(synAckPacket.as_bytes(), location)
                self.connectionState = ConnState.SYNACK

            else:
                logServer(
                    f"Expected SYN_FLAG with NO_CONNECT state, got {packet.header.FLAGS} instead")

        elif self.connectionState is ConnState.SYNACK:

            if packet.header.has_flag(ACK_FLAG):
                self.connectionState = ConnState.CONNECTED
                logServer(f"State changed to connected")
            elif packet.header.has_flag(SYN_FLAG):
                self.connectionState = ConnState.SYN
                logServer(
                    f"SYN_ACK again being sent to client at {location}")

                synAckPacket = Packet(Header(1, 3000, SYNACK_FLAG))
                self.sock.sendto(packet.as_bytes(), location)
                self.connectionState = ConnState.SYNACK
            else:
                logServer(
                    f"Expected ACK_FLAG with SYNACK state, got {packet.header.FLAGS} instead")
        else:
            logServer(f"Invalid state {self.connectionState}")

    def receive(self):
        logServer(f"Listening for connections on port {self.port}")
        while True:
            # Server ALWAYS listens. No timeout for receive.
            self.sock.settimeout(None)
            bytes_addr_pair = self.sock.recvfrom(self.buf_size)
            req, location = bytes_addr_pair
            packet = Packet(req)
            self.pushPacketToBuffer(packet, location)


if __name__ == "__main__":
    setupLogging()
    Server()
