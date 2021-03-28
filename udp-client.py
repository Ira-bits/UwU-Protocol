import socket
from header import Header


class Client:
    def __init__(self, serv_addr='127.0.0.1', serv_port=8000):
        self.sock = socket.socket(family=socket.AF_INET,
                                  type=socket.SOCK_DGRAM)
        self.buf_size = 1024
        self.server_loc = (serv_addr, serv_port)
        self.message = ''

    def request_handler(self, data):
        return Header(FLAGS=b'\x8a').return_header()+data

    def send(self, data=b'Hello, there'):
        req = self.request_handler(data)
        self.sock.sendto(req, self.server_loc)

    def rcv(self):
        message, _ = self.sock.recvfrom(self.buf_size)

        self.message, *_ = self.strip_header(message)

    def strip_header(self, pack):
        # network = big endian
        ACK_NO = int.from_bytes(pack[0:4], byteorder='big')
        SEQ_NO = int.from_bytes(pack[4:8], byteorder='big')
        FLAGS = pack[8]
        rwnd_size = int.from_bytes(pack[9:13], byteorder='big', signed=True)
        data = pack[13:]

        return data, ACK_NO, SEQ_NO, FLAGS, rwnd_size


def main():
    client = Client()
    client.send()
    client.rcv()
    print(client.message.decode('utf-8'))


if __name__ == '__main__':
    main()
