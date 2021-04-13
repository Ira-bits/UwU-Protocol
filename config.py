from enum import Enum

# | syn | ack | fin |00000|
# |-----|-----|-----|-----|


SYN_FLAG = b'\x80'
ACK_FLAG = b'\x40'
SYNACK_FLAG = b'\xc0'
FIN_FLAG = b'\x20'
FINACK_FLAG = b'\x60'
SOCKET_TIMEOUT = 5.0


class ConnState(Enum):
    NO_CONNECT = 0
    SYN = 1
    SYNACK = 2
    CONNECTED = 3
