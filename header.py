import struct

# SYN ACK FIN


class Header():
    def __init__(self, ACK=1, SEQ=1, FLAGS=b'\x00', rwnd=4, client=False):
        self.ACK_NO = ACK
        self.SEQ_NO = SEQ
        self.FLAGS = FLAGS
        self.rwnd_size = rwnd if client is False else -1

    def return_header(self):
        pack_string = '!IIcI'
        return struct.pack(pack_string, self.ACK_NO, self.SEQ_NO, self.FLAGS, self.rwnd_size)
