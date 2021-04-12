import socket
from collections import deque
from header import Header
import multiprocessing
from lib import logServer
from config import *


class ClientState:
    def __init__(self, client_loc, SEQ_NO, ACK_NO):
        self.client_loc = client_loc
        self.SEQ_NO = SEQ_NO
        self.ACK_NO = ACK_NO


class Server:
    def __init__(self, addr="127.0.0.1", port=8000, r_wnd_size=4):
        self.buf_size = 1024
        self.sock = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.sock.bind((addr, port))

        self.addr = addr
        self.port = port
        #
        self.receive_wind = set()

        self.connection_close = False
        self.recv_proc = multiprocessing.Process(
            target=self.receive)

        # Dont start a send unless there is something to send

    def send(self, packet: bytes, client_loc: tuple, FLAGS=b'\x00', SEQ_NO=1):
        """
        Sends a packet
        """
        packet = Header(FLAGS=FLAGS, SEQ=SEQ_NO).return_header()+packet
        logServer(
            f"Sending packet number: {0} of size {len(packet)} bytes to client {client_loc[0]}:{client_loc[1]}")
        self.sock.sendto(packet, client_loc)

    def appl_send(self, data, client_loc, FLAGS=b'\x00', SEQ_NO=1):
        """
        API for the application to send a file from server to client
        This function is not to be used internally except for testing
        Calls Server.send() for sending each packet
        modifies the entire buffer: splits into packets
        """
        logServer(
            f"Sending {len(data)} bytes to client with flags {bytearray(FLAGS).hex()}")
        packets = [data[i:min(len(data)-1, i+600)]
                   for i in range(0, len(data), 600)]

        for packet in packets:
            self.send(packet, client_loc, FLAGS=FLAGS)
        pass

    def strip_header(self, pack):
        # network = big endian
        ACK_NO = int.from_bytes(pack[0:4], byteorder="big")
        SEQ_NO = int.from_bytes(pack[4:8], byteorder="big")
        FLAGS = bytes([pack[8]])
        rwnd_size = int.from_bytes(pack[9:13], byteorder="big", signed=True)
        data = bytes(pack[13:])

        return data, ACK_NO, SEQ_NO, FLAGS, rwnd_size

    def handle_connect(self, req, client_loc):
        '''
        Handles a connect request from a client,
        assigns sequence numbers to a client
        '''

        req, ACK_NO, SEQ_NO, FLAGS, rwnd_size = self.strip_header(req)

        logServer(f"Flags: {FLAGS}")

        if bytes([FLAGS[0] & SYN_FLAG[0]]) != b'\x00':

            if bytes([FLAGS[0] & ACK_FLAG[0]]) == b'\x00':

                logServer(
                    f"Received connect request from client {client_loc}")

                logServer(f"Assigning SEQ_NO {3000} to client {client_loc}")

                self.send(packet=b"", client_loc=client_loc,
                          FLAGS=SYNACK_FLAG, SEQ_NO=3000)

            return True

        elif bytes([FLAGS[0] & ACK_FLAG[0]]) != b'\x00':

            self.handle_connect_ACK(client_loc)
            return True

        else:
            return False

    def handle_connect_ACK(self, client_loc):
        logServer(f"Accepting connection from client: {client_loc}")
        pass

    def receive(self):
        while not self.connection_close:
            bytes_addr_pair = self.sock.recvfrom(
                self.buf_size
            )  # recvfrom has IP address
            # todo, fork a process for each client
            req, address = bytes_addr_pair
            connect = self.handle_connect(req, address)

            if connect != True:
                payload = ("A"*1000).encode()
                self.appl_send(payload, client_loc=address)
                #self.sock.sendto(payload, address)


def run_server():
    server = Server()
    return server
