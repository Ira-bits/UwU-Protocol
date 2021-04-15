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
from sortedcontainers import SortedSet


def keySort(l: Packet):
    return l.header.SEQ_NO

# ----------start-------------
# peer1 sends: 0,1,2,3,4,5,6
# peer2 receives: 0,5,2,6
# peer2 ACKS: 0
# peer1 sends again: 1
# peer2 receives: 1
# peer2 ACKS: 2
# peer1 sends again: 3
# peer2 receives: 3
# peer2 ACKS: 3
# peer1 sends again: 4
# peer2 receives: 4
# peer2 ACKS: 6
# ----------end---------------


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

        self.has_receive_buffer = threading.Event()

        self.has_window_buffer = threading.Event()
        self.acquired_window_buffer = threading.Lock()

        self.ack_packet_fails = 0

        self.received_data_packets = SortedSet([], key=keySort)

        # client
        # 1      -> SYN
        # 2      -> SYNACK
        # 3001 2 -> ACK
        # 3000

        # Current sequence number stored by the client
        self.SEQ_NO = randint(1, 2536)

        # Current ack number stored by the client
        self.ACK_NO = 1

        self.BASE_RECEIVED_PACKET_SEQ_NO = -1

        self.process_packet_thread = threading.Thread(
            target=self.processPacketLoop)

        self.process_packet_thread.start()

        self.sendConnection()
        self.receive_thread = threading.Thread(target=self.receiveLoop)
        self.receive_thread.start()

    def fileTransfer(self, data):
        pack_len = 600

        if(len(data) > 600):
            packets = [Packet(Header(), data[i:min(i+pack_len, len(data))].encode())
                       for i in range(0, len(data), pack_len)]
            # print("Number of packets: ", len(packets))
        else:
            packets = [data]

        for packet in packets:
            self.temp_buffer.append(packet)

        self.fillWindowBuffer()
        # print("temp, ", len(self.temp_buffer))

    def sendConnection(self):
        '''
        Send a SYN packet to server
        '''

        logClient("Starting client!")
        initialSynPacket = Packet(
            Header(SEQ_NO=self.SEQ_NO, ACK_NO=self.ACK_NO, FLAGS=SYN_FLAG))
        self.connectionState = ConnState.SYN
        self.sock.sendto(initialSynPacket.as_bytes(), self.server_loc)

    def fillWindowBuffer(self):
        '''
         Update window, manage time
        '''
        self.acquired_window_buffer.acquire()
        while (len(self.window_packet_buffer) < self.rwnd_size):
            if(not self.temp_buffer):
                break
            packet = self.temp_buffer.popleft()

            self.SEQ_NO += 1
            seq_no = self.SEQ_NO.__str__()
            ack_no = self.ACK_NO.__str__()

            packet.header.SEQ_NO = int(seq_no)
            packet.header.ACK_NO = int(ack_no)

            self.window_packet_buffer.append(
                [packet, time.time(), PacketState.NOT_SENT])
        self.acquired_window_buffer.release()
        logClient("Notify WINDOW")
        self.has_window_buffer.set()

    def tryConnect(self, packet):
        '''
            Try to establish a connection or move across a connection state
        '''

        if self.connectionState is ConnState.NO_CONNECT:  # WTF
            logClient(f"Invalid state: Not connected!\n Exitting!")
            exit(1)

        elif self.connectionState is ConnState.SYN:
            if packet.header.has_flag(SYNACK_FLAG):

                logClient(
                    f"Received a SYNACK packet with SEQ:{packet.header.SEQ_NO} and ACK:{packet.header.ACK_NO}")
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
        else:
            if packet.header.has_flag(SYNACK_FLAG):

                logClient(
                    f"Received a SYNACK packet with SEQ:{packet.header.SEQ_NO} and ACK:{packet.header.ACK_NO}")
                self.ACK_NO = packet.header.SEQ_NO+1
                self.SEQ_NO = packet.header.ACK_NO

                self.connectionState = ConnState.SYNACK

                ackPacket = Packet(
                    Header(SEQ_NO=self.SEQ_NO, ACK_NO=self.ACK_NO, FLAGS=ACK_FLAG))

                self.sock.sendto(ackPacket.as_bytes(), self.server_loc)
                self.connectionState = ConnState.CONNECTED

                logClient("Connection established (again, hopefully)")

    def pushPacketToReceiveBuffer(self, packet: Packet):
        '''
            push a packet to the "received" buffer
        '''

        logClient(
            f"found packet in buffer, with flags: {bytearray(packet.header.FLAGS).hex()}")
        self.receive_packet_buffer.append(packet)
        self.has_receive_buffer.set()

    def processSinglePacket(self, packet: Packet):

        if self.connectionState is not ConnState.CONNECTED:
            self.tryConnect(packet)
        else:
            self.processData(packet)

    def processPacketLoop(self):
        '''
            main process
        '''
        while True:
            if self.connectionState != ConnState.CONNECTED:
                self.has_receive_buffer.wait()
                logClient("Waiting on receive buffer")

                self.processSinglePacket(
                    self.receive_packet_buffer.popleft())
                self.has_receive_buffer.clear()
            else:

                self.acquired_window_buffer.acquire()
                if not self.window_packet_buffer:
                    self.acquired_window_buffer.release()
                    logClient("Waiting on window")
                    self.has_window_buffer.wait()
                else:
                    self.acquired_window_buffer.release()

                for i in range(0, len(self.window_packet_buffer)):
                    # logClient("Waiting to acquire lock")

                    self.acquired_window_buffer.acquire()
                    # logClient("Acquired!")
                    if(i >= len(self.window_packet_buffer)):
                        # logClient("Releasing lock")
                        self.acquired_window_buffer.release()
                        break

                    packet, timestamp, status = self.window_packet_buffer[i]
                    if status == PacketState.NOT_SENT:
                        self.window_packet_buffer[i][2] = PacketState.SENT
                        logClient(
                            f"Sending Packet with SEQ#{packet.header.SEQ_NO} to server")
                        self.sock.sendto(packet.as_bytes(), self.server_loc)

                    elif status == PacketState.SENT:
                        if time.time() - timestamp > PACKET_TIMEOUT:
                            logClient(
                                f"Resending Packet with SEQ#{packet.header.SEQ_NO} to server")
                            self.sock.sendto(
                                packet.as_bytes(), self.server_loc)
                            self.window_packet_buffer[i][1] = time.time()

                    elif status == PacketState.ACKED and i == 0:
                        self.window_packet_buffer.popleft()
                        self.slideWindow()
                    # logClient("Releasing lock")
                    self.acquired_window_buffer.release()

    def processData(self, packet):
        '''
            Respond to a packet
        '''
        pass

    def slideWindow(self):
        if len(self.temp_buffer) != 0:
            self.window_packet_buffer.append(self.temp_buffer.popleft())
        else:
            self.has_window_buffer.clear()

    def updateWindow(self, packet):
        # Handle ack packet
        if packet.header.has_flag(SYNACK_FLAG):
            self.has_window_buffer.set()  # To allow client to read from receive buffer
            self.tryConnect(packet)
            self.has_window_buffer.clear()

        elif packet.header.has_flag(ACK_FLAG):

            ack_num = packet.header.ACK_NO
            logClient(
                f"Received an ACK packet of SEQ_NO:{packet.header.SEQ_NO} and ACK_NO: {packet.header.ACK_NO}")
            if len(self.window_packet_buffer) != 0:

                base_seq = self.window_packet_buffer[0][0].header.SEQ_NO
                index = ack_num - base_seq - 1
                logClient(
                    f"Updating packet {self.window_packet_buffer[index][0].header.SEQ_NO} to ACK'd")
                self.window_packet_buffer[index][2] = PacketState.ACKED

                '''
                if index == 0:
                    self.acquired_window_buffer.acquire()
                    self.window_packet_buffer.popleft()
                    self.slideWindow()
                    self.acquired_window_buffer.release()
                if len(self.window_packet_buffer) == 0:
                    self.has_window_buffer.clear()
                '''

        # Handle data packet
        else:

            self.received_data_packets.add(packet)
            seq_no = packet.header.SEQ_NO
            logClient(
                f"Received a DATA packet of SEQ_NO:{packet.header.SEQ_NO} and ACK_NO: {packet.header.ACK_NO}")
            ackPacket = Packet(Header(ACK_NO=seq_no+1,
                                      SEQ_NO=self.SEQ_NO,
                                      FLAGS=ACK_FLAG))

            self.sock.sendto(ackPacket.as_bytes(), self.server_loc)

    def handleHandshakeTimeout(self):
        '''
            Timeouts for handshake, fin
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
            # FIN ...
            pass

    def receiveLoop(self):
        '''
            Receive a packet
        '''
        while True:
            try:

                if(self.connectionState != ConnState.CONNECTED):
                    self.sock.settimeout(SOCKET_TIMEOUT)
                else:
                    self.sock.settimeout(None)

                message = self.sock.recv(self.buf_size)
                if(message is not None):
                    packet = Packet(message)
                    message = None

                if self.connectionState != ConnState.CONNECTED:
                    self.pushPacketToReceiveBuffer(packet)
                else:
                    self.updateWindow(packet)

            except socket.timeout as e:
                self.handleHandshakeTimeout()


if __name__ == "__main__":
    setupLogging()
    client = Client()
    while client.connectionState != ConnState.CONNECTED:
        pass
    time.sleep(0.1)
    client.fileTransfer("A"*1000)
    time.sleep(0.1)
    client.fileTransfer("A"*1000)
