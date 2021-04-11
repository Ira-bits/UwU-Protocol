import socket
from header import Header
import multiprocessing
import logging


class Client:
    def __init__(self, serv_addr='127.0.0.1', serv_port=8000):
        self.sock = socket.socket(family=socket.AF_INET,
                                  type=socket.SOCK_DGRAM)
        self.buf_size = 1024
        self.server_loc = (serv_addr, serv_port)
        self.message = ''
        self.client_ip = None
        self.client_port = None

        self.SEQ_NO = None
        self.ACK_NO = 1

        self.recv_proc = multiprocessing.Process(
            target=self.receive)

        # Dont start a send unless there is something to send

    def request_handler(self, data: bytes, FLAGS=b'\x0a'):
        return Header(FLAGS=FLAGS).return_header()+data

    def send(self, data=b'Hello, there', connect=False, ACK=False):
        flags = b'\x00'
        if connect:
            flags = bytes([flags[0] | b'\x80'[0]])
            if ACK:
                flags = bytes([flags[0] | b'\x40'[0]])

            req = self.request_handler(data, FLAGS=flags)
            self.sock.sendto(req, self.server_loc)

        req = self.request_handler(data)
        self.sock.sendto(req, self.server_loc)

    def receive(self):
        count = 0
        while(True):
            message, _ = self.sock.recvfrom(self.buf_size)

            self.message, *_ = self.strip_header(message)
            self.ACK_NO += 1
            logging.info(f"Receiving Packet #:{count} from server")

    def strip_header(self, pack):
        # network = big endian
        ACK_NO = int.from_bytes(pack[0:4], byteorder='big')
        SEQ_NO = int.from_bytes(pack[4:8], byteorder='big')
        FLAGS = pack[8]
        rwnd_size = int.from_bytes(pack[9:13], byteorder='big', signed=True)
        data = pack[13:]

        return data, ACK_NO, SEQ_NO, FLAGS, rwnd_size

    def connect_to(self):
        logging.info(f"Sending a connect request to server {self.server_loc}")
        self.send(data=b"", connect=True, ACK=False)


def run_client():
    client = Client()
    return client
