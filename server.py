
import socket
import select
import threading
from threading import Timer
from enum import Enum

from header import Header, Packet
from lib import logServer, setupLogging
from config import *


class ClientState:
    def __init__(self, client_loc, SEQ_NO, ACK_NO):
        self.client_loc = client_loc
        self.SEQ_NO = SEQ_NO
        self.ACK_NO = ACK_NO
        self.is_connected = False

# 1. no connection
# 2. syn happened
# 3. syn ack sent
# 4. ack received -> connected


class ConnState(Enum):
    NO_CONNECT = 0
    SYN = 1
    SYNACK = 2
    CONNECTED = 3


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
        self.has_send_buffer = threading.Event()
        self.send_buffer: None | Packet = None
        self.client_loc: None

        self.connect_ack_timeouts = 1
        self.recv_thread = threading.Thread(
            target=self.receive)

        # start a receive process
        self.recv_thread.start()
        self.sendLoop()

    def send(self, packet: Packet, location):
        '''
            Fills the buffer to send the packet
        '''
        self.send_buffer = packet
        self.send_location = location
        self.has_send_buffer.set()

    def sendLoop(self):
        """
        Sends a packet
        """
        while True:
            self.has_send_buffer.wait()

            # Sanity check
            if self.send_buffer is None or self.client_loc is None:
                logServer(
                    f"Execption: send() tried with empty send_buffer or client_loc")
                exit(1)

            logServer(
                f"Sending packet number: {0} of size {packet.len} bytes.")

            self.sock.sendto(packet.as_bytes(), client_loc)
            self.send_buffer = None
            self.send_location = None
            self.has_send_buffer.clear()

    # def appl_send(self, data, client_loc, FLAGS=b'\x00', SEQ_NO=1):
    #     """
    #     API for the application to send a file from server to client
    #     This function is not to be used internally except for testing
    #     Calls Server.send() for sending each packet
    #     modifies the entire buffer: splits into packets
    #     """
    #     logServer(
    #         f"Sending {len(data)} bytes to client with flags {bytearray(FLAGS).hex()}")
    #     packets = [data[i:min(len(data)-1, i+600)]
    #                for i in range(0, len(data), 600)]

    #     for packet in packets:
    #         self.send(packet, client_loc, FLAGS=FLAGS)
    #     pass

    # def recvfrom_timeout(self):
    #     ready = select.select([self.sock], [], [], SOCKET_TIMEOUT)
    #     if ready[0]:
    #         return self.sock.recvfrom(self.buf_size)

    #     return self.sock.timeout()

    # def handle_connect(self, request, client_loc):
    #     '''
    #     Handles a connect request from a client,
    #     assigns sequence numbers to a client
    #     '''

    #     if self.connect_ack_timeouts == 3:
    #         logClient(
    #             f"Failed to connect {self.connect_ack_timeouts} times. Giving up.")
    #         exit(1)

    #     req, ACK_NO, SEQ_NO, FLAGS, rwnd_size = self.strip_header(request)

    #     logServer(f"Flags: {FLAGS}")

    #     if bytes([FLAGS[0] & SYN_FLAG[0]]) != b'\x00':

    #         logServer(
    #             f"Received connect request from client {client_loc}")

    #         logServer(f"Assigning SEQ_NO {3000} to client {client_loc}")

    #         self.send(packet=b"", client_loc=client_loc,
    #                   FLAGS=SYNACK_FLAG, SEQ_NO=3000)

    #         try:
    #             self.sock.settimeout(SOCKET_TIMEOUT)
    #             message = self.sock.recv(self.buf_size)
    #         except socket.timeout as e:
    #             logServer("Timed out expecting ACK")
    #             self.connect_ack_timeouts += 1
    #             return self.handle_connect(request, client_loc)

    #         if bytes([FLAGS[0] & ACK_FLAG[0]]) != b'\x00':
    #             self.handle_connect_ACK(client_loc)
    #         else:
    #             logServer(f"Packet was not ack!")
    #         return True

    #     elif bytes([FLAGS[0] & ACK_FLAG[0]]) != b'\x00':
    #         self.is_connected = True
    #         self.handle_connect_ACK(client_loc)
    #         return True

    #     else:
    #         return False

    # def handle_connect_ACK(self, client_loc):
    #     logServer(f"Accepting connection from client: {client_loc}")
    #     pass

    def tryConnect(self, packet: Packet, location: tuple):
        if self.connectionState is ConnState.NO_CONNECT:
            if packet.header.has_flag(SYN_FLAG):
                self.connectionState = ConnState.SYN
                synAckPacket = Packet(Header(1, 3000, SYNACK_FLAG))
                self.send(packet, location)
                self.connectionState = ConnState.SYNACK

            else:
                logServer(
                    f"Expected SYN_FLAG with NO_CONNECT state, got {self.packet.header.FLAGS} instead")
        elif self.connectionState is ConnState.SYNACK:
            if packet.header.has_flag(ACK_FLAG):
                self.connectionState = ConnState.CONNECTED
                logServer(f"State changed to connected")
            else:
                logServer(
                    f"Expected ACK_FLAG with SYNACK state, got {self.packet.header.FLAGS} instead")
        else:
            logServer(f"Invalid state {self.connectionState}")

    def handlePacket(self, packet: Packet, location: tuple):
        if self.connectionState is not ConnState.CONNECTED:
            self.tryConnect(packet, location)
        else:
            self.handleRequest(packet, location)

    def receive(self):
        logServer(f"Listening for connections on port {self.port}")
        while True:
            self.sock.settimeout(None)
            bytes_addr_pair = self.sock.recvfrom(self.buf_size)
            req, location = bytes_addr_pair
            packet = Packet(req)
            self.handlePacket(packet, location)


if __name__ == "__main__":
    setupLogging()
    Server()
