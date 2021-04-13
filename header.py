import struct

# SYN ACK FIN


class Header():
    def __init__(self, ACK=1, SEQ=1, FLAGS=b'\x00', rwnd=4):
        self.ACK_NO = ACK
        self.SEQ_NO = SEQ
        self.FLAGS = FLAGS
        self.rwnd = rwnd
        # self.rwnd_size = rwnd if client is False else -1

    def has_flag(flag: bytes) -> bool:
        return (bytes(self.FLAGS[0] & flag[0]) == self.FLAGS)

    def as_bytes(self) -> bytes:
        pack_string = '!IIcI'
        return struct.pack(pack_string, self.ACK_NO, self.SEQ_NO, self.FLAGS, self.rwnd_size)


class Packet():
    def __init__(self, header: Header, data: bytes = b""):
        self.header = header
        self.data = data
        self.len = len(header.as_bytes()) + len(data)

    def __init__(self, raw_packet: bytes):
        # network = big endian
        ACK_NO = int.from_bytes(raw_pack[0:4], byteorder="big")
        SEQ_NO = int.from_bytes(raw_pack[4:8], byteorder="big")
        FLAGS = bytes([raw_packet[8]])
        rwnd_size = int.from_bytes(
            raw_packet[9:13], byteorder="big", signed=True)
        data = bytes(raw_packet[13:])

        self.header = Header(ACK_NO, SEQ_NO, FLAGS, rwnd_size)
        self.data = data

    def as_bytes(self) -> bytes:
        return self.header.return_header() + self.data
