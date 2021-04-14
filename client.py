import socket
from header import Header
import multiprocessing
from lib import logClient, setupLogging
from config import *
from threading import Timer
import threading
import time
from random import randint
from header import Header, Packet
from collections import deque
import copy


class Client:
    def __init__(self, serv_addr='127.0.0.1', serv_port=8000):
        self.sock = socket.socket(family=socket.AF_INET,
                                  type=socket.SOCK_DGRAM)

        self.rwnd_size = 100
        self.buf_size = 1024
        self.server_loc = (serv_addr, serv_port)

        self.connectionState: ConnState = ConnState.NO_CONNECT

        # use this buffer when a packet has been received, which requires to be sent
        self.receive_packet_buffer = deque([])
        # temp buffer for application to send packet
        self.temp_buffer = deque([])
        # the window
        self.window_packet_buffer = deque([])

        self.has_packet_buffer = threading.Event()
        self.has_temp_buffer = threading.Event()
        self.has_window_buffer = threading.Event()

        self.ack_packet_fails = 0

        # client
        # 1      -> SYN
        # 2      -> SYNACK
        # 3001 2 -> ACK
        # 3000

        self.SEQ_NO = randint(1, 2536)
        self.ACK_NO = 1

        self.process_packet_thread = threading.Thread(
            target=self.processPacketLoop)

        self.process_packet_thread.start()

        self.sendConnection()
        self.receive_thread = threading.Thread(target=self.receiveLoop)
        self.receive_thread.start()

    def appl_send(self, data):
        pack_len = 600

        if(len(data) > 600):
            packets = [Packet(Header(), data[i:min(i+pack_len, len(data))].encode())
                       for i in range(0, len(data), pack_len)]
            #print("Number of packets: ", len(packets))
        else:
            packets = [data]

        for packet in packets:
            self.temp_buffer.append(packet)
        #print("temp, ", len(self.temp_buffer))
        self.has_packet_buffer.set()

    def sendConnection(self):
        '''
        Send a SYN packet to server
        '''

        logClient("Starting client!")
        initialSynPacket = Packet(
            Header(SEQ_NO=self.SEQ_NO, ACK_NO=self.ACK_NO, FLAGS=SYN_FLAG))
        self.connectionState = ConnState.SYN
        self.sock.sendto(initialSynPacket.as_bytes(), self.server_loc)

    def send_function(self):
        '''
         Send packet, update window, manage time
        '''
        # manage time
        while len(self.window_packet_buffer) != 0 and self.window_packet_buffer[0][2] == True:
            self.window_packet_buffer.popleft()
        if not self.window_packet_buffer:
            logClient("Clearing packet buffer")
            self.has_packet_buffer.clear()

        while (len(self.window_packet_buffer) < self.rwnd_size):
            if(not self.temp_buffer):
                break
            packet = self.temp_buffer.popleft()

            self.SEQ_NO += 1
            seq_no = self.SEQ_NO.__str__()
            ack_no = self.ACK_NO.__str__()
            logClient(self.SEQ_NO)

            packet.header.SEQ_NO = int(seq_no)
            packet.header.ACK_NO = int(ack_no)

            self.window_packet_buffer.append((packet, time.time(), False))

    def tryConnect(self, packet):
        '''
            Try to establish a connection or move across a connection state
        '''

        if self.connectionState is ConnState.NO_CONNECT:  # WTF
            logClient(f"Invalid state: Not connected!\n Exitting!")
            exit(1)

        elif self.connectionState is ConnState.SYN:
            if packet.header.has_flag(SYNACK_FLAG):

                self.ACK_NO = packet.header.SEQ_NO+1
                self.SEQ_NO = packet.header.ACK_NO

                self.connectionState = ConnState.SYNACK

                ackPacket = Packet(
                    Header(SEQ_NO=self.SEQ_NO, ACK_NO=self.ACK_NO, FLAGS=ACK_FLAG))

                self.sock.sendto(ackPacket.as_bytes(), self.server_loc)
                self.connectionState = ConnState.CONNECTED

                logClient("Connection established (hopefully)")
            elif packet.header.has_flag(SYN_FLAG):

                logClient("Resending SYN Packet to server")
                initialSynPacket = Packet(
                    Header(SEQ_NO=self.SEQ_NO, ACK_NO=self.ACK_NO, FLAGS=SYN_FLAG))
                self.connectionState = ConnState.SYN
                self.sock.sendto(initialSynPacket.as_bytes(), self.server_loc)
        else:
            logClient(
                f"Expecting SYNACK flag at state SYN, got {packet.header.FLAGS}")

    def pushPacketToReceiveBuffer(self, packet: Packet):
        '''
            push a packet to the "received" buffer
        '''

        logClient(
            f"found packet in buffer, with flags: {bytearray(packet.header.FLAGS).hex()}")
        self.receive_packet_buffer.append(packet)
        self.has_packet_buffer.set()

    '''
    def pushPacketToWindow(self, packet):
        self.temp_buffer.append((packet, ))
        pass
    '''

    def processSinglePacket(self, packet: Packet):

        if self.connectionState is not ConnState.CONNECTED:
            self.tryConnect(packet)
        elif packet.header.has_flag(ACK_FLAG):
            self.updateWindow(packet)
        else:
            self.processData(packet)

    def processPacketLoop(self):
        '''
            main process
        '''
        while True:
            logClient("Waiting on packet buffer")
            self.has_packet_buffer.wait()
            if len(self.receive_packet_buffer) != 0:
                self.processSinglePacket(self.receive_packet_buffer.popleft())
                self.has_packet_buffer.clear()
            else:
                if (self.temp_buffer):
                    print("here")
                    self.send_function()
                for packetwrapper in self.window_packet_buffer:
                    print("here nibba")
                    if time.time() - packetwrapper[1] > PACKET_TIMEOUT:
                        logClient(
                            f"Resending Packet with SEQ#{packetwrapper[0].header.SEQ_NO} to server")
                        self.packet.sendto(
                            packetwrapper[0].as_bytes(), self.server_loc)

                for packetwrapper in self.window_packet_buffer:
                    packet, _, _ = packetwrapper
                    logClient(
                        f"Sending Packet with SEQ#{packet.header.SEQ_NO} to server")
                    self.sock.sendto(packet.as_bytes(), self.server_loc)

    def processData(self, packet):
        '''
            Respond to a packet
        '''
        logClient(packet.data)
        pass

    def handleTimeout(self):
        '''
            Timeouts for handshake, fin, and Selective repeat
        '''
        if self.connectionState is not ConnState.CONNECTED:
            if self.connectionState == ConnState.SYN:
                logClient(f"Timed out recv , cur state {self.connectionState}")
                self.ack_packet_fails += 1

                if self.ack_packet_fails >= MAX_FAIL_COUNT:
                    logClient(
                        f"Timed out recv when in state {self.connectionState}, expecting SYN_ACK. Giving up")
                    exit(1)
                else:
                    synPacket = Packet(
                        Header(SEQ_NO=self.SEQ_NO, ACK_NO=self.ACK_NO, FLAGS=SYN_FLAG))
                    self.pushPacketToReceiveBuffer(synPacket)
            else:
                logClient(f"Invalid state: {self.connectionState}")
                exit(1)
        else:
            # Data RDP ...
            pass

    def receiveLoop(self):
        '''
            Receive a packet
        '''
        while True:
            try:
                self.sock.settimeout(SOCKET_TIMEOUT)
                message = self.sock.recv(
                    self.buf_size)
                if(message is not None):
                    packet = Packet(message)
                    message = None
                self.pushPacketToReceiveBuffer(packet)
            except socket.timeout as e:
                self.handleTimeout()


if __name__ == "__main__":
    setupLogging()
    client = Client()
    while client.connectionState != ConnState.CONNECTED:
        pass
    time.sleep(0.1)
    client.appl_send("A"*1000)
