
import socket
import select
import threading
from random import randint
from threading import Timer

from header import Header, Packet
from lib import logServer, setupLogging
from config import *
from collections import deque


class Server:
    def __init__(self, addr="127.0.0.1", port=8000, r_wnd_size=4):
        self.buf_size: int = 1024
        self.sock: socket.socket = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.sock.bind((addr, port))

        self.addr: str = addr
        self.port: int = port
        self.connectionState: ConnState = ConnState.NO_CONNECT
        self.receive_wind = set()

        self.synack_packet_fails = 0
        self.temp_connection_location = None

        self.SEQ_NO: int = randint(12, 1234)
        self.ACK_NO: int = 1
        # For send()
        self.has_receive_buffer: threading.Event = threading.Event()
        self.has_window_buffer: threading.Event = threading.Event()

        self.receive_buffer = deque([])
        self.window_packet_buffer = deque([])
        # self.send_buffer: None | Packet = None

        self.client_loc: None | tuple

        self.recv_thread = threading.Thread(
            target=self.receive)

        # start a receive process
        self.recv_thread.start()
        self.processPacketLoop()

    def fillWindowBuffer(self):
        '''
         Update window, manage time
        '''

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

            self.window_packet_buffer.append(
                [packet, time.time(), PacketState.NOT_SENT])

    def pushPacketToReceiveBuffer(self, packet: Packet, location: tuple):
        '''
            Fills the buffer to send the packet
        '''
        self.receive_buffer.append((packet, location))
        self.has_receive_buffer.set()

    def processSinglePacket(self, packet: Packet, location: tuple):
        if self.connectionState is not ConnState.CONNECTED:
            self.tryConnect(packet, location)
        else:
            logServer(
                f"Sending packet number: {0} of size {len(packet.data)} bytes.")
            self.processData(packet, location)

    def processData(self, packet: Packet, location: tuple):
        '''
            Respond to a packet
        '''

        # Handle ack packet
        if packet.header.has_flag(ACK_FLAG):
            ack_num = packet.header.ACK_NO
            while len(self.window_packet_buffer) \
                    and self.window_packet_buffer[0].header.ACK_NO <= ack_num:
                # Update all ACK'd packets
                self.window_packet_buffer.popleft()

            if len(self.window_packet_buffer) == 0:
                self.has_window_buffer.clear()

        # Handle data packet
        else:
            self.received_data_packets.add(packet)
            seq_no = packet.header.SEQ_NO

            if self.ACK_NO+1 == seq_no:
                # Data packet arrived in order
                # Check if the received_data_packets has the next packet also received
                while len(self.received_data_packets) != 0:
                    if self.receive_data_packets[0] == seq_no+1:
                        seq_no += 1
                        # TBD, send it to application layer
                        self.receive_data_packets.pop(0)
                    else:
                        break

                # Finally, ACK the last received packet
                ackPacket = Packet(
                    Header(ACK_NO=seq_no+1,
                           SEQ_NO=self.SEQ_NO,
                           FLAGS=ACK_FLAG))

                self.sock.sendto(ackPacket.as_bytes(), location)

            else:
                # Data packet arrived out of order.
                # Cache it
                if self.ACK_NO+1 < seq_no:
                    # ignore, data has been resent.
                    return

                self.received_data_packets.add(packet)
                # ACK the last received packet (self.ACK_NO)
                ackPacket = Packet(
                    Header(ACK_NO=self.ACK_NO+1,
                           SEQ_NO=self.SEQ_NO,
                           FLAGS=ACK_FLAG))

                self.sock.sendto(ackPacket.as_bytes(), location)

    def processPacketLoop(self):
        """
        Sends a packet
        """
        while True:
            if self.connectionState != ConnState.CONNECTED:
                self.has_receive_buffer.wait()
                logServer("Waiting on receive buffer")
                # Sanity check
                if self.receive_buffer is None:
                    logServer(
                        f"Execption: send() tried with empty send_buffer or client_loc")
                    exit(1)

                packet, location = self.receive_buffer.popleft()

                self.processSinglePacket(packet, location)

                self.has_receive_buffer.clear()
            else:
                if self.receive_packet_buffer:
                    self.processSinglePacket(
                        self.receive_packet_buffer.popleft())

                if not self.window_packet_buffer:
                    self.has_window_buffer.wait()

                if (self.temp_buffer):
                    self.fillWindowBuffer()

                for i in range(0, len(self.window_packet_buffer)):
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

    def tryConnect(self, packet: Packet, location: tuple):
        if self.connectionState is ConnState.NO_CONNECT:

            if packet.header.has_flag(SYN_FLAG):

                self.ACK_NO = packet.header.SEQ_NO+1

                self.connectionState = ConnState.SYN
                logServer(
                    f"SYN_ACK being sent to client at {location}")

                synAckPacket = Packet(
                    Header(SEQ_NO=self.SEQ_NO, ACK_NO=self.ACK_NO, FLAGS=SYNACK_FLAG))
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

                synAckPacket = Packet(
                    Header(SEQ_NO=self.SEQ_NO, ACK_NO=self.ACK_NO, FLAGS=SYNACK_FLAG))
                self.sock.sendto(packet.as_bytes(), location)
                self.connectionState = ConnState.SYNACK
            else:
                logServer(
                    f"Expected ACK_FLAG with SYNACK state, got {packet.header.FLAGS} instead")
        else:
            logServer(f"Invalid state {self.connectionState}")

    def handleHandshakeTimeout(self, location):
        '''
            Timeouts for handshake, fin
        '''
        if self.connectionState is not ConnState.CONNECTED:
            if self.connectionState == ConnState.SYNACK:
                logClient(f"Timed out recv , cur state {self.connectionState}")
                self.synack_packet_fails += 1

                if self.synack_packet_fails >= MAX_FAIL_COUNT:
                    logClient(
                        f"Timed out recv when in state {self.connectionState}, expecting SYN_ACK. Giving up")
                    exit(1)
                else:
                    synPacket = Packet(
                        Header(SEQ_NO=self.SEQ_NO, ACK_NO=self.ACK_NO, FLAGS=SYNACK_FLAG))
                    self.pushPacketToReceiveBuffer(
                        (synackPacket, self.temp_connection_location))
            else:
                logClient(f"Invalid state: {self.connectionState}")
                exit(1)
        else:
            # FIN ...
            pass

    def receive(self):
        logServer(f"Listening for connections on port {self.port}")
        while True:
            try:
                if(self.connectionState not in [ConnState.NOT_CONNECTED, ConnState.CONNECTED]):
                    self.sock.settimeout(SOCKET_TIMEOUT)
                else:
                    self.sock.settimeout(None)
                bytes_addr_pair = self.sock.recvfrom(self.buf_size)
                req, location = bytes_addr_pair
                packet = Packet(req)
                self.pushPacketToReceiveBuffer(packet, location)
            except socket.timeout as e:
                self.handleHandshakeTimeout()


if __name__ == "__main__":
    setupLogging()
    Server()
